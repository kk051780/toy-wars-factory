-- TRAP RAIDERS D16: pure deterministic visual-only scale FX reference.
-- Trusted server-only caller MUST provide a D08-authorized single event.
-- Never bind this module directly to a client RemoteEvent. No Instance/physics writes.
local M = {}
local MAX_PLAYERS = 16
local DURATION = 8
local SCALES = { GIANT_ONE = 1600, MINI_ALL = 700 } -- milli scale, cosmetic only

local function validId(x)
    return type(x) == "string" and #x > 0 and #x <= 96 and string.match(x, "^[%w_.-]+$") ~= nil
end
local function validTime(t)
    return type(t) == "number" and t == t and t >= 0 and t ~= math.huge
end
local function canonicalRoster(xs)
    if type(xs) ~= "table" or #xs < 1 or #xs > MAX_PLAYERS then return nil end
    local out, seen = {}, {}
    for _, x in ipairs(xs) do
        if not validId(x) or seen[x] then return nil end
        seen[x] = true
        table.insert(out, x)
    end
    table.sort(out)
    return out, seen
end
local function clone(xs)
    local out = {}
    for i, x in ipairs(xs) do out[i] = x end
    return out
end
function M.new(matchId)
    assert(validId(matchId), "invalid match")
    return { matchId = matchId, lastTime = 0, used = false,
        status = "IDLE", kind = nil, eventId = nil,
        expiresAt = nil, targets = {} }
end
function M.begin(s, matchId, eventId, kind, actorId, roster, now)
    if matchId ~= s.matchId then return false, "STALE_MATCH" end
    if s.status == "CLOSED" then return false, "ROUND_CLOSED" end
    if s.used then return false, "EVENT_ALREADY_USED" end
    if not validTime(now) or now < s.lastTime then return false, "INVALID_TIME" end
    if not validId(eventId) or SCALES[kind] == nil then return false, "INVALID_EVENT" end
    local ids, lookup = canonicalRoster(roster)
    if not ids then return false, "INVALID_ROSTER" end
    if kind == "GIANT_ONE" then
        if not validId(actorId) or not lookup[actorId] then return false, "INVALID_ACTOR" end
        ids = { actorId }
    elseif actorId ~= nil then
        return false, "ACTOR_NOT_APPLICABLE"
    end
    s.used, s.status = true, "ACTIVE"
    s.kind, s.eventId, s.expiresAt = kind, eventId, now + DURATION
    s.targets, s.lastTime = ids, now
    return true, "STARTED"
end
function M.advance(s, matchId, now)
    if matchId ~= s.matchId then return false, "STALE_MATCH" end
    if not validTime(now) or now < s.lastTime then return false, "INVALID_TIME" end
    s.lastTime = now
    if s.status == "ACTIVE" and (now >= s.expiresAt or #s.targets == 0) then
        s.status, s.targets = "EXPIRED", {}
    end
    return true, s.status
end
function M.leave(s, matchId, playerId)
    if matchId ~= s.matchId then return false, "STALE_MATCH" end
    if not validId(playerId) then return false, "INVALID_PLAYER" end
    if s.status ~= "ACTIVE" then return true, "NO_ACTIVE_EFFECT" end
    local filtered = {}
    for _, id in ipairs(s.targets) do
        if id ~= playerId then table.insert(filtered, id) end
    end
    s.targets = filtered
    if #filtered == 0 then s.status = "EXPIRED" end
    return true, s.status
end
function M.close(s, matchId)
    if matchId ~= s.matchId then return false, "STALE_MATCH" end
    s.status, s.targets = "CLOSED", {}
    return true, "CLOSED"
end
function M.newRound(s, nextMatchId)
    if not validId(nextMatchId) or nextMatchId == s.matchId then
        return false, "INVALID_NEW_MATCH"
    end
    local fresh = M.new(nextMatchId)
    for k, v in pairs(fresh) do s[k] = v end
    return true, "RESET"
end
function M.snapshot(s, matchId)
    if matchId ~= s.matchId then return nil, "STALE_MATCH" end
    return { matchId = s.matchId, status = s.status, used = s.used,
        kind = s.kind, eventId = s.eventId, expiresAt = s.expiresAt,
        targets = clone(s.targets), scaleMilli = s.status == "ACTIVE" and SCALES[s.kind] or 1000 }
end
return M
