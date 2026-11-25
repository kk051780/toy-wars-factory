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
