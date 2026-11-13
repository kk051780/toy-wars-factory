--!strict
-- EGG RAID RUMBLE: pure SERVER-only collectible EVOLUTION candidate.
-- Does NOT mutate #281 XP, #275 ownership, #285 combat damage, Game or DataStore.
-- Actual owned and mastery/level must be certified by the SINGLE Game server.
local E = {}
E.MAX_FRAGMENTS = 100000
E.MAX_ROUND_RECEIPTS = 4096
E.MAX_EVOLUTION_RECEIPTS = 4096
local CATEGORIES = {
    BEAST = {assault="SKY_HUNTER",guard="EGG_GUARDIAN"},
    SPELL = {assault="STORM_ARC",guard="ICE_BRIDGE"},
    MOUNT = {assault="SKY_DASH_NO_EGG",guard="SEA_ESCORT"},
    ITEM = {assault="ENEMY_SCANNER",guard="ALLIED_SHIELD"},
    ZOMBIE = {assault="MOB_DISTRACTION",guard="GATE_BLOCK"},
    TRAP = {assault="PRESSURE_SNARE",guard="CASTLE_ALARM"},
}
-- Exactly these first 3 IDs already exist in #275 RewardEquipRules.
-- The other 5 are illustrative future catalog keys, NOT currently obtainable.
local ITEMS = {
    starter_scout = {category="BEAST",name="はじまりの小獣",liveId=true},
    forest_scout = {category="BEAST",name="森の偵察獣",liveId=true},
    star_scout = {category="BEAST",name="星の偵察獣",liveId=true},
    demo_ice_spell = {category="SPELL",name="氷の魔法",liveId=false},
    demo_cloud_mount = {category="MOUNT",name="雲の乗り物",liveId=false},
    demo_ward_item = {category="ITEM",name="守りの道具",liveId=false},
    demo_zombie = {category="ZOMBIE",name="夜のゾンビ",liveId=false},
    demo_signal_trap = {category="TRAP",name="合図の罠",liveId=false},
}
local COST = { [1]=2, [2]=5, [3]=10 }
local NEED_ACCOUNT_LV = { [1]=10, [2]=25, [3]=40 }
local NEED_MASTERY_LV = { [1]=3, [2]=6, [3]=10 }
local function integer(n,lo,hi)
    return type(n)=="number" and n==n and n%1==0 and n>=lo and n<=hi
end
local function key(s,maxLen)
    return type(s)=="string" and #s>0 and #s<=maxLen
end
local function itemOwned(ownedItems,itemId)
    return type(ownedItems)=="table" and
        integer(ownedItems[itemId],1,1000000)
end
local function state(profile,itemId)
    if type(profile)~="table" or type(profile.forms)~="table" then
        return nil
    end
    local existing=profile.forms[itemId]
    if existing==nil then return {stage=0,branch="NONE"} end
    if type(existing)~="table" or not integer(existing.stage,0,3) then return nil end
    local b=existing.branch
    if existing.stage<=1 then
        if b~="NONE" then return nil end
    elseif b~="ASSAULT" and b~="GUARD" then
        return nil
    end
    return {stage=existing.stage,branch=b}
end
local function profileOk(p)
    return type(p)=="table" and integer(p.userId,1,9999999999999)
        and integer(p.fragments,0,E.MAX_FRAGMENTS)
        and type(p.forms)=="table" and type(p.roundReceipts)=="table"
        and type(p.evoReceipts)=="table"
        and integer(p.roundCount,0,E.MAX_ROUND_RECEIPTS)
        and integer(p.evoCount,0,E.MAX_EVOLUTION_RECEIPTS)
end
local function safeCopy(t)
    local r={}
    for k,v in pairs(t) do r[k]=v end
    return r
end
function E.newProfile(userId)
    if not integer(userId,1,9999999999999) then return nil end
    return {userId=userId,fragments=0,forms={},roundReceipts={},
        evoReceipts={},roundCount=0,evoCount=0}
end
function E.catalog()
    local out={}
    for k,v in pairs(ITEMS) do out[k]=safeCopy(v) end
    return out
end
function E.costs()
    return {cost=safeCopy(COST),accountLv=safeCopy(NEED_ACCOUNT_LV),
        masteryLv=safeCopy(NEED_MASTERY_LV)}
end
-- Trusted round result MUST be minted from JobId+match epoch by canonical
-- server after real >=60s contribution. Clients must NEVER call directly.
-- award max 2 FREE evolution crystals per legitimate server-settled round.
function E.creditRound(profile,roundId,realObjectiveCount,duration,serverConfirmed)
    if not profileOk(profile) or not key(roundId,128) or
        not integer(realObjectiveCount,1,20) or
        not integer(duration,60,360) or serverConfirmed~=true then
        return false,"INVALID_ROUND"
    end
    if profile.roundReceipts[roundId]~=nil then
        return true,profile.roundReceipts[roundId],"ALREADY_CREDITED"
    end
    if profile.roundCount>=E.MAX_ROUND_RECEIPTS then
        return false,"RECEIPT_LEDGER_FULL"
    end
    local gain=realObjectiveCount>=2 and 2 or 1
    if profile.fragments+gain>E.MAX_FRAGMENTS then
        return false,"FRAGMENT_CAP"
    end
    profile.fragments+=gain
    profile.roundReceipts[roundId]=gain
    profile.roundCount+=1
    return true,gain,"CREDITED"
end
local function formValue(itemId,stage,branch)
    local entry=ITEMS[itemId]
    if not entry then return nil end
    local cat=CATEGORIES[entry.category]
    if not cat then return nil end
    local token=if stage==0 then "HATCH"
        elseif stage==1 then "GROWN"
        elseif stage==2 then "EVOLVED" else "MYTHIC"
    local suffix=if branch=="NONE" then "" else "_"..branch
    local ability=if stage<=1 then "BASE_"..entry.category
        elseif branch=="ASSAULT" then cat.assault else cat.guard
    -- These are ACTION DESIGN IDS, not world-implemented ability scripts.
    return {
        itemId=itemId,category=entry.category,stage=stage,branch=branch,
        formId=itemId.."_S"..stage..suffix,formToken=token,
        displayName=entry.name,
        abilityDesignId=ability,
        modelId="NOT_INTEGRATED",
        actualCombatImplemented=false,
        additionalPvpStatMultiplier=0,
        requiresPaidPurchase=false,
        isCurrentPlayableId=entry.liveId
    }
end
-- Read-only form preview. Only server-check trusted own and profile source.
function E.form(profile,itemId,ownedItems)
    if not profileOk(profile) or not ITEMS[itemId] or
        not itemOwned(ownedItems,itemId) then return nil end
    local f=state(profile,itemId)
    if not f then return nil end
    return formValue(itemId,f.stage,f.branch)
end
function E.nextEvolution(profile,itemId,ownedItems,accountLevel,masteryLevel)
    if not profileOk(profile) or not ITEMS[itemId] or
        not itemOwned(ownedItems,itemId) or
        not integer(accountLevel,1,50) or not integer(masteryLevel,1,10) then
        return nil
    end
    local f=state(profile,itemId)
    if not f then return nil end
    if f.stage>=3 then return {complete=true,stage=3,fragments=profile.fragments} end
    local stage=f.stage+1
    return {
        complete=false,fromStage=f.stage,toStage=stage,
        fragmentCost=COST[stage],
        accountLevelRequired=NEED_ACCOUNT_LV[stage],
        masteryRequired=NEED_MASTERY_LV[stage],
        available=accountLevel>=NEED_ACCOUNT_LV[stage] and
            masteryLevel>=NEED_MASTERY_LV[stage] and
            profile.fragments>=COST[stage],
        needsChoice=stage==2,
        missingFragments=math.max(0,COST[stage]-profile.fragments),
    }
end
-- Every evolution request ID must be server-minted and persisted in same
-- atomic profile UpdateAsync as fragments/forms, NEVER from a client.
function E.evolve(profile,itemId,ownedItems,accountLevel,masteryLevel,
    phase,requestId,choice,serverConfirmed)
    if not profileOk(profile) or not key(requestId,128) or
        phase~="LOBBY" or serverConfirmed~=true then
        return false,"INVALID_REQUEST"
    end
    local saved=profile.evoReceipts[requestId]
    if saved then
        if saved.itemId~=itemId or saved.action~="EVOLVE" or saved.choice~=choice then
            return false,"RECEIPT_CONFLICT"
        end
        return true,safeCopy(saved),"ALREADY_EVOLVED"
    end
    local next=E.nextEvolution(profile,itemId,ownedItems,accountLevel,masteryLevel)
    if not next then return false,"UNOWNED_OR_INVALID_LEVEL" end
    if next.complete then return false,"FINAL_FORM" end
    if next.toStage==2 then
        if choice~="ASSAULT" and choice~="GUARD" then
            return false,"CHOOSE_BRANCH"
        end
    elseif choice~="NONE" then
        return false,"INVALID_CHOICE"
    end
    if not next.available then return false,"GROWTH_REQUIREMENTS" end
    if profile.evoCount>=E.MAX_EVOLUTION_RECEIPTS then
        return false,"RECEIPT_LEDGER_FULL"
    end
    local old=state(profile,itemId)
    if not old then return false,"INVALID_FORM" end
    local branch=if next.toStage==2 then choice else old.branch
    local newForm=formValue(itemId,next.toStage,branch)
    if not newForm then return false,"INVALID_ITEM" end
    profile.fragments-=next.fragmentCost
    profile.forms[itemId]={stage=next.toStage,branch=branch}
    local receipt={itemId=itemId,action="EVOLVE",choice=choice,stage=next.toStage,
        branch=branch,cost=next.fragmentCost,formId=newForm.formId}
    profile.evoReceipts[requestId]=receipt
    profile.evoCount+=1
    return true,safeCopy(receipt),"EVOLVED"
end
function E.switchBranch(profile,itemId,ownedItems,phase,requestId,
    choice,serverConfirmed)
    if not profileOk(profile) or not key(requestId,128) or
        phase~="LOBBY" or serverConfirmed~=true then
        return false,"INVALID_REQUEST"
    end
    local saved=profile.evoReceipts[requestId]
    if saved then
        if saved.itemId~=itemId or saved.action~="SWITCH" or saved.choice~=choice then
            return false,"RECEIPT_CONFLICT"
        end
        return true,safeCopy(saved),"ALREADY_SWITCHED"
    end
    if not itemOwned(ownedItems,itemId) or not ITEMS[itemId] then
        return false,"NOT_OWNED"
    end
    local f=state(profile,itemId)
    if not f or f.stage<2 then return false,"NOT_BRANCH_FORM" end
    if choice~="ASSAULT" and choice~="GUARD" then return false,"INVALID_BRANCH" end
    if choice==f.branch then return false,"SAME_BRANCH" end
    if profile.fragments<3 then return false,"INSUFFICIENT_FRAGMENTS" end
    if profile.evoCount>=E.MAX_EVOLUTION_RECEIPTS then
        return false,"RECEIPT_LEDGER_FULL"
    end
    profile.fragments-=3
    profile.forms[itemId]={stage=f.stage,branch=choice}
    local f2=formValue(itemId,f.stage,choice)
    local receipt={itemId=itemId,action="SWITCH",choice=choice,stage=f.stage,
        branch=choice,cost=3,formId=f2.formId}
    profile.evoReceipts[requestId]=receipt
    profile.evoCount+=1
    return true,safeCopy(receipt),"SWITCHED"
end
return E
