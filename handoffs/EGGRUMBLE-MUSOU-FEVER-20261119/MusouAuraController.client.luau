--!strict
-- #824: Observer-local, server-attribute driven, no client-owned burst or damage authority.
-- Designed for existing StarterPlayerScripts alongside current EGGRUMBLE_CombatFeel.
local Players=game:GetService("Players")
local Aura=require(script.Parent:WaitForChild("EGGRUMBLE_MusouAuraClient"))
local connections:{[Player]:{RBXScriptConnection}}={}
local function render(user:Player)
 local character=user.Character
 if not character then return end
 local phase=user:GetAttribute("EGGRUMBLE_MusouPhase")
 local role=user:GetAttribute("EGGRUMBLE_MusouRole")
 local remaining=user:GetAttribute("EGGRUMBLE_MusouRemaining")
 local isValid=type(phase)=="string" and (phase=="MUSOU" or phase=="RUSH" or phase=="KAKUHEN")
  and type(role)=="string" and type(remaining)=="number" and remaining>0
 if not isValid then
  Aura.stop(character)
  return
 end
 Aura.update(character,{active=true,phase=phase,role=role,remaining=remaining})
end
local function watch(user:Player)
 if connections[user] then return end
 local arr={}
 connections[user]=arr
 table.insert(arr,user.CharacterAdded:Connect(function(character)
  task.defer(function()
   if user.Character==character then render(user) end
  end)
 end))
 table.insert(arr,user.CharacterRemoving:Connect(function(character) Aura.stop(character) end))
 for _,name in ipairs({"EGGRUMBLE_MusouPhase","EGGRUMBLE_MusouRole","EGGRUMBLE_MusouRemaining"}) do
  table.insert(arr,user:GetAttributeChangedSignal(name):Connect(function() render(user) end))
 end
 render(user)
end
local function unwatch(user:Player)
 local arr=connections[user]
 if arr then
  for _,signal in ipairs(arr) do signal:Disconnect() end
  connections[user]=nil
 end
 if user.Character then Aura.stop(user.Character) end
end
Players.PlayerAdded:Connect(watch)
Players.PlayerRemoving:Connect(unwatch)
for _,user in ipairs(Players:GetPlayers()) do watch(user) end
