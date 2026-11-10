--!strict
-- TRAP RAIDERS / D07. Pure SERVER-owned pose packet eligibility policy.
-- NO remote connection, event selection, rig spawn, network input, scheduler or combat.
-- Caller must source match/event/epoch/now/position ONLY from actual server round + RigDriver.
local Outbox = {}
local MIN_GAP = 0.20
local MAX_SAMPLES = 64
local TTL = 14

local function finite(v, lo, hi)
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge and v >= lo and v <= hi
end
local function validId(v)
    return type(v) == "string" and #v >= 1 and #v <= 64 and v:match("^[%w_%-]+$") ~= nil
end
local function goodPosition(p)
    return type(p) == "table" and finite(p.x,-2048,2048)
        and finite(p.y,-100,700) and finite(p.z,-2048,2048)
end
function Outbox.new(config)
    assert(type(config)=="table" and config.enabled==true and config.approvedByOwner==true,
        "D07_POSE_FOLLOW_DISABLED_DEFAULT")
    assert(validId(config.matchId) and validId(config.eventId), "SERVER_IDS_REQUIRED")
    assert(config.stageId=="S1" or config.stageId=="S3", "STAGE_NOT_APPROVED")
    assert(finite(config.epoch,0,1023) and config.epoch%1==0, "ROUND_EPOCH_INVALID")
    assert(finite(config.startedAt,0,1e12), "START_TIME_INVALID")
    assert(finite(config.endsAt,config.startedAt,config.startedAt+TTL), "LIFETIME_INVALID")
    return {
        matchId=config.matchId, eventId=config.eventId, stageId=config.stageId,
        epoch=config.epoch, startedAt=config.startedAt, endsAt=config.endsAt,
        lastAt=nil, count=0, closed=false,
    }
end

-- snapshot {matchId, eventId, stageId, epoch, now, active, position={x,y,z}}.
-- Export only a validated immutable VALUE copy, never expose the caller's mutable table.
function Outbox.sample(state, snapshot)
    if state.closed then return nil,"CLOSED" end
    if type(snapshot)~="table" or snapshot.matchId~=state.matchId
        or snapshot.eventId~=state.eventId or snapshot.stageId~=state.stageId
        or snapshot.epoch~=state.epoch or snapshot.active~=true
        or not finite(snapshot.now,state.startedAt,state.endsAt)
        or not goodPosition(snapshot.position) then
        state.closed=true
        return nil,"AUTHORITY_OR_ROUND_INVALID"
    end
    if snapshot.now >= state.endsAt then state.closed=true;return nil,"EXPIRED" end
    if state.lastAt~=nil then
        if snapshot.now < state.lastAt then state.closed=true;return nil,"CLOCK_REVERSED" end
        if snapshot.now-state.lastAt < MIN_GAP then return nil,"RATE_LIMIT" end
    end
    if state.count>=MAX_SAMPLES then state.closed=true;return nil,"SAMPLE_CAP" end
    state.lastAt=snapshot.now
    state.count+=1
    local p=snapshot.position
    return {
        kind="POSE", bossId="GOROGAN", matchId=state.matchId,
        eventId=state.eventId, stageId=state.stageId, epoch=state.epoch,
        poseSeq=state.count, position={x=p.x,y=p.y,z=p.z},
    },"EMIT"
end
function Outbox.close(state)
    state.closed=true
end
return Outbox
