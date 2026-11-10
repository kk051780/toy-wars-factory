-- P0-D v43A pure reference. Server-only RoundCoordinator calls this module.
-- No remotes, physics, hitboxes, persistence, spawning or Roblox Instances here.
-- All observations MUST be assembled from authoritative server state, never copied
-- from RemoteEvent payloads. Pure validation is not a proof of origin.
local NeutralSkirmishCore = {}

local CAPTURE_SECONDS = 3
local ALLY_SECONDS = 8
local COOLDOWN_SECONDS = 4
local CAPTURE_RADIUS = 14
local MAX_TICK_SECONDS = 1
local MAX_UNITS = 2
local MAX_CANDIDATES = 64
local MAX_CONTROLLED_PER_TEAM = 1

local function finite(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge
end

local function validId(v)
    return type(v) == "string" and #v >= 1 and #v <= 96
end

local function validTeam(team)
    return team == "BLUE" or team == "RED"
end

local function copyUnit(u)
    return {
        id = u.id, kind = u.kind, faction = u.faction,
        pendingTeam = u.pendingTeam, progress = u.progress,
        expiresAt = u.expiresAt, blockedUntil = u.blockedUntil,
    }
end

function NeutralSkirmishCore.new(matchId, rawUnits, startedAt)
    if not validId(matchId) or not finite(startedAt) then
        return nil, "INVALID_MATCH"
    end
    if type(rawUnits) ~= "table" or #rawUnits < 1 or #rawUnits > MAX_UNITS then
        return nil, "INVALID_UNITS"
    end
    local units = {}
    local order = {}
    for _, item in ipairs(rawUnits) do
        if type(item) ~= "table" or not validId(item.id)
            or (item.kind ~= "ZOMBIE" and item.kind ~= "BEAST")
            or units[item.id] ~= nil then
            return nil, "INVALID_UNIT"
        end
        units[item.id] = {
            id = item.id, kind = item.kind, faction = "NEUTRAL",
            pendingTeam = nil, progress = 0, expiresAt = 0, blockedUntil = startedAt,
        }
        table.insert(order, item.id)
    end
    table.sort(order)
    return { matchId = matchId, order = order, units = units,
        lastAt = startedAt, closed = false }, nil
end

local function candidatesTeam(candidates)
    if type(candidates) ~= "table" or #candidates > MAX_CANDIDATES then
        return nil
    end
    local found = nil
    local seen = {}
    for _, p in ipairs(candidates) do
        if type(p) ~= "table" or not validId(p.playerId) or seen[p.playerId] then
            return nil -- invalid server snapshot; contest/fail closed
        end
        seen[p.playerId] = true
        -- Distance, alive, request and team must be obtained from server.
        if p.alive == true and p.wantsCapture == true and p.carryingEgg ~= true
            and validTeam(p.team) and finite(p.distance)
            and p.distance >= 0 and p.distance <= CAPTURE_RADIUS then
            if found and found ~= p.team then
                return nil -- opposing teams contest: no progress
            end
            found = p.team
        end
    end
    return found
end

function NeutralSkirmishCore.step(previous, at, observations)
    if type(previous) ~= "table" or previous.closed or not finite(at)
        or not finite(previous.lastAt) or at < previous.lastAt
        or type(observations) ~= "table" then
        return previous, {}, "REJECTED_STEP"
    end
    local elapsed = math.min(at - previous.lastAt, MAX_TICK_SECONDS)
    local nextState = {matchId = previous.matchId, order = previous.order,
        units = {}, lastAt = at, closed = false}
    local events = {}
    local counts = { BLUE = 0, RED = 0 }
    for _, id in ipairs(previous.order) do
        local u = copyUnit(previous.units[id])
        if validTeam(u.faction) and at >= u.expiresAt then
            table.insert(events, {type = "EXPIRED", unitId = id, previousTeam = u.faction})
            u.faction = "NEUTRAL"
            u.blockedUntil = at + COOLDOWN_SECONDS
            u.pendingTeam = nil
            u.progress = 0
        end
        nextState.units[id] = u
        if validTeam(u.faction) then
            counts[u.faction] = counts[u.faction] + 1
        end
    end
    for _, id in ipairs(previous.order) do
        local u = nextState.units[id]
        if u.faction == "NEUTRAL" then
            local team = nil
            if at >= u.blockedUntil then
                team = candidatesTeam(observations[id] or {})
            end
            if team == nil or counts[team] >= MAX_CONTROLLED_PER_TEAM then
                u.pendingTeam = nil
                u.progress = 0
            else
                if u.pendingTeam ~= team then
                    u.pendingTeam = team
                    u.progress = 0
                end
                u.progress = math.min(CAPTURE_SECONDS, u.progress + elapsed)
                if u.progress >= CAPTURE_SECONDS then
                    u.faction = team
                    u.expiresAt = at + ALLY_SECONDS
                    u.progress = 0
                    u.pendingTeam = nil
                    counts[team] = counts[team] + 1
                    table.insert(events, {type = "CAPTURED", unitId = id,
                        kind = u.kind, team = team, expiresAt = u.expiresAt})
                end
            end
        end
    end
    return nextState, events, nil
end

function NeutralSkirmishCore.endRound(previous, at)
    if type(previous) ~= "table" or previous.closed or not finite(at)
        or at < previous.lastAt then
        return previous, {}, "REJECTED_END"
    end
    local nextState = {matchId = previous.matchId, order = previous.order,
        units = {}, lastAt = at, closed = true}
    for _, id in ipairs(previous.order) do
        local u = copyUnit(previous.units[id])
        u.faction = "NEUTRAL"
        u.pendingTeam = nil
        u.progress = 0
        u.expiresAt = 0
        nextState.units[id] = u
    end
    return nextState, {}, nil
end

-- Neutral vs neutral: only distinct species fight; allied same-team never fight.
function NeutralSkirmishCore.hostile(attackerFaction, defenderFaction, attackerKind, defenderKind)
    if attackerFaction == "NEUTRAL" and defenderFaction == "NEUTRAL" then
        return (attackerKind == "BEAST" or attackerKind == "ZOMBIE")
            and (defenderKind == "BEAST" or defenderKind == "ZOMBIE")
            and attackerKind ~= defenderKind
    end
    if attackerFaction == "NEUTRAL" then
        return validTeam(defenderFaction)
    end
    if defenderFaction == "NEUTRAL" then
        return validTeam(attackerFaction)
    end
    return validTeam(attackerFaction) and validTeam(defenderFaction)
        and attackerFaction ~= defenderFaction
end

NeutralSkirmishCore.RULES = {
    captureSeconds = CAPTURE_SECONDS, allySeconds = ALLY_SECONDS,
    cooldownSeconds = COOLDOWN_SECONDS, radius = CAPTURE_RADIUS,
    maxControlledPerTeam = MAX_CONTROLLED_PER_TEAM,
}
return NeutralSkirmishCore
