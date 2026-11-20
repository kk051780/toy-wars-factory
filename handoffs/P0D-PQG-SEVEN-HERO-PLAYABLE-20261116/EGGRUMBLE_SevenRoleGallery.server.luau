--!strict
-- Private Studio visual gallery; not playable rig, not production characters.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Kit=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleVisualKit"))
local gallery=Instance.new("Folder");gallery.Name="EGGRUMBLE_SevenRoleGallery";gallery.Parent=workspace
local floor=Instance.new("Part");floor.Name="GalleryFloor";floor.Anchored=true
floor.Size=Vector3.new(120,2,45);floor.Position=Vector3.new(0,-1,0);floor.Parent=gallery
for i,id in ipairs(Kit.roleIds()) do
 local x=(i-4)*15
 Kit.build(gallery,Vector3.new(x,0,-8),id)
end
local spawn=Instance.new("SpawnLocation");spawn.Name="GallerySpawn"
spawn.Anchored=true;spawn.Neutral=true;spawn.Size=Vector3.new(10,1,10)
spawn.Position=Vector3.new(0,.6,15);spawn.Parent=gallery
print("[EGGRUMBLE CHARACTER] seven independent class silhouette prototypes")
