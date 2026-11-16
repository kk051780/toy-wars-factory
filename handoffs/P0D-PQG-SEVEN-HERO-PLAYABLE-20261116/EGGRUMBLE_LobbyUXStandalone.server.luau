--!strict
-- Independent lobby UX preview. Never start production matchmaking.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Lobby=require(script.Parent:WaitForChild("EGGRUMBLE_LobbyUXPreview"))
local result=Lobby.build(workspace,Vector3.new(0,2,0))
local spawn=Instance.new("SpawnLocation");spawn.Name="LobbyUXPreviewSpawn"
spawn.Anchored=true;spawn.Neutral=true;spawn.Size=Vector3.new(12,1,12)
spawn.Position=Vector3.new(0,2.6,-38);spawn.Parent=workspace
print("[EGGRUMBLE LOBBY] private UX only",result.roles,result.portals)
