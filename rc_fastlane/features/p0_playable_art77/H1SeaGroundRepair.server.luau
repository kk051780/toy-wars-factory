--!strict
-- OWNER FB-011/FB-015: PRIVATE72 sea channel correction after #366 + #370.
-- Real dry land / water separation; no Game, Remote, egg, HP or score code.
-- This is a reversible Studio-only additive source; not a public RC fix.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local root = workspace:WaitForChild("TRAP_RAIDERS_S1", 90)
if not root then return end
local grass = root:WaitForChild("GrassArena", 30)
if not grass or not grass:IsA("BasePart") then return end
local castle = root:WaitForChild("OWNER361_CASTLE_WORLD_V1", 75)
local sea = root:WaitForChild("FB011_COASTAL_SEASCAPE_V1", 75)
if not castle or not sea then
    warn("FB011_CHANNEL_REQUIRES_BOTH_CASTLE_AND_COASTAL_ART")
    return
end
if root:FindFirstChild("FB011_REAL_OCEAN_CHANNEL_V2") then return end

-- Some scripts parent their folder before creating geometry; wait for
-- completed geometric signatures instead of trusting Start order.
local complete = false
for _ = 1, 200 do
    local wide = math.abs(grass.Size.X-370) < .05
        and math.abs(grass.Size.Z-294) < .05
        and math.abs(grass.Position.Y+3) < .05
        and math.abs(grass.Size.Y-4) < .05
    if wide and sea:GetAttribute("WaterTerrainCreated")==true
        and sea:FindFirstChild("SEA_BOARDWALK_DECK_0") then
        complete = true
        break
    end
    task.wait(.12)
end
if not complete then
    warn("FB011_CHANNEL_GEOMETRY_OR_WATER_CONTRACT_DRIFT")
    return
end

-- Keep GrassArena's original name, coordinates and dimensions in the world
-- for all legacy systems. Replace only its *render/collision* via four exact
-- dry-land fragments. A full green floor under the sea is no longer drawn.
-- Bounds: x[-185,185], z[-147,147]; channel x[-123,123], z[-83,-31].
local folder = Instance.new("Folder")
folder.Name = "FB011_REAL_OCEAN_CHANNEL_V2"
folder:SetAttribute("OwnerFeedback", "FB-011+FB-015")
folder:SetAttribute("VisualAndPhysicalLandMask", true)
folder:SetAttribute("OriginalGrassArenaSizePreserved", true)
folder:SetAttribute("GameScriptsUnchanged", true)
folder:SetAttribute("StudioSoloWaterPhysics", "NOT_TESTED")
folder:SetAttribute("AndroidPerformance", "NOT_TESTED")
folder.Parent = root

local function dryLand(name: string, dimensions: Vector3, position: Vector3): BasePart
    local p = grass:Clone()
    p.Name = name
    p.Size = dimensions
    p.Position = position
    p.Transparency = 0
    p.CanCollide = true
    p.CanTouch = false
    p.CanQuery = true
    p.Parent = folder
    return p
end
-- Physical grass remains uninterrupted along both outer flank approaches.
dryLand("SOUTH_MAINLAND", Vector3.new(370,4,178), Vector3.new(0,-3,58))
dryLand("NORTH_HIGHLANDS", Vector3.new(370,4,64), Vector3.new(0,-3,-115))
dryLand("WEST_COAST_FLANK", Vector3.new(62,4,52), Vector3.new(-154,-3,-57))
dryLand("EAST_COAST_FLANK", Vector3.new(62,4,52), Vector3.new(154,-3,-57))
grass.Transparency = 1
grass.CanCollide = false
grass.CanTouch = false
grass.CanQuery = false
grass.CastShadow = false
grass:SetAttribute("FB011WaterGapVisualOnly","OPEN")
-- Water top is about -0.5, grass top=-1, deck top=+0.45.
-- The crossing boardwalks from #370 are at x = -75,0,75. Keep their physics.
local terrain = workspace.Terrain
terrain:FillBlock(CFrame.new(0,-4.0,-57),Vector3.new(246,7,52),
    Enum.Material.Water)

-- The original tinted glass layer flattened the water into a neon stripe.
-- Actual Terrain Water and foam remain visible instead.
for _, name in ipairs({"OCEAN_SHOAL_SURFACE","DEEP_WATER_COLOR_GRADIENT"}) do
    local flat = sea:FindFirstChild(name)
    if flat and flat:IsA("BasePart") then
        flat.Transparency = 1
        flat.CanCollide = false
        flat.CanQuery = false
    end
end

local function scenic(name: string, size: Vector3, at: Vector3,
        tint: Color3, material: Enum.Material, solid: boolean): Part
    local p=Instance.new("Part")
    p.Name=name
    p.Size=size
    p.Position=at
    p.Material=material
    p.Color=tint
    p.Anchored=true
    p.CanCollide=solid
    p.CanTouch=false
    p.CanQuery=false -- scenery never blocks projectile/aim rays
    p.TopSurface=Enum.SurfaceType.Smooth
    p.BottomSurface=Enum.SurfaceType.Smooth
    p.CastShadow=solid
    p.Parent=folder
    return p
end
local SAND=Color3.fromRGB(225,203,163)
local STONE=Color3.fromRGB(91,105,113)
-- Distinct beach silhouette on both sides of the channel.
for i=1,15 do
    local x=-112+(i-1)*16
    local drift=math.sin(i*2.27)*1.6
    for _, shoreZ in ipairs({-82.7,-31.3}) do
        local shore=scenic("DUNES_"..i.."_"..tostring(shoreZ),
            Vector3.new(16.6,.28,3.4),Vector3.new(x,-.87,shoreZ+drift),
            SAND,Enum.Material.Sand,false)
        shore.CFrame=shore.CFrame*CFrame.Angles(0,drift*.055,0)
    end
end
-- North gate towers at x=+-85,z=-53 now stand on stone piers, not air.
for _, side in ipairs({-1,1}) do
    scenic("CASTLE_NORTH_GATE_ISLET_"..side,Vector3.new(24,4.5,25),
        Vector3.new(side*85,-2.95,-53),
        STONE,Enum.Material.Slate,true)
    local rock=scenic("GATE_ISLET_BREAKWATER_"..side,
        Vector3.new(29,2.4,29),Vector3.new(side*85,-3.55,-53),
        Color3.fromRGB(120,137,143),Enum.Material.Rock,false)
    rock.Shape=Enum.PartType.Ball
end

-- Authoritative egg/HP objects are untouched; existing sea crossings
-- and castle objectives still decide whether a route is playable.
folder:SetAttribute("DryLandFragments",4)
folder:SetAttribute("CrossingsRequired",3)
folder:SetAttribute("WaterGapX","-123..123")
folder:SetAttribute("WaterGapZ","-83..-31")
folder:SetAttribute("TerrainWaterTop",-0.5)
folder:SetAttribute("BuildComplete",true)
print("FB011_REAL_SEA_CHANNEL_PRIVATE72_SOURCE_ONLY_NOT_STUDIO_ACCEPTED")
