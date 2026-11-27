--!strict
-- #824: Observer-local, server-attribute driven, no client-owned burst or damage authority.
-- Bind each current character's Head lifetime without another render loop or server writer.
local Players=game:GetService("Players")
local Aura=require(script.Parent:WaitForChild("EGGRUMBLE_MusouAuraClient"))
local connections:{[Player]:{RBXScriptConnection}}={}
type CharacterBinding={
 character:Model,
 head:BasePart?,
 origin:Instance?,
 watchConnections:{RBXScriptConnection},
 signals:{RBXScriptConnection},
}
local bindings:{[Player]:CharacterBinding}={}

local function clearAura(binding:CharacterBinding)
 -- The old Head may already be detached, beyond Aura.stop's current-Head lookup.
 local origin=binding.origin
 binding.origin=nil
 if origin then origin:Destroy() end
 Aura.stop(binding.character)
end

local function render(user:Player,binding:CharacterBinding)
 if connections[user]~=binding.watchConnections or bindings[user]~=binding
  or user.Parent~=Players or user.Character~=binding.character then return end
 local character=binding.character
 local candidate=character:FindFirstChild("Head")
 local head:BasePart?=nil
 if candidate and candidate:IsA("BasePart") then head=candidate end
 if binding.head~=head then
  clearAura(binding)
  binding.head=head
 end
 local phase=user:GetAttribute("EGGRUMBLE_MusouPhase")
 local role=user:GetAttribute("EGGRUMBLE_MusouRole")
 local remaining=user:GetAttribute("EGGRUMBLE_MusouRemaining")
 local isValid=type(phase)=="string" and (phase=="MUSOU" or phase=="RUSH" or phase=="KAKUHEN")
  and type(role)=="string" and type(remaining)=="number" and remaining>0
 if not isValid or not head then
  clearAura(binding)
  return
 end
 Aura.update(character,{active=true,phase=phase,role=role,remaining=remaining})
 -- A role change replaces the attachment even when this Head is unchanged.
 binding.origin=head:FindFirstChild("MusouAuraOrigin")
end

local function retireCharacter(user:Player)
 local binding=bindings[user]
 if not binding then return end
 -- Invalidate before cleanup so deferred callbacks cannot recreate retired visuals.
 bindings[user]=nil
 for _,signal in ipairs(binding.signals) do signal:Disconnect() end
 clearAura(binding)
 binding.head=nil
end

local function bindCharacter(user:Player,character:Model,arr:{RBXScriptConnection},deferred:boolean)
 if connections[user]~=arr or user.Parent~=Players or user.Character~=character then return end
 local previous=bindings[user]
 if previous and previous.character==character then
  render(user,previous)
  return
 end
 retireCharacter(user)
 local binding:CharacterBinding={character=character,head=nil,origin=nil,watchConnections=arr,signals={}}
 bindings[user]=binding
 local function headChanged(child:Instance)
  if child==binding.head or (child.Name=="Head" and child:IsA("BasePart")) then
   render(user,binding)
  end
 end
 -- Subscribe before the first render; parts can arrive after CharacterAdded.
 table.insert(binding.signals,character.ChildAdded:Connect(headChanged))
 table.insert(binding.signals,character.ChildRemoved:Connect(headChanged))
 if deferred then
  task.defer(function() render(user,binding) end)
 else
  render(user,binding)
 end
end

local function watch(user:Player)
 if connections[user] or user.Parent~=Players then return end
 local arr:{RBXScriptConnection}={}
 connections[user]=arr
 table.insert(arr,user.CharacterAdded:Connect(function(character)
  bindCharacter(user,character,arr,true)
 end))
 table.insert(arr,user.CharacterRemoving:Connect(function(character)
  if connections[user]~=arr then return end
  local binding=bindings[user]
  if binding and binding.character==character then retireCharacter(user) end
 end))
 for _,name in ipairs({"EGGRUMBLE_MusouPhase","EGGRUMBLE_MusouRole","EGGRUMBLE_MusouRemaining"}) do
  table.insert(arr,user:GetAttributeChangedSignal(name):Connect(function()
   if connections[user]~=arr then return end
   local binding=bindings[user]
   if binding then render(user,binding) end
  end))
 end
 if user.Character then bindCharacter(user,user.Character,arr,false) end
end

local function unwatch(user:Player)
 local arr=connections[user]
 connections[user]=nil
 if arr then
  for _,signal in ipairs(arr) do signal:Disconnect() end
 end
 retireCharacter(user)
end
Players.PlayerAdded:Connect(watch)
Players.PlayerRemoving:Connect(unwatch)
for _,user in ipairs(Players:GetPlayers()) do watch(user) end
