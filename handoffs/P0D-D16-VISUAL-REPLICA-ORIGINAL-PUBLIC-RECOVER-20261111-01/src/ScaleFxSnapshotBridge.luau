-- Server-only pure serializer. Does NOT schedule events or trust player remotes.
-- Existing D08 singleton chooses kind; existing ScaleFxCore owns the round effect.
-- The server provides elapsedSeconds measured from the SAME monotonic round clock
-- used by ScaleFxCore.begin / advance. Its expiresAt is NOT a Unix timestamp.
local B = {}
local MILLI = {GIANT_ONE = 1600, MINI_ALL = 700}
local function id(x)
    return type(x) == 'string' and #x >= 1 and #x <= 96
        and string.match(x, '^[%w_.-]+$') ~= nil
end
local function finite(x)
    return type(x) == 'number' and x == x and x >= 0 and x ~= math.huge
end
local function validTargets(targets, kind, allowEmpty)
    if type(targets) ~= 'table' or #targets > 16 then return nil end
    if not allowEmpty and (#targets == 0 or (kind == 'GIANT_ONE' and #targets ~= 1)) then return nil end
    local seen, out = {}, {}
    for _, x in ipairs(targets) do
        if not id(x) or seen[x] then return nil end
        seen[x] = true
        out[#out + 1] = x
    end
    for k, _ in pairs(targets) do
        if type(k) ~= 'number' or k % 1 ~= 0 or k < 1 or k > #targets then return nil end
    end
    table.sort(out)
    return out
end
function B.build(snapshot, elapsedSeconds)
    if type(snapshot) ~= 'table' or not id(snapshot.matchId)
        or not id(snapshot.eventId) or not finite(elapsedSeconds) then return nil, 'INVALID_SOURCE' end
    local status = snapshot.status
    if status == 'ACTIVE' then
        local kind = snapshot.kind
        if MILLI[kind] == nil or snapshot.scaleMilli ~= MILLI[kind]
            or not finite(snapshot.expiresAt) then return nil, 'INVALID_ACTIVE' end
        local targets = validTargets(snapshot.targets, kind, false)
        if not targets then return nil, 'INVALID_TARGETS' end
        local ttl = snapshot.expiresAt - elapsedSeconds
        if ttl <= 0 or ttl > 8 then return nil, 'INVALID_ACTIVE_TTL' end
        return { matchId = snapshot.matchId, eventId = snapshot.eventId, status = 'ACTIVE',
            kind = kind, targets = targets, scaleMilli = MILLI[kind], remainingSeconds = ttl }
    end
    if status == 'EXPIRED' or status == 'CLOSED' then
        local targets = validTargets(snapshot.targets or {}, nil, true)
        if targets == nil or #targets ~= 0 then return nil, 'INVALID_TERMINAL' end
        return { matchId = snapshot.matchId, eventId = snapshot.eventId,
            status = status, kind = snapshot.kind, targets = {},
            scaleMilli = 1000, remainingSeconds = 0 }
    end
    return nil, 'UNEXPECTED_STATUS'
end
return B
