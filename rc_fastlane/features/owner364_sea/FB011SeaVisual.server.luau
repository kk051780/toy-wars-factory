--!strict
-- P0D FB-011 / #364: visual-only ocean route, STUDIO QA candidate.
-- Existing H1 route, Castle/MapBuilder, eggs, HP, scores and Remote stay unchanged.
-- Rendered with native Roblox Water and non-colliding original low-poly scenery.
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Workspace = game:GetService("Workspace")
if not RunService:IsStudio() then return end

local arena = Workspace:WaitForChild("TRAP_RAIDERS_S1", 180)
if not arena then warn("FB011_SEA_ARENA_MISSING"); return end
local h1 = arena:WaitForChild("H1_FUN_WORLD", 90)
if not h1 then warn("FB011_H1_WORLD_MISSING"); return end
local original = h1:FindFirstChild("COSMETIC_SEA")
local route = h1:FindFirstChild("SEA_LOW_CAUSEWAY")
if not (original and original:IsA("BasePart")
    and route and route:IsA("BasePart")) then
    warn("FB011_H1_SEA_CONTRACT_DRIFT")
    return
end
if math.abs(original.Size.X - 220) > .01
    or math.abs(original.Size.Z - 24) > .01
    or math.abs(route.Position.Z + 22) > .01 then
    warn("FB011_H1_SEA_LOCATION_DRIFT")
    return
end
if h1:FindFirstChild("P0D_FB011_SEA_ART_V1") then return end

local world = Instance.new("Folder")
world.Name = "P0D_FB011_SEA_ART_V1"
world:SetAttribute("VisualOnly", true)
world:SetAttribute("NoCombatScoreHPRemoteStore", true)
world:SetAttribute("StudioVisualQA", "NOT_TESTED")
world:SetAttribute("OwnerFeedbackID", "FB-011")
world.Parent = h1

local parts = 0
local tweens: {Tween} = {}
local function c(r: number, g: number, b: number): Color3
    return Color3.fromRGB(r, g, b)
end
local function decor(name: string, size: Vector3, position: Vector3,
    color: Color3, material: Enum.Material, alpha: number): Part
    parts += 1
    assert(parts <= 70, "FB011_VISUAL_PART_BUDGET")
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Position = position
    p.Color = color
    p.Material = material
    p.Transparency = alpha
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Parent = world
    return p
end

-- Genuine Roblox Terrain water; avoid the solid sea causeway z=-22 and
-- the original egg/score/core anchors. FillBlock is Studio-session scoped.
-- The sea is beside the bridge, not a replacement for a traversable road.
local waterCenter = Vector3.new(0, -6.0, -49)
local waterSize = Vector3.new(164, 11, 40)
Workspace.Terrain:FillBlock(CFrame.new(waterCenter), waterSize, Enum.Material.Water)
world:SetAttribute("NativeTerrainWater", true)
world:SetAttribute("WaterBounds", "x=-82..82,z=-69..-29,top=-0.5")
world:SetAttribute("NoGameplayRouteGeometryChanged", true)

-- Remove the previous thin glowing plastic sheet from view; its collision
-- was already disabled. No changes to SEA_ENTRY or SEA_LOW_CAUSEWAY.
original.Transparency = 1
original.CastShadow = false

-- Shallow sandy edges create a readable shoreline, not a floating neon strip.
for _, z in ipairs({-29.1, -68.9}) do
    decor("SAND_SHORE_" .. tostring(z), Vector3.new(164, .18, 2.5),
        Vector3.new(0, -.47, z), c(228, 207, 159), Enum.Material.Sand, .12)
end

-- Discontinuous foam ribbons animate gently and avoid the egg passage.
for i = 1, 12 do
    local x = (i - 6.5) * 13
    local z = if i % 2 == 0 then -33.1 else -65.0
    local p = decor("FOAM_RIBBON_" .. i, Vector3.new(9, .09, 1.15),
        Vector3.new(x, -.34, z), c(220, 247, 252), Enum.Material.Glass, .30)
    local drift = if i % 2 == 0 then 1.0 else -1.0
    local tween = TweenService:Create(p,
        TweenInfo.new(3.2 + (i % 4) * .6, Enum.EasingStyle.Sine,
            Enum.EasingDirection.InOut, -1, true),
        {Position = p.Position + Vector3.new(drift, 0, .55)})
    table.insert(tweens, tween)
    tween:Play()
end

-- Shore boulders and sea grass give distance cues and irregular silhouettes.
for i, x in ipairs({-74, -53, -28, 38, 59, 76}) do
    local z = if i % 2 == 0 then -62 else -58
    local b = decor("SHORE_ROCK_" .. i,
        Vector3.new(4 + i % 3, 3 + i % 2, 5 + i % 3),
        Vector3.new(x, .45, z), c(79, 105, 113), Enum.Material.Slate, 0)
    b.Shape = Enum.PartType.Ball
    for j = 1, 2 do
        local plant = decor("KELP_" .. i .. "_" .. j,
            Vector3.new(.6, 2.8 + j, .6),
            Vector3.new(x + j * 2.1, .8, z + j * 1.3),
            c(58 + j * 9, 140 + j * 11, 109),
            Enum.Material.Grass, .12)
        plant.Shape = Enum.PartType.Cylinder
    end
end

-- A recognisable wooden pier, with vertical pilings and warm lanterns.
-- All new art is non-collidable so original egg movement is unmodified.
for _, x in ipairs({-57, 57}) do
    for k = 1, 4 do
        local z = -31 - k * 5
        decor("PIER_PILING_" .. tostring(x) .. "_" .. k,
            Vector3.new(1.8, 6.5, 1.8), Vector3.new(x, 1.8, z),
            c(107, 77, 55), Enum.Material.Wood, 0)
        decor("PIER_DECK_" .. tostring(x) .. "_" .. k,
            Vector3.new(7.5, .5, 4.6), Vector3.new(x, 2.9, z),
            c(169, 121, 80), Enum.Material.WoodPlanks, 0)
    end
    local post = decor("HARBOR_LANTERN_" .. tostring(x),
        Vector3.new(1.2, 3, 1.2), Vector3.new(x, 5.0, -47),
        c(232, 196, 117), Enum.Material.Metal, 0)
    local lamp = Instance.new("PointLight")
    lamp.Color = c(255, 221, 156)
    lamp.Range = 12
    lamp.Brightness = .6
    lamp.Parent = post
end

-- A small readable sailboat makes the playable bridge visually coastal.
local hull = decor("FISHERMAN_BOAT_HULL", Vector3.new(10, 1.6, 4.5),
    Vector3.new(17, -.10, -51), c(133, 79, 54), Enum.Material.WoodPlanks, 0)
hull:SetAttribute("DecorOnly", true)
decor("FISHERMAN_MAST", Vector3.new(.45, 9, .45),
    Vector3.new(17, 5.1, -51), c(169, 123, 72), Enum.Material.Wood, 0)
local sail = Instance.new("WedgePart")
parts += 1
assert(parts <= 70)
sail.Name = "FISHERMAN_SAIL"
sail.Size = Vector3.new(6, 7, .35)
sail.CFrame = CFrame.new(19.3, 5.1, -51)
sail.Color = c(244, 240, 220)
sail.Material = Enum.Material.Fabric
sail.Transparency = .08
sail.Anchored = true
sail.CanCollide = false
sail.CanTouch = false
sail.CanQuery = false
sail.CastShadow = false
sail.Parent = world

-- Preserve a concise sea indicator without the old giant always-on-top text.
for _, signName in ipairs({"SEA_SIGN_RED", "SEA_SIGN_BLUE"}) do
    local sign = h1:FindFirstChild(signName)
    if sign then
        for _, item in ipairs(sign:GetDescendants()) do
            if item:IsA("BillboardGui") then
                item.Size = UDim2.fromOffset(96, 24)
                item.MaxDistance = 25
                item.AlwaysOnTop = false
            end
        end
    end
end

world:SetAttribute("SceneDecorParts", parts)
world:SetAttribute("WaveAnimations", #tweens)
world:SetAttribute("UnverifiedWaterPhysics", true)
world:SetAttribute("NeedsStudioSolo2ClientMobile", true)
script.Destroying:Connect(function()
    for _, tween in ipairs(tweens) do tween:Cancel() end
    -- Terrain water is generated only in Studio runtime. An OFF rebuild and
    -- a fresh Play session restores the original world; no persistent edits.
end)
print("P0D_FB011_SEA_ART_CANDIDATE_ACTIVE_NOT_OWNER_ACCEPTED")
