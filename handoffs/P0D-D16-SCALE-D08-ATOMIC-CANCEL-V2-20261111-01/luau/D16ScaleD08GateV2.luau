--!strict
-- P0D TRAP RAIDERS: independent D16/D08 gate V2, no secret and no Roblox side effects.
-- Replaces OPTIONAL V1 ac503729...; do not install both. ORIGINAL D16 AES ZIP NOT recovered.
-- Only a trusted, reviewed single D08 onWeatherActivate/onCleanup server router may call here.
-- Default OFF. Never connect this to clients or use as a second event chooser.
local Gate = {}
Gate.__index = Gate

local WEATHER = {
    WX01_METEOR = true, WX02_SMALL = true, WX03_CROWN = true,
    WX04_GLIDE = true, WX05_CLOCK = true,
}
local STAGES = { S1 = true, S2 = true, S3 = true, S4 = true }
local MAX_SEC = 10000000000
local function finite(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge
end
local function validId(s)
    return type(s) == "string" and #s >= 1 and #s <= 96
        and s:match("^[%w_%-]+$") ~= nil
end
local function roundSnapshot(self)
    if type(self.config.readRound) ~= "function" then return nil, "READ_ROUND_MISSING" end
    local ok, raw = pcall(self.config.readRound)
    if not ok or type(raw) ~= "table" then return nil, "READ_ROUND_FAILED" end
    if not validId(raw.matchId) or not STAGES[raw.stage]
        or not finite(raw.epoch) or raw.epoch % 1 ~= 0 or raw.epoch < 1 or raw.epoch >= 1024
        or not finite(raw.now) or raw.now < 0 or raw.now > MAX_SEC
        or not finite(raw.startedAt) or not finite(raw.deadline)
        or raw.startedAt < 0 or raw.startedAt > raw.now
        or raw.deadline <= raw.startedAt or raw.deadline > MAX_SEC
        or type(raw.active) ~= "boolean" then
        return nil, "ROUND_INVALID"
    end
    -- Only validated primitives cross a potentially yielding callback boundary.
    local s = { matchId = raw.matchId, stage = raw.stage, epoch = raw.epoch,
        startedAt = raw.startedAt, deadline = raw.deadline, now = raw.now, active = raw.active }
    local ms = math.floor(s.now * 1000 + 0.000001)
    if self.lastTrustedNowMs ~= nil and ms < self.lastTrustedNowMs then
        return nil, "CLOCK_BACKWARDS"
    end
    self.lastTrustedNowMs = ms
    return s, nil
end
local function sameRound(a, b)
    return a.matchId == b.matchId and a.stage == b.stage and a.epoch == b.epoch
        and a.startedAt == b.startedAt and a.deadline == b.deadline
        and b.active == true and b.now >= a.now
end
local function sameEnvelope(a, e)
    return type(e) == "table" and e.matchId == a.matchId
        and e.stage == a.stage and e.epoch == a.epoch
        and e.subtype == a.subtype and e.kind == "WEATHER"
end
local function sortedRoster(raw)
    if type(raw) ~= "table" then return nil end
    local n = #raw
    if n < 1 or n > 24 then return nil end
    local sorted, seen = {}, {}
    for i = 1, n do
        local id = raw[i]
        if not finite(id) or id < 1 or id > 9007199254740991
            or id % 1 ~= 0 or seen[id] then return nil end
        seen[id] = true
        sorted[i] = id
    end
    for k in pairs(raw) do
        if not finite(k) or k % 1 ~= 0 or k < 1 or k > n then return nil end
    end
    table.sort(sorted)
    return sorted
end
local function readRoster(self)
    if type(self.config.readRoster) ~= "function" then return nil end
    local ok, raw = pcall(self.config.readRoster)
    if not ok then return nil end
    return sortedRoster(raw)
end
local function sameRoster(a, b)
    if a == nil or b == nil or #a ~= #b then return false end
    for i = 1, #a do if a[i] ~= b[i] then return false end end
    return true
end
local function goodActivateEnvelope(e)
    return type(e) == "table" and e.kind == "WEATHER" and e.phase == "ACTIVATE"
        and WEATHER[e.subtype] == true and validId(e.matchId) and STAGES[e.stage] == true
        and finite(e.epoch) and e.epoch >= 1 and e.epoch < 1024 and e.epoch % 1 == 0
        and finite(e.validUntil) and e.validUntil <= MAX_SEC
end

function Gate.new(scaleCore, config)
    assert(type(scaleCore) == "table" and type(scaleCore.new) == "function"
        and type(scaleCore.begin) == "function" and type(scaleCore.snapshot) == "function"
        and type(scaleCore.close) == "function", "SCALE_CORE_REQUIRED")
    assert(type(config) == "table", "CONFIG_REQUIRED")
    return setmetatable({
        core = scaleCore, config = config, state = scaleCore.new(), active = nil,
        enabled = config.enabled == true and config.approvedByOwner == true
            and config.visualRendererReady == true,
        cancelGeneration = 0, inFlight = nil, busy = false,
        lastTrustedNowMs = nil, stoppedReason = nil,
    }, Gate)
end

-- The optional Core is pure and does not yield. Use only cached validated time when
-- the authoritative round is gone. A failed Core.close permanently disables the gate.
function Gate:_closeActive(reason)
    local a = self.active
    if a == nil then return true, "NOT_ACTIVE" end
    self.active = nil
    local ms = math.max(a.startedAtMs, self.lastTrustedNowMs or a.startedAtMs,
        self.state.lastNowMs or a.startedAtMs)
    local ok, closed, why = pcall(self.core.close, self.state, a.matchId, a.epoch, ms)
    if not ok or closed ~= true then
        self.enabled = false
        self.stoppedReason = "CORE_CLOSE_FAILED"
        return false, "CORE_CLOSE_FAILED"
    end
    return true, reason
end
function Gate:_cancelPending()
    self.cancelGeneration += 1
    self.inFlight = nil
end
function Gate:_isCurrent(token, pending)
    return self.enabled and self.cancelGeneration == token and self.inFlight == pending
end

-- Returns false if this subtype has not been explicitly approved for SCALE.
-- The calling server router must independently route ALL OTHER weather types,
-- not feed every D08 weather through this optional scale handler.
function Gate:onWeatherActivate(e)
    if not self.enabled then return false, self.stoppedReason or "DISABLED_DEFAULT" end
    if self.busy then return false, "BUSY" end
    if not goodActivateEnvelope(e) then return false, "INVALID_D08_ENVELOPE" end
    local mapping = self.config.approvedSubtypeEffects
    if type(mapping) ~= "table" then return false, "NO_EXPLICIT_MAPPING" end
    local effect = mapping[e.subtype]
    if effect ~= "GIANT_ONE" and effect ~= "MINI_ALL" then
        return false, "UNAPPROVED_SUBTYPE"
    end
    local pending = { matchId = e.matchId, stage = e.stage, epoch = e.epoch,
        subtype = e.subtype, kind = "WEATHER", validUntil = e.validUntil }
    local token = self.cancelGeneration
    self.inFlight = pending
    self.busy = true
    local executed, accepted, status = pcall(function()
        local start, err = roundSnapshot(self)
        if not self:_isCurrent(token, pending) then return false, "CANCELLED_DURING_CALLBACK" end
        if not start then return false, err end
        if not start.active or e.matchId ~= start.matchId
            or e.stage ~= start.stage or e.epoch ~= start.epoch then
            return false, "ROUND_MISMATCH"
        end
        if e.validUntil <= start.now or e.validUntil > start.now + 9 then
            return false, "INVALID_EVENT_DEADLINE"
        end
        local roster = readRoster(self)
        if not self:_isCurrent(token, pending) then return false, "CANCELLED_DURING_CALLBACK" end
        if not roster then return false, "ROSTER_UNAVAILABLE" end
        local target = nil
        if effect == "GIANT_ONE" then
            if type(self.config.chooseGiantTarget) ~= "function" then
                return false, "TARGET_CALLBACK_MISSING"
            end
            local targetOK, player = pcall(self.config.chooseGiantTarget, roster)
            if not self:_isCurrent(token, pending) then return false, "CANCELLED_DURING_CALLBACK" end
            if not targetOK then return false, "TARGET_CALLBACK_FAILED" end
            target = player
        end
        local fresh, reason = roundSnapshot(self)
        if not self:_isCurrent(token, pending) then return false, "CANCELLED_DURING_CALLBACK" end
        if not fresh then return false, reason end
        if not sameRound(start, fresh) or fresh.now >= e.validUntil then
            return false, "ROUND_CHANGED_DURING_CALLBACK"
        end
        local roster2 = readRoster(self)
        if not self:_isCurrent(token, pending) then return false, "CANCELLED_DURING_CALLBACK" end
        if not sameRoster(roster, roster2) then return false, "ROSTER_CHANGED" end
        local nowMs = math.floor(fresh.now * 1000 + 0.000001)
        -- A LuaU Core.begin call is pure, deterministic, and contains no task.wait.
        -- The pinned Core is required: do not inject an arbitrary yielding Core.
        local started, why = self.core.begin(self.state, {
            matchId = pending.matchId, eventId = pending.subtype .. ":" .. tostring(pending.epoch),
            epoch = pending.epoch, nowMs = nowMs, effect = effect,
            targetUserId = target, serverRoster = roster2,
        })
        if not self:_isCurrent(token, pending) then
            if started then
                self.active = {matchId = pending.matchId, stage = pending.stage,
                    epoch = pending.epoch, subtype = pending.subtype, startedAtMs = nowMs}
                self:_closeActive("CANCELLED_AFTER_BEGIN")
            end
            return false, "CANCELLED_DURING_CALLBACK"
        end
        if not started then return false, why end
        self.active = { matchId = pending.matchId, stage = pending.stage,
            epoch = pending.epoch, subtype = pending.subtype,
            deadlineMs = math.floor(pending.validUntil * 1000), startedAtMs = nowMs }
        return true, "STARTED"
    end)
    self.busy = false
    if self.inFlight == pending then self.inFlight = nil end
    if not executed then
        self:_cancelPending()
        self:_closeActive("DISPATCH_EXCEPTION")
        self.enabled = false
        self.stoppedReason = "DISPATCH_EXCEPTION"
        return false, "DISPATCH_EXCEPTION"
    end
    return accepted, status
end

function Gate:snapshot()
    if not self.enabled or self.active == nil then return nil, "INACTIVE" end
    local token, a = self.cancelGeneration, self.active
    local s, err = roundSnapshot(self)
    -- A readRound callback may yield while another thread cleans up.
    if self.cancelGeneration ~= token or self.active ~= a or not self.enabled then
        return nil, "CANCELLED_DURING_CALLBACK"
    end
    if not s then
        self:_cancelPending()
        self:_closeActive(err)
        self.enabled = false
        self.stoppedReason = err
        return nil, err
    end
    local nowMs = math.floor(s.now * 1000 + 0.000001)
    if not s.active or s.matchId ~= a.matchId or s.stage ~= a.stage
        or s.epoch ~= a.epoch or nowMs >= a.deadlineMs then
        self:_cancelPending()
        self:_closeActive("ROUND_CLOSED_OR_EXPIRED")
        return nil, "ROUND_CLOSED_OR_EXPIRED"
    end
    local output, why = self.core.snapshot(self.state, nowMs, s.matchId, s.epoch)
    if output == nil then
        self.active = nil
        if why == "CLOCK_BACKWARDS" or why == "INVALID_CLOCK_OR_STATE" then
            self.enabled = false
            self.stoppedReason = why
        end
    end
    return output, why
end

-- D08 onCleanup envelope deliberately has no phase. Accept a matching cleanup
-- even when the activation callback is still awaiting the server roster/target.
function Gate:onCleanup(e)
    if type(e) ~= "table" or e.phase ~= nil or e.kind ~= "WEATHER" then
        return false, "INVALID_CLEANUP"
    end
    local pending = self.inFlight
    if pending ~= nil and sameEnvelope(pending, e) then
        self:_cancelPending()
        if self.active == nil then return true, "CANCELLED_PENDING" end
    end
    if self.active == nil then return false, "INACTIVE" end
    if not sameEnvelope(self.active, e) then return false, "CLEANUP_MISMATCH" end
    self:_cancelPending()
    return self:_closeActive("CLOSED")
end

function Gate:stop()
    self:_cancelPending()
    self.enabled = false
    local ok = self:_closeActive("OWNER_STOP")
    self.stoppedReason = ok and "OWNER_STOP" or "CORE_CLOSE_FAILED"
    return ok, self.stoppedReason
end

return Gate
