local Projectile=require("./MageProjectiles")
local V={}
V.__index=V
function V.new(x,y,z) return setmetatable({x=x,y=y,z=z},V) end
function V.__sub(a,b) return V.new(a.x-b.x,a.y-b.y,a.z-b.z) end
function V.__mul(a,n) return V.new(a.x*n,a.y*n,a.z*n) end
function V:Dot(b) return self.x*b.x+self.y*b.y+self.z*b.z end
local origin,direction=V.new(4,2,-3),V.new(0,0,1)
local replays={}
local function target(id,along,side,radius)
 return {id=id,token=id,center=V.new(4+side,2,-3+along),radius=radius or 0}
end
local stages={8,10,12,14,16}
local counts={1,1,2,2,3}
for _,spell in ipairs({{"MAGE-033",16},{"MAGE-051",15},{"MAGE-071",14}}) do
 for k,reach in ipairs(stages) do
  local plan=assert(Projectile.plan(spell[1],k-1))
  assert(plan.reach==reach and plan.limit==counts[k] and plan.cooldown==spell[2] and plan.energy==30)
  local endTime=plan.tell+reach/plan.speed
  assert(Projectile.travel(plan,plan.tell-.0001)==0)
  assert(Projectile.travel(plan,plan.tell)==0)
  assert(Projectile.travel(plan,endTime-.0001)<reach and Projectile.travel(plan,endTime)==reach)
  local wall=reach-.001
  local physical={target("equal",reach,plan.width),target("beyond",reach+.001,plan.width),
   target("outside-lane",reach/2,plan.width+.001),target("before-wall",wall-.001,0)}
  local all=Projectile.contacts(origin,direction,0,reach,plan.width,physical,{})
  assert(#all==2 and all[1].target.id=="before-wall" and all[2].target.id=="equal")
  local beforeWall=Projectile.contacts(origin,direction,0,wall,plan.width,physical,{})
  assert(#beforeWall==1 and beforeWall[1].target.id=="before-wall")
  local arriving=target("moving",reach/2+.01,plan.width+.25)
  assert(#Projectile.contacts(origin,direction,0,reach/2,plan.width,{arriving},{})==0)
  arriving.center=target("moving",reach/2+.01,0).center
  assert(#Projectile.contacts(origin,direction,reach/2,reach,plan.width,{arriving},{})==1)
  assert(#Projectile.contacts(origin,direction,reach/2,reach,plan.width,{arriving},{moving=true})==0)
  arriving.center=target("moving",reach/2+.01,plan.width+.25).center
  assert(#Projectile.contacts(origin,direction,reach/2,reach,plan.width,{arriving},{})==0)
  local flight=Projectile.newFlight(plan,origin,direction)
  local function noWall() return nil end
  local function scan()
   return {target("human",.5,0),target("a",1,0),target("a",1,0),
    target("b",2,0),target("c",3,0),target("d",4,0)}
  end
  local hitById={}
  local function damage(candidate)
   if candidate.id=="human" then return false end
   hitById[candidate.id]=(hitById[candidate.id] or 0)+1
   return true
  end
  assert(Projectile.step(flight,plan.tell,true,noWall,scan,damage)==0)
  assert(Projectile.step(flight,endTime,true,noWall,scan,damage)==plan.limit)
  assert(flight.done and flight.hits==plan.limit and hitById.a==1 and not hitById.d)
  assert(Projectile.step(flight,endTime+1,true,noWall,scan,damage)==0)
  flight=Projectile.newFlight(plan,origin,direction)
  local function wallTie() return 1 end
  local function wallTargets() return {target("wall-edge",1,plan.width),target("behind",2,0)} end
  assert(Projectile.step(flight,endTime,true,wallTie,wallTargets,damage)==0)
  assert(flight.done and flight.travelled==1)
  flight=Projectile.newFlight(plan,origin,direction)
  assert(Projectile.step(flight,endTime,false,noWall,scan,damage)==0 and flight.done)
  table.insert(replays,plan.id..":S"..(k-1))
 end
end
assert(#replays==15)
assert(not Projectile.plan("PREMIUM-001",4))
assert(not Projectile.plan("MAGE-071",0/0))
assert(not Projectile.plan("MAGE-071",2.5))
assert(not Projectile.plan("MAGE-071",5))
assert(not Projectile.plan({},0))
local equal=Projectile.contacts(origin,direction,0,5,.20,{target("2",3,0,.35),target("1",3,0,.35)},{})
assert(#equal==2 and equal[1].target.id=="1")
-- Account for the neutral's front surface, not just its root center.
local contact=Projectile.contacts(origin,direction,0,5,.2,{target("body",5.149,0,.15)},{})
assert(#contact==1 and contact[1].distance<5)
print("PRIVATE_MAGE_PROJECTILE_3_IDS_X_5_STAGES_AND_SWEPT_CONTACT_PASS")
