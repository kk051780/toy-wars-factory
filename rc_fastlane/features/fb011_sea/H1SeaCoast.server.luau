--!nocheck
-- OWNER FB-011 / P0D #364: H1 sea-route VISUAL repair, not a new game mode.
-- Studio-only cosmetic ocean coastline. No Terrain edits, no swimming, no
-- collisions, no new rounds/HP/egg/damage/Remote/Store/rewards. Source QA is
-- not equivalent to human Studio visual acceptance.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then warn("FB011_NO_ARENA_FAIL_CLOSED"); return end
local h1 = arena:WaitForChild("H1_FUN_WORLD", 45)
if not h1 then warn("FB011_NO_H1_WORLD_FAIL_CLOSED"); return end
if h1:FindFirstChild("FB011_COASTAL_SEA_V1") then return end
local sea = h1:FindFirstChild("COSMETIC_SEA")
local lane = h1:FindFirstChild("SEA_LOW_CAUSEWAY")
if not sea or not sea:IsA("BasePart") or not lane or not lane:IsA("BasePart") then
    warn("FB011_SEA_ROUTE_ANCHORS_MISSING_FAIL_CLOSED"); return
end
-- H1 source variants show a 220x24 strip at z=-30 and 222x29 at z=-49.
-- Refuse to paint an unknown map. Do not relocate gameplay lanes.
if sea.Size.X < 210 or sea.Size.X > 228
    or sea.Size.Z < 22 or sea.Size.Z > 32
    or not (math.abs(sea.Position.Z + 30) < 2 or math.abs(sea.Position.Z + 49) < 2) then
    warn("FB011_SEA_ROUTE_DRIFT_FAIL_CLOSED"); return
end
local scenery = Instance.new("Folder")
scenery.Name = "FB011_COASTAL_SEA_V1"
scenery:SetAttribute("PreviewOnly", true)
scenery:SetAttribute("PhysicsUnchanged", true)
scenery:SetAttribute("NoGameAuthority", true)
scenery:SetAttribute("StudioVisualAcceptance", "NOT_TESTED")
scenery.Parent = h1
local count = 0
local function rgb(r,g,b) return Color3.fromRGB(r,g,b) end
local function decor(name, size, pos, color, material, alpha, rotation)
    count += 1
    assert(count <= 142, "FB011_PART_BUDGET")
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.CFrame = CFrame.new(pos) * CFrame.Angles(0, math.rad(rotation or 0), 0)
    p.Color = color
    p.Material = material
    p.Transparency = alpha or 0
    p.CastShadow = false
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.Parent = scenery
    return p
end
-- Replace just the old blue NEON lane underlay's VISUAL shading. Do not
-- change its CFrame, size, collision or any prompt.
sea.Material = Enum.Material.Glass
sea.Color = rgb(46, 147, 175)
sea.Transparency = .27
sea.Reflectance = .13
sea.CastShadow = false

-- Open bay lies on the ocean-facing (negative Z) side of the original SEA
-- route. Three depth zones give visible expanse, not a thin neon slab.
-- The playable road at z=-22 remains unchanged and well above these layers.
local shallow = decor("SHALLOW_TURQUOISE_BAY", Vector3.new(330, .36, 39),
    Vector3.new(0, -.56, -71), rgb(48, 172, 174), Enum.Material.Glass, .24)
shallow.Reflectance = .09
local middle = decor("MIDDLE_AZURE_BAY", Vector3.new(344, .34, 42),
    Vector3.new(0, -.60, -111), rgb(32, 123, 166), Enum.Material.Glass, .19)
middle.Reflectance = .11
local deep = decor("DEEP_SEA_HORIZON", Vector3.new(356, .30, 37),
    Vector3.new(0, -.65, -147), rgb(17, 80, 134), Enum.Material.Glass, .16)
deep.Reflectance = .14

-- Distinct curved sand beach/shallow foamy coast, 17 sections. Each piece is
-- decorative and cannot catch an avatar or block a raycast.
for i = -8, 8 do
    local x = i * 18
    local coastlineZ = -49 + math.sin(i * .68) * 4
    decor("SANDY_COAST_" .. i, Vector3.new(19, .35, 9),
        Vector3.new(x, -.19, coastlineZ), rgb(221, 199, 152),
        Enum.Material.Sand, .04, math.sin(i * .52) * 11)
    decor("BREAKING_SURF_" .. i, Vector3.new(17, .09, 2.2),
        Vector3.new(x, -.02, coastlineZ - 6),
        rgb(219, 246, 247), Enum.Material.Neon, .32,
        math.sin(i * .52) * 11)
end

-- Banded bright water reflections and long wave crests. Static, no costly
-- heartbeat or texture ID. Keep linework scattered to read as water at range.
for i = 1, 30 do
    local x = ((i * 89) % 307) - 153
    local z = -67 - ((i * 31) % 90)
    local band = 4 + (i % 4) * 5
    decor("SUN_GLINT_" .. i, Vector3.new(band, .055, .65 + (i % 3) * .35),
        Vector3.new(x, -.08, z), rgb(196, 234, 244),
        Enum.Material.Neon, .45, ((i % 5) - 2) * 8)
end
for i = 1, 12 do
    local x = ((i * 53) % 274) - 137
    local z = -60 - ((i * 19) % 77)
    decor("SWELL_RIDGE_" .. i, Vector3.new(15 + (i % 3) * 9, .09, 1.6),
        Vector3.new(x, -.025, z), rgb(114, 213, 221),
        Enum.Material.Glass, .4, (i % 4) * 7 - 9)
end

-- Small anchored rocks, shoals and wave skirts mark actual water/land depth.
-- All are VISUAL_ONLY and never block capture/escape paths.
for i = 1, 10 do
    local side = if i % 2 == 0 then 1 else -1
    local x = side * (81 + ((i * 13) % 70))
    local z = -68 - ((i * 17) % 70)
    local rock = decor("OFFSHORE_REEF_" .. i,
        Vector3.new(5 + i % 4 * 2, 2.6 + i % 3, 6 + i % 3 * 2),
        Vector3.new(x, -.7, z), rgb(107, 122, 128),
        Enum.Material.Slate, .05, i * 21)
    rock.Shape = Enum.PartType.Ball
    decor("REEF_WHITEWATER_" .. i, Vector3.new(11, .07, 2.2),
        Vector3.new(x, -.01, z - 4.5), rgb(224, 246, 248),
        Enum.Material.Neon, .30, i * 21)
end

-- Harbour pier silhouette: readable from the coast/sea path without adding
-- a deceptive second objective or a collidable dead-end.
for i = 0, 12 do
    local z = -52 - i * 4.2
    decor("OLD_PIER_PLANK_" .. i, Vector3.new(13.5, .38, 3.65),
        Vector3.new(-42, .10, z), rgb(138 + i % 3 * 5, 96, 63),
        Enum.Material.WoodPlanks, .02)
    if i % 3 == 0 then
        for _, side in ipairs({-1, 1}) do
            decor("OLD_PIER_POST_" .. i .. "_" .. side,
                Vector3.new(1.1, 5, 1.1),
                Vector3.new(-42 + side * 6.4, -2.5, z),
                rgb(90, 70, 53), Enum.Material.Wood, 0)
        end
    end
end
-- Distant buoys: warm vertical silhouettes against the open blue.
for _, side in ipairs({-1, 1}) do
    local x = side * 112
    local z = -112
    local buoy = decor("DISTANT_BUOY_" .. side, Vector3.new(2, 5, 2),
        Vector3.new(x, 1.4, z), rgb(232, 139, 75),
        Enum.Material.Metal, 0)
    buoy.Shape = Enum.PartType.Cylinder
    local light = Instance.new("PointLight")
    light.Range = 12
    light.Brightness = .35
    light.Color = rgb(255, 201, 139)
    light.Parent = buoy
end

-- Existing over-large SEA signs would cover both coast & wave silhouettes.
for _, name in ipairs({"SEA_SIGN_RED", "SEA_SIGN_BLUE"}) do
    local sign = h1:FindFirstChild(name)
    if sign then
        for _, child in ipairs(sign:GetChildren()) do
            if child:IsA("BillboardGui") then
                child.Size = UDim2.fromOffset(96, 28)
                child.MaxDistance = 18
                child.AlwaysOnTop = false
            end
        end
    end
end
scenery:SetAttribute("CosmeticParts", count)
scenery:SetAttribute("VisualZones", 3)
scenery:SetAttribute("ExistingSeaCollisionUnchanged", sea.CanCollide == false)
scenery:SetAttribute("OriginalSeaRoutePreserved", lane.Parent == h1)
print("FB011_H1_SEA_COASTAL_SCENE_LOADED_STUDIO_VISUAL_PENDING")
