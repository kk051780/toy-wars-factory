--!strict
-- Standalone neutral boss Studio test. Does not touch existing game host.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Boss=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralStoneGiant"))
local floor=Instance.new("Part");floor.Name="NeutralBossTestArena"
floor.Anchored=true;floor.Size=Vector3.new(100,2,100)
floor.Position=Vector3.new(0,-1,0);floor.Color=Color3.fromRGB(92,121,87);floor.Parent=workspace
local spawn=Instance.new("SpawnLocation");spawn.Name="NeutralBossTestSpawn"
spawn.Anchored=true;spawn.Size=Vector3.new(12,1,12);spawn.Position=Vector3.new(0,0.6,-34);spawn.Neutral=true;spawn.Parent=workspace
local giant=Boss.spawn(workspace,Vector3.new(0,0,0))
print("[EGGRUMBLE NEUTRAL] Giant preview",giant.maxHealth,giant.windup,giant.attackRadius)
