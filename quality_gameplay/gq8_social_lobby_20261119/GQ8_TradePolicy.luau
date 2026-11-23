--!strict
-- Pure, server-owned barter *proposal* policy. NOT inventory settlement.
-- Caller must use the existing single persistent Store owner and an idempotent two-player journal.
local M={}
local MAX=8
local DELAY=5
local TYPES={WEAPON=true,BEAST=true,GUARDIAN=true,ITEM=true,ABILITY=true,VEHICLE=true,COSMETIC=true,EGG=true}
local function side(trade,userId)
    if type(userId)~="number" then return nil end
    if userId==trade.a then return "a" end
    if userId==trade.b then return "b" end
    return nil
end
local function reset(trade,now)
    trade.revision+=1
    trade.aLocked=false;trade.bLocked=false
    trade.aConfirmed=false;trade.bConfirmed=false
    trade.readyAt=0
    trade.updatedAt=now
end
function M.new(tradeId,a,b,now)
    assert(type(tradeId)=="string" and #tradeId>=8 and #tradeId<=100,"BAD_TRADE_ID")
    assert(type(a)=="number" and type(b)=="number" and a>0 and b>0 and a~=b,"BAD_PARTICIPANTS")
    assert(type(now)=="number" and now>=0,"BAD_TIME")
    return {tradeId=tradeId,a=a,b=b,revision=0,aOffer={},bOffer={},
        aLocked=false,bLocked=false,aConfirmed=false,bConfirmed=false,
        readyAt=0,updatedAt=now,finished=false}
end
-- inventory is a trusted SERVER inventory snapshot, keyed by unique item instance ID.
-- Never accept client-provided metadata, ownership, tradeable, equip flags or versions.
function M.setOffer(trade,userId,ids,inventory,now)
    local s=side(trade,userId)
    if not s or trade.finished then return false,"TRADE_NOT_ACTIVE" end
    if type(ids)~="table" or #ids>MAX or type(inventory)~="table" then return false,"INVALID_OFFER" end
    if type(now)~="number" or now<trade.updatedAt then return false,"INVALID_TIME" end
    local seen={} local offer={}
    for _,id in ipairs(ids) do
        if type(id)~="string" or #id<3 or #id>120 or seen[id] then return false,"DUPLICATE_OR_INVALID_ITEM" end
        seen[id]=true
        local item=inventory[id]
        if type(item)~="table" or item.ownerUserId~=userId or not TYPES[item.category]
            or item.tradeable~=true or item.bound==true or item.equipped==true
            or item.escrowLocked==true or item.starterProtected==true or item.paidOrigin==true
            or type(item.version)~="number" or item.version<0 then
            return false,"ITEM_NOT_TRADABLE"
        end
        table.insert(offer,{id=id,version=item.version,category=item.category})
    end
    if s=="a" then trade.aOffer=offer else trade.bOffer=offer end
    reset(trade,now)
    return true,trade.revision
end
function M.lock(trade,userId,revision,now)
    local s=side(trade,userId)
    if not s or trade.finished or revision~=trade.revision then return false,"REVISION_MISMATCH" end
    if #trade.aOffer==0 or #trade.bOffer==0 then return false,"BOTH_SIDES_MUST_OFFER" end
    if type(now)~="number" or now<trade.updatedAt then return false,"INVALID_TIME" end
    if s=="a" then trade.aLocked=true else trade.bLocked=true end
    if trade.aLocked and trade.bLocked and trade.readyAt==0 then trade.readyAt=now+DELAY end
    return true,trade.readyAt
end
function M.confirm(trade,userId,revision,now)
    local s=side(trade,userId)
    if not s or trade.finished or revision~=trade.revision then return false,"REVISION_MISMATCH" end
    if not (trade.aLocked and trade.bLocked) or trade.readyAt==0 then return false,"NOT_LOCKED" end
    if type(now)~="number" or now<trade.readyAt then return false,"REVIEW_COUNTDOWN" end
    if s=="a" then trade.aConfirmed=true else trade.bConfirmed=true end
    return true,(trade.aConfirmed and trade.bConfirmed)
end
local function verifyOffer(offer,ownerId,inventory)
    if type(inventory)~="table" then return false end
    for _,slot in ipairs(offer) do
        local item=inventory[slot.id]
        if type(item)~="table" or item.ownerUserId~=ownerId or item.version~=slot.version
            or item.category~=slot.category or item.tradeable~=true or item.bound==true
            or item.equipped==true or item.escrowLocked==true or item.starterProtected==true
            or item.paidOrigin==true then
            return false
        end
    end
    return true
end
-- Returns only an immutable-intent PLAN. No actual inventory is ever changed here.
-- Do not call a client Remote to execute it; existing Store performs durable journal+session lock.
function M.proposeSettlement(trade,inventoryA,inventoryB)
    if trade.finished or not trade.aConfirmed or not trade.bConfirmed then return false,"NOT_CONFIRMED" end
    if not verifyOffer(trade.aOffer,trade.a,inventoryA) or not verifyOffer(trade.bOffer,trade.b,inventoryB) then
        return false,"INVENTORY_CHANGED"
    end
    local sendA={} local sendB={} local seen={}
    for _,v in ipairs(trade.aOffer) do
        if seen[v.id] then return false,"DUPLICATE_GLOBAL_INSTANCE" end
        seen[v.id]=true
        table.insert(sendA,{id=v.id,version=v.version})
    end
    for _,v in ipairs(trade.bOffer) do
        if seen[v.id] then return false,"DUPLICATE_GLOBAL_INSTANCE" end
        seen[v.id]=true
        table.insert(sendB,{id=v.id,version=v.version})
    end
    return true,{tradeId=trade.tradeId,revision=trade.revision,
        fromA=trade.a,toB=trade.b,itemsA=sendA,itemsB=sendB,
        requiresExistingStoreAtomicJournal=true,alreadySettled=false}
end
function M.markSettledAfterStoreReceipt(trade,receiptId)
    -- This must be invoked only by the existing trusted Store after confirmed durable commit.
    if trade.finished or type(receiptId)~="string" or #receiptId<8 then return false end
    trade.finished=true
    return true
end
function M.cancel(trade,userId)
    if not side(trade,userId) or trade.finished then return false end
    trade.finished=true;return true
end
return M
