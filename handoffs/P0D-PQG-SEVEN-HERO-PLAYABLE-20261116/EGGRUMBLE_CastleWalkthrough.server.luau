--!strict
-- Independent Studio castle walkthrough; not a competitive castle or live egg service.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Castle=require(script.Parent:WaitForChild("EGGRUMBLE_EnterableCastleInterior"))
local c=Castle.build(workspace,Vector3.new(0,1,0),Color3.fromRGB(225,96,89))
local spawn=Instance.new("SpawnLocation");spawn.Name="CastleWalkthroughSpawn"
spawn.Anchored=true;spawn.Neutral=true;spawn.Size=Vector3.new(10,1,10)
spawn.Position=Vector3.new(0,1.6,-37);spawn.Parent=workspace
print("[EGGRUMBLE CASTLE] private gate walkthrough",c.entryWidth,c.footprint)
