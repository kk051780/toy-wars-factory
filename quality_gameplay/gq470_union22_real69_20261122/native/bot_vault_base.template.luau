-- Native-only API fixtures. This is not Roblox physics/network/Studio evidence.
local now = 100
local os = { clock = function() return now end }
local signalCount = 0
local dispatchAsync=nil
local function signal()
 local callbacks = {}
 return {
  Connect=function(self, fn)
   signalCount += 1
   local entry={fn=fn,connected=true};table.insert(callbacks,entry)
   return {Disconnect=function() entry.connected=false end}
  end,
  Fire=function(self,...)
   for _,entry in ipairs(table.clone(callbacks)) do
    if entry.connected then entry.fn(...) end
   end
  end,
  FireAsync=function(self,...)
   for _,entry in ipairs(table.clone(callbacks))do
    if entry.connected then local args=table.pack(...);dispatchAsync(function()
     if entry.connected then entry.fn(table.unpack(args,1,args.n))end
    end)end
   end
  end,
  DisconnectAll=function(self)
   for _,entry in ipairs(callbacks) do entry.connected=false end
  end,
 }
end
local vectorMethods = {}
local vectorMeta = {}
local Vector3 = {}
function Vector3.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vectorMeta) end
vectorMeta.__index=function(v,key)
 if key=="Magnitude" then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 if key=="Unit" then local m=v.Magnitude;return Vector3.new(v.X/m,v.Y/m,v.Z/m) end
 return vectorMethods[key]
end
vectorMeta.__add=function(a,b) return Vector3.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
vectorMeta.__sub=function(a,b) return Vector3.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
vectorMeta.__mul=function(a,b)
 if type(a)=="number" then return Vector3.new(a*b.X,a*b.Y,a*b.Z) end
 return Vector3.new(a.X*b,a.Y*b,a.Z*b)
end
vectorMeta.__div=function(a,b) return Vector3.new(a.X/b,a.Y/b,a.Z/b) end
function vectorMethods:Dot(other) return self.X*other.X+self.Y*other.Y+self.Z*other.Z end
local CFrame={}
function CFrame.new(a,b,c)
 local p=if type(a)=="number" then Vector3.new(a,b,c) else (a or Vector3.new(0,0,0))
 local look=if type(b)=="table" then (b-p).Unit else Vector3.new(0,0,-1)
 return {Position=p,LookVector=look,RightVector=Vector3.new(-look.Z,0,look.X)}
end
local Color3={fromRGB=function(r,g,b) return {R=r/255,G=g/255,B=b/255} end}
local Enum=setmetatable({}, {__index=function(t,k)
 local value=setmetatable({}, {__index=function(s,v) rawset(s,v,k.."."..v);return rawget(s,v) end})
 rawset(t,k,value);return value
end})
local RaycastParams={new=function() return {} end}
local OverlapParams={new=function() return {} end}
local methods={}
local Instance={}
local allowedNil={Parent=true,Character=true,PrimaryPart=true,SeatPart=true,Part0=true,Part1=true,ToolTip=true}
local instanceMeta={}
instanceMeta.__index=function(self,key)
 if methods[key] then return methods[key] end
 local value=self._props[key]
 if value~=nil or allowedNil[key] then return value end
 for _,child in ipairs(self._children) do if child.Name==key then return child end end
 error("Invalid member "..tostring(key).." of "..self.ClassName.." "..self.Name)
end
instanceMeta.__newindex=function(self,key,value)
 if key=="Parent" then
  local old=self._props.Parent
  if old then
   for i,c in ipairs(old._children) do if c==self then table.remove(old._children,i);break end end
  end
  self._props.Parent=value
  if value then table.insert(value._children,self) end
 else
  self._props[key]=value
  if key=="CFrame" then self._props.Position=value.Position end
 end
end
function Instance.new(class)
 return setmetatable({_props={ClassName=class,Name=class,Activated=signal(),Destroying=signal(),
  CanCollide=false,Anchored=false,Health=100,MaxHealth=100,FloorMaterial=Enum.Material.Concrete,
  Position=Vector3.new(0,0,0),CFrame=CFrame.new(0,0,0),Size=Vector3.new(1,1,1)},_children={},_attributes={}},instanceMeta)
end
function methods:IsA(class)
 return self.ClassName==class or class=="Instance"
  or class=="BasePart" and (self.ClassName=="Part" or self.ClassName=="WedgePart")
end
function methods:GetChildren() return table.clone(self._children) end
function methods:FindFirstChild(name)
 for _,child in ipairs(self._children) do if child.Name==name then return child end end
 return nil
end
function methods:FindFirstChildOfClass(class)
 for _,child in ipairs(self._children) do if child:IsA(class) then return child end end
 return nil
end
function methods:WaitForChild(name) return self:FindFirstChild(name) end
function methods:GetAttribute(name) return self._attributes[name] end
function methods:SetAttribute(name,value) self._attributes[name]=value end
function methods:IsDescendantOf(parent)
 local p=self.Parent
 while p do if p==parent then return true end;p=p.Parent end
 return false
end
function methods:PivotTo(frame)
 local root=self:FindFirstChild("HumanoidRootPart")
 assert(root,"fixture model root missing")
 root.CFrame=frame
end
function methods:Destroy()
 self.Destroying:Fire()
 self.Activated:DisconnectAll()
 for _,child in ipairs(self:GetChildren()) do child:Destroy() end
 self.Parent=nil
end
local geometry={rayCalls=0,boundsCalls=0,wallDistance=nil,noGround=false,groundHeight=0,overlap=false,groundCollidable=true}
local workspace=Instance.new("Workspace")
local ground=Instance.new("Part");ground.Name="FixtureFloor";ground.CanCollide=true;ground.Parent=workspace
workspace.Raycast=function(self,origin,direction,params)
 geometry.rayCalls+=1
 assert(params.RespectCanCollide==true and #params.FilterDescendantsInstances==1,"collision query context")
 if direction.Y<0 then
  if geometry.noGround then return nil end
  ground.CanCollide=geometry.groundCollidable
  return {Instance=ground,Position=Vector3.new(origin.X,geometry.groundHeight,origin.Z),Distance=origin.Y-geometry.groundHeight}
 end
 if geometry.wallDistance then return {Instance=ground,Distance=geometry.wallDistance,Position=origin+direction.Unit*geometry.wallDistance} end
 return nil
end
workspace.GetPartBoundsInBox=function(self,frame,size,params)
 geometry.boundsCalls+=1
 assert(params.RespectCanCollide==true and #params.FilterDescendantsInstances==1,"overlap query context")
 return if geometry.overlap then {ground} else {}
end
local currentPlayers={}
local RunService={IsStudio=function() return true end,IsServer=function() return true end,Heartbeat=signal()}
local Players={GetPlayers=function() return currentPlayers end}
local Debris={AddItem=function() end}
local game={GetService=function(self,name)
 if name=="RunService" then return RunService elseif name=="Players" then return Players elseif name=="Debris" then return Debris end
 error("unhandled service "..name)
end}
local task={delay=function() end,spawn=function() end,wait=function() error("unexpected task wait in Dodge fixture") end}
local script={Parent={WaitForChild=function(self,name) return name end}}
local dependencies={}
local require=function(name)
 assert(dependencies[name],"unhandled dependency "..tostring(name))
 return dependencies[name]
end
local noop=function() end
dependencies.EGGRUMBLE_InvulRuntime={filterDamage=function(h,n) return n end}
dependencies.EGGRUMBLE_FieldItemPickups={weaponDamageMultiplier=function() return 1 end,weaponReachBonus=function() return 0 end}
dependencies.EGGRUMBLE_SkillFX={emit=noop}
dependencies.EGGRUMBLE_ImpactFeedback={attacker=noop,hit=noop,clear=noop}
dependencies.EGGRUMBLE_WeaponSilhouettes={attach=noop,clear=noop}
dependencies.EGGRUMBLE_DivineMantle={cancel=noop}
dependencies.EGGRUMBLE_AttackGeometry={allowed=function() return false end}
dependencies.EGGRUMBLE_StatusTickFence={}

local TEST_APPROACH_OFFSET=@@BOT_APPROACH_OFFSET@@
-- Bounded Native service fixtures for full, byte-identical Host execution.
-- World graph, clocks and signals are fixtures; no engine/network/Studio claim.
local Vector2={new=function(x,y)return {X=x,Y=y}end}
local UDim={new=function(s,o)return {Scale=s,Offset=o}end}
local UDim2={new=function(xs,xo,ys,yo)return {X={Scale=xs,Offset=xo},Y={Scale=ys,Offset=yo}}end,
 fromOffset=function(x,y)return {X={Scale=0,Offset=x},Y={Scale=0,Offset=y}}end,
 fromScale=function(x,y)return {X={Scale=x,Offset=0},Y={Scale=y,Offset=0}}end}
Color3.new=function(r,g,b)return {R=r,G=g,B=b}end
local frameMeta={}
frameMeta.__mul=function(a,b)
 -- Only cosmetic ramp rotation is approximated; no geometry/physics claim.
 return setmetatable({Position=a.Position+b.Position,LookVector=a.LookVector,RightVector=a.RightVector},frameMeta)
end
local baseFrameNew=CFrame.new
CFrame.new=function(...)return setmetatable(baseFrameNew(...),frameMeta)end
CFrame.Angles=function()return CFrame.new(0,0,0)end
local Random={new=function()return {NextInteger=function(_,low,_high)return low end}end}
local time=function()return now end
local warnings={}
local warn=function(...)
 local values={};for _,v in ipairs({...})do table.insert(values,tostring(v))end
 table.insert(warnings,table.concat(values," "))
end

local pending={};local serial=0;local schedulerResumes=0
local function enqueue(at,thread,args)
 serial+=1;table.insert(pending,{at=at,thread=thread,args=args or {},serial=serial})
end
task.delay=function(seconds,fn,...)
 assert(type(seconds)=="number" and seconds>=0,"fixture delay")
 enqueue(now+seconds,coroutine.create(fn),table.pack(...))
end
task.spawn=function(fn,...)
 enqueue(now,if type(fn)=="thread" then fn else coroutine.create(fn),table.pack(...))
end
task.defer=function(fn,...)enqueue(now,coroutine.create(fn),table.pack(...))end
task.wait=function(seconds)return coroutine.yield(seconds or 1/60)end
local function advanceTo(target)
 assert(target>=now,"monotonic fixture clock")
 for _=1,30000 do
  local index=nil
  for i,entry in ipairs(pending)do
   local chosen=index and pending[index] or nil
   if entry.at<=target and (not chosen or entry.at<chosen.at or
    entry.at==chosen.at and entry.serial<chosen.serial)then index=i end
  end
  if not index then now=target;return end
  local entry=table.remove(pending,index);now=entry.at;schedulerResumes+=1
  local ok,delay=coroutine.resume(entry.thread,table.unpack(entry.args,1,entry.args.n or #entry.args))
  if not ok then error("fixture task failed: "..tostring(delay).."\n"..debug.traceback(entry.thread),0)end
  if coroutine.status(entry.thread)~="dead" then
   assert(type(delay)=="number" and delay>0,"fixture task must yield bounded positive delay")
   enqueue(now+delay,entry.thread)
  end
 end
 error("fixture scheduler budget exceeded",0)
end

local phaseWrites={};local arenaLifecycle={}
local baseNew=Instance.new
Instance.new=function(class)
 local item=baseNew(class)
 item._props.Enabled=true;item._props.Visible=true;item._props.WalkSpeed=18
 item._props.Triggered=signal();item._props.Died=signal()
 item._props.CharacterAdded=signal();item._props.CharacterRemoving=signal()
 item._props.ChildAdded=signal();item._props.ChildRemoved=signal()
 return item
end
local baseIsA=methods.IsA
function methods:IsA(class)
 return baseIsA(self,class) or class=="BasePart" and self.ClassName=="SpawnLocation"
end
local baseIndex=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 local old=self._props[key]
 baseIndex(self,key,value)
 if key=="Position" then self._props.CFrame=CFrame.new(value)end
 if key=="Parent" and old~=value then
  if old and old._props and old._props.ChildRemoved then old.ChildRemoved:Fire(self)end
  if value and value._props and value._props.ChildAdded then value.ChildAdded:Fire(self)end
  if self.Name=="TEAM_Arena" or self.Name=="BATTLE_ROYALE_Arena" then
   table.insert(arenaLifecycle,{instance=self,at=now,parent=value,phase=self:GetAttribute("EGGRUMBLE_MatchPhase")})
  end
 end
end
function methods:FindFirstChildWhichIsA(class,recursive)
 for _,child in ipairs(self:GetChildren())do
  if child:IsA(class)then return child end
  if recursive then local found=child:FindFirstChildWhichIsA(class,true);if found then return found end end
 end
 return nil
end
function methods:GetDescendants()
 local result={}
 for _,child in ipairs(self:GetChildren())do
  table.insert(result,child)
  for _,descendant in ipairs(child:GetDescendants())do table.insert(result,descendant)end
 end
 return result
end
function methods:GetClosestPointOnSurface(at)
 assert(self:IsA("BasePart"))
 local p=self.Position;local half=self.Size*.5
 return Vector3.new(math.clamp(at.X,p.X-half.X,p.X+half.X),
  math.clamp(at.Y,p.Y-half.Y,p.Y+half.Y),math.clamp(at.Z,p.Z-half.Z,p.Z+half.Z))
end
function methods:GetState()return if self.Health<=0 then Enum.HumanoidStateType.Dead else Enum.HumanoidStateType.Running end
function methods:TakeDamage(amount)self.Health=math.max(0,self.Health-amount);if self.Health<=0 then self.Died:Fire()end end
local oldAttribute=methods.SetAttribute
function methods:SetAttribute(name,value)
 local changed=self:GetAttribute(name)~=value
 oldAttribute(self,name,value)
 if name=="EGGRUMBLE_MatchPhase" then
  local source,line=debug.info(2,"sl")
  table.insert(phaseWrites,{instance=self,phase=value,at=now,parent=self.Parent,source=source,line=line})
 end
 if changed and self._props.attributeSignals and self._props.attributeSignals[name] then
  self._props.attributeSignals[name]:Fire()
 end
end
function methods:GetAttributeChangedSignal(name)
 if not self._props.attributeSignals then self._props.attributeSignals={}end
 if not self._props.attributeSignals[name]then self._props.attributeSignals[name]=signal()end
 return self._props.attributeSignals[name]
end
workspace.Raycast=function(_self,_from,_direction,params)
 -- Interactions use a clear line of sight. No map collision proof is claimed.
 assert(params.RespectCanCollide==true)
 return nil
end
Players._children={};Players.PlayerAdded=signal();Players.PlayerRemoving=signal()
Players.GetPlayerByUserId=function(_self,userId)
 for _,p in ipairs(currentPlayers)do if p.UserId==userId and p.Parent==Players then return p end end
 return nil
end
local ProximityPromptService={PromptTriggered=signal()}
local baseService=game.GetService
game.GetService=function(self,name)
 if name=="Workspace" then return workspace end
 if name=="ProximityPromptService" then return ProximityPromptService end
 return baseService(self,name)
end

-- Explicit unrelated dependency stubs. They never own Rules/phase/Replay.
-- Capture only the actual session argument crossing the existing module API.
local capturedSessions={};local equips={};local stubCalls={}
local function count(name)stubCalls[name]=(stubCalls[name]or 0)+1 end
dependencies.EGGRUMBLE_CastleGuardianRuntime={attach=function(session)
 table.insert(capturedSessions,session)
 return {refresh=function()count("Guardian.refresh")end,shutdown=function()count("Guardian.shutdown")end}
end}
dependencies.EGGRUMBLE_BotActors={start=function(session)
 count("BotActors.start");session.botActors={}
end}
dependencies.EGGRUMBLE_SwarmCombat={start=function(session)
 count("Swarm.start");session.swarm={kills={}}
end}
dependencies.EGGRUMBLE_SevenRoleCombat={
 roleOrder=function()return {"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}end,
 info=function(role)return {name=role,weapon="fixture weapon",color=Color3.fromRGB(100,140,180)}end,
 equip=function(session,p,role)
  count("Combat.equip");p:SetAttribute("EGGRUMBLE_Role",role)
  table.insert(equips,{session=session,player=p,role=role,character=p.Character})
 end,
 clear=function()count("Combat.clear")end,
}
dependencies.EGGRUMBLE_InvulRuntime={attach=function()count("Invul.attach")end,filterDamage=function(_h,n)return n end}
dependencies.EGGRUMBLE_NaturalRegen={attach=function()count("Regen.attach")end}
dependencies.EGGRUMBLE_FieldItemPickups={}
dependencies.EGGRUMBLE_RaidItemIntake={start=function()count("Raid.start");return 0 end}
dependencies.EGGRUMBLE_NeutralStoneGiant={spawn=function(parent)
 count("Boss.spawn");local m=Instance.new("Model");m.Name="FIXTURE_UNRELATED_BOSS";m.Parent=parent;return m
end}
dependencies.GQ802_StageManifestPolicy={build=function(seed,mode,seats)return {seed=seed,mode=mode,seats=seats}end}
dependencies.GQ802_StageTileBlueprintPolicy={}
dependencies.GQ802_StageTileVisualRenderer={render=function(parent)
 count("Stage.render");local f=Instance.new("Folder");f.Name="FIXTURE_UNRELATED_STAGE";f.Parent=parent;return f
end,clear=function()count("Stage.clear")end}

local player=Instance.new("Player");player.Name="LifecycleHuman";player.UserId=42;player.Parent=Players
currentPlayers={player}
local playerGui=Instance.new("PlayerGui");playerGui.Parent=player
local bag=Instance.new("Backpack");bag.Parent=player
local character=Instance.new("Model");character.Name="LifecycleAvatar";character.Parent=workspace
local humanoid=Instance.new("Humanoid");humanoid.Parent=character
local rootPart=Instance.new("Part");rootPart.Name="HumanoidRootPart";rootPart.Parent=character
character.PrimaryPart=rootPart;player.Character=character

-- Additive fixture adapters only. Complete gameplay sources remain unchanged.
dispatchAsync=function(fn,...) task.spawn(fn,...) end
Players.GetPlayerFromCharacter=function(_,character)
 for _,p in ipairs(currentPlayers)do if p.Parent==Players and p.Character==character then return p end end
 return nil
end
local baseWaitForChild=methods.WaitForChild
function methods:WaitForChild(name,timeout)
 local present=self:FindFirstChild(name)
 if present or timeout==nil then return present end
 -- Explicit bounded fixture polling; tests schedule child arrival independently.
 local deadline=now+timeout
 while now<deadline and self.Parent do
  task.wait(math.min(.05,deadline-now))
  local child=self:FindFirstChild(name)
  if child then return child end
 end
 return nil
end
local resetCalls={}
function methods:LoadCharacter()
 -- Never invent an actual engine character during reset. Tests supply the
 -- character asynchronously and observe this real caller's load request.
 assert(self:IsA("Player"),"LoadCharacter receiver is Player")
 table.insert(resetCalls,{player=self,at=now})
end
local observedEvents={}
local replayObserved={}
local parentWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 parentWrite(self,key,value)
 if key=="Parent" and value and self.Name=="EGGRUMBLE_MatchResult"then
  local owner=value.Parent
  local mode=owner and owner:GetAttribute("EGGRUMBLE_QueuedMode")
  local session=nil
  for i=#capturedSessions,1,-1 do
   if capturedSessions[i].mode==mode and capturedSessions[i].world.Parent then session=capturedSessions[i];break end
  end
  table.insert(observedEvents,{kind="RESULT",at=now,phase=session and session.rules.phase,world=session and session.world})
 end
end
local actualDelay=task.delay
task.delay=function(seconds,fn,...)
 if seconds==10 then
  local session=nil
  for i=#capturedSessions,1,-1 do
   local s=capturedSessions[i]
   if s.rules.phase=="FINISHED" and s.roundReplayScheduled and not replayObserved[s]then session=s;break end
  end
  if session then replayObserved[session]=true end
  table.insert(observedEvents,{kind="REPLAY",at=now,phase=session and session.rules.phase,world=session and session.world})
 end
 return actualDelay(seconds,fn,...)
end

local function assertCheck(condition,message)assert(condition,message)end
local function runCase(name,fn)
 local ok,detail=pcall(fn)
 print("CASE\t"..name.."\t"..(if ok then "PASS"else "FAIL").."\t"..tostring(detail or ""):gsub("\n"," "))
 if not ok then error(detail,0)end
end
local function findPrompt(part,verb)
 assertCheck(part~=nil,"real prompt part exists")
 for _,child in ipairs(part:GetChildren())do
  if child:IsA("ProximityPrompt")and child.ActionText==verb then return child end
 end
 error("missing real prompt "..verb)
end
local function firePrompt(part,verb,actor,reposition)
 actor=actor or player
 local selected=findPrompt(part,verb)
 assertCheck(selected.Enabled,"real prompt enabled")
 if reposition~=false then
  local ar=actor.Character and actor.Character:FindFirstChild("HumanoidRootPart")
  assertCheck(ar~=nil,"actor has root")
  ar.CFrame=CFrame.new(part.Position+Vector3.new(0,0,1))
 end
 ProximityPromptService.PromptTriggered:Fire(selected,actor)
 selected.Triggered:Fire(actor)
 return selected
end
local function getArena(mode)
 local world=workspace:FindFirstChild("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW")
 return world and world:FindFirstChild(mode.."_Arena")or nil
end
local function finishEvidence()
 for _,v in ipairs(observedEvents)do print("TRACE\t"..v.kind.."\t"..v.at.."\t"..tostring(v.phase))end
 for _,warning in ipairs(warnings)do print("WARNING\t"..warning)end
 print("METRIC\tscheduler_resumes\t"..schedulerResumes)
 print("METRIC\tpending_after_cleanup\t"..#pending)
 assertCheck(#warnings==0,"no ignored fixture warnings")
end

-- Reused pure geometry from upstream/router_obb_fixture.luau.
-- Fixture integration only, no gameplay source replacement.
-- Native Luau comparison fixture, NOT a Roblox engine/Studio test.
-- OBB separation and continuous translation use generic geometric SAT.
local V=Vector3
local vm=vectorMeta
function V.new(x,y,z) return setmetatable({X=x,Y=y,Z=z},vm) end
vm.__add=function(a,b) return V.new(a.X+b.X,a.Y+b.Y,a.Z+b.Z) end
vm.__sub=function(a,b) return V.new(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end
vm.__mul=function(a,b) if type(a)=='number' then a,b=b,a end return V.new(a.X*b,a.Y*b,a.Z*b) end
vm.__div=function(a,b) return a*(1/b) end
vm.__unm=function(a) return a*-1 end
vm.__eq=function(a,b) return a.X==b.X and a.Y==b.Y and a.Z==b.Z end
vm.__index=function(v,k)
 if k=='Magnitude' then return math.sqrt(v.X*v.X+v.Y*v.Y+v.Z*v.Z) end
 if k=='Unit' then return v/v.Magnitude end
 if k=='Dot' then return function(a,b)return a.X*b.X+a.Y*b.Y+a.Z*b.Z end end
 if k=='Cross' then return function(a,b)return V.new(a.Y*b.Z-a.Z*b.Y,a.Z*b.X-a.X*b.Z,a.X*b.Y-a.Y*b.X)end end
end
Vector3=V
V.xAxis=V.new(1,0,0);V.yAxis=V.new(0,1,0);V.zAxis=V.new(0,0,1)
local F={}
local fm={}
local function frame(p,x,y,z)return setmetatable({Position=p,axes={x,y,z}},fm)end
function F.new(x,y,z)
 if type(x)=="table" and type(y)=="table" then return F.lookAt(x,y) end
 local p=if type(x)=='table' then x else V.new(x or 0,y or 0,z or 0)
 return frame(p,V.xAxis,V.yAxis,V.zAxis)
end
function F.lookAt(at,target)
 local z=-(target-at).Unit
 local x=V.yAxis:Cross(z).Unit
 local y=z:Cross(x).Unit
 return frame(at,x,y,z)
end
fm.__index=function(cf,k)
 if k=='RightVector' then return cf.axes[1] end
 if k=='UpVector' then return cf.axes[2] end
 if k=='LookVector' then return -cf.axes[3] end
 if k=='PointToWorldSpace' then return function(a,p)return a.Position+a.axes[1]*p.X+a.axes[2]*p.Y+a.axes[3]*p.Z end end
 if k=='VectorToWorldSpace' then return function(a,p)return a.axes[1]*p.X+a.axes[2]*p.Y+a.axes[3]*p.Z end end
 if k=='PointToObjectSpace' then return function(a,p)local d=p-a.Position;return V.new(d:Dot(a.axes[1]),d:Dot(a.axes[2]),d:Dot(a.axes[3]))end end
 if k=='VectorToObjectSpace' then return function(a,p)return V.new(p:Dot(a.axes[1]),p:Dot(a.axes[2]),p:Dot(a.axes[3]))end end
end
fm.__mul=function(a,b)
 if getmetatable(b)==vm then return a:PointToWorldSpace(b)end
 return frame(a:PointToWorldSpace(b.Position),a:VectorToWorldSpace(b.axes[1]),a:VectorToWorldSpace(b.axes[2]),a:VectorToWorldSpace(b.axes[3]))
end
-- Reused existing frame-translation API; preserves all original rotation axes.
fm.__add=function(a,v) return frame(a.Position+v,a.RightVector,a.UpVector,-a.LookVector) end
function F.Angles(x,y,z)
 local cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
 return frame(V.new(0,0,0),V.xAxis,V.new(0,cx,sx),V.new(0,-sx,cx))
  *frame(V.new(0,0,0),V.new(cy,0,-sy),V.yAxis,V.new(sy,0,cy))
  *frame(V.new(0,0,0),V.new(cz,sz,0),V.new(-sz,cz,0),V.zAxis)
end
CFrame=F

local axes={'X','Y','Z'}
local function ancestor(part,parent)
 local node=part
 while node do if node==parent then return true end;node=node.Parent end
 return false
end
local function part(name,p,size,rotation)
 local q={Name=name,Size=size,CFrame=F.new(p)*(rotation or F.new()),Position=p,CanCollide=true,CanQuery=true}
 function q:IsDescendantOf(parent)return ancestor(self,parent)end
 return q
end
local function box(cf,size)return {cf=cf,half={size.X/2,size.Y/2,size.Z/2}}end
local function projection(b,n)
 local radius=0
 for i=1,3 do radius+=b.half[i]*math.abs(n:Dot(b.cf.axes[i]))end
 return radius
end
local function separatingAxes(a,b)
 local out={}
 for _,axis in ipairs(a.cf.axes)do table.insert(out,axis)end
 for _,axis in ipairs(b.cf.axes)do table.insert(out,axis)end
 for _,u in ipairs(a.cf.axes)do for _,v in ipairs(b.cf.axes)do
  local n=u:Cross(v)
  if n.Magnitude>1e-9 then table.insert(out,n.Unit)end
 end end
 return out
end
local function overlaps(a,b)
 local rel=a.cf.Position-b.cf.Position
 for _,n in ipairs(separatingAxes(a,b))do
  if math.abs(rel:Dot(n))>projection(a,n)+projection(b,n)+1e-8 then return false end
 end
 return true
end
local function sweep(a,delta,b)
 local enter,leave=0,1
 local hitNormal=nil
 local rel=a.cf.Position-b.cf.Position
 for _,n in ipairs(separatingAxes(a,b))do
  local radius=projection(a,n)+projection(b,n)
  local offset=rel:Dot(n)
  local rate=delta:Dot(n)
  if math.abs(rate)<1e-10 then
   if math.abs(offset)>radius+1e-8 then return nil end
  else
   local first,last=(-radius-offset)/rate,(radius-offset)/rate
   if first>last then first,last=last,first end
   if first>enter then enter=first;hitNormal=n*(if rate>0 then -1 else 1)end
   leave=math.min(leave,last)
   if enter>leave+1e-9 then return nil end
  end
 end
 if enter<0 or enter>1 then return nil end
 return enter,hitNormal or -delta.Unit
end
local function rayBox(at,delta,p)
 local origin=p.CFrame:PointToObjectSpace(at)
 local d=p.CFrame:VectorToObjectSpace(delta)
 local enter,leave=0,1
 local normal=V.new(0,0,0)
 for i,key in ipairs(axes)do
  local half=p.Size[key]/2
  if math.abs(d[key])<1e-10 then
   if math.abs(origin[key])>half then return nil end
  else
   local first,last=(-half-origin[key])/d[key],(half-origin[key])/d[key]
   if first>last then first,last=last,first end
   if first>enter then enter=first;normal=p.CFrame.axes[i]*(if d[key]>0 then -1 else 1)end
   leave=math.min(leave,last)
   if enter>leave+1e-9 then return nil end
  end
 end
 if enter<0 or enter>1 then return nil end
 return enter,normal
end
local function allowed(p,params)
 if params.RespectCanCollide and not p.CanCollide then return false end
 if not params.RespectCanCollide and not p.CanQuery then return false end
 for _,excluded in ipairs(params.FilterDescendantsInstances or {})do
  if ancestor(p,excluded)then return false end
 end
 return true
end

-- Reuses the existing generic OBB SAT fixture over actual Host-created Parts.
-- No Terrain/mesh/physics or engine contact-position claim is made.
V.zero=V.new(0,0,0)
function F.Inverse(cf)
 local x=V.new(cf.axes[1].X,cf.axes[2].X,cf.axes[3].X)
 local y=V.new(cf.axes[1].Y,cf.axes[2].Y,cf.axes[3].Y)
 local z=V.new(cf.axes[1].Z,cf.axes[2].Z,cf.axes[3].Z)
 local inverse=frame(V.zero,x,y,z)
 return frame(inverse:VectorToWorldSpace(-cf.Position),x,y,z)
end
local oldFrameIndex=fm.__index
fm.__index=function(cf,key)
 if key=="Inverse"then return F.Inverse end
 if key=="ToObjectSpace"then return function(a,b)return F.Inverse(a)*b end end
 return oldFrameIndex(cf,key)
end

local worldParts={}
for _,item in ipairs(workspace:GetDescendants())do
 if item:IsA("BasePart")then
  item.CFrame=F.new(item.Position)
  item._props.CanQuery=true;item._props.CanTouch=true
  table.insert(worldParts,item)
 end
end
local createInstance=Instance.new
Instance.new=function(class)
 local item=createInstance(class)
 if item:IsA("BasePart")then
  -- Roblox Part defaults; prior full-Host fixture used false for this value.
  item._props.CanCollide=true;item._props.CanQuery=true;item._props.CanTouch=true
  table.insert(worldParts,item)
 end
 return item
end
function methods:GetPivot()
 assert(self.PrimaryPart~=nil,"Model pivot requires actual PrimaryPart")
 return self.PrimaryPart.CFrame
end
local pivotCount={}
function methods:PivotTo(cf)
 local old=self:GetPivot()
 local inverse=F.Inverse(old)
 local transformed={}
 for _,item in ipairs(self:GetDescendants())do
  if item:IsA("BasePart")then
   -- PrimaryPart is the exact pivot in this fixture. Reapplying its numerically
   -- approximate inverse would double tiny non-orthogonality on every move.
   table.insert(transformed,{item,if item==self.PrimaryPart then cf else cf*(inverse*item.CFrame)})
  end
 end
 for _,pair in ipairs(transformed)do pair[1].CFrame=pair[2]end
 pivotCount[self]=(pivotCount[self]or 0)+1
end
function methods:GetClosestPointOnSurface(at)
 assert(self:IsA("BasePart"))
 local q=self.CFrame:PointToObjectSpace(at)
 local h=self.Size*.5
 return self.CFrame:PointToWorldSpace(V.new(math.clamp(q.X,-h.X,h.X),
  math.clamp(q.Y,-h.Y,h.Y),math.clamp(q.Z,-h.Z,h.Z)))
end

local queryStats={ray=0,block=0,overlap=0}
local queryHits={}
local queryLast=nil
local boundCache={}
local function halfWorld(cf,size)
 local h=size*.5
 return V.new(math.abs(cf.axes[1].X)*h.X+math.abs(cf.axes[2].X)*h.Y+math.abs(cf.axes[3].X)*h.Z,
  math.abs(cf.axes[1].Y)*h.X+math.abs(cf.axes[2].Y)*h.Y+math.abs(cf.axes[3].Y)*h.Z,
  math.abs(cf.axes[1].Z)*h.X+math.abs(cf.axes[2].Z)*h.Y+math.abs(cf.axes[3].Z)*h.Z)
end
local function partHalf(p)
 local cached=boundCache[p]
 if cached and cached.cf==p.CFrame and cached.size==p.Size then return cached.half end
 local h=halfWorld(p.CFrame,p.Size)
 boundCache[p]={cf=p.CFrame,size=p.Size,half=h}
 return h
end
local function broad(p,lo,hi)
 local at=p.Position;local h=partHalf(p)
 return at.X+h.X>=lo.X-1e-8 and at.X-h.X<=hi.X+1e-8
  and at.Y+h.Y>=lo.Y-1e-8 and at.Y-h.Y<=hi.Y+1e-8
  and at.Z+h.Z>=lo.Z-1e-8 and at.Z-h.Z<=hi.Z+1e-8
end
local function liveAllowed(p,params)
 return p.Parent~=nil and p:IsDescendantOf(workspace)and allowed(p,params)
end
local function note(kind,from,to,hit)
 queryLast={kind=kind,from=from,to=to,hit=hit}
 if hit then queryHits[hit.Instance.Name]=(queryHits[hit.Instance.Name]or 0)+1 end
end
function workspace:Raycast(at,d,params)
 queryStats.ray+=1
 assert(params.RespectCanCollide==true,"authoritative collidable query")
 if d.Magnitude<=1e-12 then return nil end
 local target=at+d
 local lo=V.new(math.min(at.X,target.X),math.min(at.Y,target.Y),math.min(at.Z,target.Z))
 local hi=V.new(math.max(at.X,target.X),math.max(at.Y,target.Y),math.max(at.Z,target.Z))
 local best,hit=nil,nil
 for _,p in ipairs(worldParts)do if liveAllowed(p,params)and broad(p,lo,hi)then
  local t,n=rayBox(at,d,p)
  if t and(not best or t<best)then best=t;hit={Instance=p,Position=at+d*t,Normal=n,Distance=d.Magnitude*t}end
 end end
 note("ray",at,target,hit)
 return hit
end
function workspace:GetPartBoundsInBox(cf,size,params)
 queryStats.overlap+=1
 local h=halfWorld(cf,size);local lo=cf.Position-h;local hi=cf.Position+h
 local result={}
 for _,p in ipairs(worldParts)do
  if liveAllowed(p,params)and broad(p,lo,hi)and overlaps(box(cf,size),box(p.CFrame,p.Size))then
   table.insert(result,p)
   if params.MaxParts and params.MaxParts>0 and #result>=params.MaxParts then break end
  end
 end
 if #result>0 then queryHits["overlap:"..result[1].Name]=(queryHits["overlap:"..result[1].Name]or 0)+1 end
 return result
end
function workspace:Blockcast(cf,size,d,params)
 queryStats.block+=1
 assert(d.Magnitude>0,"nonzero source shapecast")
 local moving=box(cf,size);local h=halfWorld(cf,size);local target=cf.Position+d
 local lo=V.new(math.min(cf.Position.X,target.X)-h.X,math.min(cf.Position.Y,target.Y)-h.Y,math.min(cf.Position.Z,target.Z)-h.Z)
 local hi=V.new(math.max(cf.Position.X,target.X)+h.X,math.max(cf.Position.Y,target.Y)+h.Y,math.max(cf.Position.Z,target.Z)+h.Z)
 local best,hit=nil,nil
 for _,p in ipairs(worldParts)do if liveAllowed(p,params)and broad(p,lo,hi)then
  local fixed=box(p.CFrame,p.Size)
  -- Retains upstream Blockcast initial-overlap exclusion and SAT contact model.
  if not overlaps(moving,fixed)then
   local t,n=sweep(moving,d,fixed)
   if t and(not best or t<best)then
    best=t
    local point=cf.Position+d*t
    for i,u in ipairs(cf.axes)do
     local dot=n:Dot(u)
     point-=u*moving.half[i]*(if dot>1e-10 then 1 elseif dot< -1e-10 then -1 else 0)
    end
    hit={Instance=p,Position=point,Normal=n,Distance=d.Magnitude*t}
   end
  end
 end end
 note("block",cf.Position,target,hit)
 return hit
end

-- Explicit waypoint provider only. This is not Roblox navmesh computation.
-- Other bots are stationary at a declared Router boundary to isolate one route.
local routeSession=nil
local focusId=nil
local routeMoves={}
local pathCalls={}
local actionEvents={}
local ignoredRouterCalls=0
local freezeFocusedMovement=false
local clearEvents={}
local function planarDistance(a,b)
 return V.new(a.X-b.X,0,a.Z-b.Z).Magnitude
end
local function closestCastle(pos)
 local found,at,distance=nil,nil,math.huge
 for id,loc in pairs(routeSession.castleLocations)do
  local d=planarDistance(pos,loc)
  if d<distance then found=id;at=loc;distance=d end
 end
 return found,at
end
local function suppliedWaypoints(from,to)
 assert(routeSession and focusId,"waypoint request belongs to focused scenario")
 local fromId,fromCastle=closestCastle(from)
 local toId,toCastle=closestCastle(to)
 local points={{Position=from}}
 local function add(pos)
  if planarDistance(points[#points].Position,pos)>.01 then table.insert(points,{Position=pos})end
 end
 local inFrom=math.abs(from.X-fromCastle.X)<=38
  and from.Z>=fromCastle.Z-62 and from.Z<=fromCastle.Z+38
 if fromId==toId and inFrom then
  add(to)
 else
  if inFrom then
   if from.Z>fromCastle.Z-31 then
    -- Align inside the open nine-stud gate before crossing its side corners.
    -- The small opposite-side offset gives the source's 4.2-stud waypoint
    -- radius room to finish this turn before the next segment crosses a wall.
    local offset=if from.X<fromCastle.X then 2 else -2
    add(V.new(fromCastle.X+offset,from.Y,math.max(from.Z,fromCastle.Z-7)))
    add(fromCastle+V.new(0,1.5,-26))
   end
   add(fromCastle+V.new(0,-3,-62))
  end
  -- Same-column BR castles are 112 studs apart. Their front points cannot be
  -- joined through the first castle's core/vault; use the 50-stud side lane.
  if math.abs(toCastle.Z-fromCastle.Z)>10 then
   local sideX=fromCastle.X+50
   add(V.new(sideX,3,fromCastle.Z-62))
   add(V.new(sideX,3,toCastle.Z-62))
  end
  -- This test-controlled approach-point phase does not replace the requested
  -- source goal: every path still terminates at the exact ComputeAsync `to`.
  add(toCastle+V.new(0,-3,-TEST_APPROACH_OFFSET))
  add(toCastle+V.new(0,1.5,-26))
  add(to)
 end
 return points
end
local PathfindingService={}
function PathfindingService:CreatePath(config)
 assert(config.AgentRadius==2 and config.AgentHeight==5 and config.AgentCanJump==false,"actual Router path config")
 local path={Status=Enum.PathStatus.Success,Blocked=signal(),destroyed=false}
 function path:ComputeAsync(from,to)
  self.points=suppliedWaypoints(from,to)
  table.insert(pathCalls,{at=now,from=from,to=to,points=self.points})
 end
 function path:GetWaypoints()return self.points end
 function path:Destroy()self.destroyed=true;self.Blocked:DisconnectAll()end
 return path
end
local originalGetService=game.GetService
game.GetService=function(self,name)
 if name=="PathfindingService"then return PathfindingService end
 return originalGetService(self,name)
end
local emptySwarmStart=dependencies.EGGRUMBLE_SwarmCombat.start
dependencies.EGGRUMBLE_SwarmCombat.start=function(session)
 emptySwarmStart(session)
 session.swarm.damageFromBot=function()return false end
end


dependencies.EGGRUMBLE_CastleMatchRules=(function()
@@EGGRUMBLE_FULL_SOURCE_CastleMatchRules@@
end)()

dependencies.EGGRUMBLE_CastleSiegeGuardianPolicy=(function()
@@EGGRUMBLE_FULL_SOURCE_CastleSiegeGuardianPolicy@@
end)()

dependencies.EGGRUMBLE_CastleSiegeBridge=(function()
@@EGGRUMBLE_FULL_SOURCE_CastleSiegeBridge@@
end)()

dependencies.EGGRUMBLE_InteractionGuard=(function()
@@EGGRUMBLE_FULL_SOURCE_InteractionGuard@@
end)()

dependencies.EGGRUMBLE_BasicMobilityPolicy=(function()
@@EGGRUMBLE_FULL_SOURCE_BasicMobilityPolicy@@
end)()

dependencies.EGGRUMBLE_RoundReplay=(function()
@@EGGRUMBLE_FULL_SOURCE_RoundReplay@@
end)()

dependencies.EGGRUMBLE_ScoreBalance=(function()
@@EGGRUMBLE_FULL_SOURCE_ScoreBalance@@
end)()

dependencies.EGGRUMBLE_MatchResultService=(function()
@@EGGRUMBLE_FULL_SOURCE_MatchResultService@@
end)()

dependencies.EGGRUMBLE_BossSessionFence=(function()
@@EGGRUMBLE_FULL_SOURCE_BossSessionFence@@
end)()

dependencies.EGGRUMBLE_DualModeNeutralBudget=(function()
@@EGGRUMBLE_FULL_SOURCE_DualModeNeutralBudget@@
end)()

dependencies.EGGRUMBLE_InvulnerabilityPolicy=(function()
@@EGGRUMBLE_FULL_SOURCE_InvulnerabilityPolicy@@
end)()

dependencies.EGGRUMBLE_InvulCounterNeutral=(function()
@@EGGRUMBLE_FULL_SOURCE_InvulCounterNeutral@@
end)()

dependencies.EGGRUMBLE_InvulRuntime=(function()
@@EGGRUMBLE_FULL_SOURCE_InvulRuntime@@
end)()

dependencies.EGGRUMBLE_BotPathRouter=(function()
@@EGGRUMBLE_FULL_SOURCE_BotPathRouter@@
end)()

dependencies.EGGRUMBLE_BotActors=(function()
@@EGGRUMBLE_FULL_SOURCE_BotActors@@
end)()
-- Boundary observation; selected Router and Rules functions execute unchanged.
local actualNavigate=dependencies.EGGRUMBLE_BotPathRouter.navigate
dependencies.EGGRUMBLE_BotPathRouter.navigate=function(id,model,goal,dt,actors)
 if not focusId or id~=routeSession.mode..":"..focusId then
  ignoredRouterCalls+=1
  return planarDistance(model:GetPivot().Position,goal)
 end
 local before=model:GetPivot().Position
 local result=if freezeFocusedMovement then planarDistance(before,goal)else actualNavigate(id,model,goal,dt,actors)
 local after=model:GetPivot().Position
 table.insert(routeMoves,{at=now,before=before,after=after,goal=goal,dt=dt,
  held=routeSession.rules.castles[focusId].heldEggs,queryLast=queryLast})
 return result
end
local actualClear=dependencies.EGGRUMBLE_BotPathRouter.clear
dependencies.EGGRUMBLE_BotPathRouter.clear=function(id)
 table.insert(clearEvents,{id=id,at=now})
 return actualClear(id)
end
local Rules=dependencies.EGGRUMBLE_CastleMatchRules
local originalTake=Rules.takeEggs
Rules.takeEggs=function(state,id,n,from)
 local result=table.pack(originalTake(state,id,n,from))
 if routeSession and state==routeSession.rules and id==focusId then
  table.insert(actionEvents,{kind="STEAL",at=now,id=id,from=from,count=n,
   position=routeSession.botActors[id]:GetPivot().Position,
   target=routeSession.castleLocations[from]+V.new(0,3,6),
   actualPart=routeSession.castleModels[from].model:FindFirstChild("EggVault")})
 end
 return table.unpack(result,1,result.n)
end
local originalDeposit=Rules.depositEggs
Rules.depositEggs=function(state,id,n)
 local result=table.pack(originalDeposit(state,id,n))
 if routeSession and state==routeSession.rules and id==focusId then
  table.insert(actionEvents,{kind="DEPOSIT",at=now,id=id,count=n,
   position=routeSession.botActors[id]:GetPivot().Position,
   target=routeSession.castleLocations[id]+V.new(-16,3,-18),
   actualPart=routeSession.castleModels[id].model:FindFirstChild("OwnEggDeposit")})
 end
 return table.unpack(result,1,result.n)
end


do local _=(function()
@@EGGRUMBLE_FULL_SOURCE_Host@@
end)()end
local TEST_MODE="@@BOT_TEST_MODE@@"
local TEST_SLOW=@@BOT_TEST_SLOW@@
@@BOT_VAULT_CASES@@