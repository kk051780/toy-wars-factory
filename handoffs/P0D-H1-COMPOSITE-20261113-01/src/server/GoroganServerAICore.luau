--!strict
-- D07 isolated SERVER decision reference; never called from RemoteEvent directly.
-- No spawning, combat mutation, pathfinding, RNG, client data or event scheduler.
local Core = {}
local LIMIT = {TTL=14, WINDUP=2, DAMAGE=8, RADIUS=7, MAX_STOMPS=3,
    MAX_PLAYERS=24, LEASH=42, AGGRO=45, CHASE_STEP=8, MOVE_GAP=0.75, COOLDOWN=2.0}

local function finite(v: any, lo: number, hi: number): boolean
    return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge and v >= lo and v <= hi
end
local function id(v: any): boolean
    return type(v) == "string" and #v >= 1 and #v <= 64 and v:match("^[%w_-]+$") ~= nil
end
local function pos(v: any): boolean
    return type(v) == "table" and finite(v.x, -2048, 2048) and finite(v.y,-100,700) and finite(v.z,-2048,2048)
end
local function d2(a,b): number
    local x,z=a.x-b.x,a.z-b.z
    return x*x+z*z
end
local function copy(v)
    return {x=v.x, y=v.y, z=v.z}
end
local function ownerOf(input): boolean
    return input.kind == "BOSS" and input.subtype == "GOROGAN"
end
function Core.new()
    return {active=nil, seenRounds={}, seenCount=0}
end
-- Input only from canonical v40 ChaosEventCore ACTIVATE; not from a client packet.
-- The engine owns the authoritative timestamp, round ID, chosen stage and origin.
function Core.start(state, input)
    if type(input) ~= "table" or not id(input.roundId) or not id(input.eventId)
        or (input.stageId ~= "S1" and input.stageId ~= "S3") or not ownerOf(input)
        or not pos(input.origin) or not finite(input.now,0,1e12)
        or not finite(input.endsAt,0,1e12)
        or input.endsAt <= input.now or input.endsAt - input.now > LIMIT.TTL then
        return false, "REJECTED_START"
    end
    if state.active ~= nil or state.seenRounds[input.roundId] or state.seenCount >= 128 then
        return false, "REPLAY_OR_ACTIVE"
    end
    state.seenRounds[input.roundId] = true
    state.seenCount += 1
    state.active = {roundId=input.roundId,eventId=input.eventId,stageId=input.stageId,
        origin=copy(input.origin),endsAt=input.endsAt,lastNow=input.now,
        attackId=0,stomps=0,phase="ACTIVE",windupEnds=0,attackCenter=nil,
        nextAttackAt=input.now+2.0,nextMoveAt=input.now}
    return true, {kind="START", bossId="GOROGAN", roundId=input.roundId,
        eventId=input.eventId,stageId=input.stageId, position=copy(input.origin)}
end
local function makeEnd(state, reason)
    local a=state.active
    if not a then return nil end
    state.active=nil
    return {kind="END",roundId=a.roundId,eventId=a.eventId,stageId=a.stageId,
        bossId="GOROGAN",reason=reason}
end
function Core.stop(state, roundId, eventId)
    local a=state.active
    if a == nil or a.roundId ~= roundId or a.eventId ~= eventId then
        return nil, "REJECTED_EVENT"
    end
    return makeEnd(state,"ROUND_END"), nil
end
local function nearest(players, bossPos)
    if type(players) ~= "table" or #players > LIMIT.MAX_PLAYERS then
        return nil, "INVALID_ROSTER"
    end
    local best,nearestD2=nil,math.huge
    local seen={}
    for _,p in ipairs(players) do
        if type(p)~="table" or not id(p.playerId) or seen[p.playerId] then
            return nil,"INVALID_ROSTER"
        end
        seen[p.playerId]=true
        if p.alive == true and p.inSafeZone ~= true and
            (p.team == "BLUE" or p.team == "RED") and pos(p.position) then
            local dy=math.abs(bossPos.y-p.position.y)
            local distance=d2(bossPos,p.position)
            if dy <= 12 and distance <= LIMIT.AGGRO*LIMIT.AGGRO then
                if distance < nearestD2 or (distance == nearestD2 and
                        (best == nil or p.playerId < best.playerId)) then
                    best,nearestD2=p,distance
                end
            end
        end
    end
    return best,nil
end
-- Returns at most one command per tick. Caller must apply MoveTo through a
-- REAL server-rig navigator and validate line-of-sight at hit resolution.
function Core.tick(state, input)
    local a=state.active
    if not a then return nil,"INACTIVE" end
    if type(input)~="table" or input.roundId ~= a.roundId or input.eventId ~= a.eventId
        or not finite(input.now,0,1e12) or input.now < a.lastNow
        or not pos(input.bossPosition) then return nil,"STALE_OR_INVALID" end
    a.lastNow=input.now
    if input.matchActive ~= true or input.now >= a.endsAt then
        return makeEnd(state,"LIFETIME_OR_ROUND_END"),nil
    end
    if d2(input.bossPosition,a.origin) > LIMIT.LEASH*LIMIT.LEASH then
        return {kind="MOVE",position=copy(a.origin),reason="LEASH_RETURN"},nil
    end
    if a.phase=="WINDUP" then
        if input.now < a.windupEnds then return nil,nil end
        a.phase="ACTIVE"
        a.nextAttackAt=input.now+LIMIT.COOLDOWN
        return {kind="STOMP_RESOLVE",attackId=a.attackId,center=copy(a.attackCenter),
            radius=LIMIT.RADIUS,damage=LIMIT.DAMAGE,roundId=a.roundId,eventId=a.eventId},nil
    end
    local target,err=nearest(input.players,input.bossPosition)
    if err then return nil,err end
    if not target then return nil,nil end
    local distance=d2(input.bossPosition,target.position)
    if a.stomps < LIMIT.MAX_STOMPS and input.now >= a.nextAttackAt
        and input.now + LIMIT.WINDUP < a.endsAt and distance <= 9*9 then
        a.stomps += 1
        a.attackId += 1
        a.attackCenter=copy(input.bossPosition)
        a.windupEnds=input.now+LIMIT.WINDUP
        a.phase="WINDUP"
        return {kind="STOMP_WARNING",attackId=a.attackId,center=copy(a.attackCenter),
            windupEnds=a.windupEnds,roundId=a.roundId,eventId=a.eventId},nil
    end
    if input.now < a.nextMoveAt or distance <= 8*8 then return nil,nil end
    -- Bounded intent only: do not teleport rig or trust client-provided coordinates.
    local dx,dz=target.position.x-input.bossPosition.x,target.position.z-input.bossPosition.z
    local norm=math.sqrt(dx*dx+dz*dz)
    if norm <= 0 then return nil,nil end
    local step=math.min(LIMIT.CHASE_STEP,norm)
    local candidate={x=input.bossPosition.x+dx/norm*step,
        y=input.bossPosition.y,z=input.bossPosition.z+dz/norm*step}
    if d2(candidate,a.origin)>LIMIT.LEASH*LIMIT.LEASH then
        candidate=copy(a.origin)
    end
    a.nextMoveAt=input.now+LIMIT.MOVE_GAP
    return {kind="MOVE",position=candidate,reason="CHASE",targetId=target.playerId},nil
end
function Core.snapshot(state)
    local a=state.active
    if not a then return {active=false,seenRoundCount=state.seenCount} end
    return {active=true,roundId=a.roundId,phase=a.phase,stomps=a.stomps,
        nextAttackAt=a.nextAttackAt,expiresAt=a.endsAt,seenRoundCount=state.seenCount}
end
return Core
