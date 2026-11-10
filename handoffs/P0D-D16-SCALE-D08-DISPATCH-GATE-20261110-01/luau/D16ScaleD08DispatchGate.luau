--!strict
-- TRAP RAIDERS P0-D D16/D08: pure, opt-in trusted server callback adapter.
-- Independent NEW reference. NOT a recovery of D16 encrypted originals.
-- Only the single canonical D08 weather ACTIVATE/CLEANUP callback may call this.
-- NO second chooser, Remote listener, Roblox objects, scheduling, player physics.
local Gate = {}
Gate.__index = Gate

local WEATHER = {
    WX01_METEOR = true, WX02_SMALL = true, WX03_CROWN = true,
    WX04_GLIDE = true, WX05_CLOCK = true,
}
local STAGES = { S1 = true, S2 = true, S3 = true, S4 = true }
local MAX_SECONDS = 10000000000

local function finite(n)
    return type(n) == "number" and n == n and n ~= math.huge and n ~= -math.huge
end
local function validId(s)
    return type(s) == "string" and #s >= 1 and #s <= 96
        and string.match(s, "^[%w_%-]+$") ~= nil
end
local function roundSnapshot(config)
    if type(config.readRound) ~= "function" then return nil, "READ_ROUND_MISSING" end
    local ok, s = pcall(config.readRound)
    if not ok or type(s) ~= "table" then return nil, "READ_ROUND_FAILED" end
    if not validId(s.matchId) or not STAGES[s.stage]
        or not finite(s.epoch) or s.epoch % 1 ~= 0 or s.epoch < 1 or s.epoch >= 1024
        or not finite(s.now) or s.now < 0 or s.now > MAX_SECONDS
        or not finite(s.startedAt) or not finite(s.deadline)
        or s.startedAt < 0 or s.startedAt > s.now
        or s.deadline <= s.startedAt or s.deadline > MAX_SECONDS
        or type(s.active) ~= "boolean" then
        return nil, "ROUND_INVALID"
    end
    return s, nil
end
local function sameRound(a, b)
    return a.matchId == b.matchId and a.stage == b.stage and a.epoch == b.epoch
        and a.startedAt == b.startedAt and a.deadline == b.deadline
        and b.active == true and b.now >= a.now
end
local function matchesEvent(s, e)
    return s.active == true and s.matchId == e.matchId
        and s.stage == e.stage and s.epoch == e.epoch
end
local function normRoster(roster)
    if type(roster) ~= "table" then return nil end
    local n = #roster
    if n < 1 or n > 24 then return nil end
    local seen, sorted = {}, {}
    for i = 1, n do
        local id = roster[i]
        if not finite(id) or id % 1 ~= 0 or id < 1 or id > 9007199254740991
            or seen[id] then return nil end
        seen[id] = true
        sorted[i] = id
    end
    for k in pairs(roster) do
        if not finite(k) or k % 1 ~= 0 or k < 1 or k > n then return nil end
    end
    table.sort(sorted)
    return sorted
end
local function sameRoster(a, b)
    if a == nil or b == nil or #a ~= #b then return false end
    for i = 1, #a do if a[i] ~= b[i] then return false end end
    return true
end
local function readRoster(config)
    if type(config.readRoster) ~= "function" then return nil end
    local ok, r = pcall(config.readRoster)
    if not ok then return nil end
    return normRoster(r)
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
        busy = false, stoppedReason = nil,
    }, Gate)
end

function Gate:onWeatherActivate(event)
    if not self.enabled then return false, self.stoppedReason or "DISABLED_DEFAULT" end
    if self.busy then return false, "BUSY" end
    self.busy = true
    local ok, result, reason = pcall(function()
        if type(event) ~= "table" or event.kind ~= "WEATHER" or event.phase ~= "ACTIVATE"
            or not WEATHER[event.subtype] or not validId(event.matchId)
            or not STAGES[event.stage] or not finite(event.epoch)
            or event.epoch % 1 ~= 0 or event.epoch < 1 or event.epoch >= 1024
            or not finite(event.validUntil) then
            return false, "INVALID_D08_ENVELOPE"
        end
        local approvals = self.config.approvedSubtypeEffects
        if type(approvals) ~= "table" then return false, "NO_EXPLICIT_MAPPING" end
        local effect = approvals[event.subtype]
        if effect ~= "GIANT_ONE" and effect ~= "MINI_ALL" then
            return false, "UNAPPROVED_SUBTYPE"
        end
        local now, err = roundSnapshot(self.config)
        if not now then return false, err end
        if not matchesEvent(now, event) then return false, "ROUND_MISMATCH" end
        if event.validUntil <= now.now or event.validUntil > now.now + 9 then
            return false, "INVALID_EVENT_DEADLINE"
        end
        local roster = readRoster(self.config)
        if not roster then return false, "ROSTER_UNAVAILABLE" end
        local target = nil
        if effect == "GIANT_ONE" then
            if type(self.config.chooseGiantTarget) ~= "function" then
                return false, "TARGET_CALLBACK_MISSING"
            end
            local targetOk, targetId = pcall(self.config.chooseGiantTarget, roster)
            if not targetOk then return false, "TARGET_CALLBACK_FAILED" end
            target = targetId
        end
        -- All trusted callbacks above may yield. Recheck current round & roster.
        local fresh, why = roundSnapshot(self.config)
        if not fresh then return false, why end
        if not sameRound(now, fresh) or not matchesEvent(fresh, event)
            or fresh.now >= event.validUntil then return false, "ROUND_CHANGED_DURING_CALLBACK" end
        local roster2 = readRoster(self.config)
        if not sameRoster(roster, roster2) then return false, "ROSTER_CHANGED" end
        local nowMs = math.floor(fresh.now * 1000 + 0.000001)
        local started, status = self.core.begin(self.state, {
            matchId = event.matchId, eventId = event.matchId .. ":" .. tostring(event.epoch)
                .. ":" .. event.subtype,
            epoch = event.epoch, nowMs = nowMs, effect = effect,
            targetUserId = target, serverRoster = roster2,
        })
        if not started then return false, status end
        self.active = {
            matchId = event.matchId, stage = event.stage, epoch = event.epoch,
            subtype = event.subtype, deadlineMs = math.floor(event.validUntil * 1000),
        }
        return true, "STARTED"
    end)
    self.busy = false
    if not ok then
        self.enabled = false
        self.stoppedReason = "DISPATCH_EXCEPTION"
        return false, "DISPATCH_EXCEPTION"
    end
    return result, reason
end

function Gate:snapshot()
    if not self.enabled or self.active == nil then return nil, "INACTIVE" end
    local s, err = roundSnapshot(self.config)
    if not s then
        self.enabled = false
        self.stoppedReason = err
        return nil, err
    end
    local a = self.active
    local nowMs = math.floor(s.now * 1000 + 0.000001)
    if not matchesEvent(s, a) or nowMs >= a.deadlineMs then
        local closed = self.core.close(self.state, a.matchId, a.epoch, nowMs)
        self.active = nil
        if not closed then
            self.enabled = false
            self.stoppedReason = "CLOSE_FAILED"
            return nil, "CLOSE_FAILED"
        end
        return nil, "ROUND_CLOSED_OR_EXPIRED"
    end
    local out, why = self.core.snapshot(self.state, nowMs, s.matchId, s.epoch)
    if out == nil then
        self.active = nil
        if why == "CLOCK_BACKWARDS" or why == "INVALID_CLOCK_OR_STATE" then
            self.enabled = false
            self.stoppedReason = why
        end
    end
    return out, why
end

-- D08's onCleanup envelope has no phase field; never accept an ACTIVATE as cleanup.
function Gate:onCleanup(event)
    local a = self.active
    if a == nil then return false, "INACTIVE" end
    if type(event) ~= "table" or event.phase ~= nil or event.kind ~= "WEATHER"
        or event.matchId ~= a.matchId or event.stage ~= a.stage
        or event.epoch ~= a.epoch or event.subtype ~= a.subtype then
        return false, "CLEANUP_MISMATCH"
    end
    local s, err = roundSnapshot(self.config)
    if not s then
        self.enabled = false
        self.stoppedReason = err
        return false, err
    end
    local nowMs = math.floor(s.now * 1000 + 0.000001)
    local closed, why = self.core.close(self.state, a.matchId, a.epoch, nowMs)
    self.active = nil
    if not closed then
        self.enabled = false
        self.stoppedReason = "CLOSE_FAILED"
    end
    return closed, why
end

function Gate:stop()
    self.enabled = false
    self.stoppedReason = "OWNER_STOP"
    self.active = nil
end

return Gate
