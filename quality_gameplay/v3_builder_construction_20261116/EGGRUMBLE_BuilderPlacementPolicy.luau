--!strict
-- Pure numeric checks used by the server-only BUILDER construction ability.
-- No service, damage, score, data store, remote, or Roblox instance authority.
local Policy={}
Policy.LIFETIME=9
Policy.MAX_PER_HERO=2
Policy.MAX_PER_SESSION=12
Policy.CD={WALL=13,BRIDGE=17}
local function finite(n)
 return type(n)=="number" and n==n and n<math.huge and n>-math.huge
end
function Policy.capacity(total,own)
 return finite(total) and finite(own) and total>=0 and own>=0
  and total<Policy.MAX_PER_SESSION and own<Policy.MAX_PER_HERO
end
function Policy.cooldown(kind,now,last)
 return Policy.CD[kind]~=nil and finite(now) and finite(last)
  and now-last>=Policy.CD[kind]
end
function Policy.inField(x,z,halfX,halfZ)
 return finite(x) and finite(z) and finite(halfX) and finite(halfZ)
  and halfX>24 and halfZ>24
  and math.abs(x)<halfX-24 and math.abs(z)<halfZ-24
end
function Policy.support(nearY,farY,originY)
 return finite(nearY) and finite(farY) and finite(originY)
  and math.abs(nearY-originY)<=7 and math.abs(farY-originY)<=7
  and math.abs(nearY-farY)<=3
end
function Policy.safeDistance(distance)
 return finite(distance) and distance>=51
end
-- Bridge is for crossing an actual gap or lowered crossing, never flat grass.
-- Require both anchor banks via Policy.support; midpoint must be missing or
-- at least 4 studs below the LOWER bank. NaN/inf fails closed.
function Policy.bridgeGap(midY,lowerBankY)
 if not finite(lowerBankY) then return false end
 if midY==nil then return true end
 return finite(midY) and lowerBankY-midY>=4
end
-- Global overlap must catch noncollidable Humanoids and foreign copied floors.
-- Fail closed for unknown CanCollide state.
function Policy.blocksPlacement(canCollide,ownGround,isHumanoid)
 return isHumanoid==true or (canCollide~=false and ownGround~=true)
end
return Policy
