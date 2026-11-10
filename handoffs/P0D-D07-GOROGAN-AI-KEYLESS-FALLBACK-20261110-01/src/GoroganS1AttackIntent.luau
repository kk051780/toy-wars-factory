-- TRAP RAIDERS D07 S1 clean-room, keyless, server-only attack-intent policy.
-- NOT the original encrypted Gorogan AI source. No HP write, Remote, or event RNG.
-- The PC integrator must supply trusted server snapshots; default inactive.
local Core = {}
Core.__index = Core

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) <= 1000000
end

local function validPosition(p)
    return type(p) == "table" and finite(p.x) and finite(p.y) and finite(p.z)
end

local function distance2(a, b)
    local x, y, z = a.x - b.x, a.y - b.y, a.z - b.z
    return x * x + y * y + z * z
end

local function validId(id)
    return type(id) == "string" and #id >= 1 and #id <= 96
end

local function validEpoch(n)
    return finite(n) and n >= 0 and n == math.floor(n)
end

local function response(kind, info)
    return {kind = kind, info = info, damage_applied = false}
end

function Core.new()
    return setmetatable({
        active = false,
        phase = "IDLE",
        count = 0,
        serial = 0,
        last_time = nil,
        cooldown_until = 0,
        match_id = nil,
        epoch = nil,
        target_id = nil,
        tell_started = nil,
    }, Core)
end

function Core:beginRound(trusted)
    if self.active or type(trusted) ~= "table" or trusted.server_authorized ~= true
        or not validId(trusted.match_id) or not validEpoch(trusted.epoch)
        or trusted.stage ~= 1 or not finite(trusted.now) then
        return false
    end
    self.active = true
    self.phase = "READY"
    self.count = 0
    self.serial = 0
    self.last_time = trusted.now
    self.cooldown_until = trusted.now
    self.match_id = trusted.match_id
    self.epoch = trusted.epoch
    self.target_id = nil
    self.tell_started = nil
    return true
end

function Core:stop()
    self.active = false
    self.phase = "STOPPED"
    self.target_id = nil
    self.tell_started = nil
    return response("STOPPED", "no active attack")
end

local function validSnapshot(self, s)
    return type(s) == "table"
        and s.server_authorized == true
        and s.match_id == self.match_id
        and s.epoch == self.epoch
        and s.stage == 1
        and finite(s.now)
        and validPosition(s.boss)
        and validPosition(s.target)
        and validId(s.target_id)
        and type(s.boss_alive) == "boolean"
        and type(s.target_alive) == "boolean"
end

function Core:step(s)
    if not self.active then
        return response("BLOCKED", "inactive")
    end
    if not validSnapshot(self, s) then
        self:stop()
        return response("BLOCKED", "untrusted or stale snapshot")
    end
    if s.now <= self.last_time then
        return response("BLOCKED", "time replay or reversal")
    end
    self.last_time = s.now
    if not s.boss_alive then
        self:stop()
        return response("STOPPED", "boss gone")
    end
    if self.count >= 3 then
        self:stop()
        return response("COMPLETE", "attack count limit")
    end
    if self.phase == "TELL" then
        if not s.target_alive or s.target_id ~= self.target_id then
            self.phase = "COOLDOWN"
            self.target_id = nil
            self.cooldown_until = s.now + 4.5
            return response("CANCELLED", "target changed or disappeared")
        end
        if s.now - self.tell_started < 2.0 then
            return response("NOOP", "telegraph active")
        end
        self.phase = "COOLDOWN"
        self.target_id = nil
        self.cooldown_until = s.now + 4.5
        if distance2(s.boss, s.target) > 10 * 10 then
            return response("MISSED", "outside stomp radius")
        end
        self.count += 1
        self.serial += 1
        return {
            kind = "STOMP_INTENT",
            match_id = self.match_id,
            epoch = self.epoch,
            stage = 1,
            target_id = s.target_id,
            attack_id = self.match_id .. ":" .. tostring(self.epoch) .. ":" .. tostring(self.serial),
            max_damage = 8,
            receipt_required = true,
            damage_applied = false,
            source = "P0D_D07_GOROGAN_CLEAN_ROOM",
        }
    end
    if s.now < self.cooldown_until then
        return response("NOOP", "cooldown")
    end
    if not s.target_alive or distance2(s.boss, s.target) > 24 * 24 then
        return response("NOOP", "no eligible nearby target")
    end
    self.phase = "TELL"
    self.target_id = s.target_id
    self.tell_started = s.now
    return {
        kind = "TELEGRAPH",
        match_id = self.match_id,
        epoch = self.epoch,
        target_id = s.target_id,
        start_time = s.now,
        min_resolve_time = s.now + 2,
        damage_applied = false,
    }
end

return Core
