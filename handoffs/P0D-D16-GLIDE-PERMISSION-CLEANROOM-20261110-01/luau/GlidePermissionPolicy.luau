--!strict
-- TRAP RAIDERS / P0-D / independent optional policy, NOT an AES-source restoration.
-- Server-only pure decision engine. Do not pass client-derived authority snapshots.
-- Disabled unless an OWNER-reviewed server adapter explicitly supplies enabled=true.
local GlidePermissionPolicy = {}

local MAX_SECONDS = 5
local COOLDOWN_SECONDS = 25
local MAX_HORIZONTAL = 18 -- Suggested only; real server physics must enforce.
local MIN_DESCENT_VELOCITY = -10 -- Suggested only; not a physics implementation.

local function finiteNumber(x)
    return type(x) == "number" and x == x and x > -math.huge and x < math.huge
end

local function positiveInteger(x)
    return finiteNumber(x) and x >= 1 and x <= 9007199254740991 and x % 1 == 0
end

local function clone(s)
    return {
        userId = s.userId,
        epoch = s.epoch,
        lastSeq = s.lastSeq,
        lastNow = s.lastNow,
        mode = s.mode,
        activeUntil = s.activeUntil,
        cooldownUntil = s.cooldownUntil,
        teamToken = s.teamToken,
    }
end

function GlidePermissionPolicy.newState(userId, epoch)
    assert(positiveInteger(userId), "server userId must be a positive integer")
    assert(positiveInteger(epoch), "server round epoch must be a positive integer")
    return {
        userId = userId,
        epoch = epoch,
        lastSeq = 0,
        lastNow = -1,
        mode = "IDLE",
        activeUntil = 0,
        cooldownUntil = 0,
        teamToken = nil,
    }
end

local function action(name, reason, opts)
    local out = { action = name, reason = reason }
    if opts then
        out.horizontalSpeedCeiling = MAX_HORIZONTAL
        out.descentVelocityFloor = MIN_DESCENT_VELOCITY
        out.expiresAt = opts.activeUntil
    end
    return out
end

local function toCooldown(nextState, now, reason)
    nextState.mode = "COOLDOWN"
    nextState.activeUntil = 0
    nextState.teamToken = nil
    nextState.cooldownUntil = now + COOLDOWN_SECONDS
    return nextState, action("STOP", reason, nil)
end

local function serverAuthorityValid(snapshot)
    if type(snapshot) ~= "table" then return false end
    for _, field in ipairs({"alive", "activeRound", "teamValid", "onGround", "hasEgg", "mounted", "snared", "rewinding"}) do
        if type(snapshot[field]) ~= "boolean" then return false end
    end
    if type(snapshot.teamToken) ~= "string" or #snapshot.teamToken == 0 or #snapshot.teamToken > 96 then return false end
    return finiteNumber(snapshot.fallDistance) and snapshot.fallDistance >= 0
       and finiteNumber(snapshot.verticalVelocity)
end

local function canContinue(snapshot, originalTeam)
    return snapshot.alive and snapshot.activeRound and snapshot.teamValid
       and snapshot.teamToken == originalTeam
       and not snapshot.onGround and snapshot.verticalVelocity < 0
       and not snapshot.hasEgg and not snapshot.mounted
       and not snapshot.snared and not snapshot.rewinding
end

-- Call ONLY from a real server-authoritative adapter. Client may request START/STOP intent,
-- but server must supply player identity, epoch, sequence, monotonic clock and all status.
-- Returns a new state and decision. Never modifies the input state, Player or physics.
function GlidePermissionPolicy.step(state, intent, snapshot, config)
    if type(state) ~= "table" or type(snapshot) ~= "table" then
        return state, action("STOP", "SNAPSHOT_MISSING", nil)
    end
    if not positiveInteger(snapshot.userId) or snapshot.userId ~= state.userId
       or not positiveInteger(snapshot.epoch) or not positiveInteger(snapshot.seq)
       or not finiteNumber(snapshot.now) or snapshot.now < 0 then
        return state, action("STOP", "IDENTITY_OR_CLOCK_INVALID", nil)
    end
    if snapshot.epoch < state.epoch or snapshot.now < state.lastNow
       or (snapshot.epoch == state.epoch and snapshot.seq <= state.lastSeq) then
        return state, action("STOP", "STALE_AUTHORITY", nil)
    end
    if intent ~= "START" and intent ~= "STOP" and intent ~= "TICK" then
        if state.mode == "ACTIVE" then
            local failed = clone(state)
            failed.lastSeq = snapshot.seq
            failed.lastNow = snapshot.now
            return toCooldown(failed, snapshot.now, "UNKNOWN_INTENT")
        end
        return state, action("STOP", "UNKNOWN_INTENT", nil)
    end
    if not serverAuthorityValid(snapshot) then
        if state.mode == "ACTIVE" then
            local failed = clone(state)
            failed.lastSeq = snapshot.seq
            failed.lastNow = snapshot.now
            return toCooldown(failed, snapshot.now, "AUTHORITY_INCOMPLETE")
        end
        return state, action("STOP", "AUTHORITY_INCOMPLETE", nil)
    end

    local nextState = clone(state)
    nextState.lastSeq = snapshot.seq
    nextState.lastNow = snapshot.now
    if snapshot.epoch > state.epoch then
        local wasActive = state.mode == "ACTIVE"
        nextState.epoch = snapshot.epoch
        nextState.mode = "IDLE"
        nextState.activeUntil = 0
        nextState.cooldownUntil = 0
        nextState.teamToken = nil
        return nextState, action(wasActive and "STOP" or "NONE", "ROUND_CHANGED", nil)
    end

    if type(config) ~= "table" or config.enabled ~= true then
        if state.mode == "ACTIVE" then
            return toCooldown(nextState, snapshot.now, "DISABLED")
        end
        return nextState, action("NONE", "DISABLED", nil)
    end

    if state.mode == "ACTIVE" then
        if not canContinue(snapshot, state.teamToken) then
            return toCooldown(nextState, snapshot.now, "AUTHORITY_LOST")
        end
        if snapshot.now >= state.activeUntil then
            return toCooldown(nextState, snapshot.now, "TIME_LIMIT")
        end
        if intent == "STOP" then
            return toCooldown(nextState, snapshot.now, "USER_STOP")
        end
        return nextState, action("MAINTAIN", "ACTIVE", nextState)
    end

    if intent ~= "START" then
        return nextState, action("NONE", "NO_REQUEST", nil)
    end
    if snapshot.now < state.cooldownUntil then
        return nextState, action("DENY", "COOLDOWN", nil)
    end
    if not canContinue(snapshot, snapshot.teamToken)
       or snapshot.fallDistance < 3 or snapshot.fallDistance > 60 then
        return nextState, action("DENY", "NOT_ELIGIBLE", nil)
    end
    nextState.mode = "ACTIVE"
    nextState.teamToken = snapshot.teamToken
    nextState.activeUntil = snapshot.now + MAX_SECONDS
    return nextState, action("START", "ELIGIBLE", nextState)
end

return GlidePermissionPolicy
