--!strict
-- TRAP_RAIDERS P0D D14. Server-derived outbound visual frames ONLY.
-- Pure deterministic policy. It deliberately owns NO seat ledger, cart/raft movement,
-- client models, Rider Mount, RemoteEvent, or Remote inbound handler.
local Core = {}

local MAX_ABS_POSITION = 2048
local MAX_INSTANCES = 4
local MIN_INTERVAL = 0.10
local TTL = 1.5
local POS_TOLERANCE = 0.15

local function finite(n)
    return type(n) == "number" and n == n and n > -math.huge and n < math.huge
end
local function validId(id)
    return type(id) == "string" and #id >= 1 and #id <= 48 and string.match(id, "^[%w_-]+$") ~= nil
end
local function position(x)
    return type(x) == "table" and finite(x.x) and finite(x.y) and finite(x.z)
        and math.abs(x.x) <= MAX_ABS_POSITION and math.abs(x.y) <= MAX_ABS_POSITION
        and math.abs(x.z) <= MAX_ABS_POSITION
end
local function direction(x)
    if type(x) ~= "table" or not finite(x.x) or not finite(x.z) then return false end
    local lenSq = x.x*x.x + x.z*x.z
    return lenSq >= 0.90 and lenSq <= 1.10
end
local function dist(a,b)
    local x,y,z = a.x-b.x,a.y-b.y,a.z-b.z
    return math.sqrt(x*x+y*y+z*z)
end
local function count(dict)
    local n = 0
    for _, _ in pairs(dict) do n += 1 end
    return n
end

function Core.new()
    return { roundId = nil, started = false, slots = {}, lastNow = nil }
end
function Core.beginRound(self, roundId, now)
    if not validId(roundId) or not finite(now) or now < 0 then return false, "BAD_ROUND" end
    if self.lastNow ~= nil and now < self.lastNow then return false, "CLOCK_REWIND" end
    self.roundId, self.started, self.slots, self.lastNow = roundId, true, {}, now
    return true, "OK"
end
function Core.stop(self)
    self.started, self.roundId, self.slots = false, nil, {}
    return true
end

-- Input must be a server-authenticated seat+pose snapshot produced by the
-- OWNER PC's authoritative adapter, NEVER a payload from a client RemoteEvent.
-- Returns one allowlisted visual DTO or nil and a reason; no mutable instances.
function Core.publish(self, snapshot)
    if not self.started then return nil, "NOT_STARTED" end
    if type(snapshot) ~= "table" then return nil, "BAD_SNAPSHOT" end
    local now = snapshot.now
    if not finite(now) or now < 0 or (self.lastNow and now < self.lastNow) then
        return nil, "STALE_CLOCK"
    end
    if snapshot.roundId ~= self.roundId or snapshot.roundActive ~= true then
        return nil, "STALE_ROUND"
    end
    if snapshot.authorizedServer ~= true or snapshot.seatVerified ~= true then
        return nil, "NO_AUTHORITY"
    end
    if not validId(snapshot.vehicleId) or not validId(snapshot.teamId) then
        return nil, "BAD_ID"
    end
    if snapshot.kind ~= "CART" and snapshot.kind ~= "RAFT" then return nil, "BAD_KIND" end
    if snapshot.stage ~= "S1" and snapshot.stage ~= "S2" then return nil, "BAD_STAGE" end
    if type(snapshot.seatEpoch) ~= "number" or snapshot.seatEpoch % 1 ~= 0
      or snapshot.seatEpoch < 0 or snapshot.seatEpoch > 1000000000 then
        return nil, "BAD_EPOCH"
    end
    if type(snapshot.sourceSeq) ~= "number" or snapshot.sourceSeq % 1 ~= 0
      or snapshot.sourceSeq < 1 or snapshot.sourceSeq > 1000000000 then
        return nil, "BAD_SOURCE_SEQ"
    end
    if type(snapshot.driverPresent) ~= "boolean" or type(snapshot.passengerPresent) ~= "boolean"
      or type(snapshot.moving) ~= "boolean" then return nil, "BAD_SEATS" end
    if (not snapshot.driverPresent and snapshot.passengerPresent)
      or (snapshot.moving and not snapshot.driverPresent) then return nil, "UNAUTHORIZED_OCCUPANCY" end
    if not position(snapshot.position) or not direction(snapshot.direction) then
        return nil, "BAD_GEOMETRY"
    end
    local slot = self.slots[snapshot.vehicleId]
    if slot == nil and count(self.slots) >= MAX_INSTANCES then return nil, "TOO_MANY_VEHICLES" end
    if slot ~= nil then
        if slot.kind ~= snapshot.kind or slot.teamId ~= snapshot.teamId or slot.stage ~= snapshot.stage then
            return nil, "VEHICLE_ID_REUSED"
        end
        if snapshot.seatEpoch < slot.seatEpoch then return nil, "STALE_SEAT_EPOCH" end
        if snapshot.sourceSeq <= slot.sourceSeq then return nil, "REPLAY_SOURCE_SEQ" end
        if now < slot.at then return nil, "STALE_VEHICLE_CLOCK" end
        if snapshot.seatEpoch == slot.seatEpoch and slot.driverPresent == false
          and snapshot.driverPresent == true then return nil, "DRIVER_REAUTH_REQUIRED" end
        local delta = now - slot.at
        local speed = snapshot.kind == "CART" and 16 or 8
        if dist(snapshot.position,slot.position) > speed*delta + POS_TOLERANCE then
            return nil, "POSE_TELEPORT"
        end
        if not snapshot.driverPresent and dist(snapshot.position,slot.position) > POS_TOLERANCE then
            return nil, "MOTION_AFTER_DRIVER_EXIT"
        end
        if delta < MIN_INTERVAL and slot.driverPresent == snapshot.driverPresent
          and slot.passengerPresent == snapshot.passengerPresent then
            return nil, "RATE_LIMIT"
        end
    end
    local sequence = slot == nil and 1 or slot.outSeq + 1
    local frame = {
        schema = "TR_D14_VISUAL_V1", roundId = self.roundId,
        teamId = snapshot.teamId, vehicleId = snapshot.vehicleId,
        stage = snapshot.stage, kind = snapshot.kind, seq = sequence,
        serverTime = now, expiresAt = now+TTL,
        position = {x=snapshot.position.x,y=snapshot.position.y,z=snapshot.position.z},
        direction = {x=snapshot.direction.x,z=snapshot.direction.z},
        moving = snapshot.moving, driverPresent=snapshot.driverPresent,
        passengerPresent = snapshot.passengerPresent,
    }
    self.slots[snapshot.vehicleId] = {
        outSeq=sequence, sourceSeq=snapshot.sourceSeq, at=now,
        position=frame.position, seatEpoch=snapshot.seatEpoch,
        teamId=snapshot.teamId, kind=snapshot.kind, stage=snapshot.stage,
        driverPresent=snapshot.driverPresent, passengerPresent=snapshot.passengerPresent,
    }
    self.lastNow = now
    return frame, "OK"
end

return Core
