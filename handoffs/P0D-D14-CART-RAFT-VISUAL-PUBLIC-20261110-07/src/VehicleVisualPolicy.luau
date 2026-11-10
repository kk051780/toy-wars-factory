-- Pure client presentation policy. Server event origin MUST be verified by PC integrator.
-- No server, seat, velocity, ownership or gameplay mutation in this module.
local M = {}
local LIMIT = 4
local MAX_TTL_MS = 20000
local MAX_COORD = 8192

local function integer(x, lower, upper)
    return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
        and x % 1 == 0 and x >= lower and x <= upper
end
local function coordinate(x)
    return type(x) == "number" and x == x and x ~= math.huge and x ~= -math.huge
        and x >= -MAX_COORD and x <= MAX_COORD
end
local function id(x)
    return type(x) == "string" and #x >= 1 and #x <= 32 and x:match("^[A-Za-z0-9_-]+$") ~= nil
end
local function copy(x)
    local output = {}
    for k, v in pairs(x) do output[k] = v end
    return output
end

function M.new(roundId)
    assert(id(roundId), "invalid roundId")
    return { roundId = roundId, lastSeq = -1, items = {}, closed = false }
end

-- Return zero or more abstract actions for a UI-only view renderer.
function M.ingest(s, packet)
    if type(s) ~= "table" or s.closed or type(packet) ~= "table" then return {} end
    if packet.roundId ~= s.roundId or not integer(packet.seq, 0, 2147483647)
        or packet.seq <= s.lastSeq then return {} end
    local kind = packet.kind
    if kind == "ROUND_END" then
        s.lastSeq = packet.seq
        s.closed = true
        s.items = {}
        return { { op = "CLEAR" } }
    end
    if kind ~= "START" and kind ~= "UPDATE" and kind ~= "STOP" then return {} end
    if not id(packet.vehicleId) then return {} end
    if kind == "STOP" then
        s.lastSeq = packet.seq
        local had = s.items[packet.vehicleId] ~= nil
        s.items[packet.vehicleId] = nil
        if had then return { { op = "REMOVE", vehicleId = packet.vehicleId } } end
        return {}
    end
    if packet.vehicleType ~= "CART" and packet.vehicleType ~= "RAFT" then return {} end
    if packet.team ~= "BLUE" and packet.team ~= "RED" then return {} end
    if type(packet.driverOccupied) ~= "boolean" or type(packet.passengerOccupied) ~= "boolean" then return {} end
    if not integer(packet.remainingMs, 1, MAX_TTL_MS) then return {} end
    if not coordinate(packet.x) or not coordinate(packet.y) or not coordinate(packet.z)
        or not coordinate(packet.yawDeg) or math.abs(packet.yawDeg) > 360 then return {} end
    local previous = s.items[packet.vehicleId]
    if kind == "UPDATE" and previous == nil then return {} end
    if kind == "START" and previous == nil then
        local count = 0
        for _ in pairs(s.items) do count = count + 1 end
        if count >= LIMIT then return {} end
    end
    if previous ~= nil and (previous.vehicleType ~= packet.vehicleType or previous.team ~= packet.team) then
        return {}
    end
    local nextState = {
        vehicleType = packet.vehicleType, team = packet.team,
        driverOccupied = packet.driverOccupied, passengerOccupied = packet.passengerOccupied,
        x = packet.x, y = packet.y, z = packet.z, yawDeg = packet.yawDeg,
        remainingMs = packet.remainingMs,
    }
    s.lastSeq = packet.seq
    s.items[packet.vehicleId] = nextState
    return { { op = previous == nil and "SPAWN" or "MOVE", vehicleId = packet.vehicleId,
        presentation = copy(nextState) } }
end

function M.close(s)
    if type(s) ~= "table" or s.closed then return {} end
    s.closed = true
    s.items = {}
    return { { op = "CLEAR" } }
end

function M.snapshot(s)
    local result = { roundId = s.roundId, lastSeq = s.lastSeq, closed = s.closed, items = {} }
    for k, v in pairs(s.items) do result.items[k] = copy(v) end
    return result
end

return M
