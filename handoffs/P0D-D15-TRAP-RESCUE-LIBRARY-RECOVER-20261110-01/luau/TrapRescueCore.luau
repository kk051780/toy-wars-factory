--!strict
-- TRAP RAIDERS / D15 pure reference. No Roblox Instance/Remote creation.
-- Only the real server RoundCoordinator may call these functions using its
-- authoritative player roster and server-clock. Never forward client fields.
local Core = {}

Core.CONFIG = table.freeze({
    CAST_RANGE = 16,
    RESCUE_RANGE = 10,
    CAST_COOLDOWN = 12,
    ROOT_SECONDS = 2,
    ESCAPE_AFTER = 1.25,
    RESCUE_AFTER = 0.5,
    DOT_TICKS = 3,
    DOT_INTERVAL = 1,
    DOT_PER_TICK = 3,
    IMMUNITY_SECONDS = 6,
    MAX_ACTIVE_PER_TRAPPER = 1,
    MAX_ROSTER = 24,
    MAX_DURATION_SECONDS = 3600,
})

local function finite(n: any): boolean
    return type(n) == "number" and n == n and n > -math.huge and n < math.huge
end

local function validId(v: any): boolean
    return type(v) == "number" and v % 1 == 0 and v >= 1 and v <= 1000000000000000
end

local function validTeam(v: any): boolean
    return v == "BLUE" or v == "RED"
end

local function validPosition(x: any, z: any): boolean
    return finite(x) and finite(z) and math.abs(x) <= 100000 and math.abs(z) <= 100000
end

local function dist2(a: any, b: any): number
    local dx, dz = a.x - b.x, a.z - b.z
    return dx * dx + dz * dz
end

local function release(state: any, targetId: number)
    if state.effects[targetId] ~= nil then
        state.effects[targetId] = nil
        state.immuneUntil[targetId] = math.max(state.immuneUntil[targetId] or 0, state.now + Core.CONFIG.IMMUNITY_SECONDS)
    end
end

function Core.new(matchId: any)
    assert(type(matchId) == "string" and #matchId >= 1 and #matchId <= 96, "invalid server matchId")
    return {
        matchId = matchId,
        now = 0,
        closed = false,
        roster = {},
        effects = {},
        immuneUntil = {},
        casterNextAt = {},
    }
end

-- Must be supplied by the server's authoritative roster/character state.
function Core.syncPlayer(state: any, userId: any, team: any, job: any, alive: any, x: any, z: any): (boolean, string)
    if state.closed then return false, "MATCH_CLOSED" end
    if not validId(userId) or not validTeam(team) or type(job) ~= "string"
        or type(alive) ~= "boolean" or not validPosition(x, z) then
        return false, "BAD_SERVER_ROSTER"
    end
    local old = state.roster[userId]
    if old == nil then
        local count = 0
        for _ in pairs(state.roster) do count += 1 end
        if count >= Core.CONFIG.MAX_ROSTER then return false, "ROSTER_FULL" end
    end
    if old ~= nil and (old.team ~= team or old.job ~= job or (old.alive and not alive)) then
        release(state, userId)
        for targetId, fx in pairs(state.effects) do
            if fx.caster == userId then release(state, targetId) end
        end
    end
    state.roster[userId] = {team = team, job = job, alive = alive, x = x, z = z}
    return true, "SYNCED"
end

function Core.removePlayer(state: any, userId: number)
    if state.closed then return end
    release(state, userId)
    for targetId, fx in pairs(state.effects) do
        if fx.caster == userId then release(state, targetId) end
    end
    state.roster[userId] = nil
end

-- This is the ONLY method that advances time. The real server calls it BEFORE
-- any action on every Heartbeat/tick. Each returned event is a server-only
-- instruction: applying damage/root in Roblox remains the adapter's job.
function Core.advance(state: any, serverNow: any): (boolean, string, {any})
    if state.closed then return false, "MATCH_CLOSED", {} end
    if not finite(serverNow) or serverNow < state.now or serverNow > Core.CONFIG.MAX_DURATION_SECONDS then
        return false, "BAD_CLOCK", {}
    end
    state.now = serverNow
    local outputs = {}
    for targetId, fx in pairs(state.effects) do
        local target = state.roster[targetId]
        local source = state.roster[fx.caster]
        if target == nil or source == nil or not target.alive or not source.alive or target.team == source.team then
            release(state, targetId)
        else
            -- Delayed ticks are emitted AT MOST ONCE, even for long frame stalls.
            while fx.ticks < Core.CONFIG.DOT_TICKS and serverNow >= fx.started + (fx.ticks + 1) * Core.CONFIG.DOT_INTERVAL do
                fx.ticks += 1
                table.insert(outputs, {kind = "POISON_DAMAGE", targetId = targetId,
                    casterId = fx.caster, damage = Core.CONFIG.DOT_PER_TICK, tick = fx.ticks,
                    matchId = state.matchId})
            end
            if serverNow >= fx.started + Core.CONFIG.DOT_TICKS * Core.CONFIG.DOT_INTERVAL then
                release(state, targetId)
            end
        end
    end
    return true, "ADVANCED", outputs
end

local function activeCasterCount(state: any, userId: number): number
    local n = 0
    for _, fx in pairs(state.effects) do
        if fx.caster == userId then n += 1 end
    end
    return n
end

function Core.tryCast(state: any, casterId: any, targetId: any): (boolean, string)
    if state.closed then return false, "MATCH_CLOSED" end
    if not validId(casterId) or not validId(targetId) or casterId == targetId then return false, "BAD_IDS" end
    local source = state.roster[casterId]
    local target = state.roster[targetId]
    if source == nil or target == nil or not source.alive or not target.alive then return false, "NO_LIVE_PLAYER" end
    if source.job ~= "TRAPPER" then return false, "WRONG_JOB" end
    if source.team == target.team then return false, "FRIENDLY_FIRE" end
    if dist2(source, target) > Core.CONFIG.CAST_RANGE ^ 2 then return false, "OUT_OF_RANGE" end
    if state.now < (state.casterNextAt[casterId] or 0) then return false, "COOLDOWN" end
    if state.effects[targetId] ~= nil then return false, "ALREADY_TRAPPED" end
    if state.now < (state.immuneUntil[targetId] or 0) then return false, "TARGET_IMMUNE" end
    if activeCasterCount(state, casterId) >= Core.CONFIG.MAX_ACTIVE_PER_TRAPPER then return false, "CASTER_LIMIT" end
    state.effects[targetId] = {caster = casterId, started = state.now, ticks = 0}
    state.casterNextAt[casterId] = state.now + Core.CONFIG.CAST_COOLDOWN
    return true, "TRAPPED"
end

function Core.tryRescue(state: any, rescuerId: any, targetId: any): (boolean, string)
    if state.closed then return false, "MATCH_CLOSED" end
    if not validId(rescuerId) or not validId(targetId) or rescuerId == targetId then return false, "BAD_IDS" end
    local rescuer, target = state.roster[rescuerId], state.roster[targetId]
    local fx = state.effects[targetId]
    if fx == nil then return false, "NOT_TRAPPED" end
    if rescuer == nil or target == nil or not rescuer.alive or not target.alive then return false, "NO_LIVE_PLAYER" end
    if rescuer.team ~= target.team then return false, "NOT_ALLY" end
    if state.now < fx.started + Core.CONFIG.RESCUE_AFTER then return false, "RESCUE_TOO_EARLY" end
    if dist2(rescuer, target) > Core.CONFIG.RESCUE_RANGE ^ 2 then return false, "OUT_OF_RANGE" end
    release(state, targetId)
    return true, "RESCUED"
end

function Core.tryEscape(state: any, targetId: any): (boolean, string)
    if state.closed then return false, "MATCH_CLOSED" end
    if not validId(targetId) then return false, "BAD_IDS" end
    local fx = state.effects[targetId]
    if fx == nil then return false, "NOT_TRAPPED" end
    local target = state.roster[targetId]
    if target == nil or not target.alive then return false, "NO_LIVE_PLAYER" end
    if state.now < fx.started + Core.CONFIG.ESCAPE_AFTER then return false, "ESCAPE_TOO_EARLY" end
    release(state, targetId)
    return true, "ESCAPED"
end

function Core.status(state: any, userId: number)
    local fx = state.effects[userId]
    if fx == nil then
        return {trapped = false, rooted = false, poison = false, immunityRemaining = math.max(0, (state.immuneUntil[userId] or 0) - state.now)}
    end
    return {trapped = true, rooted = state.now < fx.started + Core.CONFIG.ROOT_SECONDS,
        poison = fx.ticks < Core.CONFIG.DOT_TICKS,
        immunityRemaining = 0}
end

function Core.endMatch(state: any)
    state.closed = true
    state.effects = {}
    state.roster = {}
    state.immuneUntil = {}
    state.casterNextAt = {}
end

return Core
