--!strict
-- S1 round-only bridge. No Remote listener, RunService loop, event RNG, boss AI or damage owner.
-- Owner supplies already-authorized D07 Combined callbacks and ONE existing match server.
-- This is an opt-in ModuleScript; nothing starts at require time.
local Chaos = require(script.Parent:WaitForChild("ChaosEventCore"))
local Canonical = require(script.Parent:WaitForChild("CanonicalEventBridge"))
local Mapper = require(script.Parent:WaitForChild("TrustedGoroganActivationMapper"))

local Host = {}
Host.__index = Host

local function finite(x)
    return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
end

local function trusted(deps, name)
    assert(type(deps[name]) == "function", "MISSING_SERVER_CALLBACK_" .. name)
    return deps[name]
end

-- Called once per fresh S1 serial by the single existing Game.server.luau owner.
-- True approval is explicit and separate from merely loading this source.
function Host.new(deps)
    assert(type(deps) == "table", "S1_SERVER_DEPENDENCIES_REQUIRED")
    local self = setmetatable({
        enabled = false, closed = false, reason = "DISABLED_DEFAULT",
        bridge = nil, mapper = nil, combined = nil, combinedActive = false,
        activeRoundId = nil, activeEpoch = nil, inTick = false,
        deps = deps,
    }, Host)

    if deps.approvedByOwner ~= true or deps.enableCanonicalS1 ~= true then
        return self
    end

    for _, name in ipairs({
        "readMatch", "serverTime", "serverRoll", "makeCombined",
        "abortCombined", "setAlarm", "broadcast",
    }) do trusted(deps, name) end

    local function readRound()
        local ok, match = pcall(deps.readMatch)
        if not ok or type(match) ~= "table" then return nil end
        local serial = match.serial
        local nowOk, now = pcall(deps.serverTime)
        if not nowOk or not finite(now) or now < 0 or now > 1e12
            or not finite(serial) or serial % 1 ~= 0 or serial < 1 or serial >= 1024
            or not finite(match.startedAt) or match.startedAt < 0
            or not finite(match.deadline) or match.deadline <= match.startedAt
            or now < match.startedAt
            or (match.phase ~= "ACTIVE" and match.phase ~= "RESULTS")
        then return nil end
        return {
            matchId = "S1_" .. tostring(serial), stage = "S1", epoch = serial,
            startedAt = match.startedAt, deadline = match.deadline, now = now,
            active = match.phase == "ACTIVE",
        }
    end

    local snapshot = readRound()
    if not snapshot or snapshot.active ~= true then
        self.reason = "NO_FRESH_S1_ACTIVE_ROUND"
        return self
    end
    self.activeRoundId = snapshot.matchId
    self.activeEpoch = snapshot.epoch

    -- The original mapper attests an activation TABLE BY IDENTITY while the
    -- original CombinedRuntime calls mapper:isCanonicalActivation(activation).
    -- Only the trusted owner can provide makeCombined and its physical/damage deps.
    local mapper = Mapper.new({
        enabled = true, approvedByOwner = true, readRound = readRound,
        startCombined = function(activation)
            if self.closed or self.combined == nil then return false, "HOST_CLOSED" end
            return self.combined:start(activation)
        end,
        abortCombined = function(roundId)
            -- This must stop the existing D07 rig + damage boundary even after
            -- a partially successful yielding start. It cannot be a no-op.
            local ok, result = pcall(deps.abortCombined, roundId)
            if ok and result == true then
                self.combinedActive = false
                return true
            end
            self.reason = "CRITICAL_BOSS_ABORT_NOT_CONFIRMED"
            self.enabled = false
            return false
        end,
    })
    self.mapper = mapper

    local constructed, combined = pcall(deps.makeCombined, mapper)
    if not constructed or type(combined) ~= "table"
        or type(combined.start) ~= "function"
        or type(combined.heartbeat) ~= "function"
        or type(combined.stop) ~= "function" then
        mapper:disable("COMBINED_OWNER_CALLBACK_INVALID")
        self.reason = "COMBINED_OWNER_CALLBACK_INVALID"
        return self
    end
    self.combined = combined

    local function setAlarm(state, untilAt, epoch)
        -- The owner must ignore obsolete epochs but return true for a safe no-op.
        local ok, result = pcall(deps.setAlarm, state, untilAt, epoch)
        if not ok or result ~= true then return false end
        local sent, broadcastOk = pcall(deps.broadcast)
        return sent and broadcastOk ~= false
    end

    local bridge = Canonical.new(Chaos, {
        enabled = true, readRound = readRound,
        serverRoll = function(matchId, epoch)
            local r = readRound()
            if not r or not r.active or r.matchId ~= matchId or r.epoch ~= epoch then
                return nil
            end
            -- Existing server-authoritative RNG ONLY; never use client data.
            return deps.serverRoll(matchId, epoch)
        end,
        onWarning = function(envelope)
            if envelope.stage ~= "S1" or envelope.kind ~= "BOSS"
                or envelope.subtype ~= "GOROGAN"
                or envelope.epoch ~= self.activeEpoch then return false end
            return setAlarm("WARNING", envelope.validUntil, envelope.epoch)
        end,
        onBossActivate = function(envelope)
            if self.closed or envelope.epoch ~= self.activeEpoch then return false end
            local started = mapper:handle(envelope)
            if started ~= true then return false end
            self.combinedActive = true
            if not setAlarm("SIGNAL", envelope.validUntil, envelope.epoch) then
                local ok, aborted = pcall(deps.abortCombined, self.activeRoundId)
                self.combinedActive = false
                if not ok or aborted ~= true then self.reason = "CRITICAL_ABORT_FAILED" end
                return false
            end
            return true
        end,
        -- No approved weather runtime in S1. D08 original rejects WEATHER
        -- before sending any fake warning; no placeholder mechanic promised.
        onCleanup = function(_envelope)
            local success = true
            if self.combinedActive then
                local ok, result = pcall(deps.abortCombined, self.activeRoundId)
                success = ok and result == true
                self.combinedActive = false
            end
            local cleared = setAlarm("IDLE", 0, self.activeEpoch)
            mapper:disable("CANONICAL_EVENT_CLEANED")
            self.closed = true
            if not success then self.reason = "CRITICAL_ABORT_FAILED" end
            return success and cleared
        end,
    })
    self.bridge = bridge
    self.enabled = true
    self.reason = "SERVER_ONLY_ACTIVE"
    return self
end

function Host:tick()
    if self.closed or not self.enabled or not self.bridge then
        return false, self.reason
    end
    if self.inTick then return false, "HOST_TICK_REENTRANT" end
    self.inTick = true
    local ok, succeeded, why = pcall(function() return self.bridge:tick() end)
    if not ok or succeeded == false and why ~= "NO_EVENT" then
        self.inTick = false
        self:stop("D08_FAILED")
        return false, why or "D08_FAILED"
    end
    if self.combinedActive and not self.closed then
        local good, cmd, reason = pcall(function() return self.combined:heartbeat() end)
        if not good or reason == "HEARTBEAT_FAIL_CLOSED" then
            self.inTick = false
            self:stop("D07_HEARTBEAT_FAILED")
            return false, reason or "D07_HEARTBEAT_FAILED"
        end
        if type(cmd) == "table" and cmd.kind == "END" then self.combinedActive = false end
    end
    self.inTick = false
    return true, why or "NO_EVENT"
end

function Host:stop(reason)
    if self.closed and self.bridge == nil then return true end
    self.closed = true
    self.enabled = false
    self.reason = reason or "OWNER_STOP"
    if self.bridge then
        -- Cleanup callback disarms the boss and clears HUD; bridge owns lifecycle.
        self.bridge:stop()
    elseif self.combinedActive then
        local ok, result = pcall(self.deps.abortCombined, self.activeRoundId)
        if not ok or result ~= true then self.reason = "CRITICAL_ABORT_FAILED" end
    end
    self.combinedActive = false
    if self.mapper then self.mapper:disable("OWNER_STOP") end
    return self.reason ~= "CRITICAL_ABORT_FAILED"
end

function Host:status()
    return {
        enabled = self.enabled == true and not self.closed,
        reason = self.reason,
        epoch = self.activeEpoch,
        hasCombined = self.combined ~= nil,
        bossActive = self.combinedActive == true,
        studioTested = false,
    }
end

return Host
