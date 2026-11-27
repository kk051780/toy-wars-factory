local vectors = {}
local function v(x, y, z) return setmetatable({X=x,Y=y,Z=z},vectors) end
vectors.__index = function(a,key)
 local length = math.sqrt(a.X^2+a.Y^2+a.Z^2)
 if key=="Magnitude" then return length end
 if key=="Unit" then return v(a.X/length,a.Y/length,a.Z/length) end
end
vectors.__add = function(a,b) return v(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
vectors.__mul = function(a,n) return v(a.X*n,a.Y*n,a.Z*n) end
local Vector3 = {new=v}
local frame={}
frame.__mul=function(a,b)return setmetatable({at=a.at,target=a.target,roll=b.roll},frame)end
local CFrame = {
 new=function(p)return setmetatable({at=p},frame)end,
 lookAt=function(p,to)return setmetatable({at=p,target=to},frame)end,
 Angles=function(x,y,z)return setmetatable({roll=z},frame)end,
}
local function tokens()
 return setmetatable({},{__index=function(_,name)return name end})
end
local Enum={Material=tokens(),PartType=tokens(),EasingStyle=tokens(),EasingDirection=tokens()}
local function new(...)return {...}end
local NumberRange,NumberSequence,NumberSequenceKeypoint,ColorSequence,Vector2,TweenInfo =
 {new=new},{new=new},{new=new},{new=new},{new=new},{new=new}
local Color3={fromRGB=function(r,g,b)return r*65536+g*256+b end}
local sourceTemplateEnvironment=getfenv()

local function environment()
 local parts,delays={},{}
 local services={}
 services.Debris={AddItem=function(_,part,ttl)part.debris=ttl end}
 services.TweenService={Create=function(_,part,info,goal)
  assert(part.goal==nil)
  part.goal=goal
  part.tween=info
  return {Play=function()part.started=true end}
 end}
 local env=setmetatable({
  game={GetService=function(_,name)return assert(services[name])end},
  Instance={new=function(class)
   if class=="ParticleEmitter" then
    return {Emit=function(self,count)self.Parent.sparks=count;self.Parent.sparkColor=self.Color[1]end}
   end
   assert(class=="Part")
   local value={Destroy=function(self)self.Parent=nil end}
   table.insert(parts,value)
   return value
  end},
  task={delay=function(ttl,callback)table.insert(delays,{ttl=ttl,run=callback})end},
  Vector3=Vector3,CFrame=CFrame,Enum=Enum,Color3=Color3,NumberRange=NumberRange,
  NumberSequence=NumberSequence,NumberSequenceKeypoint=NumberSequenceKeypoint,
  ColorSequence=ColorSequence,Vector2=Vector2,TweenInfo=TweenInfo,
 },{__index=sourceTemplateEnvironment})
 return env,parts,delays
end

local function moduleBody(raw)
 local env,parts,delays=environment()
 local fn=assert(loadstring(raw))
 setfenv(fn,env)
 return fn(),parts,delays
end

local function arena(name)return {Name=name,Parent=true}end
local function compare(a,b)
 assert(a.Name==b.Name and a.Color==b.Color and a.sparks==b.sparks and a.sparkColor==b.sparkColor)
 assert(a.debris==b.debris and a.tween[1]==b.tween[1] and a.started and b.started)
 for _,p in {a,b} do
  assert(p.Anchored and p.CanCollide==false and p.CanQuery==false and p.CanTouch==false and p.CastShadow==false)
 end
end

local function run(original,selected)
 local baseline,oldParts,oldDelays=moduleBody(original)
 local chosen,newParts,newDelays=moduleBody(selected)
 local roles={"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}
 local center=v(1,0,0)
 for index,role in roles do
  for _,slot in {"A","B","C"} do
   local parent=arena("TEAM_Arena")
   local radius=if index%3==0 then 1 elseif index%3==1 then 8 else 15
   local forward=if index%2==0 then v(0,1,0) else v(0,0,-1)
   local origin=v(0,0,0)
   local oldIndex,newIndex=#oldParts,#newParts
   local count=if slot=="C" then 6 else 5
   baseline.emit(parent,role,slot,origin,forward,center,radius)
   chosen.emit(parent,role,slot,origin,forward,center,radius)
   assert(#oldParts-oldIndex==count and #newParts-newIndex==count and baseline.active()==count and chosen.active()==count)
   local a,b=oldParts[oldIndex+1],newParts[newIndex+1]
   compare(a,b)
   assert(a.Shape=="Ball" and a.Material=="Neon" and a.goal.CFrame==nil)
   assert(b.Shape=="Block" and b.Material=="SmoothPlastic" and b.Transparency==.55)
   assert(b.CFrame.at.Y==1.75 and b.CFrame.target.Z==-3 and b.goal.CFrame.at.Z==-2)
   local scale=if slot=="C" then 1.4 elseif slot=="B" then 1.1 else .85
   assert(b.goal.Size.X==.24 and b.goal.Size.Y==2.8 and b.goal.Size.Z==math.clamp(radius,2,12)*.85*scale)
   for n=2,count do
    local x,y=oldParts[oldIndex+n],newParts[newIndex+n]
    compare(x,y)
    assert(x.Shape==y.Shape and x.Material==y.Material and x.Transparency==y.Transparency)
    assert(x.goal.Size.X==y.goal.Size.X and x.goal.Size.Y==y.goal.Size.Y and x.goal.Size.Z==y.goal.Size.Z)
   end
   for n=1,count do
    local x,y=oldDelays[oldIndex+n],newDelays[newIndex+n]
    assert(x.ttl==y.ttl)
    x.run();y.run()
   end
   assert(baseline.active()==0 and chosen.active()==0)
   print("PASS",role,slot,count)
  end
 end
 for _,source in {original,selected} do
  local module,parts,delays=moduleBody(source)
  local t,r=arena("TEAM_Arena"),arena("BATTLE_ROYALE_Arena")
  local function emit(parent,role)
   module.emit(parent,role or "MAGE","C",center,v(0,0,-1),center,8)
  end
  emit(t,"UNKNOWN")
  emit(arena("OUTSIDE"))
  emit({Name="TEAM_Arena"})
  assert(module.active()==0 and #parts==0)
  for _=1,13 do emit(t) end
  assert(module.active()==60 and #parts==60)
  for _=1,4 do emit(r) end
  assert(module.active()==72 and #parts==72)
  for _,scheduled in delays do scheduled.run() end
  assert(module.active()==0)
 end
 print("PASS","CAP_AND_CLEANUP",72)
end
