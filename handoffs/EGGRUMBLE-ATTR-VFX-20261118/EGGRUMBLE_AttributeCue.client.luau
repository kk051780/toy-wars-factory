-- BATTLE-ATTR-VFX: local CAST presentation only; the existing server signature is the sole trigger.
-- No HIT/weakness/block claim, gameplay write, remote, polling, or fabricated match epoch.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local Input=game:GetService("UserInputService")
local player=Players.LocalPlayer
if not player then return end
local module=ReplicatedStorage:WaitForChild("EGGRUMBLE_ElementVisuals",10)
if not module or not module:IsA("ModuleScript") then return end
local ok,Visual=pcall(require,module)
if not ok or type(Visual)~="table" or type(Visual.clear)~="function" then return end

local WORLD_NAME="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local CAST_ATTRIBUTE="EGGRUMBLE_SkillCastSignature"
local FALLEN_CORE_COLOR=Color3.fromRGB(59,54,55)
local globalConnections={}
local bindingConnections={}
local running=true
local currentBinding=nil
local lastSequence=0
local retiringCharacter=nil

local function disconnectAll(connections)
 for _,connection in ipairs(connections) do connection:Disconnect() end
 table.clear(connections)
end
local function connect(connections,event,callback)
 table.insert(connections,event:Connect(callback))
end
local function observedSequence(signature)
 -- The H93 producer's UserId sequence continues across roles and rounds.
 -- Seed from its complete wire format even when that role has no live cue.
 local signatureRole=type(signature)=="string" and string.match(signature,"^([A-Z]+):")
 if not signatureRole then return nil end
 local _,sequence=Visual.elementForServerCast(signature,signatureRole)
 return sequence
end
local function seedCurrentSignature()
 local sequence=observedSequence(player:GetAttribute(CAST_ATTRIBUTE))
 if sequence and sequence>lastSequence then lastSequence=sequence end
end
local function currentPlayer()
 return Players.LocalPlayer==player and player.Parent==Players
end
local function stop()
 if not running then return end
 running=false
 currentBinding=nil
 disconnectAll(bindingConnections)
 disconnectAll(globalConnections)
 Visual.clear()
end

local function readBinding()
 local mode=player:GetAttribute("EGGRUMBLE_QueuedMode")
 local lobby=workspace:FindFirstChild(WORLD_NAME)
 local arena=lobby and (mode=="TEAM" or mode=="BATTLE_ROYALE")
  and lobby:FindFirstChild(mode.."_Arena") or nil
 local castle=arena and arena:FindFirstChild("Castle_"..tostring(player.UserId))
 local core=castle and castle:FindFirstChild("StandardCore")
 local character=player.Character
 local humanoid=character and character:FindFirstChildOfClass("Humanoid")
 local root=character and character:FindFirstChild("HumanoidRootPart")
 local camera=workspace.CurrentCamera
 local binding={mode=mode,role=player:GetAttribute("EGGRUMBLE_Role"),lobby=lobby,
  arena=arena,castle=castle,core=core,character=character,humanoid=humanoid,root=root,camera=camera}
 binding.valid=currentPlayer() and player:GetAttribute("EGGRUMBLE_Eliminated")~=true
  and lobby~=nil and lobby.Parent==workspace
  and arena~=nil and arena.Parent==lobby and arena:GetAttribute("EGGRUMBLE_MatchPhase")=="ACTIVE"
  and castle~=nil and castle:IsA("Model") and castle.Parent==arena
  and core~=nil and core:IsA("BasePart") and core.Parent==castle and core.Color~=FALLEN_CORE_COLOR
  and character~=nil and character~=retiringCharacter and character:IsDescendantOf(workspace)
  and character:GetAttribute("EGGRUMBLE_Downed")~=true
  and humanoid~=nil and humanoid.Parent==character and humanoid.Health>0
  and root~=nil and root:IsA("BasePart") and root.Parent==character
  and camera~=nil and camera:IsDescendantOf(workspace)
 return binding
end
local function sameLiveBinding(before,after)
 if not before.valid or not after.valid then return false end
 for _,key in ipairs({"mode","role","lobby","arena","castle","core","character","humanoid","root","camera"}) do
  if before[key]~=after[key] then return false end
 end
 return true
end

local refresh
local function onConfirmedServerCast(binding)
 if not running or binding~=currentBinding then return end
 local signature=player:GetAttribute(CAST_ATTRIBUTE)
 local sequence=observedSequence(signature)
 if not sequence or sequence<=lastSequence then return end
 -- Consume observed sequences even while dead/ineligible; never replay on return.
 lastSequence=sequence
 if not currentPlayer() then stop();return end
 if not sameLiveBinding(binding,readBinding()) then refresh();return end
 local element=Visual.elementForServerCast(signature,player:GetAttribute("EGGRUMBLE_Role"))
 if not element then return end
 local root=binding.root
 local where=root.Position+root.CFrame.LookVector*3+Vector3.new(0,2.5,0)
 Visual.render(element,"ATTACK","NORMAL",where,Input.TouchEnabled)
end
refresh=function()
 if not running then return end
 if not currentPlayer() then stop();return end
 -- Disconnect explicitly: queued callbacks for an old concrete binding retire.
 disconnectAll(bindingConnections)
 Visual.clear()
 seedCurrentSignature()
 local binding=readBinding()
 currentBinding=binding
 connect(bindingConnections,player:GetAttributeChangedSignal(CAST_ATTRIBUTE),function()
  onConfirmedServerCast(binding)
 end)
 local function watchAncestry(object)
  if object then connect(bindingConnections,object.AncestryChanged,refresh) end
 end
 local function watchChild(parent,name)
  if not parent then return end
  local function changed(child) if child.Name==name then refresh() end end
  connect(bindingConnections,parent.ChildAdded,changed)
  connect(bindingConnections,parent.ChildRemoved,changed)
 end
 watchChild(workspace,WORLD_NAME)
 if binding.mode=="TEAM" or binding.mode=="BATTLE_ROYALE" then
  watchChild(binding.lobby,binding.mode.."_Arena")
 end
 watchChild(binding.arena,"Castle_"..tostring(player.UserId))
 watchChild(binding.castle,"StandardCore")
 watchChild(binding.character,"HumanoidRootPart")
 if binding.character then
  local function humanoidChanged(child) if child:IsA("Humanoid") then refresh() end end
  connect(bindingConnections,binding.character.ChildAdded,humanoidChanged)
  connect(bindingConnections,binding.character.ChildRemoved,humanoidChanged)
  connect(bindingConnections,binding.character:GetAttributeChangedSignal("EGGRUMBLE_Downed"),refresh)
 end
 for _,object in pairs({binding.lobby,binding.arena,binding.castle,binding.core,
  binding.character,binding.humanoid,binding.root,binding.camera}) do watchAncestry(object) end
 if binding.arena then
  connect(bindingConnections,binding.arena:GetAttributeChangedSignal("EGGRUMBLE_MatchPhase"),refresh)
 end
 if binding.core and binding.core:IsA("BasePart") then
  connect(bindingConnections,binding.core:GetPropertyChangedSignal("Color"),refresh)
 end
 if binding.humanoid then connect(bindingConnections,binding.humanoid.Died,refresh) end
end

connect(globalConnections,player.AncestryChanged,function() if not currentPlayer() then stop() end end)
connect(globalConnections,Players:GetPropertyChangedSignal("LocalPlayer"),function()
 if not currentPlayer() then stop() end
end)
connect(globalConnections,player.CharacterAdded,function(character)
 if character~=player.Character or character==retiringCharacter then return end
 retiringCharacter=nil
 refresh()
end)
connect(globalConnections,player.CharacterRemoving,function(character)
 -- Removing is delivered before the current Character necessarily detaches.
 -- Retire that exact instance; a delayed old-character event cannot clear a new one.
 if character~=player.Character then return end
 retiringCharacter=character
 refresh()
end)
for _,attribute in ipairs({"EGGRUMBLE_QueuedMode","EGGRUMBLE_Role","EGGRUMBLE_Eliminated"}) do
 connect(globalConnections,player:GetAttributeChangedSignal(attribute),refresh)
end
connect(globalConnections,workspace:GetPropertyChangedSignal("CurrentCamera"),refresh)
connect(globalConnections,script.AncestryChanged,function()
 if not script:IsDescendantOf(player) then stop() end
end)
-- Best effort only: a Deferred self-Destroying callback may never run.
-- The module's external Debris timer independently bounds every cue to <=0.9 s.
connect(globalConnections,script.Destroying,stop)
-- High-water is retained for this LocalScript runtime. A later attachment seeds
-- the currently observed signature; no arbitrary network/reload replay proof.
refresh()
