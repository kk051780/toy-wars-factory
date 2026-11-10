-- TRAP RAIDERS: optional, read-only presentation policy for server-owned fair progression.
-- This module does not award XP, save data, authenticate RemoteEvents, or create GUI.
-- Call only after the real PC game's trusted server presentation bridge has validated identity.
local M = {}
local MAX_XP = 1000000000
local MAX_EPOCH = 1000000000
local function isInteger(x, minValue, maxValue)
    return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
        and x % 1 == 0 and x >= minValue and x <= maxValue
end
local function validId(x, maxLen)
    return type(x) == "string" and #x > 0 and #x <= maxLen
        and string.match(x, "^[%w_.-]+$") ~= nil
end
local function validProgress(xp, required, isMax)
    if not isInteger(xp, 0, MAX_XP) or not isInteger(required, 0, MAX_XP) then
        return false
    end
    if isMax then return xp == 0 and required == 0 end
    return required > 0 and xp < required
end
local function renderProgress(xp, required, isMax)
    if isMax then return 1 end
    return xp / required
end
local function copyAllowedJobs(allowed)
    if type(allowed) ~= "table" then return nil end
    local result, seen = {}, {}
    if #allowed ~= 7 then return nil end
    for index = 1, 7 do
        local id = allowed[index]
        if not validId(id, 32) or seen[id] then return nil end
        seen[id] = true
        result[index] = id
    end
    for k, _ in pairs(allowed) do
        if not isInteger(k, 1, 7) then return nil end
    end
    return result
end
function M.project(snapshot, viewerId, expectedMatchId, expectedEpoch, allowedJobIds)
    -- Function arguments are trusted server-side context, never values supplied by client GUI.
    if not validId(viewerId, 96) or not validId(expectedMatchId, 96)
        or not isInteger(expectedEpoch, 0, MAX_EPOCH) then
        return nil, "INVALID_CONTEXT"
    end
    local jobs = copyAllowedJobs(allowedJobIds)
    if not jobs then return nil, "INVALID_JOB_ALLOWLIST" end
    if type(snapshot) ~= "table" or snapshot.authority ~= "SERVER"
        or snapshot.playerId ~= viewerId or snapshot.matchId ~= expectedMatchId
        or snapshot.epoch ~= expectedEpoch or snapshot.roundActive ~= true then
        return nil, "INVALID_SNAPSHOT_IDENTITY"
    end
    if not isInteger(snapshot.level, 1, 25) or type(snapshot.mastery) ~= "table" then
        return nil, "INVALID_PROGRESSION"
    end
    local maxLevel = snapshot.level == 25
    if not validProgress(snapshot.levelXp, snapshot.levelRequiredXp, maxLevel) then
        return nil, "INVALID_LEVEL_XP"
    end
    local allowedSet = {}
    for _, id in ipairs(jobs) do allowedSet[id] = true end
    local actualCount = 0
    for id, _ in pairs(snapshot.mastery) do
        if not allowedSet[id] then return nil, "UNKNOWN_JOB" end
        actualCount = actualCount + 1
        if actualCount > 7 then return nil, "INVALID_JOB_COUNT" end
    end
    if actualCount ~= 7 then return nil, "INVALID_JOB_COUNT" end
    local views = {}
    for _, id in ipairs(jobs) do
        local entry = snapshot.mastery[id]
        if type(entry) ~= "table" or not isInteger(entry.level, 0, 5) then
            return nil, "INVALID_MASTERY"
        end
        local maxMastery = entry.level == 5
        if not validProgress(entry.xp, entry.requiredXp, maxMastery) then
            return nil, "INVALID_MASTERY_XP"
        end
        views[#views + 1] = {
            jobId = id,
            label = string.format("%s 熟練 %d/5", id, entry.level),
            level = entry.level,
            xp = entry.xp,
            requiredXp = entry.requiredXp,
            fraction = renderProgress(entry.xp, entry.requiredXp, maxMastery),
            maxed = maxMastery,
        }
    end
    return {
        playerId = viewerId,
        matchId = expectedMatchId,
        epoch = expectedEpoch,
        level = snapshot.level,
        levelLabel = string.format("Lv %d/25", snapshot.level),
        levelXp = snapshot.levelXp,
        levelRequiredXp = snapshot.levelRequiredXp,
        levelFraction = renderProgress(snapshot.levelXp, snapshot.levelRequiredXp, maxLevel),
        maxLevel = maxLevel,
        jobs = views,
        jobCount = 7,
        sessionOnly = snapshot.sessionOnly == true,
        saved = snapshot.saved == true,
        grantsGameplayStats = false,
    }, nil
end
return M
