local fixturePrint=print
local function print(...)
 local first=(...)
 if type(first)=="string" and first:find("CASE\tGROWTH_ACCEPTANCE_",1,true)==1 then fixturePrint(...) end
end
-- Native-only API fixtures. This is not Roblox physics/network/Studio evidence.
local now = 100
local os = { clock = function() return now end }
local signalCount = 0
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
CFrame.Angles=function()return CFrame.new(0,0,0)end;frameMeta.__index={PointToObjectSpace=function(frame,point) local delta=point-frame.Position; return Vector3.new(delta:Dot(frame.RightVector),delta.Y,-delta:Dot(frame.LookVector)) end}
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

-- Additional native API fixtures for full real Combat / Item modules.
-- No selected Source or game function is modified.
script.Parent.FindFirstChild=function(_self,name)
 return if dependencies[name] then name else nil
end
Players.GetPlayerFromCharacter=function(_self,character)
 for _,p in ipairs(currentPlayers) do
  if p.Parent==Players and p.Character==character then return p end
 end
 return nil
end
local baseInstance=Instance.new
Instance.new=function(class)
 local value=baseInstance(class)
 value._props.CanQuery=true;value._props.CanTouch=true
 if value:IsA('BasePart') then value._props.CanCollide=true end
 return value
end
local ordinarySwarmStart=dependencies.EGGRUMBLE_SwarmCombat.start
dependencies.EGGRUMBLE_SwarmCombat.start=function(session,...)
 ordinarySwarmStart(session,...)
 session.swarm.damageFromPlayer=function()return 0 end
end
local ordinaryGuardianAttach=dependencies.EGGRUMBLE_CastleGuardianRuntime.attach
dependencies.EGGRUMBLE_CastleGuardianRuntime.attach=function(session,...)
 local state=ordinaryGuardianAttach(session,...)
 state.damageFromPlayer=function()return 0 end
 return state
end
dependencies.EGGRUMBLE_NeutralStoneGiant.spawn=function(parent)
 local model=Instance.new('Model');model.Name='FIXTURE_UNRELATED_BOSS';model.Parent=parent
 return {model=model}
end
workspace.Raycast=function(_self,origin,direction,params)
 assert(params.RespectCanCollide==true)
 if direction.X==0 and direction.Z==0 and direction.Y==-17 then
  local candidate=nil
  for _,item in ipairs(workspace:GetDescendants()) do
   if item.Name=='TacticalBattlefield' and item:IsA('BasePart')
    and math.abs(origin.X-item.Position.X)<item.Size.X*.5
    and math.abs(origin.Z-item.Position.Z)<item.Size.Z*.5 then candidate=item end
  end
  if candidate then
   local y=candidate.Position.Y+candidate.Size.Y*.5
   return {Instance=candidate,Position=Vector3.new(origin.X,y,origin.Z),Distance=origin.Y-y}
  end
 end
 return nil
end

-- Two connected human avatars exist before full Host bootstrap.
humanoid.WalkSpeed=20
local second=Instance.new('Player');second.Name='SpeedPeer';second.UserId=43;second.Parent=Players
local secondGui=Instance.new('PlayerGui');secondGui.Parent=second
local secondBag=Instance.new('Backpack');secondBag.Parent=second
local secondCharacter=Instance.new('Model');secondCharacter.Name='SpeedPeerAvatar';secondCharacter.Parent=workspace
local secondHumanoid=Instance.new('Humanoid');secondHumanoid.WalkSpeed=12;secondHumanoid.Parent=secondCharacter
local secondRoot=Instance.new('Part');secondRoot.Name='HumanoidRootPart';secondRoot.Parent=secondCharacter
secondCharacter.PrimaryPart=secondRoot;second.Character=secondCharacter
currentPlayers={player,second}

local loadingModule='fixture'
local mobilityRequires={}
local realFixtureRequire=require
require=function(name)
 local result=realFixtureRequire(name)
 if name=='EGGRUMBLE_BasicMobilityPolicy' then
  table.insert(mobilityRequires,{module=loadingModule,value=result})
 end
 return result
end

-- Delay selected already-registered speed expiry callbacks until after the next
-- real READY/countdown. This models late scheduling; caller/closure lines and
-- durations are recorded, while the unchanged callback runs exactly once later.
local parkSpeedExpiry=false
local parkedCallbacks={}
local sourceDelay=task.delay
task.delay=function(seconds,fn,...)
 if parkSpeedExpiry and (math.abs(seconds-2.1)<1e-6 or math.abs(seconds-1.2)<1e-6 or seconds==5) then
  local source,line=debug.info(2,'sl')
  table.insert(parkedCallbacks,{seconds=seconds,fn=fn,args=table.pack(...),registered=now,source=source,line=line})
  return
 end
 return sourceDelay(seconds,fn,...)
end
local speedWrites={}
local previousSpeedWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 previousSpeedWrite(self,key,value)
 if key=='WalkSpeed' and self:IsA('Humanoid') then
  local source,line=debug.info(2,'sl')
  table.insert(speedWrites,{humanoid=self,value=value,at=now,source=source,line=line})
 end
end

-- Native engine boundaries for the bounded full Host + Guardian + Swarm path.
-- No game policy, membership, HP gate, spawn policy or winner function is stubbed here.
local fullSourceRanges={}
local function sourceLabel(line)
 for name,range in pairs(fullSourceRanges) do
  if line>=range.first and line<=range.last then return name end
 end
 return 'fixture'
end

local oldVectorNew=Vector3.new
Vector3.new=function(x,y,z)return oldVectorNew(x or 0,y or 0,z or 0)end
vectorMeta.__unm=function(v)return Vector3.new(-v.X,-v.Y,-v.Z)end
CFrame.lookAt=function(at,towards)return CFrame.new(at,towards)end;CFrame.identity=CFrame.new(0,0,0);RunService.Heartbeat.Wait=function() return task.wait(1/60) end;game.privateTestStorage=Instance.new('Folder')
local TweenInfo={new=function(seconds,style,direction)return {Time=seconds,Style=style,Direction=direction}end}
local TweenService={Create=function(_self,object,_info,properties)
 -- Cosmetic tween properties are committed immediately; no rendering proof.
 return {Play=function()for key,value in pairs(properties)do object[key]=value end end}
end}
local beforeCombinedService=game.GetService
game.GetService=function(self,name)
 if name=='TweenService' then return TweenService elseif name=='ServerStorage' then return game.privateTestStorage end
 return beforeCombinedService(self,name)
end
local beforeCombinedInstance=Instance.new
Instance.new=function(class)
 local object=beforeCombinedInstance(class)
 object._props.HealthChanged=signal()
 return object
end
humanoid._props.HealthChanged=signal();secondHumanoid._props.HealthChanged=signal()
local healthWrites={}
local oldCombinedWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 local before=self._props[key]
 oldCombinedWrite(self,key,value)
 if key=='Health' and before~=value and self:IsA('Humanoid') then
  local _source,line=debug.info(2,'sl')
  table.insert(healthWrites,{humanoid=self,before=before,after=value,at=now,line=line})
  if self._props.HealthChanged then self._props.HealthChanged:Fire(value)end
 end
end
function methods:GetPivot()
 local root=self.PrimaryPart or self:FindFirstChild('HumanoidRootPart')
 assert(root,'fixture GetPivot requires actual model root')
 return root.CFrame
end
function methods:PivotTo(frame)
 local root=self.PrimaryPart or self:FindFirstChild('HumanoidRootPart')
 local previous=if root then root.Position else self.WorldPivot.Position
 local delta=frame.Position-previous
 for _,part in ipairs(self:GetDescendants())do
  if part:IsA('BasePart')then part.Position=part.Position+delta end
 end
 if root then root.CFrame=frame else self.WorldPivot=frame end
end
local oldCombinedDestroy=methods.Destroy
function methods:Destroy()
 oldCombinedDestroy(self)
 for _,value in pairs(self._props)do
  if type(value)=='table' and type(rawget(value,'DisconnectAll'))=='function' then value:DisconnectAll()end
 end
end
Debris.AddItem=function(_self,object,seconds)
 task.delay(seconds,function()if object.Parent then object:Destroy()end end)
end
dependencies.EGGRUMBLE_ImpactFeedback.ko=function()end -- unrelated cosmetic feedback

-- Axis-aligned current-Part queries only. Cosmetic CFrame rotations inherited
-- from the original Host fixture are approximate; no terrain/rigid-body claim.
local function queryExcluded(part,params)
 for _,object in ipairs(params.FilterDescendantsInstances or {})do
  if part==object or part:IsDescendantOf(object)then return true end
 end
 return false
end
local function queryEligible(part,params)
 if not part:IsA('BasePart') or queryExcluded(part,params)then return false end
 return if params.RespectCanCollide then part.CanCollide==true else part.CanQuery~=false
end
local rayQueries=0;local overlapQueries=0;local queryTrace={}
workspace.Raycast=function(_self,origin,delta,params)
 rayQueries+=1
 local callerLine=debug.info(2,'l')
 local best=nil;local nearest=math.huge;local normal=nil
 for _,part in ipairs(workspace:GetDescendants())do
  if queryEligible(part,params)then
   local lo=part.Position-part.Size*.5;local hi=part.Position+part.Size*.5
   local entry=0;local exit=1;local hitNormal=Vector3.new();local accepted=true
   for _,axis in ipairs({'X','Y','Z'})do
    local start=origin[axis];local direction=delta[axis]
    if math.abs(direction)<1e-10 then
     if start<lo[axis] or start>hi[axis]then accepted=false;break end
    else
     local a=(lo[axis]-start)/direction;local b=(hi[axis]-start)/direction
     local sign=-1
     if a>b then a,b=b,a;sign=1 end
     if a>entry then
      entry=a
      hitNormal=if axis=='X' then Vector3.new(sign,0,0)
       elseif axis=='Y' then Vector3.new(0,sign,0)else Vector3.new(0,0,sign)
     end
     exit=math.min(exit,b)
     if entry>exit then accepted=false;break end
    end
   end
   if accepted and entry>=0 and entry<=1 and entry<nearest then
    nearest=entry;best=part;normal=hitNormal
   end
  end
 end
 table.insert(queryTrace,{line=callerLine,source=sourceLabel(callerLine),origin=origin,delta=delta,hit=best})
 if not best then return nil end
 return {Instance=best,Position=origin+delta*nearest,Distance=delta.Magnitude*nearest,Normal=normal}
end
workspace.GetPartBoundsInBox=function(_self,frame,size,params)
 overlapQueries+=1
 local found={};local center=frame.Position;local half=size*.5
 for _,part in ipairs(workspace:GetDescendants())do
  if queryEligible(part,params)then
   local distance=part.Position-center;local extent=part.Size*.5+half
   if math.abs(distance.X)<extent.X and math.abs(distance.Y)<extent.Y and math.abs(distance.Z)<extent.Z then
    table.insert(found,part)
   end
  end
 end
 return found
end

local moduleRequires={}
local beforeCombinedRequire=require
require=function(name)
 local result=beforeCombinedRequire(name)
 table.insert(moduleRequires,{caller=loadingModule,name=name,value=result})
 return result
end

-- Only observe the original engine registration boundary. Every function is
-- forwarded unchanged; the ordinary fixture scheduler still runs its body.
local currentSwarmRegistration=nil
local swarmTasks={}
local previousSpawn=task.spawn
task.spawn=function(fn,...)
 local thread=if type(fn)=='thread' then fn else coroutine.create(fn)
 if currentSwarmRegistration and type(fn)=='function'then
  local line=debug.info(fn,'l')
  if sourceLabel(line)=='SwarmCombat'then
   table.insert(swarmTasks,{session=currentSwarmRegistration,thread=thread,line=line,at=now})
  end
 end
 previousSpawn(thread,...)
 return thread
end
local publishedWrites={}
local beforeCombinedAttribute=methods.SetAttribute
function methods:SetAttribute(name,value)
 if (self==player or self==second)and
  (name=='EGGRUMBLE_NeutralKOs'or name=='EGGRUMBLE_Combo'or name=='EGGRUMBLE_BestCombo'
   or name:match('^EGGRUMBLE_Musou'))then
  local _source,line=debug.info(2,'sl')
  table.insert(publishedWrites,{player=self,name=name,value=value,at=now,line=line})
 end
 return beforeCombinedAttribute(self,name,value)
end

local guardianAttachments={};local guardianCalls={};local guardianShutdowns={}
local swarmAttachments={}
local function installApiObservers()
 local guardianModule=dependencies.EGGRUMBLE_CastleGuardianRuntime
 local originalAttach=guardianModule.attach
 guardianModule.attach=function(session,roles)
  local controller=originalAttach(session,roles)
  table.insert(capturedSessions,session)
  table.insert(guardianAttachments,{session=session,controller=controller,module=guardianModule})
  local originalHit=controller.damageFromPlayer
  controller.damageFromPlayer=function(p,at,radius,damage,shape,attackRoot,attackCharacter)
   local result=originalHit(p,at,radius,damage,shape,attackRoot,attackCharacter)
   table.insert(guardianCalls,{session=session,controller=controller,player=p,root=attackRoot,
    character=attackCharacter,shape=shape,result=result,at=now})
   return result
  end
  local originalShutdown=controller.shutdown
  controller.shutdown=function(...)
   table.insert(guardianShutdowns,{session=session,at=now})
   return originalShutdown(...)
  end
  return controller
 end
 local swarmModule=dependencies.EGGRUMBLE_SwarmCombat
 local originalStart=swarmModule.start
 swarmModule.start=function(session)
  local previous=currentSwarmRegistration;currentSwarmRegistration=session
  local api=originalStart(session)
  currentSwarmRegistration=previous
  table.insert(swarmAttachments,{session=session,api=api,module=swarmModule})
  return api
 end
end

-- Additional engine-boundary model; frozen original fixtures remain unchanged.
-- Only explicitly selected signals defer. This is NOT global Roblox emulation.
-- Source: create.roblox.com/docs/scripting/events/deferred
-- Explicit Connection:Disconnect cancels queued invocations.
-- Destroy's implicit disconnect stops future events but retains queued ones.
local deferredSignals={}
local deferredQueue={}
local deferredTrace={}
local deferredSerial=0
local function deferredEvent(kind,detail)
 table.insert(deferredTrace,{kind=kind,detail=detail})
end
signal=function()
 local callbacks={}
 local object={}
 local meta={deferred=false,callbacks=callbacks,label='UNNAMED'}
 deferredSignals[object]=meta
 object.Connect=function(self,fn)
  signalCount+=1
  local entry={fn=fn,connected=true,cancelGeneration=0}
  table.insert(callbacks,entry)
  return {Disconnect=function()
   -- Explicit disconnect also cancels callbacks queued before implicit destroy.
   entry.connected=false
   entry.cancelGeneration+=1
   deferredEvent('EXPLICIT_DISCONNECT',meta.label)
  end}
 end
 object.Fire=function(self,...)
  local args=table.pack(...)
  for _,entry in ipairs(table.clone(callbacks)) do
   if entry.connected then
    if meta.deferred then
     deferredSerial+=1
     table.insert(deferredQueue,{entry=entry,generation=entry.cancelGeneration,
      args=args,label=meta.label,serial=deferredSerial})
     deferredEvent('QUEUED',meta.label)
    else
     entry.fn(table.unpack(args,1,args.n))
    end
   end
  end
 end
 object.DisconnectAll=function(self)
  -- This fixture-only method is used by the unchanged Instance Destroy boundary.
  for _,entry in ipairs(callbacks) do entry.connected=false end
  deferredEvent('IMPLICIT_DISCONNECT',meta.label)
 end
 return object
end
local function modelDeferred(object,label)
 local meta=deferredSignals[object]
 assert(meta,'signal must originate from additive model')
 meta.deferred=true;meta.label=label
 return object
end
local function drainDeferred()
 local delivered,cancelled=0,0
 for _=1,2000 do
  if #deferredQueue==0 then
   return delivered,cancelled
  end
  local item=table.remove(deferredQueue,1)
  if item.entry.cancelGeneration==item.generation then
   delivered+=1
   deferredEvent('DELIVERED',item.label)
   item.entry.fn(table.unpack(item.args,1,item.args.n))
  else
   cancelled+=1
   deferredEvent('CANCELLED',item.label)
  end
 end
 error('bounded deferred model queue exceeded',0)
end

local beforeDeferredInstance=Instance.new
Instance.new=function(class)
 local object=beforeDeferredInstance(class)
 object._props.AncestryChanged=signal()
 return object
end
local beforeDeferredWrite=instanceMeta.__newindex
instanceMeta.__newindex=function(self,key,value)
 local previous=self._props[key]
 beforeDeferredWrite(self,key,value)
 if key=='Parent' and previous~=value then
  local own=self._props.AncestryChanged
  if own then own:Fire(self,value)end
  -- Descendant notifications share the original changed ancestor and new parent.
  for _,descendant in ipairs(self:GetDescendants())do
   local related=descendant._props.AncestryChanged
   if related then related:Fire(self,value)end
  end
 end
end
local beforeDeferredDestroy=methods.Destroy
function methods:Destroy()
 beforeDeferredDestroy(self)
 -- Existing generic fixture auto-disconnects top-level signals on Destroy.
 -- Attribute-specific signals are nested; model the same implicit disconnect.
 for _,event in pairs(self._props.attributeSignals or {})do
  if deferredSignals[event] then event:DisconnectAll()end
 end
end

-- S1A acceptance ENGINE PREPEND ONLY.
-- Append after the immutable original fixtures and before every production body.
-- This adds scheduling controls and observations, never a B publisher or getter.
local growthEngine={
 worldSerial=0,worldPrefixes={},writes={},
 watched={
  EGGRUMBLE_BattleStage=true,EGGRUMBLE_BattleXP=true,EGGRUMBLE_GrowthActive=true,
  EGGRUMBLE_NeutralKOs=true,EGGRUMBLE_BattleLevel=true,EGGRUMBLE_Combo=true,
  EGGRUMBLE_BestCombo=true,
 },
}
function growthEngine.deferWorld(world)
 local prefix=growthEngine.worldPrefixes[world]
 if prefix then return prefix end
 growthEngine.worldSerial+=1
 prefix='GROWTH_WORLD_'..growthEngine.worldSerial..'|'
 growthEngine.worldPrefixes[world]=prefix
 modelDeferred(world:GetAttributeChangedSignal('EGGRUMBLE_MatchPhase'),prefix..'PHASE')
 modelDeferred(world.Destroying,prefix..'DESTROYING')
 modelDeferred(world.AncestryChanged,prefix..'ANCESTRY')
 local horde=world:FindFirstChild('NeutralHorde')
 if horde then modelDeferred(horde.Destroying,prefix..'HORDE_DESTROYING')end
 return prefix
end
function growthEngine.holdWorld(world)
 local prefix=growthEngine.worldPrefixes[world]
 assert(prefix,'mark real world Deferred before parking deliveries')
 local held={}
 for i=#deferredQueue,1,-1 do
  local item=deferredQueue[i]
  if item.label:sub(1,#prefix)==prefix then
   table.insert(held,1,table.remove(deferredQueue,i))
   deferredEvent('PARKED',item.label)
  end
 end
 return held
end
function growthEngine.extendHeld(destination,source)
 for _,item in ipairs(source)do table.insert(destination,item)end
end
function growthEngine.requeue(held)
 -- Preserve exact registered closure, event arguments and cancellation generation.
 -- This intentionally adversarial delay is not a claim of ordinary engine timing.
 for _,item in ipairs(held)do
  table.insert(deferredQueue,item)
  deferredEvent('REQUEUED',item.label)
 end
end
function growthEngine.writeCount(playerRef)
 local count=0
 for _,row in ipairs(growthEngine.writes)do
  if row.player==playerRef then count+=1 end
 end
 return count
end
function growthEngine.snapshot(playerRef)
 local result={}
 for key in pairs(growthEngine.watched)do result[key]=playerRef:GetAttribute(key)end
 return result
end
local beforeGrowthAcceptanceAttribute=methods.SetAttribute
function methods:SetAttribute(name,value)
 if self:IsA('Player') and growthEngine.watched[name] then
  local line=debug.info(2,'l')
  table.insert(growthEngine.writes,{
   player=self,userId=self.UserId,name=name,value=value,
   before=self:GetAttribute(name),at=now,line=line,source=sourceLabel(line),
  })
 end
 return beforeGrowthAcceptanceAttribute(self,name,value)
end

-- Observe actual functions registered through the engine Connect boundary.
-- Invocations always forward to the exact production closure with original args.
-- Cancellation alone is deliberately not accepted as stale-dispatch coverage.
growthEngine.callbackDispatches={}
local beforeGrowthObservedSignal=signal
signal=function()
 local object=beforeGrowthObservedSignal()
 local originalConnect=object.Connect
 object.Connect=function(self,fn)
  local connection=originalConnect(self,fn)
  local meta=deferredSignals[object]
  local entry=meta.callbacks[#meta.callbacks]
  local line=debug.info(fn,'l')
  entry.productionSource=sourceLabel(line)
  entry.productionLine=line
  entry.productionCallback=fn
  entry.actualInvocations=0
  entry.fn=function(...)
   entry.actualInvocations+=1
   table.insert(growthEngine.callbackDispatches,{
    entry=entry,callback=fn,source=entry.productionSource,line=line,
    label=meta.label,args=table.pack(...),at=now,
   })
   return fn(...)
  end
  return connection
 end
 return object
end
-- The frozen fixture creates this service signal before product loading.
-- It has no product subscribers yet. Recreate its engine boundary so optional
-- Deferred delivery also covers actual Host and actual Swarm PlayerRemoving.
Players.PlayerRemoving=signal()
function growthEngine.holdSignal(object,source)
 local meta=deferredSignals[object]
 assert(meta,'selected signal must use the observed boundary')
 local held={}
 for i=#deferredQueue,1,-1 do
  local item=deferredQueue[i]
  if item.label==meta.label and (source==nil or item.entry.productionSource==source)then
   table.insert(held,1,table.remove(deferredQueue,i))
   deferredEvent('PARKED',item.label)
  end
 end
 return held
end
function growthEngine.swarmWitness(held,wantedLabel)
 local result={}
 local seen={}
 for _,item in ipairs(held)do
  local entry=item.entry
  if entry.productionSource=='SwarmCombat'and not seen[entry]
   and (wantedLabel==nil or item.label==wantedLabel)then
   seen[entry]=true
   table.insert(result,{entry=entry,before=entry.actualInvocations,
    label=item.label,line=entry.productionLine,callback=entry.productionCallback})
  end
 end
 assert(#result>0,'MISSING_ACTUAL_REGISTERED_SWARM_CLOSURE_WITNESS')
 return result
end
function growthEngine.requireSwarmDispatch(witness,label)
 local delivered=0
 for _,row in ipairs(witness)do
  local count=row.entry.actualInvocations-row.before
  if count>0 then
   delivered+=count
   print('DISPATCH_WITNESS\t'..label..'\tSwarmCombat\t'..row.line..'\t'..row.label..'\t'..count)
  end
 end
 assert(delivered>0,'CANCELLED_ONLY_IS_NOT_STALE_SWARM_DISPATCH_COVERAGE:'..label)
 return delivered
end

-- Additional Native fixture capability for Guardian block casts.
-- This fixture already approximates every BasePart as an axis-aligned box.
do
    local originalFrame=CFrame.new
    local function translated(frame,delta)
        local nextFrame=table.clone(frame)
        nextFrame.Position=frame.Position+delta
        return setmetatable(nextFrame,getmetatable(frame))
    end
    CFrame.new=function(...)
        local frame=originalFrame(...)
        local original=getmetatable(frame)
        if original and original.__add then return frame end
        local extended=if original then table.clone(original) else {}
        extended.__add=translated
        return setmetatable(frame,extended)
    end
    local axes={"X","Y","Z"}
    local normals={X=Vector3.new(1,0,0),Y=Vector3.new(0,1,0),Z=Vector3.new(0,0,1)}
    workspace.Blockcast=function(_,frame,size,delta,params)
        assert(params.RespectCanCollide==true and delta.Magnitude>0,"Guardian sweep contract")
        local center=frame.Position
        local closest,normal,distance=nil,nil,math.huge
        for _,part in workspace:GetDescendants() do
            if not queryEligible(part,params) then continue end
            local half=(part.Size+size)*.5
            local rel=center-part.Position
            if math.abs(rel.X)<half.X and math.abs(rel.Y)<half.Y and math.abs(rel.Z)<half.Z then continue end
            local first,last=0,1
            local hitNormal,crosses=nil,true
            for _,axis in axes do
                local offset,extent,velocity=rel[axis],half[axis],delta[axis]
                if math.abs(velocity)<1e-10 then
                    if math.abs(offset)>=extent then crosses=false;break end
                else
                    local a,b=(-extent-offset)/velocity,(extent-offset)/velocity
                    local near,far=math.min(a,b),math.max(a,b)
                    if near>=first then
                        first=near
                        hitNormal=normals[axis]*(if velocity>0 then -1 else 1)
                    end
                    last=math.min(last,far)
                    if first>last then crosses=false;break end
                end
            end
            if crosses and hitNormal and first<distance then
                closest,normal,distance=part,hitNormal,first
            end
        end
        if closest then
            return {Instance=closest,Normal=normal,Position=center+delta*distance,Distance=delta.Magnitude*distance}
        end
        return nil
    end
end


loadingModule='BasicMobilityPolicy'
-- RANGE:BasicMobilityPolicy
dependencies.EGGRUMBLE_BasicMobilityPolicy=(function()
-- SOURCE:BasicMobilityPolicy

end)()

loadingModule='CombatBalance'
-- RANGE:CombatBalance
dependencies.EGGRUMBLE_CombatBalance=(function()
-- SOURCE:CombatBalance

end)()

loadingModule='AttackGeometry'
-- RANGE:AttackGeometry
dependencies.EGGRUMBLE_AttackGeometry=(function()
-- SOURCE:AttackGeometry

end)()

loadingModule='StatusTickFence'
-- RANGE:StatusTickFence
dependencies.EGGRUMBLE_StatusTickFence=(function()
-- SOURCE:StatusTickFence

end)()

loadingModule='CastleMatchRules'
-- RANGE:CastleMatchRules
dependencies.EGGRUMBLE_CastleMatchRules=(function()
-- SOURCE:CastleMatchRules

end)()

loadingModule='CastleSiegeGuardianPolicy'
-- RANGE:CastleSiegeGuardianPolicy
dependencies.EGGRUMBLE_CastleSiegeGuardianPolicy=(function()
-- SOURCE:CastleSiegeGuardianPolicy

end)()

loadingModule='CastleSiegeBridge'
-- RANGE:CastleSiegeBridge
dependencies.EGGRUMBLE_CastleSiegeBridge=(function()
-- SOURCE:CastleSiegeBridge

end)()

loadingModule='InteractionGuard'
-- RANGE:InteractionGuard
dependencies.EGGRUMBLE_InteractionGuard=(function()
-- SOURCE:InteractionGuard

end)()

loadingModule='RoundReplay'
-- RANGE:RoundReplay
dependencies.EGGRUMBLE_RoundReplay=(function()
-- SOURCE:RoundReplay

end)()

loadingModule='ScoreBalance'
-- RANGE:ScoreBalance
dependencies.EGGRUMBLE_ScoreBalance=(function()
-- SOURCE:ScoreBalance

end)()

loadingModule='MatchResultService'
-- RANGE:MatchResultService
dependencies.EGGRUMBLE_MatchResultService=(function()
-- SOURCE:MatchResultService

end)()

loadingModule='BossSessionFence'
-- RANGE:BossSessionFence
dependencies.EGGRUMBLE_BossSessionFence=(function()
-- SOURCE:BossSessionFence

end)()

loadingModule='DualModeNeutralBudget'
-- RANGE:DualModeNeutralBudget
dependencies.EGGRUMBLE_DualModeNeutralBudget=(function()
-- SOURCE:DualModeNeutralBudget

end)()

loadingModule='InvulnerabilityPolicy'
-- RANGE:InvulnerabilityPolicy
dependencies.EGGRUMBLE_InvulnerabilityPolicy=(function()
-- SOURCE:InvulnerabilityPolicy

end)()

loadingModule='InvulCounterNeutral'
-- RANGE:InvulCounterNeutral
dependencies.EGGRUMBLE_InvulCounterNeutral=(function()
-- SOURCE:InvulCounterNeutral

end)()

loadingModule='InvulRuntime'
-- RANGE:InvulRuntime
dependencies.EGGRUMBLE_InvulRuntime=(function()
-- SOURCE:InvulRuntime

end)()

loadingModule='NeutralFinisherPolicy'
-- RANGE:NeutralFinisherPolicy
dependencies.EGGRUMBLE_NeutralFinisherPolicy=(function()
-- SOURCE:NeutralFinisherPolicy

end)()

loadingModule='MusouFeverPolicy'
-- RANGE:MusouFeverPolicy
dependencies.EGGRUMBLE_MusouFeverPolicy=(function()
-- SOURCE:MusouFeverPolicy

end)()

loadingModule='CurseConversionPolicy'
-- RANGE:CurseConversionPolicy
dependencies.EGGRUMBLE_CurseConversionPolicy=(function()
-- SOURCE:CurseConversionPolicy

end)()

loadingModule='NeutralMeleePolicy'
-- RANGE:NeutralMeleePolicy
dependencies.EGGRUMBLE_NeutralMeleePolicy=(function()
-- SOURCE:NeutralMeleePolicy

end)()

loadingModule='NeutralSpawnPacing'
-- RANGE:NeutralSpawnPacing
dependencies.EGGRUMBLE_NeutralSpawnPacing=(function()
-- SOURCE:NeutralSpawnPacing

end)()

loadingModule='NeutralEncounterFairness'
-- RANGE:NeutralEncounterFairness
dependencies.EGGRUMBLE_NeutralEncounterFairness=(function()
-- SOURCE:NeutralEncounterFairness

end)()

loadingModule='FieldItemPickups'
-- RANGE:FieldItemPickups
dependencies.EGGRUMBLE_FieldItemPickups=(function()
-- SOURCE:FieldItemPickups

end)()

loadingModule='RaidItemIntake'
-- RANGE:RaidItemIntake
dependencies.EGGRUMBLE_RaidItemIntake=(function()
-- SOURCE:RaidItemIntake

end)()

loadingModule='CastleGuardianRuntime'
-- RANGE:CastleGuardianRuntime
dependencies.EGGRUMBLE_CastleGuardianRuntime=(function()
-- SOURCE:CastleGuardianRuntime

end)()

loadingModule='SwarmCombat'
-- RANGE:SwarmCombat
dependencies.EGGRUMBLE_SwarmCombat=(function()
-- SOURCE:SwarmCombat

end)()

loadingModule='SevenRoleCombat'
-- RANGE:SevenRoleCombat
dependencies.EGGRUMBLE_SevenRoleCombat=(function()
-- SOURCE:SevenRoleCombat

end)()

installApiObservers()

loadingModule='Host'
-- RANGE:Host
do local _=(function()
-- SOURCE:Host

end)() end
local function check(value,message)assert(value,message)end
local function equal(value,wanted,message)
 assert(type(value)=='number'and math.abs(value-wanted)<1e-6,
  message..' actual='..tostring(value)..' expected='..tostring(wanted))
end
local function pass(name,detail)print('CASE\t'..name..'\tPASS\t'..detail)end
local scenes=workspace:FindFirstChild('EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW')
local function trigger(actor,part,verb)
 check(part~=nil,'actual prompt part '..verb)
 local selected=nil
 for _,child in ipairs(part:GetChildren())do
  if child:IsA('ProximityPrompt')and child.ActionText==verb then selected=child end
 end
 check(selected and selected.Enabled,'actual enabled prompt '..verb)
 actor.Character:FindFirstChild('HumanoidRootPart').CFrame=CFrame.new(part.Position+Vector3.new(0,0,1))
 ProximityPromptService.PromptTriggered:Fire(selected,actor)
 selected.Triggered:Fire(actor)
end
local function activate(actor,slot)
 local selected=nil
 for _,container in ipairs({actor:FindFirstChildOfClass('Backpack'),actor.Character})do
  for _,item in ipairs(container:GetChildren())do
   local id=item:GetAttribute('EGGRUMBLE_InternalToolId')
   if item:IsA('Tool')and type(id)=='string'and id:match('^EGGRUMBLE_SKILL_'..slot..'_')then
    check(not selected,'one actual role skill');selected=item
   end
  end
 end
 check(selected~=nil,'actual equip skill '..slot)
 selected.Parent=actor.Character
 selected.Activated:Fire()
end
local function outsideField(session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local away=floor.Position+Vector3.new(floor.Size.X+2000,20,floor.Size.Z+2000)
 rootPart.CFrame=CFrame.new(away)
 secondRoot.CFrame=CFrame.new(away+Vector3.new(100,0,0))
end
local function sharedRequires()
 local expected={
  {'CastleGuardianRuntime','EGGRUMBLE_InvulRuntime'},
  {'SwarmCombat','EGGRUMBLE_InvulRuntime'},
  {'SevenRoleCombat','EGGRUMBLE_InvulRuntime'},
  {'Host','EGGRUMBLE_InvulRuntime'},
  {'CastleGuardianRuntime','EGGRUMBLE_AttackGeometry'},
  {'SwarmCombat','EGGRUMBLE_AttackGeometry'},
  {'SevenRoleCombat','EGGRUMBLE_AttackGeometry'},
  {'Host','EGGRUMBLE_CastleGuardianRuntime'},
  {'Host','EGGRUMBLE_SwarmCombat'},
  {'Host','EGGRUMBLE_SevenRoleCombat'},
  {'Host','EGGRUMBLE_RoundReplay'},
 }
 for _,pair in ipairs(expected)do
  local found=false
  for _,entry in ipairs(moduleRequires)do
   if entry.caller==pair[1]and entry.name==pair[2]then
    check(entry.value==dependencies[pair[2]],'same required module instance '..pair[1]..'/'..pair[2]);found=true
   end
  end
  check(found,'actual require edge '..pair[1]..'/'..pair[2])
  print('TRACE\tREQUIRE\t'..pair[1]..'\t'..pair[2]..'\tSHARED')
 end
 for _,entry in ipairs(mobilityRequires)do
  check(entry.value==dependencies.EGGRUMBLE_BasicMobilityPolicy,'same pure mobility singleton')
 end
 check(stubCalls['Swarm.start']==nil and stubCalls['Invul.attach']==nil
  and stubCalls['Guardian.refresh']==nil,'actual modules replaced preliminary unrelated stubs before Host')
end
local function ready(label)
 local count=#capturedSessions
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(second,scenes:FindFirstChild('ROLE_WARRIOR'),'職業選択')
 trigger(player,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 trigger(second,scenes:FindFirstChild('TEAM_PORTAL'),'参加する')
 local entered=now
 advanceTo(entered+11.99);equal(#capturedSessions,count,'actual READY countdown not shortened')
 advanceTo(entered+12.01);equal(#capturedSessions,count+1,'one actual new Host session')
 local session=capturedSessions[#capturedSessions]
 check(session.rules.phase=='ACTIVE'and session.mode=='TEAM','actual active TEAM')
 check(session.isCurrentHuman(player)and session.isCurrentHuman(second),'both actual Host current humans')
 check(session.rules.castles['42'].team=='RED'and session.rules.castles['43'].team=='BLUE','actual opponents')
 check(session.guardians==guardianAttachments[#guardianAttachments].controller,'Host owns returned actual Guardian API')
 check(session.swarm==swarmAttachments[#swarmAttachments].api,'Host owns returned actual Swarm API')
 check(session.world:FindFirstChild('NeutralHorde')~=nil,'real Swarm created current Horde folder')
 check(session.fieldItemCount==9 and session.itemIntakeStatus=='READY','real Item require integration preserved')
 equal(humanoid.WalkSpeed,20,'actual baseline first human')
 equal(secondHumanoid.WalkSpeed,12,'actual baseline second human')
 check(#warnings==0,'no suppressed optional dependency error')
 outsideField(session)
 pass(label,'actual prompts and 12-second READY; actual Guardian/Swarm attach; two human membership')
 return session
end
local function guardianHit(session,label)
 local siege=session.castleSiegeStates['43']
 local castle=session.rules.castles['43']
 local door=session.castleModels['43'].door
 for _=1,10 do
  advanceTo(now+3)
  trigger(player,door,'攻城攻撃')
  outsideField(session)
 end
 equal(siege.gateHP,0,'real gate cleared through five bounded prompts')
 equal(castle.hp,700,'real core reached original Guardian threshold through five further prompts')
 local guardian=nil
 for _,model in ipairs(session.world:GetChildren())do
  if model:GetAttribute('EGGRUMBLE_GuardianOwner')=='43' then
   check(not guardian,'one first-threshold Guardian');guardian=model
  end
 end
 check(guardian~=nil,'actual Guardian runtime spawned from real siege threshold')
 check(guardian:GetAttribute('EGGRUMBLE_GuardianRole')=='WARRIOR','actual owner role selected Guardian')
 local gh=guardian:FindFirstChildOfClass('Humanoid')
 local target=guardian.PrimaryPart.Position
 equal(gh.Health,110,'actual Guardian starting HP')
 -- Aim through the actual open SiegeGate (CanCollide=false), centered at x+0.
 -- A straight x+8 approach is correctly blocked by CastleFrontRight.
 local opening=Vector3.new(door.Position.X,target.Y,door.Position.Z)
 rootPart.CFrame=CFrame.new(target-(target-opening).Unit*25,target)
 local calls=#guardianCalls
 activate(player,'A')
 if gh.Health~=80 then
  print('DEBUG_GUARDIAN',#guardianCalls-calls,player:GetAttribute('EGGRUMBLE_Role'),player:GetAttribute('EGGRUMBLE_SkillCastSignature'),humanoid.Health)
  for i=math.max(1,#queryTrace-3),#queryTrace do
   local q=queryTrace[i]
   print('DEBUG_RAY',q.source,q.line,q.hit and q.hit.Name or 'CLEAR',q.origin.X,q.origin.Y,q.origin.Z,q.delta.X,q.delta.Y,q.delta.Z)
  end
 end
 equal(gh.Health,80,'GUARDIAN_INCOMING_HIT_MISSING')
 check(#guardianCalls==calls+1,'one actual Combat -> session.guardians call')
 local call=guardianCalls[#guardianCalls]
 check(call.session==session and call.controller==session.guardians and call.player==player,
  'actual Host session Guardian receives correct player')
 check(call.root==rootPart and call.character==character and call.shape=='CRYSTAL'and call.result==1,
  'actual new API root/character/shape forwarded with real hit result')
 print('TRACE\tGUARDIAN_HIT\t'..label..'\t110\t80\tCRYSTAL\tCURRENT_ROOT_CHARACTER')
 outsideField(session)
 pass(label,'10 real siege prompts -> actual Guardian spawn -> actual MAGE Tool A -> 30 HP incoming damage')
 return guardian
end
local function spawnCurrentNeutral(session)
 local floor=session.world:FindFirstChild('TacticalBattlefield')
 local at=floor.Position+Vector3.new(180,floor.Size.Y*.5+3,80)
 rootPart.CFrame=CFrame.new(at)
 local horde=session.world:FindFirstChild('NeutralHorde')
 local neutral=nil
 for _=1,6 do
  advanceTo(now+.2)
  for _,model in ipairs(horde:GetChildren())do
   local h=model:FindFirstChildOfClass('Humanoid')
   if h and h.Health>0 then neutral=model;break end
  end
  if neutral then break end
 end
 check(neutral~=nil,'actual Swarm planner and spawn clearance created a live neutral')
 check(neutral:GetAttribute('EGGRUMBLE_Neutral')==true,'real original neutral identity')
 check(neutral.Parent==horde and horde.Parent==session.world,'actual neutral belongs to this Host world')
 return neutral
end
local function clearNeutralApproach(neutral,target)
 -- Keep the original z-21 approach first, then try three fixed alternatives.
 -- Combat delegates this neutral hit to Swarm, whose LOS starts at root+Y1
 -- and ends at neutral root+Y1, excluding only this avatar and that neutral.
 local offsets={
  Vector3.new(0,1,-21),Vector3.new(0,1,21),
  Vector3.new(-21,1,0),Vector3.new(21,1,0),
 }
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={character,neutral}
 params.RespectCanCollide=true
 for index,offset in ipairs(offsets)do
  local at=target+offset
  local origin=at+Vector3.new(0,1,0)
  local delta=(target+Vector3.new(0,1,0))-origin
  if workspace:Raycast(origin,delta,params)==nil then
   print('TRACE\tSWARM_KO_APPROACH\t'..index)
   return CFrame.new(at,target)
  end
 end
 error('NO_CLEAR_SWARM_LOS_APPROACH',0)
end

local function neutralKO(session,label)
 local neutral=spawnCurrentNeutral(session)
 local target=neutral.PrimaryPart.Position
 local before=session.swarm.getTotal()
 rootPart.CFrame=clearNeutralApproach(neutral,target)
 activate(player,'B')
 local after=session.swarm.getTotal()
 check(after>before,'actual MAGE Tool B caused original Humanoid Died -> Swarm KO')
 equal(player:GetAttribute('EGGRUMBLE_NeutralKOs'),session.swarm.kills['42'],'published score equals current actual ledger')
 check(player:GetAttribute('EGGRUMBLE_NeutralKOs')>0,'actual current human received its KO')
 print('TRACE\tSWARM_KO\t'..label..'\t'..before..'\t'..after..'\tCURRENT_MEMBER')
 outsideField(session)
 advanceTo(now+.5)
 pass(label,'actual SpawnPacing/Fairness/clearance/Swarm spawn; actual Tool B -> Died -> current human KO')
 return after
end
local function parkOldSwarm(session)
 local selected={}
 for _,record in ipairs(swarmTasks)do
  if record.session==session then
   check(coroutine.status(record.thread)=='suspended','real Swarm coroutine running before park')
   selected[record.thread]=record
  end
 end
 local held={}
 for i=#pending,1,-1 do
  local entry=pending[i];local record=selected[entry.thread]
  if record then
   table.insert(held,{entry=table.remove(pending,i),record=record})
   selected[entry.thread]=nil
  end
 end
 check(next(selected)==nil,'each selected real Swarm coroutine found in engine queue')
 equal(#held,2,'exact original Swarm spawn and movement coroutines parked')
 return held
end
local function finishAndClose(session,oldHorde)
 advanceTo(session.deadlineLease.start+900.01)
 check(session.rules.phase=='FINISHED'and session.rules.winner~=nil,'actual deadline finished Rules')
 check(session.roundReplayScheduled and session.resultsDelivered,'actual Replay and Result scheduled')
 local finishAt=nil
 for _,row in ipairs(phaseWrites)do
  if row.instance==session.world and row.phase=='FINISHED'then finishAt=finishAt or row.at end
 end
 check(finishAt~=nil,'actual Host finish phase publication')
 advanceTo(finishAt+10.1)
 check(session.world.Parent==nil and oldHorde.Parent==nil,'actual Replay closeRound destroyed old world and Horde')
 check(session.neutralBudgetEpoch==nil,'Host retired old neutral epoch')
 equal(session.neutralBudget:snapshot().total,0,'old tickets released without leak')
 check(not session.isCurrentHuman(player)and not session.isCurrentHuman(second),'old Host membership retired')
 check(player:GetAttribute('EGGRUMBLE_QueuedMode')==nil and player:GetAttribute('EGGRUMBLE_Role')==nil,'actual lobby reset')
 equal(player:GetAttribute('EGGRUMBLE_NeutralKOs'),0,'actual Replay reset neutral score')
 equal(humanoid.WalkSpeed,20,'actual Replay baseline reset')
 check(#guardianShutdowns>=1 and guardianShutdowns[#guardianShutdowns].session==session,
  'actual Host called its real Guardian shutdown')
 pass('FINISH_AND_CLOSE','actual 900-second deadline; Replay 10-second close; Guardian shutdown; Horde/world destroy; budget retirement')
end


local AUDIT_VARIANT=(...)
-- S1A ACCEPTANCE CASES ONLY: append after all unchanged full production bodies
-- and the unchanged helper prefix from combined_cases_clear_los.luau.
-- No product function, KO ledger, B attribute or proposed getter is synthesized.
-- H93 is expected to stop at the actual first Host start with missing BattleStage.
local growthCases={}
function growthCases.observe(name,detail)
 print('OBSERVATION\t'..name..'\t'..detail)
end
function growthCases.describe(session,playerRef)
 return 'phase='..tostring(session.rules.phase)
  ..';currentHuman='..tostring(session.isCurrentHuman(playerRef))
  ..';ledger='..tostring(session.swarm.kills[tostring(playerRef.UserId)] or 0)
  ..';B='..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleStage'))
  ..';XP='..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleXP'))
  ..';active='..tostring(playerRef:GetAttribute('EGGRUMBLE_GrowthActive'))
  ..';KO='..tostring(playerRef:GetAttribute('EGGRUMBLE_NeutralKOs'))
  ..';legacyLevel='..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleLevel'))
end
function growthCases.expectPublic(playerRef,stage,xp,active,kos,label)
 equal(playerRef:GetAttribute('EGGRUMBLE_BattleStage'),stage,label..' stage')
 equal(playerRef:GetAttribute('EGGRUMBLE_BattleXP'),xp,label..' XP')
 check(playerRef:GetAttribute('EGGRUMBLE_GrowthActive')==active,label..' active flag')
 equal(playerRef:GetAttribute('EGGRUMBLE_NeutralKOs'),kos,label..' original KO attribute')
 local stats=playerRef:FindFirstChild('leaderstats')
 local score=stats and stats:FindFirstChild('NeutralKO')
 check(score~=nil,label..' existing KO leaderboard')
 equal(score.Value,kos,label..' existing KO leaderboard value')
end
function growthCases.expectSnapshot(session,playerRef,stage,xp,kos,label)
 check(type(session.swarm.getBattleGrowthSnapshot)=='function',
  'MISSING_PRODUCTION_GET_BATTLE_GROWTH_SNAPSHOT')
 local before=#growthEngine.writes
 local ledgerBefore=table.clone(session.swarm.kills)
 local totalBefore=session.swarm.getTotal()
 for _=1,2 do
  local value=session.swarm.getBattleGrowthSnapshot(tostring(playerRef.UserId))
  check(type(value)=='table',label..' actual snapshot object')
  equal(value.stage,stage,label..' snapshot stage')
  equal(value.xp,xp,label..' snapshot XP')
  equal(value.neutralKOs,kos,label..' snapshot KO')
 end
 equal(#growthEngine.writes,before,label..' getter must not write any watched Player attribute')
 equal(session.swarm.getTotal(),totalBefore,label..' getter preserves original total')
 for id,value in pairs(ledgerBefore)do equal(session.swarm.kills[id],value,label..' getter preserves ledger '..id)end
 for id,value in pairs(session.swarm.kills)do equal(value,ledgerBefore[id],label..' getter cannot add ledger key '..id)end
 equal(session.swarm.kills[tostring(playerRef.UserId)] or 0,kos,label..' original KO ledger retained')
end
function growthCases.expectStart(session,playerRef,label,legacyLevel)
 growthCases.observe('ACTUAL_HOST_START',label..';'..growthCases.describe(session,playerRef))
 local stage=playerRef:GetAttribute('EGGRUMBLE_BattleStage')
 if stage==nil then
  error('RED_MISSING_BATTLE_STAGE_AT_ACTUAL_HOST_START actual=nil expected=1',0)
 end
 growthCases.expectPublic(playerRef,1,0,true,0,label)
 check(playerRef:GetAttribute('EGGRUMBLE_BattleLevel')==legacyLevel,
  label..' original initial BattleLevel unchanged, actual='
   ..tostring(playerRef:GetAttribute('EGGRUMBLE_BattleLevel'))..' expected='..tostring(legacyLevel))
 growthCases.expectSnapshot(session,playerRef,1,0,0,label)
end
function growthCases.realKO(session,duplicate)
 local neutral=spawnCurrentNeutral(session)
 local human=neutral:FindFirstChildOfClass('Humanoid')
 local target=neutral.PrimaryPart.Position
 local before=session.swarm.getTotal()
 local id=tostring(player.UserId)
 local beforePlayer=session.swarm.kills[id] or 0
 modelDeferred(human.Died,'REAL_NEUTRAL_DIED|'..session.world.Name..'|'
  ..tostring(neutral:GetAttribute('EGGRUMBLE_NeutralInstanceId')))
 rootPart.CFrame=clearNeutralApproach(neutral,target)
 -- Trusted existing server API: real geometry/LOS/HP/attribution/Died/KoFence.
 -- No direct calls to credit, no synthetic KO or fabricated attribution receipt.
 local hits=session.swarm.damageFromPlayer(player,target,.01,52,'CIRCLE')
 equal(hits,1,'one actual neutral admitted by full Swarm geometry/LOS')
 equal(human.Health,0,'actual damage authority reached Humanoid death')
 equal(session.swarm.getTotal(),before,'Deferred Died has not run before resumption')
 local delivered=drainDeferred()
 check(delivered>0,'actual registered Died callback delivered at modeled resumption')
 equal(session.swarm.getTotal(),before+1,'one actual Died credited once')
 equal(session.swarm.kills[id],beforePlayer+1,'one original player KO ledger increment')
 equal(player:GetAttribute('EGGRUMBLE_NeutralKOs'),beforePlayer+1,'same original KO publisher')
 if duplicate then
  local combo=player:GetAttribute('EGGRUMBLE_Combo')
  local writes=growthEngine.writeCount(player)
  human.Died:Fire()
  drainDeferred()
  equal(session.swarm.getTotal(),before+1,'duplicate registered Died consumed once')
  equal(session.swarm.kills[id],beforePlayer+1,'duplicate Died cannot increase original ledger')
  equal(player:GetAttribute('EGGRUMBLE_Combo'),combo,'duplicate Died cannot change timed Combo')
  equal(growthEngine.writeCount(player),writes,'duplicate Died cannot republish growth/KO/legacy')
  growthCases.observe('DUPLICATE_DIED_CONSUMED',
   'explicit adversarial signal replay; genuine first damage/death; ledger='..(beforePlayer+1))
 end
 outsideField(session)
 advanceTo(now+.26)
 return neutral,human
end
function growthCases.earn(session,count)
 for _=1,count do growthCases.realKO(session,false)end
end
function growthCases.finish(session)
 advanceTo(session.deadlineLease.start+900.01)
 check(session.rules.phase=='FINISHED'and session.rules.winner~=nil,'actual 900-second deadline finished')
 check(session.roundReplayScheduled and session.resultsDelivered,'real Result and Replay executed')
 local finishAt=nil
 for _,row in ipairs(phaseWrites)do
  if row.instance==session.world and row.phase=='FINISHED'then finishAt=finishAt or row.at end
 end
 check(finishAt~=nil,'real Host FINISHED phase publication')
 check(not session.isCurrentHuman(player),'actual old membership rejects finished round')
 return finishAt
end
function growthCases.sameAttributes(playerRef,before,label)
 for name in pairs(growthEngine.watched)do
  check(playerRef:GetAttribute(name)==before[name],label..' mutated '..name)
 end
end
function growthCases.resumeOld(held)
 for _,item in ipairs(held)do enqueue(now,item.entry.thread,item.entry.args)end
 advanceTo(now)
 for _,item in ipairs(held)do
  check(coroutine.status(item.entry.thread)=='dead','exact old Swarm task terminates after late delivery')
 end
end
function growthCases.progression_and_legacy()
 local session=ready('GROWTH_ACTUAL_READY')
 growthCases.expectStart(session,player,'FIRST_START',nil)
 for count=1,25 do
  growthCases.realKO(session,count==1)
  if count==1 then
   growthCases.expectPublic(player,2,10,true,1,'KO1')
   growthCases.expectSnapshot(session,player,2,10,1,'KO1')
  elseif count==2 then
   growthCases.expectPublic(player,2,20,true,2,'KO2')
   growthCases.expectSnapshot(session,player,2,20,2,'KO2')
  elseif count==3 then
   growthCases.expectPublic(player,2,30,true,3,'KO3')
   growthCases.expectSnapshot(session,player,2,30,3,'KO3')
  elseif count==4 then
   growthCases.expectPublic(player,3,40,true,4,'KO4')
   growthCases.expectSnapshot(session,player,3,40,4,'KO4')
  elseif count==8 then
   growthCases.expectPublic(player,3,80,true,8,'KO8')
   growthCases.expectSnapshot(session,player,3,80,8,'KO8')
  elseif count==24 then
   growthCases.expectPublic(player,3,80,true,24,'KO24')
   growthCases.expectSnapshot(session,player,3,80,24,'KO24')
  elseif count==25 then
   growthCases.expectPublic(player,3,80,true,25,'KO25')
   growthCases.expectSnapshot(session,player,3,80,25,'KO25')
  end
  equal(player:GetAttribute('EGGRUMBLE_BattleLevel'),if count<25 then 1 else 2,
   'original BattleLevel still advances only at KO25')
 end
 growthCases.observe('REAL_KO_THRESHOLDS','KO1=B2/10;KO4=B3/40;KO8=B3/80;KO25=B3/80;legacy25=2')
 return 'actual Host start; 25 genuine unique neutral deaths; duplicate receipt consumed; original BattleLevel threshold'
end
function growthCases.finished_deferred_snapshot()
 local session=ready('GROWTH_FINISH_READY')
 growthCases.expectStart(session,player,'FINISH_START',nil)
 growthCases.earn(session,4)
 growthCases.expectPublic(player,3,40,true,4,'BEFORE_FINISH')
 growthEngine.deferWorld(session.world)
 -- Prove a real hittable target first. Its genuine fatal-damage Died callback
 -- is then parked, so rejection after FINISHED cannot pass merely for no target.
 local neutral=spawnCurrentNeutral(session)
 local dying=neutral:FindFirstChildOfClass('Humanoid')
 local target=neutral.PrimaryPart.Position
 modelDeferred(dying.Died,'FINISH_PENDING_GENUINE_DIED')
 rootPart.CFrame=clearNeutralApproach(neutral,target)
 equal(session.swarm.damageFromPlayer(player,target,.01,52,'CIRCLE'),1,'genuine pre-finish lethal hit')
 equal(dying.Health,0,'genuine pending Died originates from actual fatal damage')
 equal(session.swarm.getTotal(),4,'genuine Died queued before KO ledger credit')
 local heldDied=growthEngine.holdSignal(dying.Died)
 local diedWitness=growthEngine.swarmWitness(heldDied)
 outsideField(session)
 local heldTasks=parkOldSwarm(session)
 local oldCombo=player:GetAttribute('EGGRUMBLE_Combo')
 local oldLevel=player:GetAttribute('EGGRUMBLE_BattleLevel')
 growthCases.finish(session)
 growthCases.expectSnapshot(session,player,3,40,4,'BEFORE_DEFERRED_CLEANUP')
 -- No assertion of synchronous clearing inside Host.refresh/ResultService.
 growthCases.observe('BEFORE_FINISH_RESUMPTION',growthCases.describe(session,player))
 local heldCleanup=growthEngine.holdWorld(session.world)
 growthEngine.requeue(heldDied)
 drainDeferred()
 growthEngine.requireSwarmDispatch(diedWitness,'GENUINE_DIED_AFTER_FINISHED_BEFORE_CLEANUP')
 equal(session.swarm.getTotal(),4,'real delayed Died cannot credit after FINISHED')
 growthCases.expectPublic(player,3,40,true,4,'DIED_REJECTED_BEFORE_PHASE_DISPATCH')
 growthEngine.requeue(heldCleanup)
 local delivered,cancelled=drainDeferred()
 check(delivered>0,'independently owned phase cleanup delivered')
 growthCases.expectPublic(player,1,0,false,0,'AFTER_FINISH_RESUMPTION')
 growthCases.expectSnapshot(session,player,3,40,4,'FINAL_RESULT_SNAPSHOT')
 equal(player:GetAttribute('EGGRUMBLE_Combo'),oldCombo,'new cleanup does not reset legacy timed Combo')
 equal(player:GetAttribute('EGGRUMBLE_BattleLevel'),oldLevel,'new cleanup does not reset old BattleLevel')
 check(#heldTasks==2,'cleanup completed with both original Swarm loops parked')
 growthCases.observe('FINISH_DEFERRED_CLEANUP',
  'delivered='..delivered..';cancelled='..cancelled..';public=B1/0/inactive/KO0;snapshot=B3/40/4')
 return 'real FINISHED; next modeled resumption cleanup; pure final snapshot from original kills; no cleanup loop'
end
function growthCases.same_player_next_round_stale()
 local first=ready('GROWTH_OLD_READY')
 growthCases.expectStart(first,player,'OLD_START',nil)
 growthCases.earn(first,4)
 growthEngine.deferWorld(first.world)
 local heldTasks=parkOldSwarm(first)
 local finishAt=growthCases.finish(first)
 local held=growthEngine.holdWorld(first.world)
 check(#held>0,'real old phase callback queued before adversarial delay')
 advanceTo(finishAt+10.1)
 check(first.world.Parent==nil,'actual Replay close destroyed old world')
 growthEngine.extendHeld(held,growthEngine.holdWorld(first.world))
 local nextSession=ready('GROWTH_NEXT_READY')
 check(nextSession~=first and player.Character==character,'same concrete Player and avatar enter real next round')
 growthCases.expectStart(nextSession,player,'NEXT_START',1)
 growthCases.realKO(nextSession,false)
 growthCases.expectPublic(player,2,10,true,1,'NEXT_KO1')
 local before=growthEngine.snapshot(player)
 local writes=growthEngine.writeCount(player)
 local capacity=nextSession.neutralBudget:snapshot().total
 local witness=growthEngine.swarmWitness(held,growthEngine.worldPrefixes[first.world]..'PHASE')
 growthEngine.requeue(held)
 local delivered,cancelled=drainDeferred()
 growthEngine.requireSwarmDispatch(witness,'SAME_PLAYER_OLD_PHASE_CLOSURE')
 growthCases.resumeOld(heldTasks)
 growthCases.sameAttributes(player,before,'old callback after same Player next round')
 equal(growthEngine.writeCount(player),writes,'old lease cannot even republish same values to newer Player lease')
 equal(nextSession.neutralBudget:snapshot().total,capacity,'old tasks do not release new neutral epoch')
 growthCases.expectPublic(player,2,10,true,1,'AFTER_OLD_DELIVERY')
 growthCases.expectSnapshot(first,player,3,40,4,'OLD_FINAL_LEDGER')
 growthCases.expectSnapshot(nextSession,player,2,10,1,'NEW_LEDGER')
 equal(first.swarm.damageFromPlayer(player,rootPart.Position,5,52,'CIRCLE'),0,'old API rejects actual new current human')
 growthCases.observe('SAME_PLAYER_LATE_CLEANUP',
  'held='..#held..';delivered='..delivered..';cancelled='..cancelled..';new=B2/10/1;writes=0')
 return 'same concrete Player real replay; exact old registered callbacks delayed and requeued; no newer-lease write'
end
function growthCases.makeReplacement()
 local oldPlayer=player
 modelDeferred(Players.PlayerRemoving,'REPLACEMENT_OLD_PLAYER_REMOVING')
 Players.PlayerRemoving:Fire(oldPlayer)
 -- Adversarially park only the actual old Swarm listener while allowing the
 -- exact Host removal callbacks to run. No membership function is substituted.
 local heldRemoving=growthEngine.holdSignal(Players.PlayerRemoving,'SwarmCombat')
 local removalWitness=growthEngine.swarmWitness(heldRemoving)
 drainDeferred()
 oldPlayer.Parent=nil
 currentPlayers={second}
 local replacement=Instance.new('Player')
 replacement.Name='GrowthReplacement42';replacement.UserId=oldPlayer.UserId;replacement.Parent=Players
 local gui=Instance.new('PlayerGui');gui.Parent=replacement
 local backpack=Instance.new('Backpack');backpack.Parent=replacement
 local avatar=Instance.new('Model');avatar.Name='GrowthReplacementAvatar';avatar.Parent=workspace
 local human=Instance.new('Humanoid');human.WalkSpeed=20;human.Parent=avatar
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=avatar
 avatar.PrimaryPart=root;replacement.Character=avatar
 currentPlayers={replacement,second}
 Players.PlayerAdded:Fire(replacement)
 player=replacement;playerGui=gui;bag=backpack
 character=avatar;humanoid=human;rootPart=root
 check(Players:GetPlayerByUserId(42)==replacement and replacement~=oldPlayer,
  'engine fixture resolves fresh concrete Player for same numeric UserId')
 return oldPlayer,heldRemoving,removalWitness
end
function growthCases.readySoloBR()
 local count=#capturedSessions
 trigger(player,scenes:FindFirstChild('ROLE_MAGE'),'職業選択')
 trigger(player,scenes:FindFirstChild('BATTLE_ROYALE_PORTAL'),'参加する')
 local entered=now
 advanceTo(entered+11.99);equal(#capturedSessions,count,'real BR READY not shortened')
 advanceTo(entered+12.01);equal(#capturedSessions,count+1,'one real BR session')
 local session=capturedSessions[#capturedSessions]
 check(session.mode=='BATTLE_ROYALE'and session.rules.phase=='ACTIVE','real replacement BR round active')
 check(session.isCurrentHuman(player)and not session.isCurrentHuman(second),'actual BR membership fence')
 check(session.swarm==swarmAttachments[#swarmAttachments].api,'actual replacement Swarm attached')
 outsideField(session)
 return session
end
function growthCases.replacement_player_same_user_id()
 local first=ready('GROWTH_REJOIN_OLD_READY')
 growthCases.expectStart(first,player,'REJOIN_OLD_START',nil)
 growthCases.earn(first,4)
 growthEngine.deferWorld(first.world)
 local heldTasks=parkOldSwarm(first)
 local oldPlayer,heldRemoving,removalWitness=growthCases.makeReplacement()
 check(first.rules.phase=='ACTIVE'and first.isCurrentHuman(second),'remaining real human keeps old TEAM active')
 growthCases.expectPublic(second,1,0,true,0,'REMAINING_OLD_HUMAN')
 check(not first.isCurrentHuman(player),'old Host rejects replacement after real removal')
 local nextSession=growthCases.readySoloBR()
 growthCases.expectStart(nextSession,player,'REPLACEMENT_START',nil)
 growthCases.realKO(nextSession,false)
 growthCases.expectPublic(player,2,10,true,1,'REPLACEMENT_KO1')
 first.closeRound(true)
 check(first.rules.phase=='ABANDONED'and first.world.Parent==nil,'actual old Host closeRound abandoned and destroyed world')
 local held=growthEngine.holdWorld(first.world)
 check(#held>0,'old independent cleanup or implicit-destroy invocation exists at engine boundary')
 -- New genuine progress is earned while old cleanup remains parked.
 growthCases.realKO(nextSession,false)
 growthCases.expectPublic(player,2,20,true,2,'REPLACEMENT_KO2')
 local before=growthEngine.snapshot(player)
 local writes=growthEngine.writeCount(player)
 local capacity=nextSession.neutralBudget:snapshot().total
 local phaseWitness=growthEngine.swarmWitness(held,growthEngine.worldPrefixes[first.world]..'PHASE')
 growthEngine.requeue(heldRemoving)
 growthEngine.requeue(held)
 local delivered,cancelled=drainDeferred()
 growthEngine.requireSwarmDispatch(removalWitness,'REPLACEMENT_OLD_PLAYER_REMOVING_CLOSURE')
 growthEngine.requireSwarmDispatch(phaseWitness,'REPLACEMENT_OLD_PHASE_CLOSURE')
 growthCases.resumeOld(heldTasks)
 growthCases.sameAttributes(player,before,'old cleanup must target concrete old Player, not UserId lookup')
 equal(growthEngine.writeCount(player),writes,'old concrete Player cleanup performs no replacement writes')
 equal(nextSession.neutralBudget:snapshot().total,capacity,'old abandoned tasks preserve replacement BR budget')
 check(oldPlayer~=player and oldPlayer.Parent==nil,'old concrete Player stays disconnected')
 check(nextSession.isCurrentHuman(player)and not first.isCurrentHuman(player),'real new membership stays current')
 growthCases.expectPublic(player,2,20,true,2,'AFTER_REPLACEMENT_STALE_DELIVERY')
 growthCases.expectSnapshot(first,oldPlayer,3,40,4,'DISCONNECTED_OLD_LEDGER')
 growthCases.expectSnapshot(nextSession,player,2,20,2,'REPLACEMENT_NEW_LEDGER')
 growthCases.observe('REPLACEMENT_PLAYER_LATE_CLEANUP',
  'sameUserId=42;differentConcretePlayer=true;held='..#held..';delivered='..delivered
   ..';cancelled='..cancelled..';new=B2/20/2;writes=0')
 return 'actual PlayerRemoving/PlayerAdded; new concrete same-UserId Player in real BR; delayed old TEAM cleanup'
end
function growthCases.same_round_death_respawn()
 local session=ready('GROWTH_RESPAWN_READY')
 growthCases.expectStart(session,player,'RESPAWN_START',nil)
 growthCases.earn(session,4)
 local oldCombo=player:GetAttribute('EGGRUMBLE_Combo')
 humanoid:TakeDamage(humanoid.Health)
 equal(humanoid.Health,0,'real fixture Humanoid death boundary')
 growthCases.expectPublic(player,3,40,true,4,'DEAD_SAME_ROUND')
 local old=character
 player.CharacterRemoving:Fire(old)
 old:Destroy()
 local avatar=Instance.new('Model');avatar.Name='GrowthRespawnAvatar';avatar.Parent=workspace
 local human=Instance.new('Humanoid');human.WalkSpeed=20;human.Parent=avatar
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.Parent=avatar
 avatar.PrimaryPart=root;player.Character=avatar
 character=avatar;humanoid=human;rootPart=root
 player.CharacterAdded:Fire(avatar)
 growthCases.expectPublic(player,3,40,true,4,'NEW_AVATAR_BEFORE_HOST_RETURN')
 advanceTo(now+.81)
 check(session.isCurrentHuman(player)and player.Character==avatar,'same real Host owns replacement avatar')
 check(player:GetAttribute('EGGRUMBLE_Role')=='MAGE','actual Host restored selected role')
 local tools=0
 for _,container in ipairs({bag,avatar})do
  for _,item in ipairs(container:GetChildren())do
   if item:IsA('Tool')and type(item:GetAttribute('EGGRUMBLE_InternalToolId'))=='string'then tools+=1 end
  end
 end
 check(tools>=3,'actual Combat.equip restored role tools after Host .8-second return')
 growthCases.expectPublic(player,3,40,true,4,'ACTUAL_HOST_RESPAWN')
 growthCases.expectSnapshot(session,player,3,40,4,'RESPAWN_LEDGER')
 equal(player:GetAttribute('EGGRUMBLE_BattleLevel'),1,'legacy BattleLevel retained')
 equal(player:GetAttribute('EGGRUMBLE_Combo'),oldCombo,'timed Combo not relabeled or reset as death streak')
 outsideField(session)
 growthCases.observe('SAME_ROUND_REAL_HOST_RESPAWN','death->CharacterAdded->actualHost0.8s->CombatEquip;B3/40/4 retained')
 return 'same-round death and genuine Host delayed return preserve cumulative B/XP/KO'
end
function growthCases.finished_immediate_snapshot()
 local session=ready('GROWTH_IMMEDIATE_FINISH_READY')
 growthCases.expectStart(session,player,'IMMEDIATE_FINISH_START',nil)
 growthCases.earn(session,4)
 local held=parkOldSwarm(session)
 growthCases.finish(session)
 growthCases.expectPublic(player,1,0,false,0,'IMMEDIATE_FINISHED')
 growthCases.expectSnapshot(session,player,3,40,4,'IMMEDIATE_FINISHED_FINAL_SNAPSHOT')
 check(#held==2,'no growth cleanup loop')
 return 'real FINISHED under Immediate signal delivery clears public B while original final KO snapshot survives'
end
function growthCases.teardown(kind,deferred)
 local session=ready('GROWTH_TEARDOWN_READY')
 growthCases.expectStart(session,player,'TEARDOWN_START',nil)
 growthCases.realKO(session,false)
 local world=session.world
 if deferred then growthEngine.deferWorld(world)end
 -- This same actual living neutral is demonstrably hittable before detach.
 local target=spawnCurrentNeutral(session)
 local human=target:FindFirstChildOfClass('Humanoid')
 local point=target.PrimaryPart.Position
 rootPart.CFrame=clearNeutralApproach(target,point)
 equal(session.swarm.damageFromPlayer(player,point,.01,1,'CIRCLE'),1,'actual pre-teardown hittable control')
 local hp=human.Health
 local heldTasks=parkOldSwarm(session)
 local dispatchStart=#growthEngine.callbackDispatches
 local oldParent=world.Parent
 if kind=='destroy'then
  world:Destroy()
 elseif kind=='abandon'then
  session.closeRound(true)
 else
  world.Parent=nil
  equal(session.swarm.damageFromPlayer(player,point,.01,52,'CIRCLE'),0,'same hittable target rejected while exact world detached')
  equal(human.Health,hp,'detached-world API cannot damage the proven hittable neutral')
  if kind=='reattach'then world.Parent=oldParent end
 end
 if deferred then
  local queued=growthEngine.holdWorld(world)
  local label=growthEngine.worldPrefixes[world]..(
   if kind=='destroy'then 'DESTROYING'elseif kind=='abandon'then 'PHASE'else 'ANCESTRY')
  local witness=growthEngine.swarmWitness(queued,label)
  growthEngine.requeue(queued);drainDeferred()
  growthEngine.requireSwarmDispatch(witness,'TEARDOWN_'..kind)
 end
 local ownDeliveries=0
 for i=dispatchStart+1,#growthEngine.callbackDispatches do
  if growthEngine.callbackDispatches[i].source=='SwarmCombat'then ownDeliveries+=1 end
 end
 check(ownDeliveries>0,'actual candidate Swarm teardown callback executed')
 growthCases.expectPublic(player,1,0,false,0,'TEARDOWN_'..kind)
 growthCases.expectSnapshot(session,player,2,10,1,'TEARDOWN_FINAL_KO')
 if kind~='abandon'then check(session.rules.phase=='ACTIVE','external operation does not impersonate Host phase change')end
 if kind=='reattach'then
  check(world.Parent==oldParent,'captured nil-parent event still retires after reparent')
  equal(session.swarm.damageFromPlayer(player,point,.01,52,'CIRCLE'),0,'retired old world stays rejected after reparent')
  equal(human.Health,hp,'same restored target cannot be damaged through retired lease')
 end
 local writes=growthEngine.writeCount(player)
 drainDeferred()
 equal(growthEngine.writeCount(player),writes,'duplicate queued teardown does not republish')
 check(#heldTasks==2,'teardown did not need either original Swarm loop')
 growthCases.observe('ACTUAL_CANDIDATE_TEARDOWN',
  'kind='..kind..';delivery='..(if deferred then 'Deferred'else 'Immediate')
   ..';ownCallbacks='..ownDeliveries..';B1/0/inactive/KO0;final=1')
 return 'actual candidate own callback clears derived publication on '..kind
end
function growthCases.external_destroy_immediate()return growthCases.teardown('destroy',false)end
function growthCases.external_destroy_deferred()return growthCases.teardown('destroy',true)end
function growthCases.external_detach_immediate()return growthCases.teardown('detach',false)end
function growthCases.external_detach_deferred()return growthCases.teardown('detach',true)end
function growthCases.external_reattach_immediate()return growthCases.teardown('reattach',false)end
function growthCases.external_reattach_deferred()return growthCases.teardown('reattach',true)end
function growthCases.abandoned_immediate()return growthCases.teardown('abandon',false)end
function growthCases.abandoned_deferred()return growthCases.teardown('abandon',true)end
function growthCases.last_human_abandonment()
 local session=ready('GROWTH_LAST_HUMAN_READY')
 growthCases.expectStart(session,player,'LAST_HUMAN_START',nil)
 growthCases.realKO(session,false)
 growthEngine.deferWorld(session.world)
 modelDeferred(Players.PlayerRemoving,'LAST_HUMAN_REMOVING')
 Players.PlayerRemoving:Fire(player)
 player.Parent=nil;currentPlayers={second}
 drainDeferred()
 check(session.rules.phase=='ACTIVE'and session.isCurrentHuman(second),'first actual departure leaves remaining human active')
 growthCases.expectPublic(second,1,0,true,0,'REMAINING_LAST_HUMAN')
 Players.PlayerRemoving:Fire(second)
 second.Parent=nil;currentPlayers={}
 drainDeferred()
 check(session.rules.phase=='ABANDONED'and session.world.Parent==nil,'real last departure invokes Host abandonment and destroys world')
 equal(session.neutralBudget:snapshot().total,0,'real Host retired neutral epoch')
 check(not session.isCurrentHuman(player)and not session.isCurrentHuman(second),'old real memberships retired')
 growthCases.expectSnapshot(session,player,2,10,1,'ABANDONED_FINAL_KO')
 growthCases.observe('REAL_LAST_HUMAN_ABANDONMENT','actual2PlayerRemoving->HostABANDONED->worldnil;disconnected attributes are not a live UI')
 return 'actual last-human leave; disconnected concrete Player state cannot become a replacement-player publication'
end
function growthCases.false_fake_spectator_membership()
 local session=ready('GROWTH_MEMBERSHIP_READY')
 growthCases.expectStart(session,player,'MEMBERSHIP_START',nil)
 local neutral=spawnCurrentNeutral(session)
 local human=neutral:FindFirstChildOfClass('Humanoid')
 local target=neutral.PrimaryPart.Position
 rootPart.CFrame=clearNeutralApproach(neutral,target)
 equal(session.swarm.damageFromPlayer(player,target,.01,1,'CIRCLE'),1,'same target is hittable by genuine current Player')
 local health=human.Health
 local fake=Instance.new('Player');fake.Name='AdversarialSameId';fake.UserId=player.UserId;fake.Parent=Players
 fake.Character=character
 check(fake~=player and session.isCurrentHuman(fake),'actual numeric Host membership alone accepts same-id fixture double')
 equal(session.swarm.damageFromPlayer(fake,target,.01,52,'CIRCLE'),0,'concrete-token guard rejects same-id fake')
 equal(human.Health,health,'same-id fake cannot damage known hittable neutral')
 fake.Parent=nil
 local spectator=Instance.new('Player');spectator.Name='ConnectedSpectator';spectator.UserId=99;spectator.Parent=Players
 local avatar=Instance.new('Model');avatar.Parent=workspace
 local h=Instance.new('Humanoid');h.Parent=avatar
 local root=Instance.new('Part');root.Name='HumanoidRootPart';root.CFrame=rootPart.CFrame;root.Parent=avatar
 avatar.PrimaryPart=root;spectator.Character=avatar
 table.insert(currentPlayers,spectator)
 check(not session.isCurrentHuman(spectator),'actual connected spectator never joined this Host')
 equal(session.swarm.damageFromPlayer(spectator,target,.01,52,'CIRCLE'),0,'spectator rejected at concrete current-human API boundary')
 equal(human.Health,health,'spectator cannot damage same known hittable neutral')
 growthCases.expectPublic(player,1,0,true,0,'NO_FALSE_KO_PUBLICATION')
 Players.PlayerRemoving:Fire(player)
 check(session.rules.phase=='ACTIVE'and not session.isCurrentHuman(player),'actual Host removal revokes old human while peer remains')
 equal(session.swarm.damageFromPlayer(player,target,.01,52,'CIRCLE'),0,'real departed human rejected with still-valid avatar and target')
 equal(human.Health,health,'departed human cannot damage same proven target')
 equal(session.swarm.getTotal(),0,'all three negative callers leave original total unchanged')
 growthCases.expectSnapshot(session,player,1,0,0,'NO_FALSE_LEDGER_CREDIT')
 growthCases.observe('CONCRETE_CURRENT_HUMAN_NEGATIVES',
  'realControlHit=1;sameIdFake=0;connectedSpectator=0;actualDepartedHuman=0;sameTargetHPUnchanged;ledger0')
 return 'proven hittable neutral; fake same-id Player, actual spectator and actual departed human rejected without damage or KO'
end

-- MAGE_RUNTIME_CASES

local ok,result=pcall(function()
 advanceTo(now)
 sharedRequires()
 check(type(growthCases[AUDIT_VARIANT])=='function','unknown S1A acceptance variant')
 local detail=growthCases[AUDIT_VARIANT]()
 check(#warnings==0,'no suppressed dependency warning')
 return detail
end)
print('CASE\tGROWTH_ACCEPTANCE_'..AUDIT_VARIANT..'\t'..(if ok then 'PASS'else 'FAIL')
 ..'\t'..tostring(result):gsub('\n',' '))
for _,warning in ipairs(warnings)do print('WARNING\t'..warning)end
print('METRIC\tscheduler_resumes\t'..schedulerResumes)
print('METRIC\tgrowth_attribute_writes\t'..#growthEngine.writes)
print('METRIC\tdeferred_trace_entries\t'..#deferredTrace)
if not ok then error(result,0)end
