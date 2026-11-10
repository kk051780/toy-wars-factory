-- TRAP RAIDERS D16 CLOCK_RAIN: original, independent keyless fallback.
-- Not the original sealed D16 CLOCK_RAIN source. Client-only visual state.
-- All calls must come from owner-reviewed client display adapter fed by the
-- single approved server event dispatcher. No RemoteEvent or server writes.
local Policy = {}
Policy.__index = Policy

local function finite(x)
    return type(x) == "number" and x == x and math.abs(x) < 1000000
end

local function ident(x)
    return type(x) == "string" and #x >= 1 and #x <= 96
end

local function integer(x)
    return finite(x) and x >= 0 and x == math.floor(x)
end

local function reject(reason)
    return {kind = "REJECTED", reason = reason}
end

function Policy.new()
    return setmetatable({
        active = false,
        last_key = nil,
        last_sequence = -1,
        match_id = nil,
        epoch = nil,
        sequence = nil,
        started = 0,
        until_time = 0,
        max_parts = 0,
        cleared = true,
    }, Policy)
end

function Policy:stop()
    self.active = false
    self.cleared = true
    self.match_id = nil
    self.epoch = nil
    self.sequence = nil
    self.max_parts = 0
    return {kind = "CLEARED"}
end

function Policy:start(s)
    if type(s) ~= "table" or s.server_event_approved ~= true
        or s.event_name ~= "CLOCK_RAIN" or s.phase ~= "ACTIVATE"
        or not ident(s.match_id) or not integer(s.epoch)
        or not integer(s.sequence) or not finite(s.now)
        or not finite(s.event_started_at) or not finite(s.duration)
        or type(s.reduced_motion) ~= "boolean" then
        return reject("invalid or unauthorized event")
    end
    if s.event_started_at > s.now or s.now - s.event_started_at > 2.0 then
        return reject("stale or future activation")
    end
    if s.duration <= 0 or s.duration > 12.0 then
        return reject("duration outside policy")
    end
    if self.active then
        return reject("only one active display")
    end
    local key = s.match_id .. ":" .. tostring(s.epoch)
    if key == self.last_key and s.sequence <= self.last_sequence then
        return reject("duplicate or replay")
    end
    self.last_key = key
    self.last_sequence = s.sequence
    self.match_id = s.match_id
    self.epoch = s.epoch
    self.sequence = s.sequence
    self.started = s.event_started_at
    self.until_time = s.event_started_at + s.duration
    self.max_parts = s.reduced_motion and 4 or 12
    self.cleared = false
    self.active = true
    return {kind = "STARTED", parts = self.max_parts, expires_at = self.until_time}
end

function Policy:step(now, match_id, epoch)
    if not self.active then
        return {kind = "IDLE", parts = 0}
    end
    if not finite(now) or not ident(match_id) or not integer(epoch)
        or match_id ~= self.match_id or epoch ~= self.epoch then
        self:stop()
        return {kind = "CLEARED", reason = "round or clock invalid"}
    end
    if now < self.started or now >= self.until_time then
        self:stop()
        return {kind = "CLEARED", reason = "expired"}
    end
    local age = now - self.started
    local marker_data = {}
    for i = 1, self.max_parts do
        local angle = i * 2.399963229728653
        local ring = 4.0 + (i % 4) * 2.2
        local phase = (age * (0.35 + (i % 3) * 0.11) + i * 0.17) % 1
        marker_data[i] = {
            x = math.cos(angle) * ring,
            y = 9 - phase * 12,
            z = math.sin(angle) * ring,
            yaw = age * (0.3 + i * 0.04),
            opacity = math.min(1, math.max(0, (self.until_time - now) / 1.0)),
        }
    end
    return {kind = "FRAME", parts = self.max_parts, markers = marker_data}
end

return Policy
