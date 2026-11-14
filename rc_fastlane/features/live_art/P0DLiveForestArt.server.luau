--!strict
-- P0 #431 / #420: private non-Studio live forest pilot for the ORIGINAL base MapBuilder.
-- Not Studio-only Owner361 expanded terrain. No changes to Arena/AI/Game/egg/HP/roads.
-- This script never opts itself in and is not a public-release authorization.
local RunService = game:GetService("RunService")
if not RunService:IsServer() then return end
local isStudio = RunService:IsStudio()
if isStudio then
    if script:GetAttribute("EnablePrivatePreview") ~= true then return end
else
    -- Server-only DataModel.PrivateServerId, not a client-side replicated property.
    if game.PrivateServerId == "" then return end
    if workspace:GetAttribute("P0D_PRIVATE_LIVE_FOREST") ~= true then return end
end
local root = workspace:WaitForChild("TRAP_RAIDERS_S1",45)
if not root then warn("LIVE_FOREST_NO_REAL_MAP"); return end
local grass = root:WaitForChild("GrassArena",15)
local road = root:FindFirstChild("CenterRoad")
local red = root:FindFirstChild("RED_CASTLE")
local blue = root:FindFirstChild("BLUE_CASTLE")
if not grass or not grass:IsA("BasePart")
    or not road or not road:IsA("BasePart")
    or not red or not blue then
    warn("LIVE_FOREST_REAL_MAP_ANCHORS_MISSING")
    return
end
-- A non-Studio game starts with the MapBuilder 250 x 142 arena.
-- Reject author-map drift instead of silently planting into objectives.
if grass.Size.X < 249 or grass.Size.Z < 141 then
    warn("LIVE_FOREST_MAP_GEOMETRY_UNEXPECTED")
    return
end
if root:FindFirstChild("P0D_PRIVATE_LIVE_FOREST_V1") then return end

local BUDGET = 60
local made = 0
local forest = Instance.new("Folder")
forest.Name = "P0D_PRIVATE_LIVE_FOREST_V1"
forest:SetAttribute("OwnerAccepted",false)
forest:SetAttribute("VisualOnly",true)
forest:SetAttribute("SourceQAOnly",true)
forest.Parent = root

local function deco(group:Instance, name:string, size:Vector3,
    cf:CFrame, color:Color3, material:Enum.Material, shape:string)
    assert(made < BUDGET, "P0D_LIVE_FOREST_BUDGET_EXCEEDED")
    local p:BasePart
    if shape == "WEDGE" then
        p = Instance.new("WedgePart")
    else
        local v = Instance.new("Part")
        if shape == "BALL" then v.Shape = Enum.PartType.Ball
        elseif shape == "CYLINDER" then v.Shape = Enum.PartType.Cylinder end
        p = v
    end
    p.Name = name
    p.Size = size
    p.CFrame = cf
    p.Color = color
    p.Material = material
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Parent = group
    made += 1
end

-- Keep 12-stud neutral center road, egg points z=-20, score pads z=20,
-- actual tower walls z=+/-44 and boundary walls z=+/-71 entirely clear.
-- Side-of-lane visuals only. No collision or raycast blockers.
local X_POS = {-96,-66,-36,36,66,96}
local south = Color3.fromRGB(176,112,157)
local north = Color3.fromRGB(68,139,134)
for _, side in ipairs({-1,1}) do
    local grove = Instance.new("Folder")
    grove.Name = if side < 0 then "NORTH_FROST_CEDAR" else "SOUTH_SUNSET_BLOSSOM"
    grove.Parent = forest
    local foliage = if side < 0 then north else south
    local tint = if side < 0 then Color3.fromRGB(92,174,145)
        else Color3.fromRGB(211,154,163)
    local crown = if side < 0 then Color3.fromRGB(48,111,105)
        else Color3.fromRGB(132,82,130)
    for i,x in ipairs(X_POS) do
        local z = side*55
        local h = if i%2==0 then 8 else 9
        local stem = CFrame.new(x, -1+h/2,z)
        local tag = tostring(i)
        deco(grove,"TRUNK_"..tag,Vector3.new(2.1,h,2.1),stem,
            Color3.fromRGB(92,78,72),Enum.Material.Wood,"CYLINDER")
        deco(grove,"CANOPY_LOW_"..tag,Vector3.new(10,7,9),
            CFrame.new(x, h+3,z),foliage,Enum.Material.SmoothPlastic,"BALL")
        deco(grove,"CANOPY_HIGH_"..tag,Vector3.new(7,6,7),
            CFrame.new(x+1,h+7,z),crown,Enum.Material.SmoothPlastic,"BALL")
        deco(grove,"CANOPY_SIDE_"..tag,Vector3.new(6,5,6),
            CFrame.new(x-3,h+4,z+side*1.5),tint,Enum.Material.SmoothPlastic,"BALL")
        deco(grove,"GEM_ACCENT_"..tag,Vector3.new(1.4,1.7,1.4),
            CFrame.new(x+2,h+6,z-side*2),Color3.fromRGB(224,194,145),
            Enum.Material.Slate,"BALL")
    end
end
assert(made == BUDGET,"LIVE_FOREST_PART_COUNT_NOT_60")
forest:SetAttribute("DecorPartCount",made)
forest:SetAttribute("MobileStaticPartBudget",BUDGET)
forest:SetAttribute("AdditionalLightCount",0)
forest:SetAttribute("AdditionalParticleCount",0)
forest:SetAttribute("AdditionalCollisionCount",0)
forest:SetAttribute("OriginalGameMapUnaffected",true)
print("P0D_PRIVATE_LIVE_FOREST_60_ART_READY_FOR_OWNER_TEST_NOT_APPROVED",made)
