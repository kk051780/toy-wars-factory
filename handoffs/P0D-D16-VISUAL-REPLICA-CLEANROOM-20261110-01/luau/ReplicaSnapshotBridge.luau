-- D16 independent clean-room SERVER display policy. NOT legacy D16 encrypted source.
-- No RemoteEvent, no event RNG/round chooser, no player changes or physics.
local Bridge = {}
Bridge.__index = Bridge

local function finite(n)
    return type(n) == "number" and n == n and math.abs(n) < 1000000000000
end
local function positiveInt(n)
    return finite(n) and n > 0 and n == math.floor(n)
end
local function nonnegativeInt(n)
    return finite(n) and n >= 0 and n == math.floor(n)
end
local function ident(x)
    return type(x) == "string" and #x > 0 and #x <= 96
end
local function reject(r)
    return {kind = "REJECTED", reason = r, from_server_bridge = false}
end

function Bridge.new()
    return setmetatable({round = nil, sequence = -1}, Bridge)
end

function Bridge:project(s)
    if type(s) ~= "table" or s.server_authorized ~= true or s.event_approved ~= true
        or not ident(s.match_id) or not nonnegativeInt(s.epoch)
        or not nonnegativeInt(s.sequence)
        or not finite(s.server_round_elapsed_seconds)
        or not finite(s.expires_at_round_seconds)
        or type(s.target_user_ids) ~= "table" then
        return reject("untrusted/invalid server state")
    end
    if s.event_name ~= "GIANT_ONE" and s.event_name ~= "MINI_ALL" then
        return reject("not a D16 scaling event")
    end
    -- Both clocks MUST be round elapsed seconds from the SAME authoritative server.
    local remaining = s.expires_at_round_seconds - s.server_round_elapsed_seconds
    if s.server_round_elapsed_seconds < 0 or remaining <= 0 or remaining > 8 then
        return reject("expired / duration or clock mismatch")
    end
    local count = #s.target_user_ids
    if count < 1 or count > 8 then
        return reject("target cap outside 1..8")
    end
    local seen = {}
    local targetCopy = {}
    for i = 1, count do
        local id = s.target_user_ids[i]
        if not positiveInt(id) or seen[id] then
            return reject("invalid/duplicate target")
        end
        seen[id] = true
        targetCopy[i] = id
    end
    if s.event_name == "GIANT_ONE" and count ~= 1 then
        return reject("GIANT_ONE must have exactly one target")
    end
    local round = s.match_id .. ":" .. tostring(s.epoch)
    if self.round == round and s.sequence <= self.sequence then
        return reject("replayed scale snapshot")
    end
    self.round = round
    self.sequence = s.sequence
    return {
        kind = "DISPLAY", from_server_bridge = true,
        match_id = s.match_id, epoch = s.epoch, sequence = s.sequence,
        event_name = s.event_name, scale_factor = s.event_name == "GIANT_ONE" and 1.6 or 0.7,
        target_user_ids = targetCopy, remaining_seconds = remaining,
        source_clock = "SERVER_ROUND_ELAPSED", side_effects_applied = false,
    }
end

return Bridge
