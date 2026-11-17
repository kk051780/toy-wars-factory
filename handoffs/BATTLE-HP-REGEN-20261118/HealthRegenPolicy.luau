--!strict
-- BATTLE-HP-REGEN (#765): pure candidate for the existing sole-authority Combat/Host.
-- This module NEVER touches Humanoid/Remote/Game/Store; the server must pass real HP delta.
local M={}
M.OUT_OF_COMBAT_DELAY=7
M.MAX_HP_PER_SECOND=0.007
M.MAX_STEP_SECONDS=1
M.ROLE_MAX_HP={
 WARRIOR=250, MAGE=195, NINJA=185, TRAPPER=205,
 BUILDER=225, BEAST=220, ZOMBIE=230,
}
local function finite(n)
 return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end
function M.baseHP(role)
 if type(role)~="string" then return nil end
 return M.ROLE_MAX_HP[role]
end
-- Call only after a server-authoritative Humanoid health observation.
-- Healing, invalid samples and health increases never reset the damage clock.
-- All real sources (PvP, PvE, boss, hazard, DOT) must report actual HP loss here.
function M.recordRealDamage(before,after,at,previous)
 if not finite(before) or not finite(after) or not finite(at) or at<0 then return previous,false end
 if before>0 and after<before then return at,true end
 return previous,false
end
-- ctx is a fresh server-owned current session/avatar snapshot.
-- Fail closed if any required membership/liveness signal is absent.
-- Returns proposed new HP, recovered HP and a compact reason.
function M.step(health,maxHealth,lastDamageAt,now,deltaSeconds,ctx)
 if not finite(health) or not finite(maxHealth) or not finite(now)
  or not finite(deltaSeconds) or not finite(lastDamageAt)
  or maxHealth<=0 or now<0 or deltaSeconds<=0 or lastDamageAt<0
  or now<lastDamageAt or type(ctx)~="table" then
  return health,0,"INVALID"
 end
 if health<=0 then return health,0,"DOWN" end
 if health>=maxHealth then return health,0,"FULL" end
 if ctx.active~=true or ctx.currentSession~=true or ctx.currentAvatar~=true
  or ctx.alive~=true or ctx.downed==true or ctx.eliminated==true
  or ctx.hasDamageOverTime==true or ctx.inCombat==true then
  return health,0,"BLOCKED"
 end
 local t0=now-math.min(deltaSeconds,M.MAX_STEP_SECONDS)
 local resume=lastDamageAt+M.OUT_OF_COMBAT_DELAY
 if now<=resume then return health,0,"WAIT" end
 local eligible=now-math.max(t0,resume)
 if eligible<=0 then return health,0,"WAIT" end
 local gained=math.min(maxHealth-health,maxHealth*M.MAX_HP_PER_SECOND*eligible)
 return health+gained,gained,"RECOVERING"
end
return M
