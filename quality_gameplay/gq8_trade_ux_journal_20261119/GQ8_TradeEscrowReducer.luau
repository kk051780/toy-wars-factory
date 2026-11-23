--!strict
-- Pure ONE-PROFILE step reducer for an EXISTING single authoritative Store writer.
-- NOT a DataStore, Remote, player trade service, escrow settlement or UI.
-- Intended to run inside Store's atomic UpdateAsync callback, after writer has
-- verified valid profile session lock + durable trade coordinator journal.
local Escrow={}
local ALLOWED={WEAPON=true,BEAST=true,GUARDIAN=true,ITEM=true,ABILITY=true,VEHICLE=true,COSMETIC=true,EGG=true}
local MAX_VERSION=1000000000
local function validId(id)
 return type(id)=="string" and #id>=3 and #id<=120
end
local function safeNum(n)
 return type(n)=="number" and n>=0 and n<=MAX_VERSION and n==math.floor(n)
end
local function safeUser(n)
 return type(n)=="number" and n>0 and n<=9007199254740991 and n==math.floor(n)
end
local function ownerAndOffers(plan,owner)
 if type(plan)~="table" or type(plan.tradeId)~="string" or #plan.tradeId<8
    or #plan.tradeId>100 or not safeNum(plan.revision) or type(owner)~="number"
    or owner~=math.floor(owner) or not safeUser(owner)
    or not safeUser(plan.fromA) or not safeUser(plan.toB)
    or plan.fromA==plan.toB or type(plan.itemsA)~="table"
    or type(plan.itemsB)~="table" or #plan.itemsA<1 or #plan.itemsA>8
    or #plan.itemsB<1 or #plan.itemsB>8
    or plan.requiresExistingStoreAtomicJournal~=true or plan.alreadySettled~=false
 then return nil,nil end
 if owner==plan.fromA then return plan.itemsA,plan.itemsB end
 if owner==plan.toB then return plan.itemsB,plan.itemsA end
 return nil,nil
end
local function fingerprint(plan)
 local result={plan.tradeId,":",tostring(plan.revision),":",tostring(plan.fromA),":",tostring(plan.toB)}
 local ids={}
 for n,offer in ipairs({plan.itemsA,plan.itemsB}) do
  result[#result+1]=":"..tostring(n)
  for _,slot in ipairs(offer) do
   if type(slot)~="table" or not validId(slot.id) or not safeNum(slot.version)
      or slot.version>=MAX_VERSION or ids[slot.id] then return nil end
   ids[slot.id]=true
   result[#result+1]="|"..tostring(#slot.id)..":"..slot.id..":"..tostring(slot.version)
  end
 end
 return table.concat(result)
end
local function cloneItem(v)
 local n={}
 for k,val in pairs(v) do n[k]=val end -- preserve *all* existing item attributes
 return n
end
local function cloneRecord(raw,owner)
 if type(raw)~="table" or raw.userId~=owner or not safeNum(raw.revision)
    or type(raw.inventory)~="table" or type(raw.tradeState)~="table" then
  return nil
 end
 local new={}
 for k,val in pairs(raw) do new[k]=val end -- preserve wallet/progression/receipts etc!
 new.inventory={};new.tradeState={}
 for k,item in pairs(raw.inventory) do
  if not validId(k) or type(item)~="table" then return nil end
  new.inventory[k]=cloneItem(item)
 end
 for id,s in pairs(raw.tradeState) do
  if type(id)~="string" or type(s)~="table" then return nil end
  local t={fingerprint=s.fingerprint,phase=s.phase,outgoing={},receipt=s.receipt}
  if type(s.outgoing)~="table" then return nil end
  for key,v in pairs(s.outgoing) do
   if not validId(key) or type(v)~="table" then return nil end
   t.outgoing[key]=cloneItem(v)
  end
  new.tradeState[id]=t
 end
 return new
end
local function safeTradable(item,id,owner,version)
 return type(item)=="table" and item.id==id and item.ownerUserId==owner
    and item.version==version and safeNum(item.version)
    and item.version<MAX_VERSION and ALLOWED[item.category]==true
    and validId(item.itemDefId) and item.originKind=="FREE_EARNED"
    and item.paidOrigin==false and item.tradeable==true
    and item.bound==false and item.equipped==false
    and item.escrowLocked==false and item.tradeIncomingLocked~=true
    and item.starterProtected==false
end
local function clash(raw,id,tradeId)
 for tid,st in pairs(raw.tradeState) do
  if tid~=tradeId and (st.phase=="RESERVED" or st.phase=="ESCROWED") then
   for key in pairs(st.outgoing) do if key==id then return true end end
   -- An inventory record involved in an active reservation cannot be
   -- inferred from stale metadata. Caller must hold the profile session lock.
  end
 end
 return false
end
-- A can PREPARE before B, but cannot credit until BOTH ESCROW writes persisted.
-- Do not credit from a copy of only one side's local in-memory inventory.
function Escrow.prepare(raw,plan,owner)
 local mine=ownerAndOffers(plan,owner)
 local fp=fingerprint(plan)
 if not mine or not fp then return nil,"BAD_PLAN" end
 local nextRecord=cloneRecord(raw,owner)
 if not nextRecord then return nil,"UNSUPPORTED_PROFILE_SCHEMA" end
 local existing=nextRecord.tradeState[plan.tradeId]
 if existing then
  if existing.fingerprint~=fp then return nil,"REPLAY_PLAN_CONFLICT" end
  if existing.phase=="RESERVED" or existing.phase=="ESCROWED" or existing.phase=="CREDITED" then
   return nextRecord,"ALREADY_PREPARED"
  end
  return nil,"UNKNOWN_PHASE"
 end
 for _,slot in ipairs(mine) do
  local item=nextRecord.inventory[slot.id]
  if not safeTradable(item,slot.id,owner,slot.version) or clash(nextRecord,slot.id,plan.tradeId) then
   return nil,"ITEM_NOT_OWNED_FREE_UNEQUIPPED"
  end
 end
 local reserved={}
 for _,slot in ipairs(mine) do
  local item=nextRecord.inventory[slot.id]
  item.escrowLocked=true
  reserved[slot.id]=cloneItem(item)
 end
 nextRecord.tradeState[plan.tradeId]={fingerprint=fp,phase="RESERVED",outgoing=reserved}
 nextRecord.revision+=1
 return nextRecord,"PREPARED"
end
function Escrow.escrow(raw,plan,owner)
 local mine=ownerAndOffers(plan,owner)
 local fp=fingerprint(plan)
 if not mine or not fp then return nil,"BAD_PLAN" end
 local nextRecord=cloneRecord(raw,owner)
 if not nextRecord then return nil,"UNSUPPORTED_PROFILE_SCHEMA" end
 local st=nextRecord.tradeState[plan.tradeId]
 if not st or st.fingerprint~=fp then return nil,"NOT_PREPARED_OR_CONFLICT" end
 if st.phase=="ESCROWED" or st.phase=="CREDITED" or st.phase=="FINALIZED" then
  return nextRecord,"ALREADY_ESCROWED"
 end
 if st.phase~="RESERVED" then return nil,"UNKNOWN_PHASE" end
 for _,slot in ipairs(mine) do
  local owned=nextRecord.inventory[slot.id]
  local record=st.outgoing[slot.id]
  if not owned or not record or owned.ownerUserId~=owner or owned.version~=slot.version
    or owned.escrowLocked~=true or owned.paidOrigin~=false or owned.originKind~="FREE_EARNED"
    or owned.equipped~=false or owned.bound~=false or owned.starterProtected~=false
    or owned.tradeIncomingLocked==true or owned.tradeable~=true
    or owned.category~=record.category or owned.itemDefId~=record.itemDefId
    or record.id~=slot.id or record.version~=slot.version then
    return nil,"ESCROW_SOURCE_CHANGED"
  end
 end
 for _,slot in ipairs(mine) do
  nextRecord.inventory[slot.id]=nil
 end
 st.phase="ESCROWED"
 nextRecord.revision+=1
 return nextRecord,"ESCROWED"
end
function Escrow.receipt(raw,plan,owner)
 local mine=ownerAndOffers(plan,owner)
 local fp=fingerprint(plan)
 if not mine or not fp then return nil,"BAD_PLAN" end
 if type(raw)~="table" or type(raw.tradeState)~="table" then return nil,"NO_PROFILE" end
 local st=raw.tradeState[plan.tradeId]
 if type(st)~="table" or st.fingerprint~=fp or
    (st.phase~="ESCROWED" and st.phase~="CREDITED" and st.phase~="FINALIZED") then
  return nil,"ESCROW_NOT_DURABLE"
 end
 local items={}
 for _,slot in ipairs(mine) do
  local item=st.outgoing[slot.id]
  if not item or item.id~=slot.id or item.ownerUserId~=owner or item.version~=slot.version
     or item.originKind~="FREE_EARNED" or item.paidOrigin~=false then
   return nil,"ESCROW_PAYLOAD_CHANGED"
  end
  items[#items+1]=cloneItem(item)
 end
 return {tradeId=plan.tradeId,fingerprint=fp,owner=owner,items=items},"ESCROW_READ_ONLY"
end
-- CREDIT requires both persisted counterpart escrow receipts + a durable,
-- server-only coordinator stamp that exactly binds this plan fingerprint.
-- Caller MUST verify actual DataStore persistence and session locks separately.
-- No allocation or mutation of account data if *any* check fails.
function Escrow.credit(raw,plan,owner,otherReceipt,coordinatorReceipt)
 local mine,incoming=ownerAndOffers(plan,owner)
 local fp=fingerprint(plan)
 if not mine or not fp then return nil,"BAD_PLAN" end
 if type(coordinatorReceipt)~="table" or coordinatorReceipt.tradeId~=plan.tradeId
     or coordinatorReceipt.fingerprint~=fp or
     coordinatorReceipt.bothEscrowPersisted~=true or
     coordinatorReceipt.sessionLocksHeld~=true or
     not validId(coordinatorReceipt.durableId) then return nil,"NO_DURABLE_TWO_SIDED_COMMIT" end
 if type(otherReceipt)~="table" or otherReceipt.tradeId~=plan.tradeId
     or otherReceipt.fingerprint~=fp
     or otherReceipt.owner==(owner) or
     otherReceipt.owner~=(owner==plan.fromA and plan.toB or plan.fromA)
     or type(otherReceipt.items)~="table" or #otherReceipt.items~=#incoming then
   return nil,"INVALID_COUNTERPART_ESCROW"
 end
 local nextRecord=cloneRecord(raw,owner)
 if not nextRecord then return nil,"UNSUPPORTED_PROFILE_SCHEMA" end
 local st=nextRecord.tradeState[plan.tradeId]
 if not st or st.fingerprint~=fp or (st.phase~="ESCROWED" and st.phase~="CREDITED") then
  return nil,"SELF_ESCROW_NOT_PERSISTED"
 end
 if st.phase=="CREDITED" or st.phase=="FINALIZED" then
  if st.receipt==coordinatorReceipt.durableId then return nextRecord,"ALREADY_CREDITED" end
  return nil,"CREDIT_RECEIPT_CONFLICT"
 end
 for i,slot in ipairs(incoming) do
  local other=otherReceipt.items[i]
  if not other or other.id~=slot.id or other.version~=slot.version
     or other.ownerUserId~=otherReceipt.owner or
     other.originKind~="FREE_EARNED" or other.paidOrigin~=false
     or not ALLOWED[other.category] or not validId(other.itemDefId)
     or nextRecord.inventory[slot.id] then return nil,"INCOMING_ITEM_INVALID_OR_DUPLICATE" end
 end
 for _,other in ipairs(otherReceipt.items) do
  local newItem=cloneItem(other)
  newItem.ownerUserId=owner
  newItem.version+=1
  newItem.escrowLocked=false
  newItem.tradeIncomingLocked=true -- do not equip/retrade until BOTH credited and durable COMMIT
  nextRecord.inventory[newItem.id]=newItem
 end
 st.phase="CREDITED"
 st.receipt=coordinatorReceipt.durableId
 nextRecord.revision+=1
 return nextRecord,"CREDITED"
end
-- Release received items ONLY after the single durable coordinator has completed
-- both Credit_A and Credit_B, then COMMIT. Fail closed if either account is pending.
function Escrow.finalize(raw,plan,owner,committed)
 local mine,incoming=ownerAndOffers(plan,owner)
 local fp=fingerprint(plan)
 if not mine or not fp or type(committed)~="table" or
    committed.tradeId~=plan.tradeId or committed.fingerprint~=fp or
    committed.globalCommitPersisted~=true or not validId(committed.durableId) then
  return nil,"NO_DURABLE_GLOBAL_COMMIT"
 end
 local nextRecord=cloneRecord(raw,owner)
 if not nextRecord then return nil,"UNSUPPORTED_PROFILE_SCHEMA" end
 local st=nextRecord.tradeState[plan.tradeId]
 if not st or st.fingerprint~=fp or st.receipt~=committed.durableId then
  return nil,"CREDIT_NOT_CONFIRMED"
 end
 if st.phase=="FINALIZED" then return nextRecord,"ALREADY_FINALIZED" end
 if st.phase~="CREDITED" then return nil,"NOT_CREDITED" end
 for _,slot in ipairs(incoming) do
  local item=nextRecord.inventory[slot.id]
  if not item or item.ownerUserId~=owner or item.id~=slot.id
   or item.version~=slot.version+1 or item.tradeIncomingLocked~=true then
    return nil,"CREDIT_LOCKED_ITEM_MISSING"
  end
 end
 for _,slot in ipairs(incoming) do
  nextRecord.inventory[slot.id].tradeIncomingLocked=false
 end
 st.phase="FINALIZED";nextRecord.revision+=1
 return nextRecord,"FINALIZED"
end
return Escrow
