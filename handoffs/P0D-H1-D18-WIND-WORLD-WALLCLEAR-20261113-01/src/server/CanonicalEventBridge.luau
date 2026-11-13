--!strict
-- P0-D D08: single canonical server event bridge for existing v40 ChaosEventCore.
-- Reference-only: no Roblox RemoteEvent receiver, RNG, AI, new weather effects or second event selector.
local Bridge = {}
Bridge.__index = Bridge

local VALID_STAGE = { S1 = true, S2 = true, S3 = true, S4 = true }
local VALID_WEATHER = {
    WX01_METEOR = true, WX02_SMALL = true, WX03_CROWN = true,
    WX04_GLIDE = true, WX05_CLOCK = true,
}

local function finite(v)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end
local function validId(v)
    return type(v) == "string" and #v >= 1 and #v <= 96 and v:match("^[%w_%-]+$") ~= nil
end
local function call(fn, ...)
    if type(fn) ~= "function" then return false, "MISSING_TRUSTED_CALLBACK" end
    local ok, result = pcall(fn, ...)
    if not ok then return false, "TRUSTED_CALLBACK_FAILED" end
    if result == false then return false, "TRUSTED_CALLBACK_REJECTED" end
    return true, result
end
local function equivalentRound(a, b)
    return type(b) == "table" and a.matchId == b.matchId
        and a.stage == b.stage and a.epoch == b.epoch
        and a.startedAt == b.startedAt and a.deadline == b.deadline
end

-- All arguments are OWNER-reviewed trusted server modules/callbacks, never RemoteEvent data.
-- enabled defaults FALSE. PC must validate the only active event chooser before enabling.
function Bridge.new(v40Core, config)
    assert(type(v40Core) == "table" and type(v40Core.new) == "function"
        and type(v40Core.advance) == "function", "V40_CORE_REQUIRED")
    assert(type(config) == "table", "SERVER_CONFIG_REQUIRED")
    assert(type(config.readRound) == "function", "TRUSTED_READ_ROUND_REQUIRED")
    local self = setmetatable({
        core = v40Core, callbacks = config, enabled = config.enabled == true,
        current = nil, retired = {}, retiredCount = 0, busy = false, disabledReason = nil,
    }, Bridge)
    return self
end

function Bridge:cleanup(reason)
    local cur = self.current
    if not cur then return end
    if not cur.clean then
        cur.clean = true
        if cur.activated or cur.warned then
            -- A cleanup failure is recorded, but no second cleanup is attempted.
            local ok = call(self.callbacks.onCleanup, {
                matchId = cur.matchId, stage = cur.stage, epoch = cur.epoch,
                kind = cur.kind, subtype = cur.externalSubtype, reason = reason,
            })
            if not ok then
                self.disabledReason = "CLEANUP_CALLBACK_FAILED"
                self.enabled = false
            end
        end
    end
    local key = cur.matchId .. ":" .. tostring(cur.epoch)
    if not self.retired[key] then
        self.retired[key] = true
        self.retiredCount += 1
    end
    -- Bounded state: stop rather than evict anti-replay evidence silently.
    if self.retiredCount >= 512 then
        self.enabled = false
        self.disabledReason = "RETIRED_ROUND_LIMIT_REACHED"
    end
    self.current = nil
end

local function decideSubtype(self, stage, kind, subtype)
    if kind == "WEATHER" then
        if not VALID_WEATHER[subtype] then return nil, "UNKNOWN_WEATHER" end
        return subtype, nil
    end
    if kind ~= "BOSS" then return nil, "UNKNOWN_EVENT_KIND" end
    if (stage == "S1" or stage == "S3") and subtype == "GOROGAN" then
        return subtype, nil
    end
    -- OLD v40 emits RAIGALD while the later D07 packet spells LIGARDO.
    -- PC must validate the actual game ID and explicitly approve the mapping.
    if (stage == "S2" or stage == "S4") and subtype == "RAIGALD" then
        if self.callbacks.approvedRaigaldAsLigardo == true then return "LIGARDO", nil end
        return nil, "RAIGALD_LIGARDO_ALIAS_REVIEW_REQUIRED"
    end
    return nil, "UNKNOWN_BOSS"
end

local function trustedRound(config)
    local ok, snapshot = pcall(config.readRound)
    if not ok or type(snapshot) ~= "table" then return nil, "ROUND_SNAPSHOT_UNAVAILABLE" end
    if not validId(snapshot.matchId) or not VALID_STAGE[snapshot.stage]
        or not finite(snapshot.startedAt) or not finite(snapshot.deadline)
        or not finite(snapshot.now) or not finite(snapshot.epoch)
        or snapshot.epoch % 1 ~= 0 or snapshot.epoch < 0
        or snapshot.epoch >= 1024 or snapshot.startedAt < 0
        or snapshot.deadline <= snapshot.startedAt or snapshot.now < snapshot.startedAt then
        return nil, "ROUND_SNAPSHOT_INVALID"
    end
    if type(snapshot.active) ~= "boolean" then return nil, "ROUND_ACTIVE_INVALID" end
    return snapshot, nil
end

function Bridge:tickInternal()
    if not self.enabled then return false, self.disabledReason or "DISABLED_DEFAULT" end
    local snapshot, reason = trustedRound(self.callbacks)
    if not snapshot then
        self:cleanup(reason)
        self.enabled = false
        return false, reason
    end
    local cur = self.current
    if cur and not equivalentRound(cur, snapshot) then
        self:cleanup("ROUND_REPLACED")
        if not self.enabled then return false, self.disabledReason or "CLEANUP_FAILED" end
        cur = nil
    end
    if not cur then
        if not snapshot.active or snapshot.now >= snapshot.deadline then return false, "ROUND_INACTIVE" end
        if self.retired[snapshot.matchId .. ":" .. tostring(snapshot.epoch)] then
            return false, "ROUND_REPLAY_DENIED"
        end
        local ok, state = pcall(self.core.new, snapshot.matchId, snapshot.stage, snapshot.startedAt)
        if not ok then self.enabled = false; return false, "V40_NEW_FAILED" end
        cur = { matchId = snapshot.matchId, stage = snapshot.stage,
            epoch = snapshot.epoch, startedAt = snapshot.startedAt,
            deadline = snapshot.deadline, lastNow = snapshot.startedAt,
            state = state, rollUsed = false, activated = false, warned = false,
            kind = "NONE", externalSubtype = "NONE", clean = false,
            emitted = {}, }
        self.current = cur
    end
    if snapshot.now < cur.lastNow then
        self:cleanup("TIME_REVERSED")
        self.enabled = false
        return false, "TIME_REVERSED"
    end
    cur.lastNow = snapshot.now
    local roll = nil
    -- Exactly one server roll. The trusted producer must NOT call client supplied RNG.
    if not cur.state.decided and snapshot.active and snapshot.now >= cur.startedAt + 20
        and snapshot.now < cur.deadline and (cur.deadline - snapshot.now) >= 19 then
        if cur.rollUsed then
            self:cleanup("DUPLICATE_ROLL")
            self.enabled = false
            return false, "DUPLICATE_ROLL"
        end
        cur.rollUsed = true
        local ok, result = call(self.callbacks.serverRoll, snapshot.matchId, snapshot.epoch)
        if not ok or not finite(result) or result % 1 ~= 0 or result < 0 or result >= 100 then
            self:cleanup("SERVER_ROLL_INVALID")
            self.enabled = false
            return false, "SERVER_ROLL_INVALID"
        end
        roll = result
        local fresh, why = trustedRound(self.callbacks)
        if not fresh or not equivalentRound(cur, fresh) or fresh.now < snapshot.now
            or not fresh.active then
            self:cleanup(why or "ROUND_CHANGED_DURING_RNG")
            self.enabled = false
            return false, "ROUND_CHANGED_DURING_RNG"
        end
    end
    local ok, nextState, event = pcall(self.core.advance,
        cur.state, snapshot.now, snapshot.deadline, roll, snapshot.active)
    if not ok or type(nextState) ~= "table" then
        self:cleanup("V40_ADVANCE_FAILED")
        self.enabled = false
        return false, "V40_ADVANCE_FAILED"
    end
    cur.state = nextState
    if not event then
        if nextState.finished or nextState.phase == "DONE" then self:cleanup("V40_FINISHED") end
        return true, "NO_EVENT"
    end
    if type(event) ~= "table" or event.matchId ~= cur.matchId
        or (event.event ~= "WARNING" and event.event ~= "ACTIVATE" and event.event ~= "CLEANUP") then
        self:cleanup("BAD_V40_EVENT")
        self.enabled = false
        return false, "BAD_V40_EVENT"
    end
    if cur.emitted[event.event] then
        self:cleanup("REPLAYED_V40_EVENT")
        self.enabled = false
        return false, "REPLAYED_V40_EVENT"
    end
    cur.emitted[event.event] = true
    if event.event == "CLEANUP" then
        self:cleanup("V40_CLEANUP")
        return true, "CLEANUP"
    end
    local subtype, err = decideSubtype(self, cur.stage, event.kind, event.subtype)
    if err then
        self:cleanup(err)
        self.enabled = false
        return false, err
    end
    -- Weather warning is suppressed if the server has no approved weather runtime.
    -- Otherwise the player would see a promise of a mechanic that cannot activate.
    if event.kind == "WEATHER" and type(self.callbacks.onWeatherActivate) ~= "function" then
        self:cleanup("WEATHER_RUNTIME_MISSING")
        self.enabled = false
        return false, "WEATHER_RUNTIME_MISSING"
    end
    if event.event == "ACTIVATE" and cur.emitted.WARNING ~= true then
        self:cleanup("ACTIVATE_WITHOUT_WARNING")
        self.enabled = false
        return false, "ACTIVATE_WITHOUT_WARNING"
    end
    if event.event == "ACTIVATE" then cur.activated = true else cur.warned = true end
    cur.kind = event.kind
    cur.externalSubtype = subtype
    local envelope = {matchId = cur.matchId, stage = cur.stage, epoch = cur.epoch,
        kind = event.kind, subtype = subtype, phase = event.event,
        validUntil = event.untilAt}
    local handler = event.event == "WARNING" and self.callbacks.onWarning
        or (event.kind == "BOSS" and self.callbacks.onBossActivate or self.callbacks.onWeatherActivate)
    if type(handler) ~= "function" then
        self:cleanup("HANDLER_MISSING")
        self.enabled = false
        return false, "HANDLER_MISSING"
    end
    local dispatched = call(handler, envelope)
    if not dispatched then
        self:cleanup("HANDLER_REJECTED")
        self.enabled = false
        return false, "HANDLER_REJECTED"
    end
    -- Handlers may yield; their authoritative round must still be current on resume.
    local fresh, why = trustedRound(self.callbacks)
    if not fresh or not equivalentRound(cur, fresh) or fresh.now < snapshot.now
        or not fresh.active or fresh.now >= fresh.deadline then
        self:cleanup(why or "ROUND_CHANGED_DURING_CALLBACK")
        self.enabled = false
        return false, "ROUND_CHANGED_DURING_CALLBACK"
    end
    return true, event.event
end

function Bridge:tick()
    if self.busy then return false, "TICK_BUSY" end
    self.busy = true
    local ok, a, b = pcall(self.tickInternal, self)
    self.busy = false
    if not ok then
        self:cleanup("TICK_EXCEPTION")
        self.enabled = false
        return false, "TICK_EXCEPTION"
    end
    return a, b
end

function Bridge:stop()
    self:cleanup("OWNER_STOP")
    self.enabled = false
    self.disabledReason = "OWNER_STOP"
end

return Bridge
