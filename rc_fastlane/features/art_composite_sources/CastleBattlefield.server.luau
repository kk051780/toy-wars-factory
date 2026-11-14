--!strict
-- #361 P0-C: isolated additive authored 3D world. ONE existing Game still owns
-- eggs / HP / round / damage / score. No clone of MapBuilder or Game.
-- The rich66 MapBuilder remains source/byte identical; this Script only
-- augments the already-created world, and is Studio-private.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local world = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not world then
    warn("OWNER361_CASTLE_WORLD_MISSING_FAIL_CLOSED")
    return
end
if world:FindFirstChild("OWNER361_CASTLE_WORLD_V1") then return end
local grass = world:WaitForChild("GrassArena", 10)
local north = world:WaitForChild("ARENA_BOUNDARY_N", 10)
local south = world:WaitForChild("ARENA_BOUNDARY_S", 10)
local red = world:WaitForChild("RED_CASTLE", 10)
local blue = world:WaitForChild("BLUE_CASTLE", 10)
if not grass or not grass:IsA("BasePart")
    or not north or not north:IsA("BasePart")
    or not south or not south:IsA("BasePart")
    or not red or not blue then
    warn("OWNER361_CASTLE_MAP_ANCHOR_MISSING_FAIL_CLOSED")
    return
end
-- Original objective coordinates / hit-targets and all Game networking remain
-- exactly as set by MapBuilder; no changes to _CORE/_EGG/_SCORE_PAD/_SPAWN.
local folder = Instance.new("Folder")
folder.Name = "OWNER361_CASTLE_WORLD_V1"
folder.Parent = world
local stone = Color3.fromRGB(151, 158, 169)
local dark = Color3.fromRGB(67, 76, 91)
local green = Color3.fromRGB(57, 112, 75)
local wood = Color3.fromRGB(96, 68, 46)
local water = Color3.fromRGB(48, 126, 169)
local trail = Color3.fromRGB(190, 172, 136)

local function part(parent: Instance, name: string, size: Vector3, position: Vector3,
        color: Color3, material: Enum.Material, collide: boolean): BasePart
    local obj = Instance.new("Part")
    obj.Name = name
    obj.Size = size
    obj.Position = position
    obj.Anchored = true
    obj.CanCollide = collide
    obj.CanTouch = false
    obj.CanQuery = collide -- non-colliding decoration never occludes castle damage rays
    obj.Color = color
    obj.Material = material
    obj.Parent = parent
    return obj
end

-- Widen a LIVE map created by the canonical MapBuilder. Leave every objective
-- location untouched. Existing center Road / WCS routes remain undisturbed.
grass.Size = Vector3.new(370, 4, 294)
north.Size = Vector3.new(370, 15, 4)
north.Position = Vector3.new(0, 7, -147)
south.Size = Vector3.new(370, 15, 4)
south.Position = Vector3.new(0, 7, 147)
for _, item in ipairs({
    {"WEST", -185}, {"EAST", 185},
}) do
    local boundary = part(folder, "ARENA_BOUNDARY_" .. item[1],
        Vector3.new(4, 15, 294), Vector3.new(item[2], 7, 0),
        dark, Enum.Material.Rock, true)
    boundary.Transparency = .3
end

local function fortress(side: number, team: string, accent: Color3)
    local group = Instance.new("Folder")
    group.Name = team .. "_CASTLE_ARCHITECTURE"
    group.Parent = folder
    part(group, "COURTYARD", Vector3.new(54, .18, 81),
        Vector3.new(side * 108, -.78, 0), stone, Enum.Material.Slate, false)
    for _, s in ipairs({-1, 1}) do
        -- A wide open ground-level gate preserves access to the original egg
        -- (z=-20), delivery pad (z=20) and glowing core (z=0).
        local z = s * 53
        part(group, "GATE_TOWER_" .. s, Vector3.new(16, 30, 16),
            Vector3.new(side * 85, 15, z), dark, Enum.Material.Brick, true)
        part(group, "GATE_TOWER_CROWN_" .. s, Vector3.new(19, 2.4, 19),
            Vector3.new(side * 85, 31, z), stone, Enum.Material.Slate, true)
        part(group, "CURTAIN_WALL_" .. s, Vector3.new(34, 18, 4),
            Vector3.new(side * 102, 9, s * 47), stone, Enum.Material.Cobblestone, true)
        part(group, "INNER_TOWER_" .. s, Vector3.new(14, 26, 14),
            Vector3.new(side * 123, 13, s * 36), stone, Enum.Material.Brick, true)
        part(group, "INNER_TOWER_CROWN_" .. s, Vector3.new(17, 2, 17),
            Vector3.new(side * 123, 27, s * 36), dark, Enum.Material.Slate, true)
        part(group, "BANNER_" .. s, Vector3.new(.4, 8, 7),
            Vector3.new(side * 78, 35, z), accent, Enum.Material.SmoothPlastic, false)
        part(group, "BANNER_POLE_" .. s, Vector3.new(.8, 14, .8),
            Vector3.new(side * 79, 37, z), stone, Enum.Material.Metal, false)
    end
    -- Elevated lintel does not obstruct a player at ground level.
    part(group, "OPEN_GATE_ARCH", Vector3.new(9, 6, 80),
        Vector3.new(side * 85, 24, 0), dark, Enum.Material.Cobblestone, true)
    part(group, "OPEN_GATE_CREST", Vector3.new(10, 6, 10),
        Vector3.new(side * 85, 30, 0), accent, Enum.Material.SmoothPlastic, false)
    for z = -38, 38, 9.5 do
        part(group, "GATE_MERLON_" .. z, Vector3.new(9, 5, 5),
            Vector3.new(side * 85, 29, z), stone, Enum.Material.Brick, true)
    end
    -- A keep at x=+/-145 is behind the original core x=+/-107.
    part(group, "GRAND_KEEP", Vector3.new(20, 40, 36),
        Vector3.new(side * 145, 20, 0), dark, Enum.Material.Brick, true)
    part(group, "GRAND_KEEP_CROWN", Vector3.new(24, 3, 40),
        Vector3.new(side * 145, 42, 0), stone, Enum.Material.Slate, true)
    for z = -16, 16, 8 do
        part(group, "KEEP_MERLON_" .. z, Vector3.new(5, 5, 5),
            Vector3.new(side * 135, 46, z), stone, Enum.Material.Brick, true)
    end
end
fortress(-1, "RED", Color3.fromRGB(231, 82, 88))
fortress(1, "BLUE", Color3.fromRGB(71, 149, 241))

-- Center path remains original; two physical flanks through forest & wetlands.
part(folder, "NORTH_WOODLAND_TRAIL", Vector3.new(285, .24, 19),
    Vector3.new(0, -.80, -112), trail, Enum.Material.Sand, false)
part(folder, "SOUTH_WETLAND_TRAIL", Vector3.new(285, .24, 19),
    Vector3.new(0, -.80, 111), trail, Enum.Material.Sand, false)
local river = part(folder, "LOW_STREAM", Vector3.new(14, .15, 265),
    Vector3.new(0, -.68, 0), water, Enum.Material.Glass, false)
river.Transparency = .52
for _, side in ipairs({-1, 1}) do
    part(folder, "NORTH_LOOKOUT_PLATEAU_" .. side, Vector3.new(36, 3.5, 34),
        Vector3.new(side * 67, .75, -110), stone, Enum.Material.Rock, true)
    part(folder, "NORTH_LOOKOUT_STEP_" .. side, Vector3.new(18, 1.2, 23),
        Vector3.new(side * 40, -.25, -110), stone, Enum.Material.Slate, true)
    local pond = part(folder, "SOUTH_SHALLOW_WATER_" .. side,
        Vector3.new(48, .15, 28), Vector3.new(side * 65, -.70, 111),
        water, Enum.Material.Glass, false)
    pond.Transparency = .4
    for j = -1, 1 do
        part(folder, "SOUTH_STEPPING_STONE_" .. side .. "_" .. j,
            Vector3.new(8, 1, 8), Vector3.new(side * (65 + j * 12), -.3, 111),
            stone, Enum.Material.Slate, true)
    end
    for j = 1, 6 do
        local px = side * (20 + (j % 3) * 31)
        local pz = -80 - math.floor((j - 1) / 3) * 49
        part(folder, "FOREST_TRUNK_" .. side .. "_" .. j, Vector3.new(4, 12, 4),
            Vector3.new(px, 5, pz), wood, Enum.Material.Wood, true)
        local crown = part(folder, "FOREST_CROWN_" .. side .. "_" .. j,
            Vector3.new(15, 12, 15), Vector3.new(px, 14, pz),
            green, Enum.Material.Grass, false)
        crown.Shape = Enum.PartType.Ball
    end
end

-- Shrink only WORLD labels belonging to the original arena; do not disable
-- remote UI, objective prompts, or touch action buttons.
for _, descendant in ipairs(world:GetDescendants()) do
    if descendant:IsA("BillboardGui") and descendant.Name == "StatusLabel" then
        descendant.Size = UDim2.fromOffset(96, 22)
        descendant.MaxDistance = 26
        descendant.AlwaysOnTop = false
    end
end
print("OWNER361_CASTLE_WORLD_PRIVATE_STUDIO_ADDED_NO_GAME_AUTHORITY")
