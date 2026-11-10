--!strict
-- Pure CLIENT presentation policy. Not a second OnClientEvent subscriber.
-- Feed only server FireClient POSE from the existing approved visual adapter.
-- Original GoroganVisualPolicy stays authoritative for START/STOMP/END lifecycle.
local Follower={}
local MAX_AGE_GAP=1.5
local MAX_FOLLOW_SPEED=48
local EPSILON=2
local MIN_GAP=0.12
local function finite(v,lo,hi)
    return type(v)=="number" and v==v and v~=math.huge and v~=-math.huge and v>=lo and v<=hi
end
local function validId(v)
    return type(v)=="string" and #v>=1 and #v<=64 and v:match("^[%w_%-]+$")~=nil
end
local function pos(v)
    return type(v)=="table" and finite(v.x,-2048,2048)
        and finite(v.y,-100,700) and finite(v.z,-2048,2048)
end
local function distance(a,b)
    local x,y,z=a.x-b.x,a.y-b.y,a.z-b.z
    return math.sqrt(x*x+y*y+z*z)
end
function Follower.new(matchId,eventId,stageId,epoch,initialPosition,now)
    assert(validId(matchId) and validId(eventId),"VISUAL_CONTEXT_REQUIRED")
    assert(stageId=="S1" or stageId=="S3","VISUAL_STAGE_INVALID")
    assert(finite(epoch,0,1023) and epoch%1==0,"VISUAL_EPOCH_INVALID")
    assert(pos(initialPosition) and finite(now,0,1e12),"INITIAL_POSE_INVALID")
    return {matchId=matchId,eventId=eventId,stageId=stageId,epoch=epoch,
        current={x=initialPosition.x,y=initialPosition.y,z=initialPosition.z},
        startAt=now,lastNow=now, lastAcceptedAt=nil, lastSeq=0, closed=false, invalidCount=0}
end
-- approvedLifeCycleActive must come from existing VisualPolicy.state.active, not a POSE packet.
function Follower.accept(state,packet,now,approvedLifeCycleActive)
    if state.closed then return nil,"CLOSED" end
    if approvedLifeCycleActive~=true then state.closed=true;return nil,"VISUAL_ENDED" end
    if not finite(now,0,1e12) or now<state.lastNow then
        state.closed=true;return nil,"LOCAL_CLOCK_REVERSED"
    end
    state.lastNow=now
    if type(packet)~="table" or packet.kind~="POSE" or packet.bossId~="GOROGAN"
        or packet.matchId~=state.matchId or packet.eventId~=state.eventId
        or packet.stageId~=state.stageId or packet.epoch~=state.epoch
        or not finite(packet.poseSeq,1,64)
        or packet.poseSeq%1~=0 or not pos(packet.position) then
        state.invalidCount+=1
        return nil,"INVALID_POSE"
    end
    if packet.poseSeq<=state.lastSeq then return nil,"POSE_REPLAY" end
    local dt=now-(state.lastAcceptedAt or state.startAt)
    if state.lastAcceptedAt~=nil and dt<MIN_GAP then return nil,"RATE_LIMIT" end
    -- Including the FIRST pose, reject stale delivery or impossible jumps.
    if dt>MAX_AGE_GAP then
        state.closed=true
        return nil,"CLIENT_SUSPENDED_REQUIRES_NEW_AUTH_START"
    end
    if distance(state.current,packet.position)>MAX_FOLLOW_SPEED*dt+EPSILON then
        state.invalidCount+=1
        return nil,"IMPOSSIBLE_VISUAL_JUMP"
    end
    local p=packet.position
    state.current={x=p.x,y=p.y,z=p.z}
    state.lastSeq=packet.poseSeq
    state.lastAcceptedAt=now
    return {x=p.x,y=p.y,z=p.z},"FOLLOW"
end
function Follower.close(state) state.closed=true end
return Follower
