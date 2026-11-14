--!strict
-- FB-016 P0: Prevent camera from being buried in thick opaque tree crowns.
-- Client-only LOD fade; never modifies physics, UI, damage or other players.
local RunService=game:GetService("RunService")
if not RunService:IsStudio() then return end
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
    if obj:IsA("BasePart") and isLeaf(obj.Name) then tracked[obj]=true end
end
for _,obj in ipairs(root:GetDescendants()) do add(obj) end
root.DescendantAdded:Connect(add)
root.DescendantRemoving:Connect(function(obj)
    if obj:IsA("BasePart") and tracked[obj] then
        obj.LocalTransparencyModifier=0
        tracked[obj]=nil
    end
end)
local elapsed=0
RunService.RenderStepped:Connect(function(dt:number)
    elapsed+=math.min(dt,.25)
    if elapsed<.12 then return end
    elapsed=0
    local cam=workspace.CurrentCamera
    if not cam then return end
    local cameraPos=cam.CFrame.Position
    for p,_ in pairs(tracked) do
        if not p:IsDescendantOf(root) then
            tracked[p]=nil
        else
            -- Crowns may be much larger than the avatar and entirely swallow
            -- a third-person camera. Fade only nearby crowns, restore when far.
            local radius=math.max(p.Size.X,p.Size.Y,p.Size.Z)*.5
            local dist=(p.Position-cameraPos).Magnitude
            p.LocalTransparencyModifier=if dist<radius+9 then .96 else 0
        end
    end
end)
