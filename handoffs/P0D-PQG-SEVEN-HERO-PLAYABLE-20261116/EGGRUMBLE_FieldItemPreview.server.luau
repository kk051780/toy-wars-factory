--!strict
-- ITEM-LANE independent private Studio preview. Run alone, never alongside V3 lobby host.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Items=require(script.Parent:WaitForChild("EGGRUMBLE_FieldItemPickups"))
local world=Instance.new("Folder");world.Name="EGGRUMBLE_ItemPreviewWorld";world.Parent=workspace
local roster={}
local Players=game:GetService("Players")
local function register(player:Player)
 roster[tostring(player.UserId)]={alive=true}
end
Players.PlayerAdded:Connect(register)
for _,player in ipairs(Players:GetPlayers()) do register(player) end
Players.PlayerRemoving:Connect(function(p) roster[tostring(p.UserId)]=nil end)
local spawn=workspace:FindFirstChildWhichIsA("SpawnLocation",true)
local origin=spawn and spawn.Position or Vector3.new(0,5,0)
local positions={}
for i=1,9 do
 local x=((i-1)%3-1)*13
 local z=math.floor((i-1)/3)*13+15
 local at=origin+Vector3.new(x,0,z)
 local floor=Instance.new("Part");floor.Name="ItemPreviewFloor_"..i
 floor.Size=Vector3.new(12,1,12);floor.Anchored=true;floor.Position=at-Vector3.new(0,3,0)
 floor.Color=Color3.fromRGB(83,107,90);floor.Parent=world
 table.insert(positions,at+Vector3.new(0,1.5,0))
end
Items.start({world=world,rules={phase="ACTIVE",castles=roster}},positions)
print("[EGGRUMBLE ITEM] private 9-item HEAL/DASH/SHIELD preview ready")
