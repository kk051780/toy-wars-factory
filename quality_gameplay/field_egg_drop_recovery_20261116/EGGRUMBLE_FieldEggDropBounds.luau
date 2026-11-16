--!strict
-- GQ FIELD-EGG-RECOVERY V1. Pure server-side TEAM/BR drop position policy.
-- Source-only candidate. No egg counts, attribution, remotes, item effects, or currency.
local Drop={}
local WORLD_X={TEAM=-620,BATTLE_ROYALE=620}
local HALF_X=445
local HALF_Z=525
local CENTER_Z=465
local MARGIN=40 -- protects all 3 released-egg parts, each shifted at most 3 studs

local function finite(value:any):boolean
 return type(value)=="number" and value==value and value~=math.huge and value~=-math.huge
end
local function clamp(value:number,low:number,high:number):number
 return math.max(low,math.min(value,high))
end

function Drop.recover(mode:string,rootX:number,rootZ:number,
 impactX:any,impactZ:any,homeX:any,homeZ:any):any
 local offset=WORLD_X[mode]
 assert(offset~=nil,"unknown TEAM/BR mode")
 assert(finite(rootX) and finite(rootZ),"invalid server world root")
 local centerX=rootX+offset
 local centerZ=rootZ+CENTER_Z
 local minX=centerX-HALF_X+MARGIN
 local maxX=centerX+HALF_X-MARGIN
 local minZ=centerZ-HALF_Z+MARGIN
 local maxZ=centerZ+HALF_Z-MARGIN
 -- The fall may have destroyed the character root before the Died callback.
 -- Fallback is exclusively the server's own preexisting castle coordinate.
 local x=if finite(impactX) then impactX
  elseif finite(homeX) then homeX else centerX
 local z=if finite(impactZ) then impactZ
  elseif finite(homeZ) then homeZ else centerZ
 local finalX=clamp(x,minX,maxX)
 local finalZ=clamp(z,minZ,maxZ)
 return {x=finalX,z=finalZ,corrected=finalX~=impactX or finalZ~=impactZ,
  minX=minX,maxX=maxX,minZ=minZ,maxZ=maxZ}
end
return Drop
