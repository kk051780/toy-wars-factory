-- TRAP RAIDERS D14 two-seat authority CLEAN-ROOM candidate.
-- NOT byte-identical to old encrypted D14 SeatReference_v2 ZIP.
-- Server-only pure policy: emits receipts, no Roblox services, Seat/Weld/Remote
-- or physical movement. Default disabled; owner Windows Codex must compare
-- with the authentic original and choose ONE seat authority implementation.
local Policy = {}
Policy.__index = Policy

local ROLES = { DRIVER = true, PASSENGER = true }

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) < 100000000
end

local function ordinal(n)
    return finite(n) and n >= 0 and n == math.floor(n)
end

local function identifier(s)
    return type(s) == "string" and #s >= 1 and #s <= 96
end

local function result(kind, why)
    return { kind = kind, reason = why, physical_mount_performed = false }
end

function Policy.new()
    return setmetatable({
        enabled = false,
        match_id = nil,
        epoch = nil,
        stage = nil,
        vehicle_id = nil,
        last_sequence = -1,
        last_now = nil,
        occupants = {},
    }, Policy)
end

function Policy:stop()
    self.enabled = false
    self.match_id = nil
    self.epoch = nil
    self.stage = nil
    self.vehicle_id = nil
    self.last_sequence = -1
    self.last_now = nil
    self.occupants = {}
    return result("STOPPED", "cleared all seat intents")
end

function Policy:beginRound(s)
    if self.enabled or type(s) ~= "table" or s.server_authorized ~= true
        or not identifier(s.match_id) or not identifier(s.vehicle_id)
        or not ordinal(s.epoch) or not ordinal(s.stage)
        or s.stage < 1 or s.stage > 4 or not finite(s.now) then
        return result("REJECTED", "invalid trusted round start")
    end
    self.enabled = true
    self.match_id = s.match_id
    self.epoch = s.epoch
    self.stage = s.stage
    self.vehicle_id = s.vehicle_id
    self.last_sequence = -1
    self.last_now = s.now
    self.occupants = {}
    return result("STARTED", "server round authority only")
end

local function roundValid(self, s)
    return type(s) == "table" and s.server_authorized == true
        and s.match_id == self.match_id and s.epoch == self.epoch
        and s.stage == self.stage and s.vehicle_id == self.vehicle_id
        and finite(s.now) and ordinal(s.sequence)
end

local function accepting(self, s)
    if not self.enabled then
        return false, "inactive"
    end
    if not roundValid(self, s) then
        self:stop()
        return false, "unauthorized or changed round"
    end
    if s.now <= self.last_now or s.sequence <= self.last_sequence then
        return false, "replayed time or sequence"
    end
    return true, "valid"
end

function Policy:assign(s)
    local ok, reason = accepting(self, s)
    if not ok then
        return result("REJECTED", reason)
    end
    if not ROLES[s.role] or not identifier(s.player_id)
        or not ordinal(s.character_generation) or s.player_alive ~= true
        or s.server_seat_occupant_verified ~= true then
        return result("REJECTED", "missing real occupant authority")
    end
    if self.occupants[s.role] then
        return result("REJECTED", "seat already occupied")
    end
    for _, held in pairs(self.occupants) do
        if held.player_id == s.player_id then
            return result("REJECTED", "player already in another seat")
        end
    end
    self.last_now = s.now
    self.last_sequence = s.sequence
    self.occupants[s.role] = {
        player_id = s.player_id,
        character_generation = s.character_generation,
        expires_at = s.now + 1.5,
    }
    return {
        kind = "MOUNT_INTENT",
        role = s.role,
        player_id = s.player_id,
        character_generation = s.character_generation,
        match_id = self.match_id,
        epoch = self.epoch,
        vehicle_id = self.vehicle_id,
        sequence = s.sequence,
        expires_at = s.now + 1.5,
        physical_mount_performed = false,
        authority_receipt_required = true,
    }
end

function Policy:refresh(s)
    local ok, reason = accepting(self, s)
    if not ok then
        return result("REJECTED", reason)
    end
    if not ROLES[s.role] or not identifier(s.player_id)
        or not ordinal(s.character_generation) or s.player_alive ~= true
        or s.server_seat_occupant_verified ~= true then
        return result("REJECTED", "revalidation failed")
    end
    local existing = self.occupants[s.role]
    if not existing or existing.player_id ~= s.player_id
        or existing.character_generation ~= s.character_generation
        or s.now > existing.expires_at then
        self.occupants[s.role] = nil
        return result("REJECTED", "seat lease stale or generation changed")
    end
    self.last_now = s.now
    self.last_sequence = s.sequence
    existing.expires_at = s.now + 1.5
    return result("REFRESHED", "same server-verified occupant")
end

function Policy:release(s)
    local ok, reason = accepting(self, s)
    if not ok then
        return result("REJECTED", reason)
    end
    if not ROLES[s.role] or not identifier(s.player_id)
        or not ordinal(s.character_generation) then
        return result("REJECTED", "invalid release identity")
    end
    local held = self.occupants[s.role]
    if not held or held.player_id ~= s.player_id
        or held.character_generation ~= s.character_generation then
        return result("REJECTED", "non-owner release")
    end
    self.last_now = s.now
    self.last_sequence = s.sequence
    self.occupants[s.role] = nil
    return result("RELEASED", "matching seat occupant cleared")
end

function Policy:tick(s)
    if not self.enabled then
        return result("REJECTED", "inactive")
    end
    if type(s) ~= "table" or s.server_authorized ~= true
        or s.match_id ~= self.match_id or s.epoch ~= self.epoch
        or s.stage ~= self.stage or s.vehicle_id ~= self.vehicle_id
        or not finite(s.now) or s.now < self.last_now then
        self:stop()
        return result("STOPPED", "round changed or invalid trusted clock")
    end
    self.last_now = s.now
    local expired = 0
    for role, held in pairs(self.occupants) do
        if s.now > held.expires_at then
            self.occupants[role] = nil
            expired += 1
        end
    end
    return { kind = "TICK", expired = expired, occupied = self:occupiedCount(), physical_mount_performed = false }
end

function Policy:occupiedCount()
    local n = 0
    for _ in pairs(self.occupants) do
        n += 1
    end
    return n
end

return Policy
