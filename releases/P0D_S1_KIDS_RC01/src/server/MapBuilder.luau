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
    b.Size = UDim2.fromOffset(210, 44)
    b.StudsOffsetWorldSpace = Vector3.new(0, offset or 4, 0)
    b.AlwaysOnTop = true
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

function MapBuilder.build(config)
    assert(workspace:FindFirstChild("TRAP_RAIDERS_S1") == nil,
        "S1_MAP_ALREADY_EXISTS: do not overwrite another map")
    local folder = Instance.new("Folder")
    folder.Name = "TRAP_RAIDERS_S1"
    folder.Parent = workspace
    part(folder, "GrassArena", Vector3.new(250, 4, 142), Vector3.new(0, -3, 0), COLOR.grass, Enum.Material.Grass)
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
        billboard(core, (if name == "RED" then "赤チームの城" else "青チームの城"), 11)
        local egg = part(base, name .. "_EGG", Vector3.new(4, 5, 4),
            Vector3.new(sign * 98, 2.5, -20), COLOR.gold, Enum.Material.Neon, false)
        egg.Shape = Enum.PartType.Ball
        local eggPrompt = prompt(egg, "卵を取る", (if name == "RED" then "赤チームの卵" else "青チームの卵"))
        billboard(egg, (if name == "RED" then "赤チームの卵" else "青チームの卵"), 5)
        local pad = part(base, name .. "_SCORE_PAD", Vector3.new(12, .5, 12),
            Vector3.new(sign * 82, -.5, 20), accent, Enum.Material.Neon, false)
        local scorePrompt = prompt(pad, "卵を届ける", (if name == "RED" then "赤の納品台" else "青の納品台"))
        billboard(pad, "卵はここへ！", 4)
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
        billboard(spawn, (if name == "RED" then "赤チームのスタート" else "青チームのスタート"), 4)
        result.teams[name] = {core = core, egg = egg, eggPrompt = eggPrompt,
            scorePad = pad, scorePrompt = scorePrompt,
            spawn = CFrame.new(sign * 68, 5, 0)}
    end
    local topWall = part(folder, "ARENA_BOUNDARY_N", Vector3.new(250, 15, 4),
        Vector3.new(0, 7, -71), COLOR.stone, Enum.Material.Rock)
    topWall.Transparency = 0.25
    local bottomWall = part(folder, "ARENA_BOUNDARY_S", Vector3.new(250, 15, 4),
        Vector3.new(0, 7, 71), COLOR.stone, Enum.Material.Rock)
    bottomWall.Transparency = 0.25
    return result
end
return MapBuilder
