--!strict
-- Source-only Roblox map, no external private Place / IDs / plugins necessary.
local MapBuilder = {}
local COLOR = {
    grass = Color3.fromRGB(69, 120, 84),
    stone = Color3.fromRGB(104, 115, 130),
    wall = Color3.fromRGB(132, 142, 156),
    road = Color3.fromRGB(190, 174, 146),
    gold = Color3.fromRGB(255, 214, 75),
}

local function part(parent, name, size, pos, color, material, collide)
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Position = pos
    p.Color = color
    p.Material = material or Enum.Material.SmoothPlastic
    p.Anchored = true
    p.CanCollide = collide ~= false
    p.CanTouch = false
    p.CanQuery = true
    p.Parent = parent
    return p
end

local function billboard(partRef, text, offset)
    local b = Instance.new("BillboardGui")
    b.Name = "StatusLabel"
    b.Size = UDim2.fromOffset(96, 22)
    b.MaxDistance = 26
    b.StudsOffsetWorldSpace = Vector3.new(0, offset or 4, 0)
    b.AlwaysOnTop = false
    b.Parent = partRef
    local t = Instance.new("TextLabel")
    t.BackgroundColor3 = Color3.fromRGB(22, 29, 39)
    t.BackgroundTransparency = 0.2
    t.Size = UDim2.fromScale(1, 1)
    t.TextColor3 = Color3.new(1, 1, 1)
    t.TextScaled = true
    t.Font = Enum.Font.GothamBold
    t.Text = text
    t.Parent = b
    return t
end

local function prompt(parent, action, object)
    local p = Instance.new("ProximityPrompt")
    p.ActionText = action
    p.ObjectText = object
    p.HoldDuration = 0.35
    p.MaxActivationDistance = 10
    p.RequiresLineOfSight = false
    p.Enabled = false
    p.Parent = parent
    return p
end

-- OWNER #361 P0-C: authored geometry in the ONE existing MapBuilder.
-- All server-held core/egg/score-pad/spawn objects and their coordinates remain
-- unchanged. Do not place decorative geometry in front of central castle gate.
local function castleArchitecture(base, sign, accent)
    local pale = Color3.fromRGB(167, 171, 179)
    local dark = Color3.fromRGB(71, 79, 92)
    local trim = Color3.fromRGB(206, 185, 126)
    part(base, "STONE_COURTYARD", Vector3.new(51, .22, 79),
        Vector3.new(sign * 105, -.74, 0), pale, Enum.Material.Slate, false)
    -- The open, central passage is 50+ studs wide; the original delivery pad
    -- at z=+20 and treasure at z=-20 remain reachable from the open gate.
    for _, side in ipairs({-1, 1}) do
        local z = side * 44
        part(base, "FRONT_CURTAIN_WALL_" .. side, Vector3.new(7, 20, 18),
            Vector3.new(sign * 83, 10, z), pale, Enum.Material.Cobblestone)
        part(base, "FRONT_TOWER_" .. side, Vector3.new(16, 31, 16),
            Vector3.new(sign * 86, 15.5, side * 53), dark, Enum.Material.Brick)
        part(base, "FRONT_TOWER_CAP_" .. side, Vector3.new(19, 2, 19),
            Vector3.new(sign * 86, 32, side * 53), pale, Enum.Material.Slate)
        part(base, "INNER_TOWER_" .. side, Vector3.new(14, 28, 14),
            Vector3.new(sign * 120, 14, side * 36), pale, Enum.Material.Brick)
        part(base, "INNER_TOWER_CAP_" .. side, Vector3.new(17, 2, 17),
            Vector3.new(sign * 120, 29, side * 36), dark, Enum.Material.Slate)
        part(base, "TEAM_BANNER_" .. side, Vector3.new(.4, 7, 6),
            Vector3.new(sign * 76, 34, side * 53), accent, Enum.Material.SmoothPlastic, false)
        part(base, "BANNER_POLE_" .. side, Vector3.new(1, 13, 1),
            Vector3.new(sign * 77, 35, side * 53), trim, Enum.Material.Metal, false)
    end
    -- A recognisable gate arch overhead without blocking the gate or LOS to
    -- the server-authoritative castle core at x=+/-107, z=0.
    part(base, "GATE_ARCH", Vector3.new(8, 6, 57),
        Vector3.new(sign * 83, 24, 0), dark, Enum.Material.Cobblestone)
    part(base, "GATE_EMBLEM", Vector3.new(9, 5, 9),
        Vector3.new(sign * 83, 29, 0), accent, Enum.Material.Metal, false)
    for z = -48, 48, 8 do
        if math.abs(z) >= 31 then
            part(base, "GATE_BATTLEMENT_" .. z, Vector3.new(8, 5, 5),
                Vector3.new(sign * 83, 24, z), pale, Enum.Material.Brick)
        end
    end
    -- True multi-level keep is behind the existing hit-target, rather than
    -- an opaque block directly in front of its attack ray.
    part(base, "GREAT_KEEP", Vector3.new(16, 36, 30),
        Vector3.new(sign * 139, 18, 0), dark, Enum.Material.Brick)
    part(base, "GREAT_KEEP_CROWN", Vector3.new(20, 3, 34),
        Vector3.new(sign * 139, 38, 0), pale, Enum.Material.Slate)
    for z = -12, 12, 8 do
        part(base, "KEEP_CRENEL_" .. z, Vector3.new(4, 6, 4),
            Vector3.new(sign * 132, 42, z), pale, Enum.Material.Brick)
    end
    local crest = part(base, "KEEP_HERALDRY", Vector3.new(.5, 11, 8),
        Vector3.new(sign * 130, 24, 0), accent, Enum.Material.SmoothPlastic, false)
    crest.Transparency = .12
end

local function battlefieldRoutes(folder)
    local soil = Color3.fromRGB(118, 128, 102)
    local bark = Color3.fromRGB(95, 67, 46)
    local foliage = Color3.fromRGB(49, 107, 70)
    local waterColor = Color3.fromRGB(47, 117, 156)
    -- Three real traversable lanes: middle road, northern tree/highland
    -- approach and southern wetlands/stone passage. No dojo pads here.
    part(folder, "NORTH_WOODLAND_TRAIL", Vector3.new(292, .25, 19),
        Vector3.new(0, -.79, -105), COLOR.road, Enum.Material.Sand, false)
    part(folder, "SOUTH_WETLAND_TRAIL", Vector3.new(292, .25, 19),
        Vector3.new(0, -.79, 105), COLOR.road, Enum.Material.Sand, false)
    for _, side in ipairs({-1, 1}) do
        part(folder, "NORTH_LOOKOUT_PLATEAU_" .. side, Vector3.new(45, 4, 36),
            Vector3.new(side * 65, .8, -112), soil, Enum.Material.Rock)
        part(folder, "NORTH_LOOKOUT_STEP_" .. side, Vector3.new(16, 1.5, 22),
            Vector3.new(side * 36, -.15, -112), COLOR.stone, Enum.Material.Slate)
        local pond = part(folder, "SOUTH_SHALLOW_WATER_" .. side,
            Vector3.new(43, .18, 28), Vector3.new(side * 61, -.64, 111),
            waterColor, Enum.Material.Glass, false)
        pond.Transparency = .42
        for i = -1, 1 do
            local stone = part(folder, "SOUTH_STEPPING_STONE_" .. side .. "_" .. i,
                Vector3.new(8, 1.2, 8), Vector3.new(side * (61 + i * 12), -.25, 111),
                COLOR.stone, Enum.Material.Slate)
            stone.Shape = Enum.PartType.Cylinder
        end
        -- 6 trunks per flank; trees use simple geometry and no heavy meshes.
        for j = 1, 6 do
            local tx = side * (22 + (j % 3) * 32)
            local tz = -76 - (math.floor((j - 1) / 3) * 49)
            part(folder, "WOOD_TRUNK_" .. side .. "_" .. j, Vector3.new(4, 12, 4),
                Vector3.new(tx, 5, tz), bark, Enum.Material.Wood)
            local crown = part(folder, "WOOD_CROWN_" .. side .. "_" .. j,
                Vector3.new(15, 13, 15), Vector3.new(tx, 14, tz),
                foliage, Enum.Material.Grass, false)
            crown.Shape = Enum.PartType.Ball
        end
        for j = 1, 4 do
            local x = side * (30 + j * 27)
            local rock = part(folder, "SOUTH_RIDGE_" .. side .. "_" .. j,
                Vector3.new(9, 7 + j % 2 * 3, 13), Vector3.new(x, 2, 75),
                COLOR.stone, Enum.Material.Rock)
            rock.Shape = Enum.PartType.Block
        end
    end
    -- Clearly visible central stream; its existing safe crossings, including
    -- WCS authored bridges, are preserved. Stream itself is non-blocking.
    local stream = part(folder, "CENTER_STREAM", Vector3.new(16, .18, 276),
        Vector3.new(0, -.67, 0), waterColor, Enum.Material.Glass, false)
    stream.Transparency = .52
end

function MapBuilder.build(config)
    assert(workspace:FindFirstChild("TRAP_RAIDERS_S1") == nil,
        "S1_MAP_ALREADY_EXISTS: do not overwrite another map")
    local folder = Instance.new("Folder")
    folder.Name = "TRAP_RAIDERS_S1"
    folder.Parent = workspace
    part(folder, "GrassArena", Vector3.new(370, 4, 294), Vector3.new(0, -3, 0), COLOR.grass, Enum.Material.Grass)
    part(folder, "CenterRoad", Vector3.new(226, .3, 24), Vector3.new(0, -.85, 0), COLOR.road, Enum.Material.Sand)
    for i = -2, 2 do
        local rock = part(folder, "CenterPillar_" .. tostring(i), Vector3.new(7, 7, 7),
            Vector3.new(i * 20, 3, if i % 2 == 0 then 32 else -32), COLOR.stone, Enum.Material.Slate)
        rock.Shape = Enum.PartType.Cylinder
    end
    local result = {model = folder, teams = {}}
    for _, name in ipairs({"RED", "BLUE"}) do
        local sign = if name == "RED" then -1 else 1
        local accent = config.TeamColors[name]
        local base = Instance.new("Folder")
        base.Name = name .. "_CASTLE"
        base.Parent = folder
        local core = part(base, name .. "_CASTLE_CORE", Vector3.new(10, 13, 10),
            Vector3.new(sign * 107, 6.5, 0), accent, Enum.Material.Neon)
        billboard(core, name .. " CASTLE HP", 11)
        local egg = part(base, name .. "_EGG", Vector3.new(4, 5, 4),
            Vector3.new(sign * 98, 2.5, -20), COLOR.gold, Enum.Material.Neon, false)
        egg.Shape = Enum.PartType.Ball
        local eggPrompt = prompt(egg, "Steal egg", name .. " treasure")
        billboard(egg, name .. " EGG", 5)
        local pad = part(base, name .. "_SCORE_PAD", Vector3.new(12, .5, 12),
            Vector3.new(sign * 82, -.5, 20), accent, Enum.Material.Neon, false)
        local scorePrompt = prompt(pad, "Deliver egg", name .. " scoring pad")
        billboard(pad, "DELIVER HERE", 4)
        for _, z in ipairs({-44, 44}) do
            part(base, name .. "_WALL", Vector3.new(40, 14, 5),
                Vector3.new(sign * 103, 7, z), COLOR.wall, Enum.Material.Cobblestone)
        end
        part(base, name .. "_BACK_WALL", Vector3.new(5, 14, 93),
            Vector3.new(sign * 123, 7, 0), COLOR.wall, Enum.Material.Cobblestone)
        for _, z in ipairs({-35, 35}) do
            local tower = part(base, name .. "_TOWER", Vector3.new(10, 19, 10),
                Vector3.new(sign * 115, 9.5, z), accent, Enum.Material.Brick)
            tower.Shape = Enum.PartType.Block
        end
        local spawn = part(base, name .. "_SPAWN", Vector3.new(13, .5, 13),
            Vector3.new(sign * 68, -.5, 0), accent, Enum.Material.Neon, false)
        billboard(spawn, name .. " SPAWN", 4)
        castleArchitecture(base, sign, accent)
        result.teams[name] = {core = core, egg = egg, eggPrompt = eggPrompt,
            scorePad = pad, scorePrompt = scorePrompt,
            spawn = CFrame.new(sign * 68, 5, 0)}
    end
    battlefieldRoutes(folder)
    local topWall = part(folder, "ARENA_BOUNDARY_N", Vector3.new(370, 15, 4),
        Vector3.new(0, 7, -147), COLOR.stone, Enum.Material.Rock)
    topWall.Transparency = 0.25
    local bottomWall = part(folder, "ARENA_BOUNDARY_S", Vector3.new(370, 15, 4),
        Vector3.new(0, 7, 147), COLOR.stone, Enum.Material.Rock)
    bottomWall.Transparency = 0.25
    local west = part(folder, "ARENA_BOUNDARY_W", Vector3.new(4, 15, 294),
        Vector3.new(-185, 7, 0), COLOR.stone, Enum.Material.Rock)
    west.Transparency = .25
    local east = part(folder, "ARENA_BOUNDARY_E", Vector3.new(4, 15, 294),
        Vector3.new(185, 7, 0), COLOR.stone, Enum.Material.Rock)
    east.Transparency = .25
    return result
end
return MapBuilder
