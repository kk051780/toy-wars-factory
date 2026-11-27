
local now=0
local parts, expiration, animations = {}, {}, {}
local world={Parent=true}
local vector={}
vector.__index=function(v,key)
 if key=="Magnitude" then return math.sqrt(v.X^2+v.Y^2+v.Z^2) end
 if key=="Unit" then return vector.new(v.X/v.Magnitude,v.Y/v.Magnitude,v.Z/v.Magnitude) end
end
vector.__add=function(a,b) return vector.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
function vector.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vector) end
local frame={}
frame.__mul=function(a,b) return a end
local function cf(at,look) return setmetatable({Position=at,LookVector=look},frame) end
local function clearDue()
 for part,expires in pairs(expiration) do
  if expires<=now then part.Parent=nil;expiration[part]=nil end
 end
end
local function loadBody(raw)
 now=0
 table.clear(parts);table.clear(expiration);table.clear(animations)
 local services={
  Debris={AddItem=function(_,part,ttl) assert(ttl==.53);expiration[part]=now+ttl end},
  TweenService={Create=function(_,part,ttl,goal)
   assert(part.Parent==world)
   local jobs=animations[part] or {}
   animations[part]=jobs
   local target=if goal.Transparency then "Fade" else "Geometry"
   assert(not jobs[target])
   jobs[target]={ttl=ttl,goal=goal,count=0}
   return {Play=function() jobs[target].count+=1 end}
  end},
 }
 local enum=setmetatable({}, {__index=function(_,kind)
  return setmetatable({}, {__index=function(_,key) return kind.."."..key end})
 end})
 local env=setmetatable({
  game={GetService=function(_,key) return assert(services[key]) end},
  Instance={new=function(class)
   local part={ClassName=class};table.insert(parts,part);return part
  end},
  Enum=enum, os={clock=function() return now end}, Vector3=vector,
  Color3={fromRGB=function(r,g,b) return {r,g,b} end},
  TweenInfo={new=function(ttl,style,direction,repeatCount,reverses,delay)
   return {ttl=ttl,style=style,direction=direction,repeatCount=repeatCount,reverses=reverses,delay=delay}
  end},
  CFrame={lookAt=function(at,to)
   assert(to.X==0 and to.Z==-1)
   return cf(at,to)
  end,new=function(x,y,z) return cf(vector.new(x,y,z)) end,Angles=function() return cf() end},
 },{__index=getfenv()})
 local chunk=assert(loadstring(raw))
 setfenv(chunk,env)
 return chunk()
end
local function countLive()
 local count=0
 for _,part in ipairs(parts) do
  if part.Parent then
   count+=1
   assert(part.ClassName=="WedgePart" and part.Material=="Material.SmoothPlastic"
    and not part.CanCollide and not part.CanQuery and not part.CanTouch and not part.CastShadow)
  end
 end
 return count
end

local function timedBurst(raw)
 local victim={PrimaryPart={CFrame=cf(vector.new(0,0,0),vector.new(0,1,0))}}
 local feedback=loadBody(raw)
 now=.99
 for _=1,6 do assert(feedback.ko(world,victim,"MAGE")) end
 assert(not feedback.ko(world,victim,"MAGE") and countLive()==12)
 for _,part in ipairs(parts) do
  local jobs=assert(animations[part])
  local geometry,fade=jobs.Geometry,jobs.Fade
  assert(part.Transparency==.12 and fade.count==1 and geometry.count==1)
  assert(geometry.goal.CFrame and geometry.goal.Size and not geometry.goal.Transparency
   and geometry.ttl.ttl==.23 and geometry.ttl.style=="EasingStyle.Quad" and not geometry.ttl.delay)
  assert(fade.goal.Transparency==1 and not fade.goal.CFrame and not fade.goal.Size
   and fade.ttl.ttl==.18 and fade.ttl.style=="EasingStyle.Linear" and fade.ttl.delay==.31
   and fade.ttl.repeatCount==0 and fade.ttl.reverses==false)
  assert(expiration[part]>=now+fade.ttl.delay+fade.ttl.ttl)
 end
 print("KO_GEOMETRY_AND_DELAYED_FADE",countLive())
 now=1.31;clearDue()
 assert(not feedback.ko(world,victim,"MAGE") and countLive()==12)
 now=1.51;clearDue()
 assert(not feedback.ko(world,victim,"MAGE") and countLive()==12)
 parts[1].Parent=nil
 assert(not feedback.ko(world,victim,"MAGE") and countLive()==11)
 parts[2].Parent=nil
 assert(feedback.ko(world,victim,"MAGE") and countLive()==12)
 print("KO_CROSS_SECOND_PARTIAL_PAIR_SUPPRESSED",countLive())
 now=1.54;clearDue()
 assert(countLive()==2)
 for _=1,5 do assert(feedback.ko(world,victim,"MAGE")) end
 assert(not feedback.ko(world,victim,"MAGE") and countLive()==12)
 print("KO_RECLAIM_AND_REFILL",countLive())
 world.Parent=nil
 assert(not feedback.ko(world,victim,"MAGE"))
 now=2.1;clearDue()
 assert(countLive()==0)
 print("KO_TEARDOWN_NO_RESIDUE",countLive())
end
