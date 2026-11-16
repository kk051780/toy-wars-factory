--!strict
-- EGGRUMBLE V3 isolated personal-castle defense policy.
-- Pure Luau: this file does not create Game, Remote, DataStore or paid advantages.
local Policy={}
Policy.TICK_SECONDS=0.35
Policy.MAX_CASTLES=16
Policy.CONFIG={
 TURRET={cooldown=2.4,range=35,damage=12,needsLOS=true},
 TRAP={cooldown=7.0,range=9,damage=8,needsLOS=true},
 SENSOR={cooldown=1.0,range=30,damage=0,needsLOS=false},
}
Policy.ORDER={"SENSOR","TRAP","TURRET"}

local function finite(n:any):boolean
 return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge
end

function Policy.hasModule(owner:any,kind:string):boolean
 if not owner or not Policy.CONFIG[kind] then return false end
 for _,name in ipairs(owner.modules or {}) do
  if name==kind then return true end
 end
 return false
end

function Policy.canTarget(mode:string,owner:any,intruder:any):boolean
 if mode~="TEAM" and mode~="BATTLE_ROYALE" then return false end
 if not owner or not intruder or owner.id==nil or intruder.id==nil then return false end
 if owner.alive~=true or intruder.alive~=true or tostring(owner.id)==tostring(intruder.id) then return false end
 if mode=="TEAM" then
  if (owner.team~="RED" and owner.team~="BLUE")
   or (intruder.team~="RED" and intruder.team~="BLUE") then return false end
  if owner.team==intruder.team then return false end
 end
 return true
end

function Policy.mayActivate(kind:string,phase:string,now:number,last:number?,
 distance:number,hasLOS:boolean):boolean
 local config=Policy.CONFIG[kind]
 if not config or phase~="ACTIVE" then return false end
 if not finite(now) or not finite(distance) or distance<0 or distance>config.range then return false end
 if last~=nil and (not finite(last) or now<last or now-last<config.cooldown) then return false end
 return not config.needsLOS or hasLOS==true
end

-- Transparent Assassin bypasses automatic turret/trap targeting until detected.
-- The SENSOR is a counterpick and fires only against genuinely invisible human heroes.
function Policy.canAcquire(kind:string,now:number,stealthUntil:any):boolean
 if not Policy.CONFIG[kind] or not finite(now) or not finite(stealthUntil) then return false end
 local invisible=stealthUntil>now
 if kind=="SENSOR" then return invisible end
 return not invisible
end

return Policy
