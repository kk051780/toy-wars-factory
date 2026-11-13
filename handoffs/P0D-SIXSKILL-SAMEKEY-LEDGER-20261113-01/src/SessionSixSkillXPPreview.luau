--!strict
-- V4 PRIVATE STUDIO ONLY: six-skill XP/levels in THIS SESSION, never real rewards.
-- Pure policy. No DataStore, Remotes, Marketplace, real ability/buff writes.
local Model = {}
Model.SKILLS = {"BEAST","MAGIC","WEAPON","ZOMBIE","VEHICLE","BUILDING"}
Model.MAX_LEVEL = 30 -- PROVISIONAL, NOT approved gameplay balance.
Model.BASE_XP_PER_SECOND = 10
Model.MICRO = 1000000
Model.MAX_SEGMENT_SECONDS = 120
Model.MAX_SESSION_MICRO = 9000000000000

local function isInt(value: any, low: number, high: number): boolean
    return type(value)=="number" and value==value and value~=math.huge
        and value~=-math.huge and value%1==0 and value>=low and value<=high
end

local function isSkill(value: any): boolean
    for _,skill in ipairs(Model.SKILLS) do
        if skill==value then return true end
    end
    return false
end

local function costsForLevel(level: number): number
    return 100 * level * level * Model.MICRO
end

function Model.new(): {[string]: number}
    local totals={}
    for _,skill in ipairs(Model.SKILLS) do totals[skill]=0 end
    return totals
end

function Model.viewXP(total: any): {[string]: any}
    if not isInt(total,0,Model.MAX_SESSION_MICRO) then
        return {level=1,xp=0,xpToNext=100,max=false,valid=false}
    end
    local remaining=total
    for lv=1,Model.MAX_LEVEL-1 do
        local cost=costsForLevel(lv)
        if remaining<cost then
            return {
                level=lv, xp=math.floor(remaining/Model.MICRO),
                xpToNext=math.ceil((cost-remaining)/Model.MICRO),
                max=false, valid=true,
            }
        end
        remaining-=cost
    end
    return {level=Model.MAX_LEVEL,xp=0,xpToNext=0,max=true,valid=true}
end

function Model.snapshot(totals: any): {[string]: any}
    local result={}
    if type(totals)~="table" then return result end
    for _,skill in ipairs(Model.SKILLS) do
        result[skill]=Model.viewXP(totals[skill])
    end
    return result
end

-- Inputs are solely server-generated FocusTrainingScheduler.settle() segments.
-- Failure is atomic (no partial awards). An invalid or tampered segment blocks ALL.
-- This method is intentionally independent from true persistent profile XP.
function Model.apply(totals: any, segments: any): (any, string?)
    if type(totals)~="table" or type(segments)~="table" or #segments>24 then
        return nil,"BAD_INPUT"
    end
    local nextTotals={}
    for _,skill in ipairs(Model.SKILLS) do
        if not isInt(totals[skill],0,Model.MAX_SESSION_MICRO) then
            return nil,"INCOMPLETE_SIX_SKILL_PROFILE"
        end
        nextTotals[skill]=totals[skill]
    end
    if #segments==0 then return nextTotals,nil end
    local totalSeconds=0
    for _,segment in ipairs(segments) do
        if type(segment)~="table" or not isSkill(segment.skill)
            or not isInt(segment.seconds,1,Model.MAX_SEGMENT_SECONDS)
            or not isInt(segment.bonusBps,10000,20000)
            or (segment.bonusBps-10000)%2500~=0
            or (segment.mode~="FOCUS" and segment.mode~="RANDOM") then
            return nil,"INVALID_SEGMENT"
        end
        totalSeconds+=segment.seconds
        if totalSeconds>Model.MAX_SEGMENT_SECONDS then return nil,"TOO_MANY_SECONDS" end
        -- microXP = 10 XP/sec * 1e6 * seconds * basis points/1e4
        local credit=segment.seconds * Model.BASE_XP_PER_SECOND * 100 * segment.bonusBps
        -- Wait: microXP formula simplifies to 10 * 100 * bps: 10000 -> 10,000,000.
        if not isInt(credit,1,2400000000) then return nil,"INVALID_CREDIT" end
        local amount=nextTotals[segment.skill]+credit
        if amount>Model.MAX_SESSION_MICRO then return nil,"SESSION_LIMIT" end
        nextTotals[segment.skill]=amount
    end
    return nextTotals,nil
end

return Model
