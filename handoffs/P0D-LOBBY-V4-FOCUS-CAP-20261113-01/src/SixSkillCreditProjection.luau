--!strict
-- P0D training V4: pure six-skill accrued-XP projection (NOT a Store or XP writer).
-- Supports only a FULL six-skill integer microXP snapshot. Missing legacy fields => block;
-- persistent migration is exclusively owned by the canonical profile Store author.
-- Caller obtains quote exclusively from server-side TrainingIntegrationGate.quote
-- and still must atomically commit through the existing Game/Store authority.
local Projection = {}
Projection.SKILLS = {"BEAST","MAGIC","WEAPON","ZOMBIE","VEHICLE","BUILDING"}
Projection.MAX_LEVEL = 30 -- candidate S2 balancing limit, NOT yet game-authorized
Projection.MAX_TOTAL_MICROXP = 9000000000000
Projection.MAX_QUOTE_MICROXP = 240000000000
Projection.XP_MICRO = 1000000

local function safeInteger(value: any, lower: number, upper: number): boolean
    return type(value) == "number" and value == value
        and value ~= math.huge and value ~= -math.huge
        and value % 1 == 0 and value >= lower and value <= upper
end
local function skillKnown(value: any): boolean
    for _, skill in ipairs(Projection.SKILLS) do
        if skill == value then return true end
    end
    return false
end
local function err(code: string): {[string]: any}
    return {ok=false, problem=code, applied=false}
end

function Projection.blank(): {[string]: number}
    local result = {}
    for _, skill in ipairs(Projection.SKILLS) do
        result[skill]=0
    end
    return result
end

function Projection.checkTotals(totals: any): (boolean, string?)
    if type(totals) ~= "table" then return false, "MISSING_PROFILE" end
    for _,skill in ipairs(Projection.SKILLS) do
        if not safeInteger(totals[skill],0,Projection.MAX_TOTAL_MICROXP) then
            return false,"MISSING_OR_INVALID_" .. skill
        end
    end
    -- Extra skills would be silently erased by projection; block rather than truncate.
    for key in pairs(totals) do
        if not skillKnown(key) then return false,"UNKNOWN_SKILL_PROFILE" end
    end
    return true,nil
end

function Projection.costToNextMicroXP(level: any): number?
    if not safeInteger(level,1,Projection.MAX_LEVEL-1) then return nil end
    -- Deliberately simple, monotonically increasing candidate curve.
    -- Cost to Lv(N+1) = 100 * N^2 XP (base training rate still needs FUN tuning).
    return 100 * level * level * Projection.XP_MICRO
end

function Projection.viewLevel(totalMicroXP: any): {[string]: any}
    if not safeInteger(totalMicroXP,0,Projection.MAX_TOTAL_MICROXP) then
        return {ok=false,problem="INVALID_XP_TOTAL"}
    end
    local xpLeft = totalMicroXP
    for level=1,Projection.MAX_LEVEL-1 do
        local nextCost = Projection.costToNextMicroXP(level)
        if xpLeft < nextCost then
            return {ok=true,level=level,microIntoLevel=xpLeft,microToNext=nextCost-xpLeft,
                nextLevelCostMicroXP=nextCost,maxLevel=false}
        end
        xpLeft-=nextCost
    end
    return {ok=true,level=Projection.MAX_LEVEL,microIntoLevel=0,microToNext=0,
        nextLevelCostMicroXP=0,maxLevel=true}
end

function Projection.prepare(totals:any, revision:any, quote:any): {[string]: any}
    local valid,reason=Projection.checkTotals(totals)
    if not valid then return err(reason or "INVALID_PROFILE") end
    if not safeInteger(revision,0,1000000000) then return err("INVALID_REVISION") end
    if type(quote) ~= "table" or quote.ok ~= true or quote.applied ~= false
        or type(quote.nonce) ~= "string" or #quote.nonce<8 or #quote.nonce>128
    then return err("INVALID_QUOTE") end
    if not safeInteger(quote.grantCount,1,24)
        or type(quote.grants)~="table"
        or #quote.grants ~= quote.grantCount
        or not safeInteger(quote.totalSeconds,1,120)
        or not safeInteger(quote.totalMicroXP,1,Projection.MAX_QUOTE_MICROXP)
    then return err("INVALID_QUOTE_SHAPE") end

    local nextTotals = table.clone(totals)
    local totalSeconds=0
    local totalMicroXP=0
    local granted = {}
    for _,grant in ipairs(quote.grants) do
        if type(grant)~="table" or not skillKnown(grant.skill)
            or not safeInteger(grant.seconds,1,120)
            or not safeInteger(grant.microXP,1,Projection.MAX_QUOTE_MICROXP)
            or not safeInteger(grant.bonusBps,10000,20000)
            or ((grant.bonusBps-10000)%2500 ~=0)
            or (grant.mode~="FOCUS" and grant.mode~="RANDOM")
        then return err("INVALID_GRANT") end
        totalSeconds+=grant.seconds
        totalMicroXP+=grant.microXP
        if totalSeconds > 120 or totalMicroXP > Projection.MAX_QUOTE_MICROXP
        then return err("QUOTE_LIMIT_EXCEEDED") end
        nextTotals[grant.skill]+=grant.microXP
        if nextTotals[grant.skill]>Projection.MAX_TOTAL_MICROXP
        then return err("TOTAL_XP_CAP") end
        granted[grant.skill]=(granted[grant.skill] or 0)+grant.microXP
    end
    if totalSeconds~=quote.totalSeconds or totalMicroXP~=quote.totalMicroXP
    then return err("QUOTE_CHECKSUM_MISMATCH") end
    local views={}
    for _,skill in ipairs(Projection.SKILLS) do
        views[skill]=Projection.viewLevel(nextTotals[skill])
        if not views[skill].ok then return err("LEVEL_VIEW_FAILED") end
    end
    return {
        ok=true,applied=false,nonce=quote.nonce,expectedRevision=revision,
        proposedRevision=revision+1,totals=nextTotals,added=granted,
        totalMicroXP=totalMicroXP,levels=views,
    }
end

return Projection
