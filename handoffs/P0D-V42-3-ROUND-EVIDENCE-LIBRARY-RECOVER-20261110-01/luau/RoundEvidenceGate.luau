--!strict
-- TRAP RAIDERS v42.3: pure, server-only round-evidence adapter.
-- This is a REFERENCE MODULE, not wired to the current v36 game.
-- Input MUST originate from server-owned MatchCoordinator state; booleans are
-- validation checks, not proof of origin or substitutes for authorization.
local RoundEvidenceGate = {}

local ALLOWED_MAPS = {S1=true, S2=true, S3=true, S4=true}
local ALLOWED_JOBS = {
    WARRIOR=true, NINJA=true, TRAPPER=true, ZOMBIE_MASTER=true,
    BEAST_TAMER=true, MAGE=true, BUILDER=true,
}
local ALLOWED_TEAMS = {BLUE=true, RED=true}
local ALLOWED_WINNERS = {BLUE=true, RED=true, DRAW=true}
local MEANINGFUL_ACTIONS = {
    "enemyHits", "objectiveInteractions", "trapsTriggered", "minionOrders",
    "allySupport", "structuresBuilt", "eggCarryActions",
}
local ASSIST_CATEGORIES = {"defense", "rescue", "siege"}

local function isFiniteInteger(x, minValue, maxValue)
    return type(x) == "number"
        and x == x and x ~= math.huge and x ~= -math.huge
        and x % 1 == 0 and x >= minValue and x <= maxValue
end

local function isFiniteNumber(x, low, high)
    return type(x) == "number"
        and x == x and x ~= math.huge and x ~= -math.huge
        and x >= low and x <= high
end

local function hasMember(members, userId)
    if type(members) ~= "table" then return false end
    local n = #members
    if n < 1 or n > 50 then return false end
    local found = false
    local seen = {}
    local count = 0
    for index, candidate in pairs(members) do
        if not isFiniteInteger(index, 1, n)
            or not isFiniteInteger(candidate, 1, 9007199254740991)
            or seen[candidate] then
            return false
        end
        seen[candidate] = true
        count += 1
        if candidate == userId then found = true end
    end
    return count == n and found
end

-- Returns normalized evidence, nil on success, or nil, reason on failure.
-- The expectedUserId is taken from a server Player.UserId, NEVER from a remote payload.
function RoundEvidenceGate.derive(round, player, expectedUserId)
    if type(round) ~= "table" or type(player) ~= "table" then
        return nil, "INVALID_SNAPSHOT"
    end
    if round.serverOwned ~= true or round.phase ~= "RESULT_FINALIZED" then
        return nil, "ROUND_NOT_FINALIZED"
    end
    if type(round.matchId) ~= "string" or #round.matchId < 8
        or #round.matchId > 80 or not string.match(round.matchId, "^[%w_-]+$") then
        return nil, "INVALID_MATCH_ID"
    end
    if not ALLOWED_MAPS[round.mapId] then return nil, "INVALID_MAP" end
    if not ALLOWED_WINNERS[round.winnerTeam] then return nil, "INVALID_WINNER" end
    if not isFiniteNumber(round.durationSeconds, 1, 3600) then
        return nil, "INVALID_DURATION"
    end
    if not isFiniteInteger(expectedUserId, 1, 9007199254740991)
        or player.userId ~= expectedUserId
        or not hasMember(round.participantUserIds, expectedUserId) then
        return nil, "PARTICIPANT_MISMATCH"
    end
    if not ALLOWED_JOBS[player.job] then return nil, "INVALID_JOB" end
    if not ALLOWED_TEAMS[player.team] then return nil, "INVALID_TEAM" end
    -- Roster authority remains with MatchCoordinator, never user attributes.
    if type(round.participantTeams) ~= "table"
        or round.participantTeams[expectedUserId] ~= player.team then
        return nil, "ROSTER_TEAM_MISMATCH"
    end
    for _, member in ipairs(round.participantUserIds) do
        if not ALLOWED_TEAMS[round.participantTeams[member]] then
            return nil, "ROSTER_TEAM_MISMATCH"
        end
    end
    if not isFiniteNumber(player.activeSeconds, 0, round.durationSeconds) then
        return nil, "INVALID_ACTIVE_TIME"
    end
    if type(player.actionCounts) ~= "table" then
        return nil, "INVALID_ACTION_COUNTS"
    end
    local totalActions = 0
    for _, key in ipairs(MEANINGFUL_ACTIONS) do
        local count = player.actionCounts[key]
        if not isFiniteInteger(count, 0, 100000) then
            return nil, "INVALID_ACTION_COUNTS"
        end
        totalActions += count
    end
    if type(player.assistFlags) ~= "table" then
        return nil, "INVALID_ASSIST_FLAGS"
    end
    local assists = {}
    for _, key in ipairs(ASSIST_CATEGORIES) do
        local flag = player.assistFlags[key]
        if type(flag) ~= "boolean" then
            return nil, "INVALID_ASSIST_FLAGS"
        end
        if flag then table.insert(assists, key) end
    end
    local eggDelivered = false
    if round.eggDeliveredByUserId ~= nil then
        if not isFiniteInteger(round.eggDeliveredByUserId, 1, 9007199254740991)
            or not hasMember(round.participantUserIds, round.eggDeliveredByUserId) then
            return nil, "INVALID_EGG_RECEIPT"
        end
        if round.winnerTeam == "DRAW" then
            return nil, "INVALID_EGG_RECEIPT"
        end
        if round.eggDeliveredByTeam ~= round.winnerTeam
            or round.participantTeams[round.eggDeliveredByUserId] ~= round.winnerTeam then
            return nil, "INVALID_EGG_RECEIPT"
        end
        eggDelivered = round.eggDeliveredByUserId == expectedUserId
            and player.team == round.winnerTeam
    elseif round.eggDeliveredByTeam ~= nil then
        return nil, "INVALID_EGG_RECEIPT"
    end
    return {
        -- This is a normalized input for an INTEGRATION MAPPER, not direct
        -- ProgressionCore input: actual Core signature is not available here.
        userId = expectedUserId,
        matchId = round.matchId,
        mapId = round.mapId,
        job = player.job,
        participationSeconds = player.activeSeconds,
        matchDurationSeconds = round.durationSeconds,
        meaningfulActionCount = totalActions,
        won = (round.winnerTeam ~= "DRAW" and player.team == round.winnerTeam),
        eggDelivered = eggDelivered,
        assistKinds = assists,
        matchCompleted = true,
        -- Do NOT mint serverValidated/isCurrentActiveMatch. Only the trusted
        -- live coordinator may supply authoritative Core context.
    }, nil
end

return RoundEvidenceGate
