-- TRAP RAIDERS D07 LIGARDO S2/S4: client visual policy only.
-- This is NOT a boss AI, event scheduler or trusted server verifier.
local M = {}
local MAX_WINDOW_MS = 20000
local function idok(s)
    return type(s) == "string" and #s >= 1 and #s <= 64 and s:match("^[%w_%-]+$") ~= nil
end
local function int(v, low, high)
    return type(v) == "number" and v == v and v % 1 == 0 and v >= low and v <= high
end
local function timeok(t)
    return type(t) == "number" and t == t and t >= 0 and t < 10000000000
end
function M.new(roundId)
    assert(idok(roundId), "roundId")
    return {roundId = roundId, closed = false, used = false, eventId = nil,
        lastSeq = 0, phase = "IDLE", deadline = nil, lastNow = 0}
end
function M.snapshot(s, p, now)
    if type(s) ~= "table" or s.closed or type(p) ~= "table" or not timeok(now)
        or now < s.lastNow then return {kind = "IGNORE", reason = "INVALID_STATE_OR_TIME"} end
    if p.roundId ~= s.roundId or p.boss ~= "LIGARDO" or
        not int(p.stage, 1, 4) or (p.stage ~= 2 and p.stage ~= 4) or
        not idok(p.eventId) or not int(p.seq, 1, 10000000) or
        not int(p.remainingMs, 0, MAX_WINDOW_MS) or
        (p.phase ~= "TELEGRAPH" and p.phase ~= "ACTIVE" and p.phase ~= "END") then
        return {kind = "IGNORE", reason = "INVALID_PAYLOAD"}
    end
    if s.used and p.eventId ~= s.eventId then
        return {kind = "IGNORE", reason = "ALREADY_USED_THIS_ROUND"}
    end
    if s.used and p.seq <= s.lastSeq then
        return {kind = "IGNORE", reason = "STALE_SEQUENCE"}
    end
    if s.phase == "ENDED" then return {kind = "IGNORE", reason = "TERMINATED"} end
    if not s.used then
        if p.phase ~= "TELEGRAPH" or p.remainingMs == 0 then
            return {kind = "IGNORE", reason = "MUST_TELEGRAPH_FIRST"}
        end
        s.used, s.eventId, s.lastSeq, s.phase = true, p.eventId, p.seq, "TELEGRAPH"
        s.deadline = now + math.min(p.remainingMs / 1000, 20)
        s.lastNow = now
        return {kind = "SPAWN", phase = "TELEGRAPH", remainingMs = p.remainingMs}
    end
    if now >= s.deadline or p.phase == "END" or p.remainingMs == 0 then
        s.lastNow, s.lastSeq, s.phase = now, p.seq, "ENDED"
        return {kind = "DESPAWN", reason = "END_OR_TIMEOUT"}
    end
    if s.phase == "ACTIVE" and p.phase == "TELEGRAPH" then
        return {kind = "IGNORE", reason = "PHASE_ROLLBACK"}
    end
    local newDeadline = now + p.remainingMs / 1000
    -- Never permit a later server message to prolong the client visual effect.
    s.deadline = math.min(s.deadline, newDeadline)
    s.lastNow, s.lastSeq, s.phase = now, p.seq, p.phase
    return {kind = "UPDATE", phase = p.phase, remainingMs = math.floor(math.max(0, (s.deadline - now) * 1000))}
end
function M.tick(s, now)
    if type(s) ~= "table" or not timeok(now) or now < s.lastNow then
        return {kind = "IGNORE", reason = "INVALID_TIME"}
    end
    s.lastNow = now
    if s.closed or s.phase == "ENDED" then return {kind = "IGNORE", reason = "CLOSED"} end
    if s.used and s.deadline and now >= s.deadline then
        s.phase = "ENDED"
        return {kind = "DESPAWN", reason = "TTL"}
    end
    return {kind = "NOOP"}
end
function M.close(s)
    if type(s) ~= "table" then return {kind = "IGNORE"} end
    s.closed, s.phase = true, "ENDED"
    return {kind = "DESPAWN", reason = "ROUND_CLOSED"}
end
return M
