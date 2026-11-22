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
