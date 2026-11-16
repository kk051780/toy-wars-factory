--!strict
-- Isolated Musou combo playtest: prompts + 18 dummies; no authoritative RC edits.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
if not RunService:IsStudio() then return end
local Combo=require(script.Parent:WaitForChild("EGGRUMBLE_MusouComboPreview"))
local scene=Instance.new("Folder");scene.Name="EGGRUMBLE_ComboPlaytest";scene.Parent=workspace
local floor=Instance.new("Part");floor.Name="ArenaFloor";floor.Anchored=true
floor.Size=Vector3.new(90,2,90);floor.Position=Vector3.new(0,-1,0)
floor.Color=Color3.fromRGB(79,115,83);floor.Parent=scene
local spawn=Instance.new("SpawnLocation");spawn.Name="ComboSpawn";spawn.Anchored=true
spawn.Neutral=true;spawn.Size=Vector3.new(10,1,10);spawn.Position=Vector3.new(0,0.6,15);spawn.Parent=scene
local targets={}
for i=1,18 do
 local theta=(i-1)*math.pi/9
 local radius=if i<=9 then 7 else 11
 local at=Vector3.new(math.sin(theta)*radius,3,math.cos(theta)*radius)
 local model=Instance.new("Model");model.Name="NeutralTraining_"..i;model:SetAttribute("EGGRUMBLE_NeutralTarget",true)
 local root=Instance.new("Part");root.Name="HumanoidRootPart";root.Size=Vector3.new(2,3,2)
 root.Anchored=true;root.CanCollide=false;root.Position=at;root.Color=Color3.fromRGB(173,92,86);root.Parent=model
 model.PrimaryPart=root
 local h=Instance.new("Humanoid");h.MaxHealth=200;h.Health=200;h.Parent=model
 model.Parent=scene;table.insert(targets,model)
end
local console=Instance.new("Part");console.Name="ComboTrainingConsole";console.Anchored=true
console.Size=Vector3.new(5,4,3);console.Position=Vector3.new(0,2,9)
console.Color=Color3.fromRGB(235,178,65);console.Parent=scene
local prompt=Instance.new("ProximityPrompt");prompt.ActionText="連撃";prompt.ObjectText="無双コンボ"
prompt.MaxActivationDistance=12;prompt.HoldDuration=0;prompt.Parent=console
prompt.Triggered:Connect(function(player:Player)
 local result=Combo.attack(player,targets,scene)
 if result.ok then print("[COMBO]",player.UserId,result.step,result.hits) end
end)
Players.PlayerRemoving:Connect(function(player) Combo.clear(player) end)
print("[EGGRUMBLE BATTLE] 18 neutral targets, 3-hit combo, max 12 hits per strike")
