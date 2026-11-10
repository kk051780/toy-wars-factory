-- TRAP RAIDERS P0-D D14: server-only rider mount policy REFERENCE.
-- Caller MUST derive the snapshot from server VehicleSeatCore/round/roster.
-- Never pass RemoteEvent payload fields as authority. No CFrame/physics in this module.
local M = {}
local MAX_ID_LEN = 80
local LEASE_MS = 1500
local MAX_SNAPSHOT_AGE_MS = 350
local MAX_SEAT_DISTANCE_STUDS = 8
local ROLES = {"DRIVER", "PASSENGER"}
local function ident(x)
    return type(x) == "string" and #x >= 1 and #x <= MAX_ID_LEN
        and string.match(x, "^[%w_.-]+$") ~= nil
end
local function integer(x, lower, upper)
    return type(x) == "number" and x == x and x % 1 == 0 and x >= lower and x <= upper
end
local function number(x, lower, upper)
    return type(x) == "number" and x == x and x >= lower and x <= upper
end
local function same(a,b)
    return a ~= nil and b ~= nil and a.userId == b.userId and a.characterEpoch == b.characterEpoch
        and a.seatEpoch == b.seatEpoch and a.role == b.role
end
local function copy(a)
    if a == nil then return nil end
    return {role=a.role,userId=a.userId,characterEpoch=a.characterEpoch,seatEpoch=a.seatEpoch}
end
local function unmountAll(s, why)
    local out = {}
    for _, role in ipairs(ROLES) do
        local previous = s.slots[role]
        if previous then
            table.insert(out, {role=role,userId=previous.userId,characterEpoch=previous.characterEpoch,reason=why})
            s.slots[role] = nil
        end
    end
    return out
end
function M.new(roundId, vehicleId, vehicleType)
    assert(ident(roundId) and ident(vehicleId), "invalid ids")
    assert(vehicleType == "CART" or vehicleType == "RAFT", "invalid vehicle kind")
    return {roundId=roundId,vehicleId=vehicleId,vehicleType=vehicleType,closed=false,
        authorityEpoch=0,lastSeq=0,lastNow=0,expiresAt=0,slots={}}
end
function M.close(s, why)
    s.closed = true
    s.expiresAt = 0
    return {ok=true,mounts={},unmounts=unmountAll(s,why or "ROUND_CLOSED"),reason="CLOSED"}
end
function M.watchdog(s, nowMs)
    if not integer(nowMs,0,2147483647) then return {ok=false,reason="INVALID_TIME",mounts={},unmounts={}} end
    if nowMs < s.lastNow then return {ok=false,reason="TIME_ROLLBACK",mounts={},unmounts={}} end
    s.lastNow = nowMs
    if s.closed then return {ok=false,reason="CLOSED",mounts={},unmounts={}} end
    if s.expiresAt > 0 and nowMs >= s.expiresAt then
        s.expiresAt = 0
        return {ok=true,reason="AUTH_LEASE_EXPIRED",mounts={},unmounts=unmountAll(s,"AUTH_EXPIRED")}
    end
    return {ok=true,reason="NO_CHANGE",mounts={},unmounts={}}
end
local function goodActor(x, role, seatEpoch, team)
    if x == nil then return true end
    if type(x) ~= "table" or x.role ~= role then return false end
    if not integer(x.userId,1,2147483647) or not integer(x.characterEpoch,1,2147483647) then return false end
    if x.seatEpoch ~= seatEpoch or x.team ~= team or x.alive ~= true or x.isSeated ~= true then return false end
    if x.hasEgg ~= false or x.isSnared ~= false or x.isRewinding ~= false or x.isGliding ~= false then return false end
    if not number(x.distanceStuds,0,MAX_SEAT_DISTANCE_STUDS) then return false end
    return true
end
function M.update(s, snap, nowMs)
    local empty = {mounts={},unmounts={}}
    if s.closed then return {ok=false,reason="CLOSED",mounts={},unmounts={}} end
    if not integer(nowMs,0,2147483647) or nowMs < s.lastNow then
        return {ok=false,reason="INVALID_OR_REWOUND_CLOCK",mounts={},unmounts={}}
    end
    -- An authentic round mismatch is terminal: do not leave riders welded to a previous round.
    if type(snap) == "table" and snap.roundId ~= s.roundId then
        s.lastNow = nowMs
        local r = M.close(s,"ROUND_CHANGED")
        r.reason = "ROUND_CHANGED"
        return r
    end
    if type(snap) == "table" and snap.roundId == s.roundId and snap.roundOpen == false then
        s.lastNow = nowMs
        local result = M.close(s,"ROUND_CLOSED")
        result.reason = "ROUND_CLOSED"
        return result
    end
    if type(snap) ~= "table" or snap.vehicleId ~= s.vehicleId or snap.vehicleType ~= s.vehicleType
        or (snap.stage ~= "S1" and snap.stage ~= "S2") or not ident(snap.team)
        or not integer(snap.authorityEpoch,1,2147483647)
        or not integer(snap.seq,1,2147483647)
        or not integer(snap.issuedAtMs,0,2147483647)
        or snap.issuedAtMs > nowMs or nowMs - snap.issuedAtMs > MAX_SNAPSHOT_AGE_MS
        or type(snap.slots) ~= "table" or snap.roundOpen ~= true then
        return {ok=false,reason="INVALID_AUTHORITY_SNAPSHOT",mounts={},unmounts={}}
    end
    if snap.authorityEpoch < s.authorityEpoch or (snap.authorityEpoch == s.authorityEpoch and snap.seq <= s.lastSeq) then
        return {ok=false,reason="REPLAY_OR_OLD_EPOCH",mounts={},unmounts={}}
    end
    local driver=snap.slots.DRIVER
    local passenger=snap.slots.PASSENGER
    if not goodActor(driver,"DRIVER",snap.authorityEpoch,snap.team)
        or not goodActor(passenger,"PASSENGER",snap.authorityEpoch,snap.team)
        or (passenger and not driver)
        or (driver and passenger and driver.userId == passenger.userId) then
        -- An authentic invalid roster may mean death, team switch or leaving: release NOW.
        s.lastNow = nowMs
        s.lastSeq = snap.seq
        s.authorityEpoch = snap.authorityEpoch
        s.expiresAt = 0
        return {ok=false,reason="INVALID_ROSTER",mounts={},unmounts=unmountAll(s,"INVALID_ROSTER")}
    end
    -- With epoch change, force release even if same user ID is present (stale-character safety).
    local changedEpoch = snap.authorityEpoch ~= s.authorityEpoch
    local mounts,unmounts={},{}
    for _,role in ipairs(ROLES) do
        local prev=s.slots[role]
        local desired=snap.slots[role]
        if prev and (changedEpoch or not same(prev,desired)) then
            table.insert(unmounts,{role=role,userId=prev.userId,characterEpoch=prev.characterEpoch,reason=changedEpoch and "NEW_AUTH_EPOCH" or "SEAT_CHANGED"})
        end
        if desired and (changedEpoch or not same(prev,desired)) then
            table.insert(mounts,{role=role,userId=desired.userId,characterEpoch=desired.characterEpoch,seatEpoch=desired.seatEpoch})
        end
        s.slots[role]=copy(desired)
    end
    s.authorityEpoch=snap.authorityEpoch
    s.lastSeq=snap.seq
    s.lastNow=nowMs
    s.expiresAt=nowMs+LEASE_MS
    return {ok=true,reason="AUTH_SYNC",mounts=mounts,unmounts=unmounts}
end
function M.releaseFailedMount(s, role, userId, characterEpoch)
    if role ~= "DRIVER" and role ~= "PASSENGER" then return false end
    local current=s.slots[role]
    if current and current.userId==userId and current.characterEpoch==characterEpoch then
        s.slots[role]=nil
        -- Driver mount fails: passenger must be detached in caller by using explicit close/watchdog.
        return true
    end
    return false
end
M.MAX_SEAT_DISTANCE_STUDS=MAX_SEAT_DISTANCE_STUDS
M.AUTH_LEASE_MS=LEASE_MS
return M
