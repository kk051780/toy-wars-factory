-- Deterministic engine boundary, not a Roblox/Studio or network simulator.
-- Product decisions belong only to the full unchanged source bodies below.
local rawTypeof=typeof
local vectorMeta={}
vectorMeta.__index=vectorMeta
local function vector(x,y,z)return setmetatable({X=x,Y=y,Z=z,__kind="Vector3"},vectorMeta)end
local Vector3={new=vector,zero=vector(0,0,0)}
function vectorMeta.__add(a,b)return vector(a.X+b.X,a.Y+b.Y,a.Z+b.Z)end
function vectorMeta.__sub(a,b)return vector(a.X-b.X,a.Y-b.Y,a.Z-b.Z)end
function vectorMeta.__mul(a,b)
 if type(a)=="number"then return vector(a*b.X,a*b.Y,a*b.Z)end
 return vector(a.X*b,a.Y*b,a.Z*b)
end
local function typeof(value)
 return if type(value)=="table"and value.__kind then value.__kind else rawTypeof(value)
end
local CFrame={}
function CFrame.new(at,y,z)
 if type(at)=="number"then at=vector(at,y,z)end
 return{Position=at or vector(0,0,0),RightVector=vector(1,0,0),UpVector=vector(0,1,0),LookVector=vector(0,0,-1)}
end
local colorMeta={__eq=function(a,b)return a.R==b.R and a.G==b.G and a.B==b.B end}
local Color3={fromRGB=function(r,g,b)
 return setmetatable({R=r/255,G=g/255,B=b/255,__kind="Color3"},colorMeta)
end}
local ColorSequence={new=function(color)return{color=color}end}
local mode="Immediate"
local callbackQueue={}
local sourceContext=nil
local now=0
local debrisQueue={}
local timedTasks={}
local objects={}
local workspace,Players,ReplicatedStorage,RunService,Input,Debris,game
local currentFixture=nil
local moduleLoads=0
local runtimeClient=true
local moduleCache={}
local cueHistory={}
local peakCues=0
local loadActualModule,loadActualClient
local function sourceAlive(owner)
 return owner==nil or (not owner._destroyed and owner.Disabled~=true and owner.Enabled~=false)
end
local function runInSource(owner,callback,...)
 local previous=sourceContext
 sourceContext=owner
 local results=table.pack(pcall(callback,...))
 sourceContext=previous
 if not results[1]then error(results[2],0)end
 return table.unpack(results,2,results.n)
end
local function invoke(entry)
 -- Explicit Disconnect removes pending work. Implicit owner destruction does
 -- not; a destroyed/disabled *script* still cannot execute its own callback.
 if entry.connection and entry.connection.explicitlyDisconnected then return end
 if not sourceAlive(entry.owner)then return end
 runInSource(entry.owner,entry.callback,table.unpack(entry.args,1,entry.args.n))
end
local signalMethods={}
local function signal(owner,name)
 return setmetatable({owner=owner,name=name,connections={}}, {__index=signalMethods})
end
function signalMethods:Connect(callback)
 local connection={Connected=true,explicitlyDisconnected=false,callback=callback,owner=sourceContext}
 function connection:Disconnect()
  self.Connected=false
  self.explicitlyDisconnected=true
 end
 table.insert(self.connections,connection)
 return connection
end
function signalMethods:Once(callback)
 local connection
 connection=self:Connect(function(...)
  connection:Disconnect()
  callback(...)
 end)
 return connection
end
function signalMethods:Fire(...)
 local args=table.pack(...)
 local eligible={}
 for _,connection in ipairs(self.connections)do
  if connection.Connected then table.insert(eligible,connection)end
 end
 for _,connection in ipairs(eligible)do
  local entry={connection=connection,callback=connection.callback,owner=connection.owner,args=args}
  if mode=="Immediate"then invoke(entry)else table.insert(callbackQueue,entry)end
 end
end
function signalMethods:implicitDisconnect()
 for _,connection in ipairs(self.connections)do connection.Connected=false end
end
local function drain()
 local count=0
 while #callbackQueue>0 do
  count+=1
  assert(count<20000,"unbounded deferred callback loop")
  local entry=table.remove(callbackQueue,1)
  invoke(entry)
 end
end
local methods={}
local instanceMeta={}
local namedSignals={Changed=true,AncestryChanged=true,Destroying=true,ChildAdded=true,ChildRemoved=true,
 DescendantAdded=true,DescendantRemoving=true,CharacterAdded=true,CharacterRemoving=true,
 PlayerAdded=true,PlayerRemoving=true,Died=true,HealthChanged=true}
local function getSignal(object,key)
 local found=object._signals[key]
 if not found then found=signal(object,key);object._signals[key]=found end
 return found
end
function instanceMeta.__index(self,key)
 if methods[key]then return methods[key]end
 if key=="__kind"then return"Instance"end
 if namedSignals[key]then return getSignal(self,key)end
 return self._props[key]
end
local function isDescendant(object,ancestor)
 local cursor=object.Parent
 local seen={}
 while cursor do
  if cursor==ancestor then return true end
  assert(not seen[cursor],"cyclic fixture parenting")
  seen[cursor]=true
  cursor=cursor.Parent
 end
 return false
end
local function isCue(object)
 return object.ClassName=="Part"and type(object.Name)=="string"
  and string.sub(object.Name,1,17)=="EGG_AttributeCue_"
end
local function cueCount()
 local count=0
 for _,object in ipairs(objects)do
  if isCue(object)and not object._destroyed and isDescendant(object,workspace)then count+=1 end
 end
 return count
end
local function beamCount()
 local count=0
 for _,object in ipairs(objects)do
  if object.ClassName=="Beam"and not object._destroyed and isDescendant(object,workspace)then count+=1 end
 end
 return count
end
local function children(object)
 local result={}
 for _,candidate in ipairs(objects)do
  if candidate.Parent==object then table.insert(result,candidate)end
 end
 return result
end
local function fireExisting(object,key,...)
 local found=object._signals[key]
 if found then found:Fire(...)end
end
local function notifyAncestors(object,key,descendant)
 local cursor=object
 while cursor do fireExisting(cursor,key,descendant);cursor=cursor.Parent end
end
local function notifyAncestry(object)
 fireExisting(object,"AncestryChanged",object,object.Parent)
 for _,child in ipairs(children(object))do notifyAncestry(child)end
end
function instanceMeta.__newindex(self,key,value)
 local old=self._props[key]
 if old==value then return end
 if key=="Character"and self.ClassName=="Player"and old then
  fireExisting(self,"CharacterRemoving",old)
 end
 if key=="Parent"and old then notifyAncestors(old,"DescendantRemoving",self)end
 self._props[key]=value
 if key=="CFrame"and self:IsA("BasePart")then self._props.Position=value.Position end
 if key=="Position"and self:IsA("BasePart")then self._props.CFrame=CFrame.new(value)end
 fireExisting(self,"property:"..key)
 fireExisting(self,"Changed",key)
 if key=="Parent"then
  if old then fireExisting(old,"ChildRemoved",self)end
  if value then fireExisting(value,"ChildAdded",self);notifyAncestors(value,"DescendantAdded",self)end
  notifyAncestry(self)
  if isCue(self)and value and isDescendant(self,workspace)then
   table.insert(cueHistory,{name=self.Name,position=self.Position,time=now,object=self})
  end
  peakCues=math.max(peakCues,cueCount())
 elseif key=="Character"and self.ClassName=="Player"and value then
  fireExisting(self,"CharacterAdded",value)
 elseif key=="Health"and self.ClassName=="Humanoid"then
  fireExisting(self,"HealthChanged",value)
  if type(old)=="number"and old>0 and value<=0 then fireExisting(self,"Died")end
 end
end
function methods:IsA(class)
 return self.ClassName==class or class=="Instance"
  or (class=="BasePart"and(self.ClassName=="Part"or self.ClassName=="SpawnLocation"))
  or (class=="LuaSourceContainer"and(self.ClassName=="LocalScript"or self.ClassName=="ModuleScript"))
end
function methods:GetChildren()return children(self)end
function methods:GetDescendants()
 local result={}
 for _,candidate in ipairs(objects)do
  if isDescendant(candidate,self)then table.insert(result,candidate)end
 end
 return result
end
function methods:IsDescendantOf(ancestor)return isDescendant(self,ancestor)end
function methods:FindFirstChild(name,recursive)
 for _,candidate in ipairs(children(self))do if candidate.Name==name then return candidate end end
 if recursive then
  for _,candidate in ipairs(self:GetDescendants())do if candidate.Name==name then return candidate end end
 end
 return nil
end
function methods:FindFirstChildOfClass(class)
 for _,candidate in ipairs(children(self))do if candidate.ClassName==class then return candidate end end
 return nil
end
function methods:FindFirstChildWhichIsA(class,recursive)
 for _,candidate in ipairs(if recursive then self:GetDescendants()else children(self))do
  if candidate:IsA(class)then return candidate end
 end
 return nil
end
function methods:WaitForChild(name,_timeout)
 -- Only the already-replicated lookup path is modeled. No fabricated yield.
 return self:FindFirstChild(name)
end
function methods:GetAttribute(name)return self._attributes[name]end
function methods:GetAttributes()return table.clone(self._attributes)end
function methods:SetAttribute(name,value)
 if self._attributes[name]==value then return end
 self._attributes[name]=value
 fireExisting(self,"attribute:"..name)
end
function methods:GetAttributeChangedSignal(name)return getSignal(self,"attribute:"..name)end
function methods:GetPropertyChangedSignal(name)return getSignal(self,"property:"..name)end
function methods:GetFullName()
 return if self.Parent then self.Parent:GetFullName().."."..self.Name else self.Name
end
function methods:Destroy()
 self._destroyCalls+=1
 if self._destroyed then return end
 fireExisting(self,"Destroying")
 self._destroyed=true
 for _,child in ipairs(children(self))do child:Destroy()end
 self.Parent=nil
 for _,event in pairs(self._signals)do event:implicitDisconnect()end
end
function methods:GetPlayers()
 local result={}
 for _,child in ipairs(children(self))do if child:IsA("Player")then table.insert(result,child)end end
 return result
end
function methods:GetPlayerByUserId(id)
 for _,player in ipairs(self:GetPlayers())do if player.UserId==id then return player end end
 return nil
end
local Instance={}
function Instance.new(class,parent)
 local object=setmetatable({_props={ClassName=class,Name=class},_signals={},_attributes={},_destroyed=false,_destroyCalls=0},instanceMeta)
 table.insert(objects,object)
 if class=="Part"or class=="SpawnLocation"then object.Position=vector(0,0,0)end
 if class=="Camera"then object.CFrame=CFrame.new(vector(0,0,0))end
 if class=="Humanoid"then object.Health=100 end
 if class=="LocalScript"then object.Disabled=false;object.Enabled=true end
 if parent then object.Parent=parent end
 return object
end
local task={}
function task.defer(callback,...)
 table.insert(callbackQueue,{callback=callback,owner=sourceContext,args=table.pack(...)})
end
function task.delay(seconds,callback,...)
 table.insert(timedTasks,{deadline=now+seconds,callback=callback,owner=sourceContext,args=table.pack(...)})
end
local function advance(seconds)
 now+=seconds
 for _,entry in ipairs(debrisQueue)do
  if not entry.done and entry.deadline<=now+1e-9 then entry.done=true;entry.object:Destroy()end
 end
 for _,entry in ipairs(timedTasks)do
  if not entry.done and entry.deadline<=now+1e-9 then entry.done=true;invoke(entry)end
 end
 drain()
end
local function require(module)
 assert(module and module:IsA("ModuleScript"),"fixture requires a ModuleScript instance")
 if moduleCache[module]~=nil then return moduleCache[module]end
 moduleLoads+=1
 local result=runInSource(module,loadActualModule,module)
 moduleCache[module]=result
 return result
end
local function makeAvatar(player,x)
 local character=Instance.new("Model",workspace);character.Name="Character_"..player.UserId
 local humanoid=Instance.new("Humanoid",character)
 local root=Instance.new("Part",character);root.Name="HumanoidRootPart";root.Position=vector(x or 0,0,0)
 player.Character=character
 return character,humanoid,root
end
local function makePlayer(id,x)
 local player=Instance.new("Player",Players);player.Name="Player_"..id;player.UserId=id
 local playerScripts=Instance.new("Folder",player);playerScripts.Name="PlayerScripts"
 local character,humanoid,root=makeAvatar(player,x)
 player:SetAttribute("EGGRUMBLE_Role","MAGE")
 player:SetAttribute("EGGRUMBLE_QueuedMode","TEAM")
 player:SetAttribute("EGGRUMBLE_Eliminated",false)
 return player,character,humanoid,root
end
local function makeWorld(lobby,modeName,phase)
 local world=Instance.new("Folder");world.Name=modeName.."_Arena"
 world:SetAttribute("EGGRUMBLE_MatchPhase",phase or"ACTIVE");world.Parent=lobby
 local castle=Instance.new("Model");castle.Name="Castle_42";castle.Parent=world
 local core=Instance.new("Part");core.Name="StandardCore";core.Color=Color3.fromRGB(172,166,147);core.Parent=castle
 return world
end
local function freshEnvironment(behavior,existingSignature,touch)
 mode=behavior;callbackQueue={};sourceContext=nil;now=0;debrisQueue={};timedTasks={};objects={}
 moduleCache={};moduleLoads=0;runtimeClient=true;cueHistory={};peakCues=0
 workspace=Instance.new("Workspace");workspace.Name="Workspace"
 Players=Instance.new("Players");Players.Name="Players"
 ReplicatedStorage=Instance.new("ReplicatedStorage");ReplicatedStorage.Name="ReplicatedStorage"
 RunService={IsClient=function()return runtimeClient end,IsStudio=function()return false end}
 Input={TouchEnabled=touch==true}
 Debris={AddItem=function(_,object,seconds)
  table.insert(debrisQueue,{object=object,deadline=now+seconds})
 end}
 game={GetService=function(_,name)
  local services={Players=Players,ReplicatedStorage=ReplicatedStorage,UserInputService=Input,
   RunService=RunService,Debris=Debris,Workspace=workspace}
  assert(services[name],"unmodeled service "..name)
  return services[name]
 end}
 local camera=Instance.new("Camera",workspace);workspace.CurrentCamera=camera
 local lobby=Instance.new("Folder",workspace);lobby.Name="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
 local world=makeWorld(lobby,"TEAM","ACTIVE")
 local player,character,humanoid,root=makePlayer(42,0)
 Players.LocalPlayer=player
 if existingSignature then player:SetAttribute("EGGRUMBLE_SkillCastSignature",existingSignature)end
 local module=Instance.new("ModuleScript",ReplicatedStorage);module.Name="EGGRUMBLE_ElementVisuals"
 currentFixture={player=player,character=character,humanoid=humanoid,root=root,lobby=lobby,
  world=world,camera=camera,module=module}
 drain()
 return currentFixture
end
local function attachClient(fixture)
 local client=Instance.new("LocalScript",fixture.player:FindFirstChild("PlayerScripts"))
 client.Name="EGGRUMBLE_AttributeCue"
 runInSource(client,loadActualClient,client)
 fixture.client=client
 return client
end
local function setCast(fixture,role,slot,sequence,flush)
 fixture.player:SetAttribute("EGGRUMBLE_Role",role)
 fixture.player:SetAttribute("EGGRUMBLE_SkillCastSignature",role..":"..slot..":"..tostring(sequence))
 if flush~=false then drain()end
end
local function lastCue()
 return cueHistory[#cueHistory]
end
local function snapshot()
 return{cues=cueCount(),beams=beamCount(),admissions=#cueHistory,peak=peakCues,moduleLoads=moduleLoads}
end
local function ownedConnectionCount(owner)
 local count=0
 for _,object in ipairs(objects)do
  for _,event in pairs(object._signals)do
   for _,connection in ipairs(event.connections)do
    if connection.Connected and connection.owner==owner then count+=1 end
   end
  end
 end
 return count
end

-- GQ778_INSERT_SOURCE_BODIES_HERE
-- Observable scenarios invoke the actual full LocalScript's subscribed callback.
-- Original expectations document defects; proposal expectations are the contract.
local scenarioCount=0
local gapCount=0
local function check(label,actual,original,repaired,detail)
 local wanted=if expectation=="original"then original else repaired
 assert(actual==wanted,label.." expected "..tostring(wanted)..", got "..tostring(actual))
 scenarioCount+=1
 if original~=repaired then gapCount+=1 end
 print("OBS "..mode.." "..label.."="..tostring(actual)
  ..";original="..tostring(original)..";contract="..tostring(repaired)
  ..(if detail then";"..detail else""))
end
local function attach(behavior,signature,touch)
 local fixture=freshEnvironment(behavior,signature,touch)
 attachClient(fixture)
 drain()
 return fixture
end
local function signalSemantics(behavior)
 local fixture=freshEnvironment(behavior)
 local owner=Instance.new("Folder",workspace)
 local explicitCount=0
 local connection=owner:GetAttributeChangedSignal("Probe"):Connect(function()explicitCount+=1 end)
 owner:SetAttribute("Probe",1);connection:Disconnect();drain()
 local explicitWanted=if behavior=="Immediate"then 1 else 0
 assert(explicitCount==explicitWanted,"explicit Disconnect pending cancellation")
 local implicitCount=0
 owner=Instance.new("Folder",workspace)
 owner:GetAttributeChangedSignal("Probe"):Connect(function()implicitCount+=1 end)
 owner:SetAttribute("Probe",1);owner:Destroy();drain()
 assert(implicitCount==1,"implicit Destroy preserves queued external callback")
 local selfDestroyCount=0
 local ownerScript=Instance.new("LocalScript",fixture.player:FindFirstChild("PlayerScripts"))
 runInSource(ownerScript,function()
  ownerScript.Destroying:Connect(function()selfDestroyCount+=1 end)
 end)
 ownerScript:Destroy();drain()
 local selfWanted=if behavior=="Immediate"then 1 else 0
 assert(selfDestroyCount==selfWanted,"own deferred Destroying callback must not execute")
 print("BOUNDARY "..behavior.." explicit="..explicitCount..";implicit="..implicitCount..";selfDestroying="..selfDestroyCount)
end
local maps={{"MAGE","A","ICE",7},{"MAGE","B","FIRE",7},{"MAGE","C","LIGHTNING",5},
 {"WARRIOR","C","DIVINE",8},{"ZOMBIE","C","CURSE",7}}
for _,behavior in ipairs({"Immediate","Deferred"})do
 signalSemantics(behavior)
 for _,touch in ipairs({false,true})do
  for _,map in ipairs(maps)do
   local fixture=freshEnvironment(behavior,nil,touch)
   fixture.player:SetAttribute("EGGRUMBLE_Role",map[1])
   attachClient(fixture);drain()
   setCast(fixture,map[1],map[2],1)
   local detail=(if touch then"touch"else"pc")..";element="..lastCue().name
   check("LIVE_"..map[1].."_"..map[2],cueCount(),1,1,detail)
   local beams=if touch then 4 else map[4]
   check("BEAMS_"..map[3],beamCount(),beams,beams,detail)
  end
 end
 do
  local fixture=attach(behavior,"MAGE:A:50")
  check("ATTACH_NO_IMMEDIATE_REPLAY",cueCount(),0,0)
  setCast(fixture,"MAGE","B",49)
  check("ATTACH_REJECT_OBSERVED_OLDER",cueCount(),1,0)
  setCast(fixture,"MAGE","C",51)
  check("ATTACH_ALLOW_HIGHER",#cueHistory,2,1)
 end
 do
  local fixture=attach(behavior,"BEAST:A:80")
  setCast(fixture,"MAGE","A",79)
  check("ATTACH_SEEDS_OLD_ROLE_UNMAPPED_CAST",#cueHistory,1,0)
  setCast(fixture,"MAGE","B",81)
  check("ROLE_CHANGE_GLOBAL_SEQUENCE_CONTINUES",#cueHistory,2,1)
 end
 do
  local fixture=freshEnvironment(behavior)
  fixture.world=makeWorld(fixture.lobby,"BATTLE_ROYALE","ACTIVE")
  fixture.player:SetAttribute("EGGRUMBLE_QueuedMode","BATTLE_ROYALE")
  attachClient(fixture);drain()
  setCast(fixture,"MAGE","A",1)
  check("BATTLE_ROYALE_EXISTING_WORLD_LIVE",cueCount(),1,1)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",7)
  setCast(fixture,"MAGE","A",7)
  setCast(fixture,"MAGE","B",7)
  setCast(fixture,"MAGE","C",6)
  setCast(fixture,"MAGE","C",8)
  check("DUPLICATE_AND_LOWER_REJECTED",#cueHistory,2,2)
  fixture.player:SetAttribute("EGGRUMBLE_SkillCastSignature","MAGE:A:2147483648");drain()
  fixture.player:SetAttribute("EGGRUMBLE_SkillCastSignature","MAGE:A:NaN");drain()
  fixture.player:SetAttribute("EGGRUMBLE_SkillCastSignature","MAGE:A:0");drain()
  fixture.player:SetAttribute("EGGRUMBLE_SkillCastSignature","WARRIOR:C:9");drain()
  fixture.player:SetAttribute("EGGRUMBLE_SkillCastSignature","MAGE:A:9:extra");drain()
  check("INVALID_OR_ROLE_MISMATCH_REJECTED",#cueHistory,2,2)
 end
 do
  local fixture=attach(behavior)
  fixture.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED");drain()
  setCast(fixture,"MAGE","A",1)
  check("FINISHED_WORLD_REJECT",cueCount(),1,0)
 end
 do
  local fixture=attach(behavior)
  fixture.player:SetAttribute("EGGRUMBLE_QueuedMode",nil);drain()
  setCast(fixture,"MAGE","A",1)
  check("UNQUEUED_PLAYER_REJECT",cueCount(),1,0)
 end
 do
  local fixture=attach(behavior)
  fixture.world:Destroy();drain()
  setCast(fixture,"MAGE","A",1)
  check("ABSENT_ARENA_REJECT",cueCount(),1,0)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1)
  local core=fixture.world:FindFirstChild("Castle_42"):FindFirstChild("StandardCore")
  core.Color=Color3.fromRGB(59,54,55);drain()
  check("FALLEN_OWN_CASTLE_CLEARS",cueCount(),1,0)
  setCast(fixture,"MAGE","B",2)
  check("FALLEN_OWN_CASTLE_REJECTS",#cueHistory,2,1)
 end
 do
  local fixture=attach(behavior)
  fixture.world:FindFirstChild("Castle_42"):Destroy();drain()
  setCast(fixture,"MAGE","A",1)
  check("ABSENT_OWN_CASTLE_REJECTS",cueCount(),1,0)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1)
  fixture.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED");drain()
  check("DELIVERED_FINISH_CLEARS_CUE",cueCount(),1,0)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","C",1,false)
  fixture.world:Destroy()
  fixture.world=makeWorld(fixture.lobby,"TEAM","ACTIVE")
  drain()
  check("CONCRETE_WORLD_REPLACEMENT_RETIRES_OLD",cueCount(),1,0)
  setCast(fixture,"MAGE","A",2)
  check("NEW_WORLD_FRESH_SEQUENCE",#cueHistory,2,if behavior=="Immediate"then 2 else 1)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1,false)
  fixture.character,fixture.humanoid,fixture.root=makeAvatar(fixture.player,100)
  drain()
  local renderedX=if lastCue()then lastCue().position.X else -1
  check("CONCRETE_AVATAR_REPLACEMENT_RETIRES_OLD",cueCount(),1,0,"lastRenderedX="..renderedX)
  setCast(fixture,"MAGE","B",2)
  check("NEW_AVATAR_FRESH_SEQUENCE",#cueHistory,2,if behavior=="Immediate"then 2 else 1)
 end
 do
  local fixture=attach(behavior)
  -- CharacterRemoving may be delivered before Character/Parent/Health changes.
  -- This explicit boundary input does not claim a particular Studio schedule.
  fixture.player.CharacterRemoving:Fire(fixture.character);drain()
  assert(fixture.player.Character==fixture.character and fixture.character.Parent==workspace and fixture.humanoid.Health>0)
  setCast(fixture,"MAGE","A",1)
  check("DELIVERED_REMOVING_CHARACTER_REJECTS",cueCount(),1,0)
  fixture.character,fixture.humanoid,fixture.root=makeAvatar(fixture.player,100);drain()
  setCast(fixture,"MAGE","B",2)
  check("NEW_ADDED_CHARACTER_AFTER_REMOVING_LIVE",#cueHistory,2,1)
 end
 do
  local fixture=attach(behavior)
  fixture.player.CharacterRemoving:Connect(function(removing)
   if removing==fixture.character then setCast(fixture,"MAGE","A",1,false)end
  end)
  fixture.player.CharacterRemoving:Fire(fixture.character);drain()
  check("REENTRANT_REMOVING_LISTENER_CAST_REJECTS",cueCount(),1,0)
 end
 do
  local fixture=attach(behavior)
  local oldCharacter=fixture.character
  fixture.character,fixture.humanoid,fixture.root=makeAvatar(fixture.player,100);drain()
  setCast(fixture,"MAGE","A",1)
  fixture.player.CharacterRemoving:Fire(oldCharacter);drain()
  check("DELAYED_OLD_REMOVING_PRESERVES_NEW_CUE",cueCount(),1,1)
  setCast(fixture,"MAGE","B",2)
  check("DELAYED_OLD_REMOVING_CURRENT_CAST_STILL_LIVE",#cueHistory,2,2)
 end
 do
  local fixture=attach(behavior)
  local oldCharacter=fixture.character
  fixture.character,fixture.humanoid,fixture.root=makeAvatar(fixture.player,100);drain()
  fixture.player.CharacterRemoving:Fire(fixture.character);drain()
  fixture.player.CharacterAdded:Fire(oldCharacter);drain()
  setCast(fixture,"MAGE","A",1)
  check("DELAYED_OLD_ADDED_CANNOT_REVIVE_REMOVING_CURRENT",cueCount(),1,0)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1,false)
  fixture.root.Parent=nil
  local replacement=Instance.new("Part");replacement.Name="HumanoidRootPart"
  replacement.Position=vector(300,0,0);replacement.Parent=fixture.character
  fixture.root=replacement;drain()
  check("CONCRETE_ROOT_REPLACEMENT_RETIRES_OLD",cueCount(),1,0)
  setCast(fixture,"MAGE","B",2)
  check("NEW_ROOT_FRESH_SEQUENCE",#cueHistory,2,if behavior=="Immediate"then 2 else 1)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1,false)
  local oldPlayer=fixture.player
  oldPlayer.Parent=nil
  local replacement=makePlayer(oldPlayer.UserId,200)
  Players.LocalPlayer=replacement
  drain()
  check("SAME_USERID_NEW_PLAYER_RETIRES_OLD",cueCount(),1,0)
  check("SAME_USERID_IS_DISTINCT_INSTANCE",oldPlayer==replacement,false,false)
  check("OBSERVED_PLAYER_EXIT_DISCONNECTS_OWNED",ownedConnectionCount(fixture.client),1,0)
 end
 do
  local fixture=attach(behavior)
  local before=ownedConnectionCount(fixture.client)
  for index=1,12 do
   workspace.CurrentCamera=Instance.new("Camera",workspace);drain()
  end
  local after=ownedConnectionCount(fixture.client)
  check("REBINDS_KEEP_CONNECTIONS_BOUNDED",after<=before,true,true,"before="..before..";after="..after)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",40)
  fixture.humanoid.Health=0;drain()
  check("DELIVERED_DEATH_CLEARS_CUE",cueCount(),1,0)
  setCast(fixture,"MAGE","B",41)
  fixture.character,fixture.humanoid,fixture.root=makeAvatar(fixture.player,50);drain()
  setCast(fixture,"MAGE","C",41)
  check("DEATH_OBSERVED_SEQUENCE_NOT_REUSED",#cueHistory,1,1)
  setCast(fixture,"MAGE","A",42)
  check("RESPAWN_GLOBAL_SEQUENCE_CONTINUES",#cueHistory,2,2)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1)
  fixture.character:SetAttribute("EGGRUMBLE_Downed",true);drain()
  check("DOWNED_AVATAR_CLEARS_CUE",cueCount(),1,0)
  setCast(fixture,"MAGE","B",2)
  check("DOWNED_AVATAR_REJECTS",#cueHistory,2,1)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1)
  workspace.CurrentCamera=Instance.new("Camera",workspace);drain()
  check("DELIVERED_CAMERA_REPLACEMENT_CLEARS",cueCount(),1,0)
  workspace.CurrentCamera=nil;drain()
  setCast(fixture,"MAGE","B",2)
  check("NO_CAMERA_REJECTS_NEW_CUE",#cueHistory,1,1)
  workspace.CurrentCamera=Instance.new("Camera",workspace);drain()
  setCast(fixture,"MAGE","C",3)
  check("CAMERA_RETURN_FRESH_SEQUENCE",#cueHistory,2,2)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",100)
  advance(.9)
  fixture.client:Destroy();drain()
  attachClient(fixture);drain()
  check("REATTACH_SAME_MODULE_CACHE",moduleLoads,1,1)
  setCast(fixture,"MAGE","B",99)
  check("REATTACH_SEEDS_CURRENT_OBSERVED_SIGNATURE",#cueHistory,2,1)
  setCast(fixture,"MAGE","C",101)
  check("REATTACH_HIGHER_SEQUENCE_ACCEPTED",#cueHistory,3,2)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",100)
  advance(.9)
  fixture.world:SetAttribute("EGGRUMBLE_MatchPhase","FINISHED");drain()
  fixture.world:Destroy();drain()
  fixture.world=makeWorld(fixture.lobby,"TEAM","ACTIVE");drain()
  setCast(fixture,"MAGE","B",1)
  check("ROUND_DOES_NOT_RESET_GLOBAL_SEQUENCE",#cueHistory,1,1)
  setCast(fixture,"MAGE","C",101)
  check("ROUND_HIGHER_SEQUENCE_ACCEPTED",#cueHistory,2,2)
 end
 do
  local fixture=attach(behavior)
  setCast(fixture,"MAGE","A",1)
  fixture.client:Destroy();drain()
  -- Deferred self-Destroying cannot guarantee synchronous teardown. All that
  -- must survive loss of the source script is the external Debris deadline.
  local maxNow=if behavior=="Deferred"then 1 else 0
  if expectation=="proposal"then assert(cueCount()<=maxNow,"script exit immediate contract")end
  advance(.9)
  check("DESTROYED_SCRIPT_DEBRIS_FALLBACK",cueCount(),0,0)
 end
 do
  local fixture=attach(behavior)
  local visual=require(fixture.module)
  assert(visual.render("DIVINE","SHIELD","NORMAL",vector(0,0,0),false))
  fixture.client.Disabled=true
  fixture.client.Enabled=false
  drain()
  advance(.899)
  local before=cueCount()
  advance(.001)
  check("DISABLED_SCRIPT_MAX_DURATION_FALLBACK",cueCount(),0,0,"beforeDeadline="..before)
 end
end
local rendererCases=0
local function rendererCase(label,originalPass,callback)
 local fixture=freshEnvironment("Immediate")
 local visual=require(fixture.module)
 local passed,detail=pcall(callback,visual)
 rendererCases+=1
 check(label,passed,originalPass,true,tostring(detail):gsub("\n"," "))
end
local function onlyCue()
 for _,object in ipairs(objects)do
  if isCue(object)and not object._destroyed and isDescendant(object,workspace)then return object end
 end
 error("expected one owned cue")
end
rendererCase("STRICT_LIVE_ANCHOR_LIMIT",false,function(visual)
 for index=1,9 do assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false))end
 assert(peakCues<=8,"peak anchors="..peakCues)
 assert(cueCount()==8 and beamCount()==56,"settled budget")
 advance(.63)
 assert(cueCount()==0 and beamCount()==0,"Debris expiry")
 return"peak="..peakCues..";settled=8;expired=0"
end)
rendererCase("CLEAR_OWNED_IDEMPOTENT",false,function(visual)
 assert(type(visual.clear)=="function","missing clear API")
 local unrelated=Instance.new("Part",workspace);unrelated.Name="Unrelated"
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false))
 assert(visual.render("DIVINE","SHIELD","NORMAL",vector(0,0,0),false))
 visual.clear();visual.clear()
 assert(cueCount()==0 and beamCount()==0,"owned effects not cleared")
 assert(unrelated.Parent==workspace and not unrelated._destroyed,"unowned object touched")
 advance(1)
 assert(unrelated.Parent==workspace and cueCount()==0,"old expiry after clear")
 return"owned=0;unrelated=preserved;repeat=safe"
end)
rendererCase("DETACHED_OWNER_PRUNED",false,function(visual)
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false))
 local detached=onlyCue();detached.Parent=nil
 assert(not detached._destroyed,"detach differs from destroy")
 assert(visual.render("WATER","ATTACK","NORMAL",vector(0,0,0),false))
 assert(detached._destroyed,"detached owner retained")
 assert(cueCount()==1,"new cue alive")
 visual.clear()
 assert(cueCount()==0 and beamCount()==0,"owned children leaked")
 return"detached=destroyed;new=unaffected"
end)
rendererCase("EXPIRED_REFERENCES_PRUNED",false,function(visual)
 for index=1,8 do assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false))end
 local expired={}
 for _,object in ipairs(objects)do if isCue(object)then table.insert(expired,object)end end
 advance(.63);assert(cueCount()==0)
 assert(visual.render("WATER","ATTACK","NORMAL",vector(0,0,0),false))
 local calls={}
 for _,object in ipairs(expired)do calls[object]=object._destroyCalls end
 visual.clear()
 for _,object in ipairs(expired)do assert(object._destroyCalls==calls[object],"clear still retains expired reference")end
 assert(cueCount()==0 and beamCount()==0)
 return"expired references absent from later clear"
end)
rendererCase("OLD_EXPIRY_CANNOT_CLEAR_NEW_CUE",false,function(visual)
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false))
 advance(.2);visual.clear()
 assert(visual.render("WATER","SHIELD","NORMAL",vector(0,0,0),false))
 local current=onlyCue()
 advance(.43)
 assert(cueCount()==1 and not current._destroyed,"old expiry affected new cue")
 advance(.48)
 assert(cueCount()==0 and beamCount()==0,"new expiry retained")
 return"old .62s expiry isolated;new .9s lifetime preserved"
end)
rendererCase("CAMERA_OWNER_CAN_CLEAR_AND_RESUME",false,function(visual)
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false))
 workspace.CurrentCamera=nil;visual.clear()
 assert(cueCount()==0 and beamCount()==0,"camera owner cleanup")
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false)==false)
 workspace.CurrentCamera=Instance.new("Camera",workspace)
 assert(visual.render("ICE","ATTACK","NORMAL",vector(0,0,0),true))
 assert(cueCount()==1 and beamCount()==4,"renderer cannot resume")
 visual.clear()
 return"camera cleanup;renderer reusable"
end)
rendererCase("ALL_RENDER_BUDGETS_AND_LIFETIMES",true,function(_visual)
 local renders=0
 for _,element in ipairs({"FIRE","WATER","LIGHTNING","WIND","EARTH","ICE","DIVINE","CURSE"})do
  for _,kind in ipairs({"WEAPON","ATTACK","SHIELD"})do
   for _,outcome in ipairs({"NORMAL","ADVANTAGE","RESIST","IMMUNE"})do
    for _,touch in ipairs({false,true})do
     local fixture=freshEnvironment("Immediate")
     local visual=require(fixture.module)
     assert(visual.render(element,kind,outcome,vector(0,0,0),touch))
     renders+=1
     assert(cueCount()==1 and peakCues==1,"one cue per actual render")
     assert(beamCount()>=1 and beamCount()<=(if touch then 4 else 8),"actual beam cap")
     assert(#debrisQueue==1 and debrisQueue[1].deadline>0 and debrisQueue[1].deadline<=.9,"external Debris deadline")
     advance(debrisQueue[1].deadline+.001)
     assert(cueCount()==0 and beamCount()==0,"complete descendant expiry")
    end
   end
  end
 end
 assert(renders==192)
 return"actual renders=192;all budgets;all expiry"
end)
rendererCase("INVALID_SERVER_AND_NIL_CAMERA",true,function(visual)
 local before=#objects
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0/0,0,0),false)==false)
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(math.huge,0,0),false)==false)
 assert(visual.render("FIRE","ATTACK","NORMAL","bad",false)==false)
 assert(visual.render("UNKNOWN","ATTACK","NORMAL",vector(0,0,0),false)==false)
 assert(visual.render("FIRE","UNKNOWN","NORMAL",vector(0,0,0),false)==false)
 assert(visual.render("FIRE","ATTACK","UNKNOWN",vector(0,0,0),false)==false)
 runtimeClient=false
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false)==false)
 runtimeClient=true;workspace.CurrentCamera=nil
 assert(visual.render("FIRE","ATTACK","NORMAL",vector(0,0,0),false)==false)
 assert(#objects==before,"rejected input allocated instances")
 return"invalid/server/nil-camera allocations=0"
end)
print("GQ778_FULL_BODY_COMPLETE sourceMode="..expectation..";assertions="..scenarioCount..";gapChecks="..gapCount
 ..";rendererCases="..rendererCases..";rendererMatrix=192;NOT_STUDIO_NOT_RC_ACCEPTANCE")
