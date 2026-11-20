--!strict
-- Independent FIELD art Studio test. Do not run alongside the V3 match host.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Kit=require(script.Parent:WaitForChild("EGGRUMBLE_ValleyLandmarkKit"))
local origin=Vector3.new(0,2,0)
local result=Kit.build(workspace,origin,20261116)
local spawn=Instance.new("SpawnLocation")
spawn.Name="FIELD_ArtPreviewSpawn";spawn.Size=Vector3.new(12,1,12)
spawn.Anchored=true;spawn.Neutral=true;spawn.Position=origin+Vector3.new(0,0.6,-118)
spawn.Parent=workspace
print("[EGGRUMBLE FIELD] private scenic test; bridges=",result.bridgeCount," parts=",result.partCount)
