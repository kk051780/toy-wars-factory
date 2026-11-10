-- Pure client-only DISPLAY policy for a server-owned D16 ScaleFxCore snapshot.
-- This is NOT an authorizer for combat, movement, win/loss or purchases.
local P = {}
local MAX_TARGETS = 16
local MAX_SECONDS = 8
local MILLI = {GIANT_ONE = 1600, MINI_ALL = 700}
local function validId(value)
    return type(value) == "string" and #value >= 1 and #value <= 96
        and string.match(value, "^[%w_.-]+$") ~= nil
end
local function finite(value)
    return type(value) == "number" and value == value
        and value ~= math.huge and value ~= -math.huge
end
local function validTargets(list, kind, allowEmpty)
    if type(list) ~= "table" then return nil end
    local count = #list
    if count > MAX_TARGETS or (not allowEmpty and count == 0) then return nil end
    if not allowEmpty and kind == "GIANT_ONE" and count ~= 1 then return nil end
    local out, seen = {}, {}
    for i = 1, count do
        local value = list[i]
        if not validId(value) or seen[value] then return nil end
        seen[value] = true
        out[#out + 1] = value
    end
    -- No sparse or non-array members, even if #list truncates.
    for k, _ in pairs(list) do
        if type(k) ~= "number" or k % 1 ~= 0 or k < 1 or k > count then
            return nil
        end
    end
    table.sort(out)
    return out, seen
end
function P.new(matchId)
    assert(validId(matchId), "INVALID_MATCH")
    return {matchId = matchId, eventId = nil, closed = false,
        status = "IDLE", kind = nil, targets = {}, scaleMilli = 1000, deadline = nil}
end
function P.accept(state, packet, expectedMatchId, now)
    if not finite(now) or now < 0 then return false, "BAD_CLIENT_TIME" end
    if type(packet) ~= "table" then return false, "BAD_PACKET" end
    if not validId(expectedMatchId) or state.matchId ~= expectedMatchId
        or packet.matchId ~= expectedMatchId then return false, "STALE_MATCH" end
    if not validId(packet.eventId) then return false, "BAD_EVENT_ID" end
    if state.eventId ~= nil and packet.eventId ~= state.eventId then
        return false, "SECOND_EVENT_REJECTED"
    end
    local status = packet.status
    if status ~= "ACTIVE" and status ~= "EXPIRED" and status ~= "CLOSED" then
        return false, "BAD_STATUS"
    end
    if status ~= "ACTIVE" then
        if state.closed then return false, "TERMINAL_REPLAY" end
        if state.eventId == nil then return false, "UNKNOWN_TERMINAL" end
        state.status, state.closed, state.targets, state.deadline = status, true, {}, nil
        state.scaleMilli = 1000
        return true, "CLEARED"
    end
    if state.closed then return false, "CLOSED_EVENT_REPLAY" end
    if MILLI[packet.kind] == nil or packet.scaleMilli ~= MILLI[packet.kind] then
        return false, "BAD_SCALE" end
    if not finite(packet.remainingSeconds) or packet.remainingSeconds <= 0
        or packet.remainingSeconds > MAX_SECONDS then return false, "BAD_TTL" end
    local targets, targetSet = validTargets(packet.targets, packet.kind, false)
    if targets == nil then return false, "BAD_TARGETS" end
    local nextDeadline = now + packet.remainingSeconds
    if state.eventId ~= nil then
        if state.kind ~= packet.kind then return false, "KIND_CHANGED" end
        local prior = {}
        for _, id in ipairs(state.targets) do prior[id] = true end
        for id, _ in pairs(targetSet) do
            if not prior[id] then return false, "TARGET_ADDED_AFTER_START" end
        end
        -- A duplicate packet must NEVER extend an effect, even with a forged TTL.
        nextDeadline = math.min(state.deadline, nextDeadline)
        if nextDeadline <= now then return false, "ALREADY_EXPIRED" end
    end
    state.status, state.eventId, state.kind = "ACTIVE", packet.eventId, packet.kind
    state.targets, state.scaleMilli, state.deadline = targets, packet.scaleMilli, nextDeadline
    return true, "DISPLAY_ONLY"
end
function P.tick(state, expectedMatchId, now)
    if state.matchId ~= expectedMatchId then
        state.status, state.targets, state.deadline, state.closed = "EXPIRED", {}, nil, true
        state.scaleMilli = 1000
        return "MATCH_CHANGED"
    end
    if not finite(now) then return "TIME_UNAVAILABLE" end
    if state.status == "ACTIVE" and now >= state.deadline then
        state.status, state.targets, state.deadline, state.closed = "EXPIRED", {}, nil, true
        state.scaleMilli = 1000
        return "EXPIRED"
    end
    return state.status
end
return P
