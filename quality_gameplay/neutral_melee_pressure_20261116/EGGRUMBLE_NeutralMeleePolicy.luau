--!strict
-- GQ-V3-NEUTRAL-MELEE-20261116: pure, testable per-soldier/per-victim melee policy.
-- No Game, Remote, score, egg, role, or neutral-spawner authority.
local Policy={}
Policy.DAMAGE=4
Policy.RANGE=4.25
Policy.SOLDIER_COOLDOWN=1.4
Policy.VICTIM_COOLDOWN=0.8
Policy.MAX_RAYS_PER_TICK=24

function Policy.ready(lastSoldier:any,lastVictim:any,soldier:any,victim:any,now:number,distance:number,
 active:boolean,attackerAlive:boolean,victimAlive:boolean):boolean
 if not active or not attackerAlive or not victimAlive then return false end
 if type(now)~="number" or now~=now or type(distance)~="number" or distance~=distance then return false end
 if distance<0 or distance>Policy.RANGE then return false end
 local s=lastSoldier[soldier]
 local v=lastVictim[victim]
 if s~=nil and now-s<Policy.SOLDIER_COOLDOWN then return false end
 if v~=nil and now-v<Policy.VICTIM_COOLDOWN then return false end
 return true
end

-- Commit only AFTER a real server-side unobstructed ray. Failed LOS never spends a cooldown.
function Policy.commit(lastSoldier:any,lastVictim:any,soldier:any,victim:any,now:number):()
 lastSoldier[soldier]=now
 lastVictim[victim]=now
end
return Policy
