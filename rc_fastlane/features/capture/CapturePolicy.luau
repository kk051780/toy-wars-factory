--!nocheck
-- P0D-018 source PREP ONLY. The original Game remains sole movement/match/Remote authority.
-- Callers MUST provide server-observed state; never pass unvalidated client coordinates.
local Capture={}
Capture.DURATION=4
Capture.COOLDOWN=18
Capture.RANGE=9
Capture.RESCUE_RANGE=7
local active=setmetatable({},{__mode="k"})
local recent=setmetatable({},{__mode="k"})
local function finite(n)
    return type(n)=="number" and n==n and n>=0 and n<math.huge
end
local function team(t)
    return t=="RED" or t=="BLUE"
end
local function round(n)
    return finite(n) and n==math.floor(n) and n>0
end
function Capture.status(target,now,epoch)
    if not target or not finite(now) or not round(epoch) then return nil end
    local c=active[target]
    if not c then return nil end
    if c.epoch~=epoch or now>=c.expires then active[target]=nil return nil end
    return {remaining=c.expires-now,team=c.team,expires=c.expires}
end
function Capture.begin(attacker,target,s)
    if not attacker or not target or attacker==target or type(s)~="table"
        or not finite(s.now) or not round(s.epoch)
        or s.phase~="ACTIVE" or s.role~="TRAPPER"
        or not team(s.attackerTeam) or not team(s.targetTeam)
        or s.attackerTeam==s.targetTeam
        or s.attackerAlive~=true or s.targetAlive~=true
        or s.targetInvulnerable==true or s.attackerCarrying==true
        or s.targetCarrying==true or s.serverLineOfSight~=true
        or not finite(s.serverDistance) or s.serverDistance>Capture.RANGE then
        return false,"INELIGIBLE"
    end
    if Capture.status(target,s.now,s.epoch) then return false,"ALREADY_CAPTURED" end
    if recent[attacker] and s.now-recent[attacker]<Capture.COOLDOWN then
        return false,"COOLDOWN"
    end
    for other,c in pairs(active) do
        if Capture.status(other,s.now,s.epoch)
            and c.ownerTeam==s.attackerTeam then return false,"TEAM_LIMIT" end
    end
    active[target]={owner=attacker,ownerTeam=s.attackerTeam,team=s.targetTeam,
        epoch=s.epoch,expires=s.now+Capture.DURATION}
    recent[attacker]=s.now
    return true,"CAPTURED"
end
function Capture.rescue(rescuer,target,s)
    if not rescuer or not target or rescuer==target or type(s)~="table"
        or not finite(s.now) or not round(s.epoch) or s.phase~="ACTIVE"
        or s.rescuerAlive~=true or s.targetAlive~=true
        or not team(s.rescuerTeam) or not finite(s.serverDistance)
        or s.serverDistance>Capture.RESCUE_RANGE then return false end
    local c=active[target]
    if not c or not Capture.status(target,s.now,s.epoch)
        or c.team~=s.rescuerTeam then return false end
    active[target]=nil
    return true
end
function Capture.release(target)
    if target then active[target]=nil end
end
function Capture.clearRound()
    for p in pairs(active) do active[p]=nil end
    for p in pairs(recent) do recent[p]=nil end
end
function Capture.forget(p)
    if not p then return end
    active[p]=nil
    recent[p]=nil
    for target,c in pairs(active) do
        if c.owner==p then active[target]=nil end
    end
end
return Capture
