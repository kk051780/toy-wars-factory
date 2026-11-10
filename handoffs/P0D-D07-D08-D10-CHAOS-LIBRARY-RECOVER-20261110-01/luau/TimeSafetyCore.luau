--!strict
-- TRAP RAIDERS v41: self-only local rewind of safe position, NOT the match timeline.
-- A server-owned spatial validator MUST revalidate the destination immediately.
local Core = {}
local function finite(n): boolean
    return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
local function safeVec(p)
    if type(p)~="table" or not (finite(p.x) and finite(p.y) and finite(p.z)) then return nil end
    if math.abs(p.x)>10000 or math.abs(p.y)>10000 or math.abs(p.z)>10000 then return nil end
    return {x=p.x,y=p.y,z=p.z}
end
function Core.new(matchId: string)
    assert(type(matchId)=="string" and #matchId>0 and #matchId<=96)
    return {matchId=matchId,lastAt=0,samples={},used={},closed=false}
end
function Core.record(state, now:number, userId:number, p, serverSnapshot)
    if state.closed or not finite(now) or now<state.lastAt then return false,"TIME_INVALID" end
    state.lastAt=now
    if type(userId)~="number" or userId<1 or userId%1~=0 or type(serverSnapshot)~="table"
       or serverSnapshot.matchId~=state.matchId or serverSnapshot.alive~=true
       or serverSnapshot.safeFloor~=true or serverSnapshot.carryingEgg==true then return false,"RECORD_BLOCKED" end
    local v=safeVec(p)
    if not v then return false,"POSITION_INVALID" end
    local h=state.samples[userId] or {}
    h[#h+1]={at=now,pos=v,matchId=state.matchId}
    -- max three seconds of safe position data, bounded memory per player
    while #h>0 and (now-h[1].at>3 or #h>10) do table.remove(h,1) end
    state.samples[userId]=h
    return true,"RECORDED"
end
function Core.rewind(state,now:number,userId:number,serverCurrent,isSafeDestination)
    if state.closed or not finite(now) or now<state.lastAt then return nil,"TIME_INVALID" end
    state.lastAt=now
    if type(serverCurrent)~="table" or serverCurrent.matchId~=state.matchId
       or serverCurrent.userId~=userId or serverCurrent.alive~=true
       or serverCurrent.carryingEgg==true or serverCurrent.activeMatch~=true
       or serverCurrent.serverRosterConfirmed~=true or state.used[userId] then return nil,"RECALL_BLOCKED" end
    if type(isSafeDestination)~="function" then return nil,"VALIDATOR_REQUIRED" end
    local h=state.samples[userId] or {}
    local target=nil
    for _,sample in ipairs(h) do
        if sample.at<=now-2 and sample.at>=now-3 then target=sample.pos end
    end
    if not target or not isSafeDestination(target,serverCurrent) then return nil,"NO_SAFE_SNAPSHOT" end
    state.used[userId]=true -- one use each match; no HP/score/revival change
    return {x=target.x,y=target.y,z=target.z},"RECALL_POSITION_ONLY"
end
function Core.close(state)
    state.closed=true
    state.samples={}
end
return Core
