--!strict
-- TRAP RAIDERS: optional PC-reviewed compatibility boundary ONLY, not event chooser or boss runtime.
-- D08 onBossActivate envelope (phase/stage/validUntil) -> D07 Combined.start
-- ACTIVATE shape (event/matchId/untilAt); server-only trusted RoundCoordinator required.
-- Never call this from a client RemoteEvent, client attribute, or self-made event scheduler.
local Mapper = {}
Mapper.__index = Mapper

local MAX_ATTEMPTS = 128

local function finite(v: any, lo: number, hi: number): boolean
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
        and v >= lo and v <= hi
end

local function validId(v: any): boolean
    return type(v) == "string" and #v > 0 and #v <= 64
        and v:match("^[%w_%-]+$") ~= nil
end

local function validStage(v: any): boolean
    return v == "S1" or v == "S3"
end

-- deps.readRound: actual server RoundCoordinator snapshot:
-- {matchId, stage, epoch, now, deadline, active}; no client-derived fields.
-- deps.startCombined: function(activation) return combined:start(activation) end
-- deps.abortCombined: function(roundId) stop the combined rig/damage/runtime for that round;
--   this MUST be implemented by Windows Codex before approving, for callback-yield safety.
-- Both callbacks must be server-owned. No Roblox data mutation occurs in this module.
function Mapper.new(deps: any)
    assert(type(deps) == "table", "DEPS_REQUIRED")
    for _, name in ipairs({"readRound", "startCombined", "abortCombined"}) do
        assert(type(deps[name]) == "function", "TRUSTED_CALLBACK_REQUIRED_" .. name)
    end
    return setmetatable({
        deps = deps,
        enabled = deps.enabled == true and deps.approvedByOwner == true,
        disabledReason = nil,
        inCallback = false,
        attestedActivation = nil,
        attempted = {},
        attemptedCount = 0,
        lastNow = nil,
    }, Mapper)
end

-- Wire exclusively into D07 CombinedRuntime deps.isCanonicalActivation.
-- Not a generic type/contents check: only the CURRENT server-created table is attested.
function Mapper:isCanonicalActivation(activation: any): boolean
    return self.enabled == true and self.inCallback == true
        and self.attestedActivation ~= nil and self.attestedActivation == activation
end

local function safeRound(self)
    local ok, r = pcall(self.deps.readRound)
    if not ok or type(r) ~= "table" then return nil end
    if not validId(r.matchId) or not validStage(r.stage)
        or not finite(r.epoch, 0, 1023) or r.epoch % 1 ~= 0
        or not finite(r.now, 0, 1e12) or not finite(r.deadline, 0, 1e12)
        or r.deadline <= r.now or r.active ~= true then
        return nil
    end
    -- Copy the authoritative evidence before a callback can yield and mutate the
    -- table returned by the owner's RoundCoordinator. Identity comparisons must
    -- NOT retain the original mutable table as their baseline.
    return {matchId=r.matchId,stage=r.stage,epoch=r.epoch,now=r.now,
        deadline=r.deadline,active=r.active}
end

local function sameRound(a, b): boolean
    return a ~= nil and b ~= nil and a.matchId == b.matchId
        and a.stage == b.stage and a.epoch == b.epoch
        and b.now >= a.now and b.deadline == a.deadline and b.active == true
end

-- Use this function ONLY as D08 CanonicalEventBridge.onBossActivate's trusted
-- server callback, not through any RemoteEvent. One attempt only per match+epoch.
function Mapper:handle(envelope: any)
    if not self.enabled then return false, self.disabledReason or "DISABLED_DEFAULT" end
    if self.inCallback then return false, "REENTRANT_CALLBACK" end
    if type(envelope) ~= "table" or envelope.phase ~= "ACTIVATE"
        or envelope.kind ~= "BOSS" or envelope.subtype ~= "GOROGAN"
        or not validId(envelope.matchId) or not validStage(envelope.stage)
        or not finite(envelope.epoch, 0, 1023) or envelope.epoch % 1 ~= 0
        or not finite(envelope.validUntil, 0, 1e12) then
        return false, "INVALID_D08_ENVELOPE"
    end
    local snapshot = safeRound(self)
    if not snapshot or envelope.matchId ~= snapshot.matchId
        or envelope.stage ~= snapshot.stage or envelope.epoch ~= snapshot.epoch
        or envelope.validUntil <= snapshot.now + 2
        or envelope.validUntil > snapshot.deadline then
        return false, "SERVER_ROUND_MISMATCH"
    end
    if self.lastNow ~= nil and snapshot.now < self.lastNow then
        self.enabled = false
        self.disabledReason = "SERVER_CLOCK_REVERSED"
        return false, self.disabledReason
    end
    self.lastNow = snapshot.now
    local key = snapshot.matchId .. ":" .. tostring(snapshot.epoch)
    if self.attempted[key] then return false, "EVENT_REPLAY" end
    if self.attemptedCount >= MAX_ATTEMPTS then
        self.enabled = false
        self.disabledReason = "ATTEMPT_CAP_REACHED"
        return false, self.disabledReason
    end
    -- Consume before any possibly yielding callback. Never restart a partially
    -- spawned physical boss on a duplicate delivery or callback exception.
    self.attempted[key] = true
    self.attemptedCount += 1
    local activation = {
        event = "ACTIVATE", kind = "BOSS", subtype = "GOROGAN",
        matchId = snapshot.matchId, untilAt = envelope.validUntil,
    }
    local untilAt = envelope.validUntil -- immutable scalar across yielding callbacks
    self.inCallback = true
    self.attestedActivation = activation
    local ok, started, reason = pcall(self.deps.startCombined, activation)
    -- Revoke by table identity before any other callback, even on failure.
    self.attestedActivation = nil
    self.inCallback = false
    local fresh = safeRound(self)
    if not ok or started ~= true or not sameRound(snapshot, fresh)
        or (fresh ~= nil and fresh.now >= untilAt) then
        -- startCombined might have partially created rig/gate prior to a yield;
        -- PC must wire abortCombined to fail closed in that exact case.
        local abortOk, abortResult = pcall(self.deps.abortCombined, snapshot.matchId)
        self.enabled = false
        self.disabledReason = if not abortOk or abortResult ~= true
            then "CRITICAL_ABORT_NOT_CONFIRMED" else "START_FAILED_OR_STALE"
        return false, self.disabledReason
    end
    self.lastNow = fresh.now
    return true, "DELIVERED_ONCE"
end

-- Disables further starts. Does not stop the boss: OWNER's actual RoundCoordinator
-- remains responsible for its genuine round cleanup and boss runtime lifecycle.
function Mapper:disable(reason: string?)
    self.enabled = false
    self.disabledReason = reason or "OWNER_STOP"
    self.attestedActivation = nil
    self.inCallback = false
end

return Mapper
