-- BATTLE-HP-REGEN | pure, server-only policy; NOT a second Health/Combat writer.
-- Call from the unique existing Game/Combat/Host HP owner after server damage settles.
-- The caller is solely responsible for Humanoid.Health writes and match authority.
local Policy = {}
local QUIET_SECONDS = 7
local RATE_PER_SECOND = 0.007
local MAX_ELAPSED_STEP = 0.5
local EPS = 0.000001

local ROLE_MAX_HP = {
    WARRIOR = 250,
    MAGE = 195,
    NINJA = 185, -- player-facing name: Assassin; preserve internal ID
    TRAPPER = 205,
    BUILDER = 225,
    BEAST_TAMER = 220,
    ZOMBIE_MASTER = 230,
}

local function finite(n)
    return type(n) == "number" and n == n and n >= 0 and n < math.huge
end

function Policy.maxHPForRole(roleId)
    return ROLE_MAX_HP[roleId]
end

function Policy.new(sessionId, now, health, maxHP)
    assert(type(sessionId) == "string" and #sessionId > 0, "session id required")
    assert(finite(now) and finite(maxHP) and maxHP > 0, "invalid clock/maxHP")
    assert(finite(health) and health <= maxHP, "invalid health")
    return {
        sessionId = sessionId,
        lastDamageAt = now,
        lastSampleAt = now,
        lastHealth = health,
        lastMaxHP = maxHP,
    }
end

local function sample(state, now, hp, maxHP)
    state.lastSampleAt = now
    state.lastHealth = hp
    state.lastMaxHP = maxHP
end

-- step returns (nonnegative HEAL DELTA, reason); it never mutates player HP.
-- input must be server-trusted: sessionId, now, health, maxHP, inMatch, downed, hasDot.
-- Recreate/reset state per match or avatar. Never feed a client-provided clock or HP.
function Policy.step(state, input)
    if type(state) ~= "table" or type(input) ~= "table" then
        return 0, "INVALID_STATE"
    end
    local now, hp, maxHP = input.now, input.health, input.maxHP
    if type(input.sessionId) ~= "string" or #input.sessionId == 0
        or not finite(now) or not finite(hp) or not finite(maxHP)
        or maxHP <= 0 or hp > maxHP then
        return 0, "INVALID_SAMPLE"
    end
    if input.sessionId ~= state.sessionId then
        local reset = Policy.new(input.sessionId, now, hp, maxHP)
        for key, value in pairs(reset) do
            state[key] = value
        end
        return 0, "SESSION_RESET"
    end
    if not finite(state.lastSampleAt) or now < state.lastSampleAt
        or not finite(state.lastHealth) or not finite(state.lastMaxHP)
        or not finite(state.lastDamageAt) or now < state.lastDamageAt then
        state.lastDamageAt = now
        sample(state, now, hp, maxHP)
        return 0, "CLOCK_RESET"
    end
    if math.abs(maxHP - state.lastMaxHP) > EPS then
        state.lastDamageAt = now
        sample(state, now, hp, maxHP)
        return 0, "MAXHP_CHANGE"
    end
    -- Detect actual decreases, including PVP, bosses, environmental hits and DOT.
    -- Positive HP changes from a dedicated healer are not treated as attacks.
    if hp < state.lastHealth - EPS then
        state.lastDamageAt = now
        sample(state, now, hp, maxHP)
        return 0, "REAL_DAMAGE"
    end
    if input.inMatch ~= true or input.downed == true or input.hasDot == true or hp <= 0 then
        state.lastDamageAt = now
        sample(state, now, hp, maxHP)
        return 0, "BLOCKED"
    end
    local elapsed = math.min(now - state.lastSampleAt, MAX_ELAPSED_STEP)
    local recoverable = math.min(elapsed, math.max(0, now - math.max(state.lastDamageAt + QUIET_SECONDS, state.lastSampleAt)))
    local amount = math.min(math.max(maxHP - hp, 0), maxHP * RATE_PER_SECOND * recoverable)
    sample(state, now, hp, maxHP)
    if amount > 0 then
        return amount, "REGEN"
    end
    return 0, "WAIT"
end

return Policy
