--!strict
-- EGG RAID RUMBLE: persistent owned/free-hatch/equip data server-only.
-- Atomic UpdateAsync transactions, NO yielding callback and no SetAsync overwrites.
-- This module is intentionally separate from canonical Game and original #275 rules.
-- The actual DataStore handle is injected by Game; safe to exercise with mocked handle.
local Store={}
-- Original #281 117-native-tested purely server-only policy (unchanged source).
local Progression=require(script.Parent:WaitForChild("ProgressionRules"))
Store.MAX_PROGRESS_ROUNDS=Progression.MAX_RECORDED_ROUNDS
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
-- Original immutable #281 policy permits integers < 100 million. Roblox real
-- UserIds can exceed that ceiling; Datastore still uses FULL real UserId.
-- This normalized value is only a per-record policy identity, never a key.
function Store.policyUserId(realId:any)
    if not integer(realId) or realId<=0 or realId>999999999999999 then return nil end
    return (realId % 99999998)+1
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

local function safeProgressRecord(progress:any): boolean
    if progress==nil then return true end -- schema1 pre-XP users migrate at first legitimate settlement
    if type(progress)~="table" or not integer(progress.level)
        or progress.level<1 or progress.level>Progression.PLAYER_MAX_LEVEL
        or not integer(progress.xp) or progress.xp<0
        or not integer(progress.settledCount) or progress.settledCount<0
        or progress.settledCount>Store.MAX_PROGRESS_ROUNDS
        or type(progress.mastery)~="table"
        or type(progress.claimedRoundIds)~="table" then return false end
    if progress.level==Progression.PLAYER_MAX_LEVEL then
        if progress.xp~=0 then return false end
    elseif progress.xp>=Progression.xpToNext(progress.level) then return false end
    local settled=0
    for id,yes in pairs(progress.claimedRoundIds) do
        settled+=1
        if settled>Store.MAX_PROGRESS_ROUNDS or yes~=true or not validReceipt(id) then return false end
    end
    if settled~=progress.settledCount then return false end
    for item,value in pairs(progress.mastery) do
        if Store.ITEMS[item]~=true or type(value)~="table"
            or not integer(value.level) or value.level<1
            or value.level>Progression.MASTERY_MAX_LEVEL
            or not integer(value.xp) or value.xp<0 then return false end
        if value.level==Progression.MASTERY_MAX_LEVEL then
            if value.xp~=0 then return false end
        elseif value.xp>=Progression.masteryToNext(value.level) then return false end
    end
    return true
end
local function cloneProgress(p:any)
    if p==nil then return nil end
    local out={level=p.level,xp=p.xp,settledCount=p.settledCount,
        mastery={},claimedRoundIds={}}
    for id,done in pairs(p.claimedRoundIds) do out.claimedRoundIds[id]=done end
    for item,lv in pairs(p.mastery) do
        out.mastery[item]={level=lv.level,xp=lv.xp}
    end
    return out
end
-- A transient ProgressionRules profile adds playerUserId to one trusted store's
-- profile. Never trust a playerUserId supplied by a client or saved record.
function Store.toProgressProfile(raw:any,uid:any)
    local innerUid=Store.policyUserId(uid)
    if innerUid==nil or not Store.validate(raw) then return nil end
    local profile=Progression.newProfile(innerUid)
    if profile==nil then return nil end
    local current=raw.progress
    if current~=nil then
        profile.level=current.level
        profile.xp=current.xp
        profile.settledCount=current.settledCount
        profile.mastery=cloneProgress(current).mastery
        profile.claimedRoundIds=copyMap(current.claimedRoundIds)
    end
    return profile
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
    if not safeProgressRecord(raw.progress) then return false end
    return true
end
local function normalized(raw:any)
    if raw==nil then return Store.blank() end
    if not Store.validate(raw) then return nil end
    return {
        schema=Store.SCHEMA,revision=raw.revision,
        owned=copyMap(raw.owned),receipts=copyMap(raw.receipts),
        equipped=raw.equipped,
        progress=cloneProgress(raw.progress)
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

-- One atomic DataStore UpdateAsync owns inventory and progression together.
-- Callback can be replayed by DataStore; rebuilds NEW mutable policy objects
-- from immutable server-authored event values, NEVER modifies original input.
local function roundSummaryValid(data:any)
    if type(data)~="table" or not validReceipt(data.id)
        or (data.mode~="CLASSIC" and data.mode~="SCORE")
        or (data.outcome~="WIN" and data.outcome~="LOSS" and data.outcome~="DRAW")
        or not integer(data.duration) or data.duration<60 or data.duration>360
        or type(data.events)~="table" or #data.events>20
        or #data.events<1 then return false end
    for i=1,#data.events do
        local event=data.events[i]
        if type(event)~="table" or type(event.id)~="string"
            or #event.id<1 or #event.id>96
            or type(event.kind)~="string" then return false end
    end
    return true
end
function Store.settleProgressTransition(raw:any,uid:any,data:any)
    if not integer(uid) or uid<1 or not roundSummaryValid(data) then
        return nil,"INVALID_ROUND"
    end
    local state=normalized(raw)
    if not state then return nil,"CORRUPT_RECORD" end
    local profile=Store.toProgressProfile(state,uid)
    if not profile then return nil,"INVALID_PROFILE" end
    if profile.claimedRoundIds[data.id]==true then
        return state,"ALREADY_SETTLED"
    end
    if profile.settledCount>=Store.MAX_PROGRESS_ROUNDS then
        return nil,"ROUND_LEDGER_FULL"
    end
    -- Match-start equipped item must STILL be owned by the DataStore's
    -- canonical inventory to earn mastery. XP for objective play stays fair.
    local item=if type(data.itemId)=="string"
        and Store.ITEMS[data.itemId]==true
        and state.owned[data.itemId] and state.owned[data.itemId]>0
        and state.equipped==data.itemId then data.itemId else nil
    local round=Progression.newRound(data.id,profile.playerUserId,data.mode,item,item~=nil)
    if not round then return nil,"INVALID_ROUND" end
    for _,event in ipairs(data.events) do
        if not Progression.recordEvent(round,event.id,event.kind,true) then
            return nil,"DUPLICATE_OR_UNAUTHORIZED_EVENT"
        end
    end
    local receipt=Progression.commit(profile,round,data.outcome,data.duration,true)
    if receipt==nil then return nil,"ZERO_OR_INVALID_XP" end
    if receipt.requiresPaidPurchase~=false or receipt.gameplayStatsIncreased~=false
        or receipt.grantedXp>Progression.XP_CAP_PER_ROUND then return nil,"UNFAIR_XP" end
    state.progress={
        level=profile.level,xp=profile.xp,
        mastery=cloneProgress(profile).mastery,
        claimedRoundIds=copyMap(profile.claimedRoundIds),
        settledCount=profile.settledCount
    }
    state.revision+=1
    if not Store.validate(state) then return nil,"POST_UPDATE_CORRUPT" end
    return state,"SETTLED"
end
function Store.settleProgress(store:any,uid:any,data:any)
    local key=userKey(uid)
    if not store or not key or not roundSummaryValid(data) then
        return false,nil,"INVALID_STORE_OR_ROUND"
    end
    -- Defensive snapshot: async DataStore callbacks must never retain a mutable
    -- Game round or access player/Remote/state while retrying.
    local fixed={id=data.id,mode=data.mode,outcome=data.outcome,
        duration=data.duration,itemId=data.itemId,events={}}
    for _,event in ipairs(data.events) do
        table.insert(fixed.events,{id=event.id,kind=event.kind})
    end
    local ok,updated=pcall(function()
        return store:UpdateAsync(key,function(original)
            local nextState=Store.settleProgressTransition(original,uid,fixed)
            return nextState -- nil means fail-closed; never clobber inventory
        end)
    end)
    if not ok then return false,nil,"WRITE_UNCONFIRMED" end
    if not Store.validate(updated) or not updated.progress
        or updated.progress.claimedRoundIds[data.id]~=true then
        return false,nil,"PROGRESS_NOT_CONFIRMED"
    end
    return true,updated,"PROGRESS_PERSISTED_OR_ALREADY_SETTLED"
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
