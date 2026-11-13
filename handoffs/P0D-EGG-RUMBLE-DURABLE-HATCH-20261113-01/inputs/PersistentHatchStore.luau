--!strict
-- EGG RAID RUMBLE: persistent owned/free-hatch/equip data server-only.
-- Atomic UpdateAsync transactions, NO yielding callback and no SetAsync overwrites.
-- This module is intentionally separate from canonical Game and original #275 rules.
-- The actual DataStore handle is injected by Game; safe to exercise with mocked handle.
local Store={}
Store.SCHEMA=1
Store.MAX_RECEIPTS=2048 -- fail closed when full; NEVER silently evict replay keys
Store.ITEMS={starter_scout=true,forest_scout=true,star_scout=true}
local function integer(v:any)
    return type(v)=="number" and v==v and v~=math.huge and v~=-math.huge
        and v==math.floor(v)
end
local function userKey(uid:any)
    if not integer(uid) or uid<=0 or uid>999999999999999 then return nil end
    return "U_"..tostring(uid)
end
local function validReceipt(receipt:any)
    return type(receipt)=="string" and #receipt>=12 and #receipt<=110
        and receipt:match("^S[%w%-_]+:%d+$")~=nil
end
local function copyMap(map:any)
    local out={}
    for k,v in pairs(map) do out[k]=v end
    return out
end
function Store.blank()
    return {
        schema=Store.SCHEMA,revision=0,
        owned={starter_scout=1},
        receipts={},
        equipped="starter_scout"
    }
end
function Store.validate(raw:any)
    if type(raw)~="table" or raw.schema~=Store.SCHEMA
        or not integer(raw.revision) or raw.revision<0
        or type(raw.owned)~="table" or type(raw.receipts)~="table"
        or type(raw.equipped)~="string" then return false end
    local receiptn=0
    for item,amount in pairs(raw.owned) do
        if Store.ITEMS[item]~=true or not integer(amount)
            or amount<0 or amount>100000 then return false end
    end
    if raw.owned.starter_scout~=1 then return false end
    if Store.ITEMS[raw.equipped]~=true
        or not raw.owned[raw.equipped]
        or raw.owned[raw.equipped]<1 then return false end
    for receipt,item in pairs(raw.receipts) do
        receiptn+=1
        if receiptn>Store.MAX_RECEIPTS or not validReceipt(receipt)
            or Store.ITEMS[item]~=true or item=="starter_scout" then return false end
    end
    return true
end
local function normalized(raw:any)
    if raw==nil then return Store.blank() end
    if not Store.validate(raw) then return nil end
    return {
        schema=Store.SCHEMA,revision=raw.revision,
        owned=copyMap(raw.owned),receipts=copyMap(raw.receipts),
        equipped=raw.equipped
    }
end
function Store.toRulesRecord(persistent:any)
    if not Store.validate(persistent) then return nil end
    local discovered={starter_scout=true}
    for item,amount in pairs(persistent.owned) do
        if amount>=1 then discovered[item]=true end
    end
    -- RewardEquipRules V1 receipts are server-local numeric round epochs.
    -- NEVER smuggle GLOBAL string receipt identifiers into that in-memory module.
    -- Only this Store has the durable global idempotency receipt ledger.
    return {
        owned=copyMap(persistent.owned),
        discovered=discovered,
        equipped=persistent.equipped,
        receipts={}
    }
end
function Store.grantTransition(raw:any,receipt:any,item:any)
    if not validReceipt(receipt) or Store.ITEMS[item]~=true
        or item=="starter_scout" then return nil,"INVALID_GRANT" end
    local state=normalized(raw)
    if not state then return nil,"CORRUPT_RECORD" end
    if state.receipts[receipt] then
        return state,"ALREADY_GRANTED" -- do not increment and do not silently reroll
    end
    local n=0
    for _ in pairs(state.receipts) do n+=1 end
    if n>=Store.MAX_RECEIPTS then
        return nil,"RECEIPT_LEDGER_FULL" -- explicit migration required
    end
    local count=state.owned[item] or 0
    if count>=100000 then return nil,"ITEM_COUNT_LIMIT" end
    state.receipts[receipt]=item
    state.owned[item]=count+1
    state.revision+=1
    return state,"GRANTED"
end
function Store.equipTransition(raw:any,item:any)
    if type(item)~="string" or Store.ITEMS[item]~=true then
        return nil,"UNKNOWN_ITEM"
    end
    local state=normalized(raw)
    if not state then return nil,"CORRUPT_RECORD" end
    if not state.owned[item] or state.owned[item]<1 then return nil,"NOT_OWNED" end
    if state.equipped==item then return state,"ALREADY_EQUIPPED" end
    state.equipped=item
    state.revision+=1
    return state,"EQUIPPED"
end
-- Avoid GetAsync's cache when possible: caller passes DataStoreGetOptions.UseCache=false.
function Store.load(store:any,uid:any,options:any)
    local key=userKey(uid)
    if key==nil or not store then return false,nil,"INVALID_STORE_OR_PLAYER" end
    local ok,raw=pcall(function()
        if options~=nil then return store:GetAsync(key,options) end
        return store:GetAsync(key)
    end)
    if not ok then return false,nil,"READ_FAILED" end
    local current=normalized(raw)
    if not current then return false,nil,"CORRUPT_RECORD" end
    return true,current,"LOADED"
end
function Store.grant(store:any,uid:any,receipt:any,item:any)
    local key=userKey(uid)
    if key==nil or not store or not validReceipt(receipt)
        or Store.ITEMS[item]~=true or item=="starter_scout" then
        return false,nil,"INVALID_GRANT"
    end
    -- Callback can be called multiple times by Roblox. It MUST be pure and
    -- MUST NOT do task.wait(), server RNG, Remote or external side effects.
    local ok,updated=pcall(function()
        return store:UpdateAsync(key,function(original)
            local nextRecord=Store.grantTransition(original,receipt,item)
            return nextRecord -- nil: abort corrupt/ledger-full transaction
        end)
    end)
    if not ok then return false,nil,"WRITE_UNCONFIRMED" end
    if not Store.validate(updated) then return false,nil,"WRITE_NOT_CONFIRMED" end
    local confirmed=updated.receipts[receipt]
    if Store.ITEMS[confirmed]~=true then return false,nil,"WRITE_NOT_CONFIRMED" end
    if confirmed~=item then return true,updated,"ALREADY_GRANTED_DIFFERENT_ITEM" end
    return true,updated,"PERSISTED_OR_ALREADY_GRANTED"
end
function Store.equip(store:any,uid:any,item:any)
    local key=userKey(uid)
    if key==nil or not store or Store.ITEMS[item]~=true then
        return false,nil,"INVALID_EQUIP"
    end
    local ok,updated=pcall(function()
        return store:UpdateAsync(key,function(original)
            local nextRecord=Store.equipTransition(original,item)
            return nextRecord
        end)
    end)
    if not ok then return false,nil,"WRITE_UNCONFIRMED" end
    if not Store.validate(updated) or updated.equipped~=item then
        return false,nil,"EQUIP_NOT_CONFIRMED"
    end
    return true,updated,"EQUIPPED_PERSISTED"
end
function Store.makeReceipt(sessionId:any,roundId:any)
    if type(sessionId)~="string" or #sessionId<12 or #sessionId>76
        or not sessionId:match("^[%w%-_]+$")
        or not integer(roundId) or roundId<1 or roundId>99999999 then return nil end
    local id="S"..sessionId..":"..tostring(roundId)
    if not validReceipt(id) then return nil end
    return id
end
return Store
