-- D16 independent clean-room CLIENT display filter. No network listener.
-- Owner adapter must pass ONLY approved server bridge payload and local-view avatars.
local Policy = {}
Policy.__index = Policy
local function finite(x)
    return type(x) == "number" and x == x and math.abs(x) < 1000000000000
end
local function ident(x)
    return type(x) == "string" and #x > 0 and #x <= 96
end
local function nonnegativeInt(x)
    return finite(x) and x >= 0 and x == math.floor(x)
end
local function validVec(v)
    return type(v) == "table" and finite(v.x) and finite(v.y) and finite(v.z)
end
local function distance2(a,b)
    local x,y,z = a.x-b.x, a.y-b.y, a.z-b.z
    return x*x+y*y+z*z
end

function Policy.new()
    return setmetatable({active=false, match_id=nil, epoch=nil, expires_local=0,
        target_ids={}, scale_factor=1, max_parts=0, max_avatars=0,
        previous_round=nil, previous_sequence=-1, last_local=nil}, Policy)
end

function Policy:clear()
    self.active = false
    self.match_id = nil
    self.epoch = nil
    self.expires_local = 0
    self.last_local = nil
    self.target_ids = {}
    self.max_parts = 0
    self.max_avatars = 0
    return {kind="CLEAR"}
end

function Policy:begin(payload, local_now, reduced_motion)
    if type(payload) ~= "table" or payload.from_server_bridge ~= true
        or payload.kind ~= "DISPLAY" or payload.source_clock ~= "SERVER_ROUND_ELAPSED"
        or not ident(payload.match_id) or not nonnegativeInt(payload.epoch)
        or not nonnegativeInt(payload.sequence)
        or not finite(payload.remaining_seconds) or payload.remaining_seconds <= 0
        or payload.remaining_seconds > 8 or not finite(local_now)
        or type(reduced_motion) ~= "boolean"
        or type(payload.target_user_ids) ~= "table"
        or (payload.event_name ~= "GIANT_ONE" and payload.event_name ~= "MINI_ALL")
        or (payload.event_name == "GIANT_ONE" and payload.scale_factor ~= 1.6)
        or (payload.event_name == "MINI_ALL" and payload.scale_factor ~= 0.7)
        or self.active then
        return {kind="REJECTED"}
    end
    local n = #payload.target_user_ids
    if n < 1 or n > 8 or (payload.event_name == "GIANT_ONE" and n ~= 1) then
        return {kind="REJECTED"}
    end
    local ids = {}
    for i=1,n do
        local userId = payload.target_user_ids[i]
        if not finite(userId) or userId <= 0 or userId ~= math.floor(userId) or ids[userId] then
            return {kind="REJECTED"}
        end
        ids[userId] = true
    end
    local round = payload.match_id .. ":" .. tostring(payload.epoch)
    if self.previous_round == round and payload.sequence <= self.previous_sequence then
        return {kind="REJECTED"}
    end
    self.previous_round = round
    self.previous_sequence = payload.sequence
    self.active = true
    self.match_id = payload.match_id
    self.epoch = payload.epoch
    self.target_ids = ids
    self.scale_factor = payload.scale_factor
    self.expires_local = local_now + payload.remaining_seconds
    self.last_local = local_now
    self.max_avatars = reduced_motion and 4 or 8
    self.max_parts = reduced_motion and 6 or 18
    return {kind="START", expires_local=self.expires_local,
        max_avatars=self.max_avatars, max_parts_per_avatar=self.max_parts}
end

function Policy:frame(local_now, match_id, epoch, viewer, avatarPositions)
    if not self.active then return {kind="IDLE"} end
    if not finite(local_now) or local_now < self.last_local
        or local_now >= self.expires_local
        or not ident(match_id) or not nonnegativeInt(epoch)
        or match_id ~= self.match_id or epoch ~= self.epoch
        or not validVec(viewer) or type(avatarPositions) ~= "table" then
        self:clear()
        return {kind="CLEAR"}
    end
    self.last_local = local_now
    local seen = {}
    local visible = {}
    for _, avatar in ipairs(avatarPositions) do
        if #visible >= self.max_avatars then break end
        if type(avatar) == "table" and self.target_ids[avatar.user_id]
            and not seen[avatar.user_id] and validVec(avatar.position)
            and distance2(viewer, avatar.position) <= 90*90 then
            seen[avatar.user_id] = true
            table.insert(visible, avatar.user_id)
        end
    end
    return {kind="FRAME", users=visible, scale_factor=self.scale_factor,
        max_parts_per_avatar=self.max_parts, noninteractive=true}
end

return Policy
