--!strict
-- P0D-LOBBY-TRAINING-001 / V4 Integration Gate
-- Pure data contract: refuses to quote grants for the legacy two-skill dojo.
-- NEVER awards XP, writes profiles, invokes DataStore/Marketplace or creates Remotes.
-- Server-only callers must use original authoritative session-lock + saved XP ledger.
local Gate = {}

Gate.EXPECTED_SKILLS = {"BEAST", "MAGIC", "WEAPON", "ZOMBIE", "VEHICLE", "BUILDING"}
Gate.MAX_SEGMENTS = 24
Gate.MAX_SEGMENT_SECONDS = 120
Gate.BONUS_BASE_BPS = 10000
Gate.MAX_BONUS_BPS = 20000
Gate.BONUS_STEP_BPS = 2500

local function integer(value: any, lower: number, upper: number): boolean
    return type(value) == "number"
        and value == value and value ~= math.huge and value ~= -math.huge
        and value % 1 == 0 and value >= lower and value <= upper
end

local function skillKnown(value: any): boolean
    for _, skill in ipairs(Gate.EXPECTED_SKILLS) do
        if value == skill then return true end
    end
    return false
end

function Gate.checkCapabilities(caps: any): (boolean, {string})
    local problems = {}
    if type(caps) ~= "table" then
        return false, {"MISSING_CAPABILITIES"}
    end
    if type(caps.skills) ~= "table" then
        table.insert(problems, "NO_SKILL_REGISTRY")
    else
        for _, skill in ipairs(Gate.EXPECTED_SKILLS) do
            if caps.skills[skill] ~= true then
                table.insert(problems, "MISSING_SKILL_" .. skill)
            end
        end
    end
    if caps.singleXPAuthority ~= true then table.insert(problems, "DUPLICATE_XP_AUTHORITY_RISK") end
    if caps.persistentProfile ~= true then table.insert(problems, "NO_PERSISTENT_PROFILE") end
    if caps.atomicSessionLock ~= true then table.insert(problems, "NO_ATOMIC_SESSION_LOCK") end
    if caps.friendModel ~= "COUNT_25_CAP4" then table.insert(problems, "WRONG_FRIEND_BONUS_MODEL") end
    if caps.acceptsMicroXP ~= true then table.insert(problems, "MICRO_XP_NOT_SUPPORTED") end
    if caps.serverAuthoritativeTime ~= true then table.insert(problems, "UNTRUSTED_CLOCK") end
    if caps.pvpNormalized ~= true then table.insert(problems, "PVP_NORMALIZATION_MISSING") end
    if not integer(caps.maxSegmentSeconds, Gate.MAX_SEGMENT_SECONDS, 100000)
    then table.insert(problems, "SEGMENT_DURATION_UNSUPPORTED") end
    return #problems == 0, problems
end

local function failed(problem: string): {[string]: any}
    return {ok=false, problem=problem, grants={}, grantCount=0, totalMicroXP=0}
end

-- This is an immutable *quote* for the existing official XP authority, not a grant.
-- Caller obtains chunks exclusively from server-owned FocusTrainingScheduler.settle().
function Gate.quote(
    caps: any,
    segments: any,
    baseMilliXPPerSecond: any,
    serverNonce: any
): {[string]: any}
    local ready, missing = Gate.checkCapabilities(caps)
    if not ready then
        return {ok=false, problem="INTEGRATION_BLOCKED", blockers=missing,
            grants={}, grantCount=0, totalMicroXP=0}
    end
    if not integer(baseMilliXPPerSecond, 1, 1000000)
    then return failed("BAD_XP_RATE") end
    if type(serverNonce) ~= "string" or #serverNonce < 8 or #serverNonce > 128
    then return failed("BAD_SERVER_NONCE") end
    if type(segments) ~= "table" or #segments == 0 or #segments > Gate.MAX_SEGMENTS
    then return failed("BAD_SEGMENTS") end
    local totalSeconds = 0
    local totalMicroXP = 0
    local grants = {}
    for _, segment in ipairs(segments) do
        if type(segment) ~= "table" or not skillKnown(segment.skill)
            or not integer(segment.seconds, 1, Gate.MAX_SEGMENT_SECONDS)
            or not integer(segment.bonusBps, Gate.BONUS_BASE_BPS, Gate.MAX_BONUS_BPS)
            or ((segment.bonusBps - Gate.BONUS_BASE_BPS) % Gate.BONUS_STEP_BPS ~= 0)
            or (segment.mode ~= "FOCUS" and segment.mode ~= "RANDOM")
        then return failed("INVALID_SEGMENT") end
        totalSeconds += segment.seconds
        if totalSeconds > Gate.MAX_SEGMENT_SECONDS then
            return failed("EXCESS_SESSION_SECONDS")
        end
        -- milliXP to microXP: (milli * 1000) * (bonus bps / 10000)
        -- = milli * bonusBps / 10, exact integer for bps 10000..20000 step2500.
        local microXP = segment.seconds * baseMilliXPPerSecond * segment.bonusBps / 10
        if not integer(microXP, 0, 240000000000) then
            return failed("MICRO_XP_OVERFLOW")
        end
        table.insert(grants, {
            skill=segment.skill, seconds=segment.seconds, microXP=microXP,
            bonusBps=segment.bonusBps, mode=segment.mode,
        })
        totalMicroXP += microXP
    end
    return {
        ok=true, problem=nil, nonce=serverNonce,
        grants=grants, grantCount=#grants,
        totalSeconds=totalSeconds, totalMicroXP=totalMicroXP,
        applied=false, -- ONLY the canonical Store writer may apply idempotently
    }
end

return Gate
