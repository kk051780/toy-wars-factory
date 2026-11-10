-- Optional adapter; only the server's trusted round and roster may supply data.
-- Never requires RemoteEvent, never directly calls TakeDamage or manipulates NPC physics.
local Adapter = {}
function Adapter.newLedger(roundId,eventId)
    if type(roundId)~="string" or type(eventId)~="string" then return nil end
    return {roundId=roundId,eventId=eventId,consumed={}}
end
local function valid(x)
    return type(x)=="number" and x==x and x>-100000 and x<100000
end
local function d(a,b)
    local dx=a.x-b.x;local dz=a.z-b.z
    return math.sqrt(dx*dx+dz*dz)
end
-- Integration must pass a fresh snapshot generated from the authoritative server
-- immediately before applying an intention. The LOS function must raycast on SERVER.
function Adapter.authorizeLightning(intent, snapshot, serverLineOfSight, ledger)
    if type(intent)~="table" or intent.kind~="LIGHTNING_INTENT" then return false,"NO_INTENT" end
    if type(snapshot)~="table" or snapshot.authorized~=true or snapshot.running~=true then return false,"UNTRUSTED_ROUND" end
    if type(ledger)~="table" or ledger.roundId~=intent.roundId or ledger.eventId~=intent.eventId or type(ledger.consumed)~="table" then return false,"LEDGER_REQUIRED" end
    if snapshot.roundId~=intent.roundId or snapshot.eventId~=intent.eventId then return false,"STALE_ROUND" end
    if not valid(intent.attackNo) or intent.attackNo~=math.floor(intent.attackNo) or intent.attackNo<1 or intent.attackNo>3 or intent.damageCap~=7 then return false,"CAP" end
    if type(intent.bossPos)~="table" or not valid(intent.bossPos.x) or not valid(intent.bossPos.z) or
        type(snapshot.bossPos)~="table" or not valid(snapshot.bossPos.x) or not valid(snapshot.bossPos.z) or
        d(snapshot.bossPos,intent.bossPos)>2 then return false,"BOSS_POSITION" end
    if ledger.consumed[intent.attackNo] then return false,"REPLAY" end
    if type(snapshot.roster)~="table" or #snapshot.roster>16 then return false,"ROSTER" end
    if type(serverLineOfSight)~="function" then return false,"LOS_REQUIRED" end
    local target=nil
    for _,p in ipairs(snapshot.roster) do
        if p.id==intent.targetId then
            if target then return false,"DUPLICATE_PLAYER" end
            target=p
        end
    end
    if type(target)~="table" or target.alive~=true or target.team~="RAIDERS" or target.invulnerable==true
        or type(target.pos)~="table" or not valid(target.pos.x) or not valid(target.pos.z)
        or d(snapshot.bossPos,target.pos)>12 then return false,"INVALID_TARGET" end
    if serverLineOfSight(snapshot.bossPos,target.pos,intent.targetId)~=true then return false,"LOS_BLOCKED" end
    -- Persist before returning so repeated adapter calls cannot issue another intent.
    ledger.consumed[intent.attackNo]=true
    -- Real damage applier must use its own server-owned exactly-once transaction.
    -- Return data only: NEVER call Humanoid:TakeDamage in this reference.
    return true,{targetId=target.id,maxDamage=7,roundId=intent.roundId,
        eventId=intent.eventId,attackNo=intent.attackNo}
end
return Adapter
