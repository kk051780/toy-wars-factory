--!strict
-- P0 #431 FB011 LIVE COAST V1: visual scenery, not water physics.
-- Source-only private production-parity PREP. No public release permission.
-- Does NOT remove any existing Studio-only script guard.
local RunService = game:GetService("RunService")
if not RunService:IsServer() then return end
-- Public server protection is independent of the Workspace opt-in flag.
-- DataModel.PrivateServerId is read on the server only (non-replicated).
if not RunService:IsStudio() and game.PrivateServerId == "" then
    warn("P0D_LIVE_COAST_PUBLIC_SERVER_ALWAYS_OFF")
    return
end

-- In both Studio and private non-Studio Roblox, opt-in must be explicitly
-- set by the server/OWNER. NEVER enable cosmetic parity on public by default.
if workspace:GetAttribute("P0D_PRIVATE_LIVE_COAST") ~= true then return end

local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then
    warn("P0D_LIVE_COAST_MAP_MISSING_NO_WRITE")
    return
end
if arena:FindFirstChild("P0D_PRIVATE_LIVE_COAST_V1") then return end

-- Hard-lock to REAL default MapBuilder. Owner361 expands/mutates the arena
-- in Studio (250x142 -> 370x294). Mixing these layouts would make a wrong
-- coastal route, so fail closed and preserve original Studio sea preview.
local ground = arena:FindFirstChild("GrassArena")
local road = arena:FindFirstChild("CenterRoad")
local north = arena:FindFirstChild("ARENA_BOUNDARY_N")
local red = arena:FindFirstChild("RED_CASTLE")
local blue = arena:FindFirstChild("BLUE_CASTLE")
if not ground or not ground:IsA("BasePart")
    or not road or not road:IsA("BasePart")
    or not north or not north:IsA("BasePart")
    or not red or not blue then
    warn("P0D_LIVE_COAST_BASE_MAP_ANCHOR_MISSING_NO_WRITE")
    return
end
if math.abs(ground.Size.X - 250) > .1 or math.abs(ground.Size.Z - 142) > .1
    or math.abs(ground.Position.Y + 3) > .1
    or math.abs(road.Position.Z) > .1 or math.abs(road.Size.Z - 24) > .1
    or math.abs(north.Position.Z + 71) > .1 or math.abs(north.Size.Z - 4) > .1 then
    warn("P0D_LIVE_COAST_GEOMETRY_DRIFT_NO_WRITE")
    return
end

local folder = Instance.new("Folder")
folder.Name = "P0D_PRIVATE_LIVE_COAST_V1"
folder.Parent = arena

local MAX_PARTS = 40
local created = 0
local C = Color3.fromRGB
local AZURE = C(49, 135, 170)
local DEEP = C(27, 88, 126)
local FOAM = C(218, 237, 229)
local SAND = C(213, 196, 156)
local ROCK = C(112, 127, 133)
local ROCK_LIGHT = C(161, 161, 147)
local WOOD = C(109, 80, 56)
local SAIL = C(241, 229, 203)
local LEAF = C(68, 126, 88)

local function scenic(name: string, size: Vector3, location: Vector3,
    material: Enum.Material, tint: Color3, transparency: number,
    ellipse: boolean): Part
    assert(created < MAX_PARTS, "LIVE_COAST_MOBILE_PART_BUDGET_EXCEEDED")
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Position = location
    p.Material = material
    p.Color = tint
    p.Transparency = transparency
    p.Shape = if ellipse then Enum.PartType.Ball else Enum.PartType.Block
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Parent = folder
    created += 1
    return p
end

-- Entirely OUTSIDE the original play rectangle (north boundary z=-71).
-- No terrain carving, no water physics, no real player-crossing claim.
-- Main water begins at z=-76; original wall ends at z=-73.
scenic("COAST_WATER_MAIN", Vector3.new(246, .2, 58),
    Vector3.new(0, -1.5, -105), Enum.Material.SmoothPlastic, AZURE, .06, false)
scenic("COAST_DEEP_HORIZON", Vector3.new(246, .18, 28),
    Vector3.new(0, -1.55, -148), Enum.Material.SmoothPlastic, DEEP, .08, false)

-- Shoreline contour: six broad material pieces, not expensive tiny geometry.
for i = 0, 5 do
    local x = -100 + i * 40
    local beach = scenic("SAND_EDGE_" .. i,
        Vector3.new(41, .45, 4.6), Vector3.new(x, -1.42, -76),
        Enum.Material.Sand, SAND, 0, false)
    beach.CFrame = beach.CFrame * CFrame.Angles(0, math.rad(i % 2 == 0 and 2 or -2), 0)
end

-- Static whitewater short strips communicate water movement without 12 Tween
-- loops or a long-lived ParticleEmitter on low-end Android.
for i = 0, 11 do
    local x = -110 + i * 20
    local z = -81 - (i % 3) * 10
    local wave = scenic("SHORE_WAVE_" .. i,
        Vector3.new(11.5, .09, .55), Vector3.new(x, -1.33, z),
        Enum.Material.SmoothPlastic, FOAM, .2, false)
    wave.CFrame = wave.CFrame * CFrame.Angles(0, math.rad((i % 4) * 7 - 10), 0)
end

-- Readable irregular rock silhouettes; collision and aiming rays unaffected.
for i = 0, 7 do
    local x = -102 + i * 29
    local z = -98 - (i % 3) * 7
    local rock = scenic("COAST_REEF_" .. i,
        Vector3.new(3 + (i % 3), 2.4, 5.5 + (i % 2) * 2),
        Vector3.new(x, -1.0, z), Enum.Material.Slate,
        if i % 2 == 0 then ROCK else ROCK_LIGHT, 0, true)
    rock.CFrame = rock.CFrame * CFrame.Angles(.07, math.rad(i * 17), .08)
end

-- Two headlands and two sails are bold distant landmarks using 12 parts.
for _, side in ipairs({-1, 1}) do
    local x = side * 103
    scenic("ISLAND_HEADLAND_" .. side,
        Vector3.new(17, 5, 22), Vector3.new(x, -.8, -120),
        Enum.Material.Sand, SAND, 0, true)
    scenic("ISLAND_PALM_TRUNK_" .. side,
        Vector3.new(2, 10, 2), Vector3.new(x - side * 3, 5.7, -121),
        Enum.Material.Wood, WOOD, 0, false)
    scenic("ISLAND_PALM_CROWN_" .. side,
        Vector3.new(11, 3.2, 10), Vector3.new(x - side * 3, 11, -121),
        Enum.Material.Grass, LEAF, 0, true)

    local boatX = side * 57
    scenic("SAIL_BOAT_HULL_" .. side,
        Vector3.new(15, 2.8, 6), Vector3.new(boatX, .5, -109),
        Enum.Material.WoodPlanks, WOOD, 0, true)
    scenic("SAIL_BOAT_MAST_" .. side,
        Vector3.new(.7, 11, .7), Vector3.new(boatX, 6.6, -109),
        Enum.Material.Wood, ROCK, 0, false)
    scenic("SAIL_BOAT_CLOTH_" .. side,
        Vector3.new(6.5, 7, .2), Vector3.new(boatX + 3.4, 7.2, -109),
        Enum.Material.Fabric, SAIL, 0, false)
end

assert(created == MAX_PARTS, "LIVE_COAST_PART_COUNT_MISMATCH")
folder:SetAttribute("VisualOnly", true)
folder:SetAttribute("PrivateOptIn", "P0D_PRIVATE_LIVE_COAST")
folder:SetAttribute("ActualPartCount", created)
folder:SetAttribute("MaxMobileStaticParts", MAX_PARTS)
folder:SetAttribute("CollisionPartCount", 0)
folder:SetAttribute("PhysicsWaterAdded", false)
folder:SetAttribute("TerrainModified", false)
folder:SetAttribute("DynamicLightCount", 0)
folder:SetAttribute("ParticleEmitterCount", 0)
folder:SetAttribute("TweenAndHeartbeatCount", 0)
folder:SetAttribute("NoPlayRouteChanged", true)
folder:SetAttribute("OwnerAccepted", false)
print("P0D_PRIVATE_LIVE_COAST_SOURCE_PREP", created)
