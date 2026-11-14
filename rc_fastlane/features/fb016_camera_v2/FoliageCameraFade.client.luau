--!strict
-- FB-016 / FB-015 ART-SIGHTLINE V2: reveal a player obscured by nonblocking foliage.
-- Studio-only, client-only, no collision, character, damage, Remote, HUD or store writes.
-- This replaces only the earlier FB016 foliage camera script in a private candidate.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players=game:GetService("Players")
local player=Players.LocalPlayer
if not player then return end
local root=workspace:WaitForChild("TRAP_RAIDERS_S1",90)
if not root then return end

local tracked:{[BasePart]:boolean}={}
local function isLeaf(n:string):boolean
    return string.sub(n,1,13)=="FOREST_CROWN_"
        or string.sub(n,1,9)=="LeafMass_"
        or string.sub(n,1,13)=="BrushCluster_"
        or string.sub(n,1,10)=="RootFlare_"
        or string.sub(n,1,11)=="PALM_FROND_"
end
local function add(obj:Instance)
    if obj:IsA("BasePart") and isLeaf(obj.Name) then
        tracked[obj]=true
    end
end
for _,obj in ipairs(root:GetDescendants()) do add(obj) end
local added=root.DescendantAdded:Connect(add)
local removed=root.DescendantRemoving:Connect(function(obj)
    if obj:IsA("BasePart") and tracked[obj] then
        obj.LocalTransparencyModifier=0
        tracked[obj]=nil
    end
end)

-- Geometry-only segment test; does NOT raycast, edit CanCollide, or change pathfinding.
-- Large irregular crowns are approximated conservatively by their enclosing radius.
local function blocksAvatar(p:BasePart,cameraPos:Vector3,avatarPos:Vector3):boolean
    local ray=avatarPos-cameraPos
    local lengthSq=ray:Dot(ray)
    if lengthSq<.01 then return false end
    local t=(p.Position-cameraPos):Dot(ray)/lengthSq
    if t<=0 or t>=1 then return false end
    local closest=cameraPos+ray*t
    local radius=math.max(p.Size.X,p.Size.Y,p.Size.Z)*.5
    return (p.Position-closest).Magnitude<radius+2.5
end

local elapsed=0
local renderConn
renderConn=RunService.RenderStepped:Connect(function(dt:number)
    elapsed+=math.min(dt,.25)
    if elapsed<.12 then return end
    elapsed=0
    local camera=workspace.CurrentCamera
    if not camera then return end
    local cameraPos=camera.CFrame.Position
    local char=player.Character
    local hrp=if char then char:FindFirstChild("HumanoidRootPart") else nil
    local avatarPos:Vector3?=if hrp and hrp:IsA("BasePart") then hrp.Position else nil
    for p,_ in pairs(tracked) do
        if not p:IsDescendantOf(root) then
            p.LocalTransparencyModifier=0
            tracked[p]=nil
        else
            local radius=math.max(p.Size.X,p.Size.Y,p.Size.Z)*.5
            local nearCamera=(p.Position-cameraPos).Magnitude<radius+9
            local hidesAvatar=if avatarPos then blocksAvatar(p,cameraPos,avatarPos) else false
            -- Only foliage intersecting the gameplay view becomes translucent.
            -- Distant world, scenery and all combat objects remain untouched.
            p.LocalTransparencyModifier=if nearCamera or hidesAvatar then .93 else 0
        end
    end
end)
script.Destroying:Connect(function()
    if renderConn then renderConn:Disconnect() end
    added:Disconnect()
    removed:Disconnect()
    for p,_ in pairs(tracked) do
        if p.Parent then p.LocalTransparencyModifier=0 end
    end
    table.clear(tracked)
end)
print("FB016_ART_SIGHTLINE_V2_CAMERA_TO_AVATAR_FOLIAGE_ONLY_STUDIO")
