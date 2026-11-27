--!strict
-- Shared V3 shape filter for real NPC and hero damage. Direction is server-side.
-- Circle = mage/explosions/curse, fan = melee slash, lane = rifle/spear/rail.
local Geometry={}
local FAN={BLADE=true,SHADOW=true,SHURIKEN=true,WIND=true,FANG=true}
local LANE={RAIL=true,LANCE=true}
function Geometry.allowed(origin:Vector3,center:Vector3,target:Vector3,radius:number,shape:string):boolean
 if radius<=0 or radius>22 then return false end
 local dx=target.X-center.X
 local dz=target.Z-center.Z
 local radial=math.sqrt(dx*dx+dz*dz)
 if not FAN[shape] and not LANE[shape] then return radial<=radius end
 local x=center.X-origin.X
 local z=center.Z-origin.Z
 local range=math.sqrt(x*x+z*z)
 if range<.5 then return radial<=radius end
 local ux=x/range
 local uz=z/range
 local deltaX=target.X-origin.X
 local deltaZ=target.Z-origin.Z
 local forward=deltaX*ux+deltaZ*uz
 if forward<1 or forward>range+radius then return false end
 local cross=math.abs(deltaX*(-uz)+deltaZ*ux)
 if LANE[shape] then
  local laneWidth=math.min(4.5,math.max(2.5,radius*.44))
  return cross<=laneWidth
 end
 -- fan gets wider after leaving the sword/hand, rewarding frontal positioning
 local fanWidth=math.max(3.3,radius*(.26+.84*math.min(1,forward/(range+radius))))
 return cross<=fanWidth
end
function Geometry.kind(shape:string):string
 if LANE[shape] then return "LANE" end
 if FAN[shape] then return "FAN" end
 return "CIRCLE"
end
return Geometry
