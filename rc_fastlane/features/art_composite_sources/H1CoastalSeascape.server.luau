--!strict
-- FB-011 / OWNER Studio feedback: "海の道が海に見えない".
-- Studio-only additive visual replacement for the actual H1 COSMETIC_SEA slab.
-- Existing Game, MapBuilder, Egg, Castle, Remote, Store, HP, score and save are untouched.
-- A wide shallow visible coast + genuine shallow Terrain water + three dry
-- boardwalk crossings make this a recognisable SEA ROUTE instead of a neon stripe.
-- This is an experimental scene, NOT a passed Studio/Android visual acceptance.
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
if not RunService:IsStudio() then return end

local stage = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not stage then
    warn("FB011_SEA_STAGE_MISSING_NO_MUTATION")
    return
end
local arena = stage:FindFirstChild("GrassArena")
if not arena or not arena:IsA("BasePart") then return end

local originalSea: BasePart? = nil
for _ = 1, 90 do
    local found = workspace:FindFirstChild("COSMETIC_SEA", true)
    if found and found:IsA("BasePart") then
        originalSea = found
        break
    end
    task.wait(0.25)
end
if not originalSea then
    warn("FB011_H1_SEA_ANCHOR_ABSENT_FAIL_CLOSED")
    return
end
local sea = originalSea :: BasePart
if sea.Name ~= "COSMETIC_SEA"
    or math.abs(sea.Size.X - 220) > 2
    or math.abs(sea.Size.Y - 0.2) > 0.2
    or math.abs(sea.Size.Z - 24) > 2
    or math.abs(sea.Position.X) > 3
    or math.abs(sea.Position.Z + 30) > 3 then
    warn("FB011_H1_SEA_GEOMETRY_DRIFT_FAIL_CLOSED")
    return
end
if stage:FindFirstChild("FB011_COASTAL_SEASCAPE_V1") then return end

local visual = Instance.new("Folder")
visual.Name = "FB011_COASTAL_SEASCAPE_V1"
visual.Parent = stage
visual:SetAttribute("OwnerFeedback", "FB-011")
visual:SetAttribute("SeaRouteVisualOnly", true)
visual:SetAttribute("StudioHumanFUN", "NOT_TESTED")
local sand = Color3.fromRGB(225, 200, 155)
local deeperBlue = Color3.fromRGB(28, 100, 143)
local shallowBlue = Color3.fromRGB(74, 170, 190)
local seaFoam = Color3.fromRGB(220, 243, 240)
local charcoal = Color3.fromRGB(75, 90, 100)
local seaRock = Color3.fromRGB(123, 136, 143)
local jungle = Color3.fromRGB(44, 121, 79)
local timber = Color3.fromRGB(126, 93, 60)

local function block(name: string, dimensions: Vector3, position: Vector3,
    tint: Color3, material: Enum.Material, solid: boolean?): Part
    local p = Instance.new("Part")
    p.Name = name
    p.Anchored = true
    p.Size = dimensions
    p.Position = position
    p.Material = material
    p.Color = tint
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.CanTouch = false
    p.CanQuery = false -- decorative objects never hide a castle-combat raycast
    p.CanCollide = solid == true
    p.CastShadow = material ~= Enum.Material.Glass and material ~= Enum.Material.Neon
    p.Parent = visual
    return p
end

-- The old narrow neon part stays physically present but invisible. This is a
-- Studio runtime visual replacement; disabling the SOURCE overlay restores it.
sea.Transparency = 1
sea.CanCollide = false
sea.CanQuery = false

-- Ocean surface has continuous breadth and depth cues, not just a bright strip.
-- The former GrassArena surface is at Y=-1; keep water under player action height.
local surface = block("OCEAN_SHOAL_SURFACE", Vector3.new(252, .18, 66),
    Vector3.new(0, -.61, -55), shallowBlue, Enum.Material.Glass, false)
surface.Transparency = .31
local blueDepth = block("DEEP_WATER_COLOR_GRADIENT", Vector3.new(252, .14, 25),
    Vector3.new(0, -.52, -76), deeperBlue, Enum.Material.Glass, false)
blueDepth.Transparency = .26

-- A REAL Roblox Terrain water region, bounded to the northern sea side.
-- This is deliberately away from RED/BLUE eggs (z=-20), castle cores (z=0),
-- main road (z=0) and the north forest flank (z=-112); do not flood the
-- objectives or replace terrain outside the single sea channel.
local terra = workspace.Terrain
terra.WaterColor = Color3.fromRGB(34, 123, 159)
terra.WaterTransparency = .32
terra.WaterWaveSize = .25
terra.WaterWaveSpeed = 8
terra:FillBlock(CFrame.new(0, -3.2, -68), Vector3.new(246, 5.0, 24),
    Enum.Material.Water)

-- Two irregular coastlines and sand borders make the WATER/LAND boundary legible.
-- The path z=-30 stays dry on the original raised causeways and new decks.
for i = 1, 14 do
    local x = -117 + (i - 1) * 18
    local meander = math.sin(i * 1.85) * 3.5
    local near = block("FORESHORE_SAND_" .. i, Vector3.new(19, .36, 6.5),
        Vector3.new(x, -.58, -25 + meander), sand, Enum.Material.Sand, false)
    near.CFrame = near.CFrame * CFrame.Angles(0, math.rad(meander * 1.1), 0)
    local far = block("OUTER_COAST_SAND_" .. i, Vector3.new(18, .34, 6.0),
        Vector3.new(x, -.55, -91 + meander * .65), sand, Enum.Material.Sand, false)
    far.CFrame = far.CFrame * CFrame.Angles(0, math.rad(meander), 0)
end

-- Surf moves slowly, with only eight independent tweens for mobile budgets.
for i = 1, 16 do
    local x = -111 + (i - 1) * 15
    local z = -34 - (i % 3) * 18
    local foam = block("SURF_BREAK_" .. i, Vector3.new(11, .16, .55),
        Vector3.new(x, -.39, z), seaFoam, Enum.Material.SmoothPlastic, false)
    foam.Transparency = .34
    foam.CFrame = foam.CFrame * CFrame.Angles(0, math.rad((i % 5) * 7 - 14), 0)
    if i % 2 == 0 then
        local tween = TweenService:Create(foam,
            TweenInfo.new(3.0 + i * .09, Enum.EasingStyle.Sine,
                Enum.EasingDirection.InOut, -1, true),
            {Transparency = .73})
        tween:Play()
    end
end

-- Three dry timber crossings follow the established route across the shoal.
-- No forced teleporting or altered collection inputs. New physical decks stay
-- outside the battle objective locations, and never become raycast targets.
for _, x in ipairs({-75, 0, 75}) do
    local number = tostring(x)
    block("SEA_BOARDWALK_DECK_" .. number, Vector3.new(11, .8, 56),
        Vector3.new(x, .05, -57), timber, Enum.Material.WoodPlanks, true)
    for _, z in ipairs({-81, -62, -43, -33}) do
        block("SEA_BOARDWALK_POST_" .. number .. "_" .. z,
            Vector3.new(1.4, 4.0, 1.4), Vector3.new(x - 5.3, -1.4, z),
            charcoal, Enum.Material.Wood, false)
        block("SEA_BOARDWALK_POST_R_" .. number .. "_" .. z,
            Vector3.new(1.4, 4.0, 1.4), Vector3.new(x + 5.3, -1.4, z),
            charcoal, Enum.Material.Wood, false)
    end
end

-- Broken reefs, not repeated cube pillars, give the water silhouette.
for i = 1, 12 do
    local x = -119 + (i - 1) * 21
    local z = -81 + math.sin(i * 2.2) * 7
    local reef = block("REEF_ROCK_" .. i,
        Vector3.new(4 + i % 4, 3 + i % 3, 7 + (i * 2) % 4),
        Vector3.new(x, -.4, z), seaRock, Enum.Material.Slate, false)
    reef.Shape = Enum.PartType.Ball
    reef.CFrame = reef.CFrame * CFrame.Angles(0, math.rad(i * 17), .12)
end

-- Two offshore island silhouettes, palms and mooring structures.
for _, side in ipairs({-1, 1}) do
    local x = side * 110
    local isle = block("COAST_ISLAND_" .. side, Vector3.new(20, 6.5, 26),
        Vector3.new(x, .0, -101), sand, Enum.Material.Sand, false)
    isle.Shape = Enum.PartType.Ball
    local rock = block("ISLAND_HEADLAND_" .. side, Vector3.new(14, 11, 10),
        Vector3.new(x + side * 6, 2.0, -104), seaRock, Enum.Material.Slate, false)
    rock.Shape = Enum.PartType.Ball
    local trunk = block("COAST_PALM_TRUNK_" .. side, Vector3.new(2.6, 16, 2.6),
        Vector3.new(x - side * 3, 10.5, -101), timber, Enum.Material.Wood, false)
    trunk.CFrame = trunk.CFrame * CFrame.Angles(0, 0, math.rad(side * 8))
    for leaf = 1, 5 do
        local angle = (leaf - 1) * math.pi * 2 / 5
        local canopy = block("PALM_FROND_" .. side .. "_" .. leaf,
            Vector3.new(13, 1.7, 4.0),
            Vector3.new(x - side * 3 + math.cos(angle) * 6.0, 18.5,
                -101 + math.sin(angle) * 6.0), jungle, Enum.Material.Grass, false)
        canopy.CFrame = CFrame.new(canopy.Position) * CFrame.Angles(0, -angle, .11)
    end
end

-- Decorative boats and harbor silhouettes clearly communicate a coastline.
for _, s in ipairs({-1, 1}) do
    local bx = s * 49
    local boat = block("FISHING_BOAT_HULL_" .. s, Vector3.new(17, 3.2, 7),
        Vector3.new(bx, .4, -91), charcoal, Enum.Material.WoodPlanks, false)
    boat.CFrame = boat.CFrame * CFrame.Angles(0, math.rad(s * 16), 0)
    block("FISHING_BOAT_MAST_" .. s, Vector3.new(.6, 17, .6),
        Vector3.new(bx, 10, -91), timber, Enum.Material.Wood, false)
    local sail = block("FISHING_BOAT_SAIL_" .. s, Vector3.new(9, 10, .38),
        Vector3.new(bx + 4, 12, -91), Color3.fromRGB(233, 224, 198),
        Enum.Material.Fabric, false)
    sail.CFrame = sail.CFrame * CFrame.Angles(0, math.rad(s * 16), math.rad(-10))
end

-- No giant BillboardGui, no ScreenGui, no Remote, no XP/HP/damage/egg handler.
visual:SetAttribute("OceanFrontCreated", true)
visual:SetAttribute("CrossingCount", 3)
visual:SetAttribute("WaterTerrainCreated", true)
print("P0D_FB011_REAL_COAST_WATER_SURF_ROCKS_BOARDWALKS_PRIVATE_SOURCE_READY")
