--!strict
-- TRAP RAIDERS D07 visual-only policy. No NPC spawn, physics, damage, loot or scheduler.
-- Trusted server must own the match, stage, event choice and RemoteEvent firing.
-- This reducer additionally rejects malformed/replayed visual snapshots but cannot authenticate origin.
local Policy = {}

local MAX_COORD = 2048
local MAX_Y = 700
local MIN_Y = -100
local MAX_LIFETIME = 14
local MAX_STOMP_COUNT = 3

local function validId(value: any): boolean
    return type(value) == "string" and #value >= 1 and #value <= 64
        and string.match(value, "^[%w_-]+$") ~= nil
end

local function finiteNumber(value: any, lo: number, hi: number): boolean
    return type(value) == "number" and value == value
        and value ~= math.huge and value ~= -math.huge
        and value >= lo and value <= hi
end

local function validPosition(position: any): boolean
    return type(position) == "table"
        and finiteNumber(position.x, -MAX_COORD, MAX_COORD)
        and finiteNumber(position.y, MIN_Y, MAX_Y)
        and finiteNumber(position.z, -MAX_COORD, MAX_COORD)
end

function Policy.new(matchId: string, stageId: string)
    assert(validId(matchId), "matchId must be the authoritative server round ID")
    assert(stageId == "S1" or stageId == "S3", "Gorogan is restricted to S1/S3")
    return {
        matchId = matchId,
        stageId = stageId,
        highestSeq = 0,
        seenStart = false,
        active = false,
        eventId = nil,
        phase = "IDLE",
        position = nil,
        expiresAt = 0,
        telegraphUntil = 0,
        stompCount = 0,
        lastNow = 0,
    }
end

function Policy.expire(state, now: number)
    if not finiteNumber(now, 0, 1e12) or now < state.lastNow then
        return "IGNORED_CLOCK"
    end
    state.lastNow = now
    if state.active then
        if now >= state.expiresAt then
            state.active = false
            state.phase = "ENDED"
            state.position = nil
            return "EXPIRED"
        elseif (state.phase == "STOMP" or state.phase == "WARNING") and now >= state.telegraphUntil then
            state.phase = "ACTIVE"
            return "STOMP_CLEARED"
        end
    end
    return "UNCHANGED"
end

-- Snapshot format {kind="START"|"STOMP"|"END", matchId, stageId,
-- bossId="GOROGAN", eventId, seq, position={x,y,z}}.
-- Neither client inputs nor arbitrary external event/physics sources may call this method.
function Policy.apply(state, snapshot: any, now: number)
    local clockResult = Policy.expire(state, now)
    if clockResult == "IGNORED_CLOCK" then
        return "REJECTED_CLOCK"
    end
    if type(snapshot) ~= "table" then
        return "REJECTED_PACKET"
    end
    if snapshot.matchId ~= state.matchId or snapshot.stageId ~= state.stageId
        or snapshot.bossId ~= "GOROGAN" or not validId(snapshot.eventId) then
        return "REJECTED_IDENTITY"
    end
    local seq = snapshot.seq
    if not finiteNumber(seq, 1, 1e9) or seq % 1 ~= 0 or seq <= state.highestSeq then
        return "REJECTED_REPLAY"
    end
    if snapshot.kind == "START" then
        if state.seenStart or state.active or not validPosition(snapshot.position) then
            return "REJECTED_START"
        end
        state.highestSeq = seq
        state.seenStart = true -- one boss max per round, including after early END
        state.active = true
        state.eventId = snapshot.eventId
        state.phase = "WARNING"
        state.position = {x=snapshot.position.x,y=snapshot.position.y,z=snapshot.position.z}
        state.expiresAt = math.min(now + MAX_LIFETIME, 1e12)
        state.telegraphUntil = now + 2
        return "STARTED"
    end
    if not state.active or snapshot.eventId ~= state.eventId then
        return "REJECTED_EVENT"
    end
    if snapshot.kind == "STOMP" then
        if state.stompCount >= MAX_STOMP_COUNT then
            return "REJECTED_STOMP_LIMIT"
        end
        -- Do not expose a telegraph after the boss's local deadline.
        if now + 2 > state.expiresAt then
            return "REJECTED_STOMP_TIME"
        end
        state.highestSeq = seq
        state.stompCount += 1
        state.phase = "STOMP"
        state.telegraphUntil = now + 2
        return "STOMP_STARTED"
    elseif snapshot.kind == "END" then
        state.highestSeq = seq
        state.active = false
        state.phase = "ENDED"
        state.position = nil
        return "ENDED"
    end
    return "REJECTED_KIND"
end

function Policy.snapshot(state)
    return {
        active=state.active,
        phase=state.phase,
        eventId=state.eventId,
        position=state.position,
        expiresAt=state.expiresAt,
        telegraphUntil=state.telegraphUntil,
        stompCount=state.stompCount,
    }
end

return Policy
