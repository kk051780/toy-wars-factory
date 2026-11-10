-- TRAP_RAIDERS: pure, server-side Ligardo S2/S4 intention policy.
-- NEVER called directly with RemoteEvent/client input. An authorized game server must
-- supply fresh round snapshots. This module does NOT move Models or deal damage.
local Policy = {}

local MAX_LIFE = 16
local TARGET_RANGE = 55
local LIGHTNING_RANGE = 12
local CHARGE_SECONDS = 2
local COOLDOWN_SECONDS = 2.5
local MAX_ATTACKS = 3
local LEASH = 36
local SPEED = 10
local MAX_FRAME = 0.5

local function num(x)
    return type(x) == "number" and x == x and x > -100000 and x < 100000
end
local function ident(s)
    return type(s) == "string" and #s > 0 and #s <= 64 and string.match(s, "^[%w_.%-]+$") ~= nil
end
local function validPoint(p)
    return type(p) == "table" and num(p.x) and num(p.z)
end
local function distance(a,b)
    local dx = a.x-b.x
    local dz = a.z-b.z
    return math.sqrt(dx*dx + dz*dz)
end
local function copyPoint(p)
    return {x=p.x,z=p.z}
end
local function eligible(actor, s)
    return type(actor)=="table" and ident(actor.id) and actor.id ~= s.bossId
        and actor.alive == true and actor.team == "RAIDERS"
        and actor.invulnerable ~= true and validPoint(actor.pos)
        and distance(actor.pos,s.spawn) <= TARGET_RANGE
end
local function chooseTarget(s, roster)
    if type(roster)~="table" or #roster>16 then return nil end
    local seen = {}
    local best,bestDist = nil,nil
    for _,v in ipairs(roster) do
        if type(v)=="table" and ident(v.id) then
            if seen[v.id] then return nil end
            seen[v.id]=true
        end
        if eligible(v,s) then
            local d=distance(v.pos,s.pos)
            if best==nil or d < bestDist-0.00001 or (math.abs(d-bestDist)<0.00001 and v.id<best.id) then
                best=v;bestDist=d
            end
        end
    end
    return best
end
local function findTarget(s,roster,targetId)
    if type(roster)~="table" or #roster>16 then return nil end
    local matched=nil
    for _,v in ipairs(roster) do
        if type(v)=="table" and v.id==targetId then
            if matched ~= nil then return nil end
            matched=v
        end
    end
    if matched ~= nil and eligible(matched,s) then return matched end
    return nil
end
local function getMovement(s,target,dt)
    if not target or dt<=0 then return nil end
    local dx=target.pos.x-s.pos.x
    local dz=target.pos.z-s.pos.z
    local d=math.sqrt(dx*dx+dz*dz)
    if d<=0.001 then return nil end
    local step=math.min(SPEED*math.min(dt,MAX_FRAME),d)
    local intent={x=s.pos.x+dx/d*step,z=s.pos.z+dz/d*step}
    local fromSpawn=distance(intent,s.spawn)
    if fromSpawn>LEASH then
        local rx=intent.x-s.spawn.x
        local rz=intent.z-s.spawn.z
        intent.x=s.spawn.x+rx/fromSpawn*LEASH
        intent.z=s.spawn.z+rz/fromSpawn*LEASH
    end
    return intent
end

function Policy.begin(roundId,eventId,bossId,stage,spawn,now)
    if not ident(roundId) or not ident(eventId) or not ident(bossId)
        or (stage~="S2" and stage~="S4") or not validPoint(spawn)
        or not num(now) or now<0 then return nil,"INVALID_START" end
    return {roundId=roundId,eventId=eventId,bossId=bossId,stage=stage,
        spawn=copyPoint(spawn),pos=copyPoint(spawn),started=now,lastTime=now,
        seq=-1,phase="SEEK",targetId=nil,chargeUntil=nil,cooldownUntil=now,
        attempts=0,closed=false},nil
end

function Policy.close(s)
    if type(s)~="table" then return false end
    s.closed=true;s.phase="CLOSED";s.targetId=nil;s.chargeUntil=nil
    return true
end

function Policy.tick(s,round,now,seq)
    if type(s)~="table" or s.closed then return {},"CLOSED" end
    if type(round)~="table" or round.roundId~=s.roundId or round.eventId~=s.eventId
        or round.stage~=s.stage or round.bossId~=s.bossId or round.authorized~=true
        or round.running~=true then
        Policy.close(s)
        return {{kind="STOP",why="ROUND_MISMATCH"}},"ROUND_MISMATCH"
    end
    if not num(now) or now<s.lastTime or not num(seq) or seq~=math.floor(seq) or seq<=s.seq then
        return {},"STALE_INPUT"
    end
    if type(round.roster)~="table" or #round.roster>16 then return {},"INVALID_ROSTER" end
    local dt=now-s.lastTime
    s.lastTime=now;s.seq=seq
    if round.bossAlive~=true or now>=s.started+MAX_LIFE then
        Policy.close(s)
        return {{kind="STOP",why="BOSS_DEAD_OR_EXPIRED"}},nil
    end
    if s.phase=="CHARGE" then
        if now<s.chargeUntil then return {},nil end
        local target=findTarget(s,round.roster,s.targetId)
        local result={}
        if target and distance(target.pos,s.pos)<=LIGHTNING_RANGE then
            -- This is an INTENT. Adapter must freshly recheck team/LOS/range.
            result[#result+1]={kind="LIGHTNING_INTENT",targetId=target.id,
                damageCap=7,roundId=s.roundId,eventId=s.eventId,
                attackNo=s.attempts,bossPos=copyPoint(s.pos)}
        end
        s.targetId=nil;s.chargeUntil=nil;s.phase="COOLDOWN"
        s.cooldownUntil=now+COOLDOWN_SECONDS
        return result,nil
    end
    if s.phase=="COOLDOWN" then
        if now<s.cooldownUntil then return {},nil end
        s.phase="SEEK"
    end
    if s.attempts>=MAX_ATTACKS then
        return {},nil
    end
    local target=chooseTarget(s,round.roster)
    if not target then return {},nil end
    if distance(target.pos,s.pos)<=LIGHTNING_RANGE then
        s.phase="CHARGE";s.targetId=target.id
        s.chargeUntil=now+CHARGE_SECONDS;s.attempts=s.attempts+1
        return {{kind="TELEGRAPH",targetId=target.id,seconds=CHARGE_SECONDS,
            attackNo=s.attempts,roundId=s.roundId,eventId=s.eventId}},nil
    end
    local move=getMovement(s,target,dt)
    if move then
        -- Intended path waypoint only. Server-owned pathfinder must apply/verify movement.
        s.pos=copyPoint(move)
        return {{kind="MOVE_INTENT",position=move,roundId=s.roundId,eventId=s.eventId}},nil
    end
    return {},nil
end
return Policy
