--!strict
-- P0D / QA independent optional S1 six-skill persistence transition policy.
-- MUST be called only inside original PersistentHatchStore's SAME-key UpdateAsync.
-- This module NEVER accesses DataStore, Remotes, Marketplace, Players or Workspace.
-- Grant values MUST originate from original Game's verified physical-pad/tick record,
-- never from a client Remote or saved input. No new PvP/ability effects here.
local Scheduler = require(script.Parent:WaitForChild("FocusTrainingScheduler"))
local XP = require(script.Parent:WaitForChild("SessionSixSkillXPPreview"))
local Ledger = {}
Ledger.MAX_RECEIPTS_PER_JST_DAY = 3000
Ledger.MAX_TOTAL_MICRO = XP.MAX_SESSION_MICRO -- source-model bound; capped skill needs tuning
Ledger.MIN_SECONDS_PER_BATCH = 30 -- budget safety: aggregate server ticks, not 1 write/s
Ledger.MAX_SECONDS_PER_BATCH = Scheduler.MAX_SETTLE_SECONDS
local MAX_UID = 999999999999999
local JST_OFFSET = 32400
local function integer(x: any, lo: number, hi: number): boolean
    return type(x)=="number" and x==x and x~=math.huge and x~=-math.huge
        and x%1==0 and x>=lo and x<=hi
end
local function validSkill(x: any): boolean
    for _,skill in ipairs(XP.SKILLS) do
        if x==skill then return true end
    end
    return false
end
local function dayOf(unix: number): number
    return math.floor((unix+JST_OFFSET)/86400)
end
local function validReceipt(x: any): boolean
    return type(x)=="string" and #x>=14 and #x<=110
        and x:match("^T[%w%-_]+:%d+$")~=nil
end
local function copyReceipts(source: any): any
    local o={}
    for k,v in pairs(source) do o[k]=v end
    return o
end
local function copyTotals(source: any): any
    local o={}
    for _,skill in ipairs(XP.SKILLS) do o[skill]=source[skill] end
    return o
end
function Ledger.blank(): any
    return {version=1,dayIndex=0,focusedSeconds=0,selectedSkill=nil,
        randomCycle=0,randomPosition=1,randomRemaining=600,
        totalsMicro=XP.new(),receipts={},receiptCount=0,lastCreditEnd=0}
end
function Ledger.valid(input: any): boolean
    if input==nil then return true end -- legacy schema1 compatible
    if type(input)~="table" or input.version~=1
        or not integer(input.dayIndex,0,1000000)
        or not integer(input.focusedSeconds,0,1800)
        or (input.selectedSkill~=nil and not validSkill(input.selectedSkill))
        or not integer(input.randomCycle,0,1000000)
        or not integer(input.randomPosition,1,6)
        or not integer(input.randomRemaining,1,600)
        or type(input.totalsMicro)~="table" or type(input.receipts)~="table"
        or not integer(input.receiptCount,0,Ledger.MAX_RECEIPTS_PER_JST_DAY)
        or not integer(input.lastCreditEnd,0,4102444800)
        then return false end
    for key,value in pairs(input.totalsMicro) do
        if not validSkill(key) or not integer(value,0,Ledger.MAX_TOTAL_MICRO) then
            return false
        end
    end
    for _,skill in ipairs(XP.SKILLS) do
        if not integer(input.totalsMicro[skill],0,Ledger.MAX_TOTAL_MICRO) then
            return false
        end
    end
    local count=0
    for receipt,used in pairs(input.receipts) do
        count+=1
        if count>Ledger.MAX_RECEIPTS_PER_JST_DAY or used~=true
            or not validReceipt(receipt) then return false end
    end
    return count==input.receiptCount
end
function Ledger.clone(input: any): any
    if not Ledger.valid(input) then return nil end
    if input==nil then return Ledger.blank() end
    return {version=1,dayIndex=input.dayIndex,
        focusedSeconds=input.focusedSeconds,
        selectedSkill=input.selectedSkill,
        randomCycle=input.randomCycle,randomPosition=input.randomPosition,
        randomRemaining=input.randomRemaining,totalsMicro=copyTotals(input.totalsMicro),
        receipts=copyReceipts(input.receipts),receiptCount=input.receiptCount,
        lastCreditEnd=input.lastCreditEnd}
end
-- Pure; retries with the same receipt yield SAME record and no 2nd XP.
-- Caller MUST authorize grant only after server verified valid live training pad,
-- no egg carry, alive, right team, 30-120 real seconds, and real same-server friends.
function Ledger.settle(raw: any, realUserId: any, grant: any): (any,string)
    if not integer(realUserId,1,MAX_UID) or type(grant)~="table"
        or grant.verifiedByCanonicalGame~=true
        or not validReceipt(grant.receipt)
        or not integer(grant.utcStart,946684800,4102444800)
        or not integer(grant.utcEnd,946684800,4102444800)
        or grant.utcEnd-grant.utcStart<Ledger.MIN_SECONDS_PER_BATCH
        or grant.utcEnd-grant.utcStart>Ledger.MAX_SECONDS_PER_BATCH
        or dayOf(grant.utcStart)~=dayOf(grant.utcEnd)
        or not integer(grant.friendCount,0,4)
        or (grant.selectedSkill~=nil and not validSkill(grant.selectedSkill))
        then return nil,"UNTRUSTED_OR_INVALID_GRANT" end
    local next = Ledger.clone(raw)
    if not next then return nil,"CORRUPT_TRAINING_PROFILE" end
    local day=dayOf(grant.utcStart)
    if next.dayIndex~=0 and day<next.dayIndex then return nil,"STALE_DAY" end
    if next.dayIndex~=day then
        next.dayIndex=day
        next.focusedSeconds=0
        next.receipts={}
        next.receiptCount=0
        next.randomCycle=0
        next.randomPosition=1
        next.randomRemaining=600
    end
    if next.receipts[grant.receipt] then return next,"ALREADY_SETTLED" end
    if grant.utcStart<next.lastCreditEnd then
        return nil,"OVERLAPPING_SESSION_INTERVAL" end
    if next.receiptCount>=Ledger.MAX_RECEIPTS_PER_JST_DAY then
        return nil,"DAILY_RECEIPT_LEDGER_FULL"
    end
    if grant.selectedSkill~=nil then next.selectedSkill=grant.selectedSkill end
    -- Full real UserId remains caller's ORIGINAL DataStore key. This normalized
    -- policy seed only satisfies original Scheduler's numeric seed bound.
    local policySeed=(realUserId % 99999998)+1
    local state=Scheduler.newState(policySeed,grant.utcStart,{
        dayIndex=next.dayIndex,focusedSeconds=next.focusedSeconds,
        selectedSkill=next.selectedSkill,randomCycle=next.randomCycle,
        randomPosition=next.randomPosition,randomRemaining=next.randomRemaining,
    })
    local settled,segments=Scheduler.settle(state,grant.utcEnd,true,grant.friendCount,false)
    -- Validate EXACT original author XP policy on the source segments, but
    -- saturate totals once a Lv30 track is maxed rather than abort all six.
    local earned,errorCode=XP.apply(XP.new(),segments)
    if not earned then return nil,errorCode or "XP_REJECTED" end
    local awarded=copyTotals(next.totalsMicro)
    for _,skill in ipairs(XP.SKILLS) do
        awarded[skill]=math.min(Ledger.MAX_TOTAL_MICRO,awarded[skill]+earned[skill])
    end
    local counted=0
    for _,segment in ipairs(segments) do counted+=segment.seconds end
    if counted~=grant.utcEnd-grant.utcStart then return nil,"INCOMPLETE_SETTLEMENT" end
    local snap=Scheduler.snapshot(settled)
    next.focusedSeconds=snap.focusedSeconds
    next.selectedSkill=snap.selectedSkill
    next.randomCycle=snap.randomCycle
    next.randomPosition=snap.randomPosition
    next.randomRemaining=snap.randomRemaining
    next.totalsMicro=awarded
    next.receipts[grant.receipt]=true
    next.receiptCount+=1
    next.lastCreditEnd=grant.utcEnd
    if not Ledger.valid(next) then return nil,"INVALID_POST_SETTLEMENT" end
    return next,"SETTLED"
end
return Ledger
