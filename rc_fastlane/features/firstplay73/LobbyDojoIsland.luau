--!strict
-- FB-007: One real isolated lobby/dojos island, no score/HP/Remote/Store authority.
-- Required by the ORIGINAL singleton Game before players are placed.
local Lobby = {}
local Y = 41
local Z = 411
local PAIRS = {
    BEAST = {42, 414},
    WEAPON = {42, 438},
    MAGIC = {62, 414},
    ZOMBIE = {62, 438},
    VEHICLE = {82, 414},
    BUILDING = {82, 438},
}
function Lobby.padPosition(team: string, skill: string): Vector3
    assert(team == "RED" or team == "BLUE", "LOBBY_TEAM_INVALID")
    local at = PAIRS[skill]
    assert(at ~= nil, "LOBBY_SKILL_INVALID")
    return Vector3.new((if team == "RED" then -1 else 1) * at[1], Y + 0.15, at[2])
end
function Lobby.spawn(team: string): CFrame
    assert(team == "RED" or team == "BLUE", "LOBBY_SPAWN_TEAM_INVALID")
    local x = if team == "RED" then -47 else 47
    return CFrame.new(x, Y + 5, 382)
end
function Lobby.inLobby(position: Vector3): boolean
    return math.abs(position.X) <= 115
        and position.Z >= 356 and position.Z <= 466
        and position.Y >= Y - 8 and position.Y <= Y + 75
end
local function part(parent: Instance, name: string, sz: Vector3, cf: CFrame,
    color: Color3, material: Enum.Material, solid: boolean): BasePart
    local p = Instance.new("Part")
    p.Name = name
    p.Size = sz
    p.CFrame = cf
    p.Anchored = true
    p.CanCollide = solid
    p.CanTouch = false
    p.CanQuery = solid
    p.Color = color
    p.Material = material
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Parent = parent
    return p
end
function Lobby.build(world: Instance): Folder
    assert(world.Name == "TRAP_RAIDERS_S1", "WRONG_WORLD")
    assert(world:FindFirstChild("P0D_SAFE_LOBBY") == nil, "LOBBY_DUPLICATE")
    local floor = Instance.new("Folder")
    floor.Name = "P0D_SAFE_LOBBY"
    floor:SetAttribute("StudioOnly", true)
    floor:SetAttribute("NoDamageNoEggNoScoring", true)
    floor:SetAttribute("FB_ID", "FB-007")
    floor.Parent = world
    local cream = Color3.fromRGB(210, 194, 160)
    local stone = Color3.fromRGB(127, 139, 148)
    local timber = Color3.fromRGB(110, 75, 58)
    local grass = Color3.fromRGB(100, 150, 104)
    -- Floor top Y=41; game automatically places players at Y=46.
    part(floor, "LOBBY_SOLID_BASE", Vector3.new(230, 6, 114),
        CFrame.new(0, Y - 3, Z), stone, Enum.Material.Cobblestone, true)
    part(floor, "LOBBY_MEADOW", Vector3.new(214, .25, 101),
        CFrame.new(0, Y + .13, Z), grass, Enum.Material.Grass, true)
    for _, side in ipairs({"RED", "BLUE"}) do
        local sign = if side == "RED" then -1 else 1
        local accent = if side == "RED" then Color3.fromRGB(205, 76, 71)
            else Color3.fromRGB(66, 132, 222)
        local name = side .. "_DOJO"
        -- Wide training courtyard, with physically reachable all-six pads.
        part(floor, name .. "_COURT", Vector3.new(97, .32, 69),
            CFrame.new(sign * 59, Y + .34, 421), cream, Enum.Material.WoodPlanks, true)
        part(floor, name .. "_WALK", Vector3.new(26, .34, 38),
            CFrame.new(sign * 49, Y + .35, 382), cream, Enum.Material.Slate, true)
        for _, dz in ipairs({-1, 1}) do
            part(floor, name .. "_PAVILION_POST", Vector3.new(2.3, 15, 2.3),
                CFrame.new(sign * 60, Y + 7.6, 419 + dz * 34),
                timber, Enum.Material.Wood, true)
        end
        part(floor, name .. "_ROOFLINE", Vector3.new(24, 2.5, 77),
            CFrame.new(sign * 61, Y + 16.2, 421), timber, Enum.Material.WoodPlanks, false)
        part(floor, name .. "_HERO_BANNER", Vector3.new(1, 11, 6.5),
            CFrame.new(sign * 59, Y + 9, 458), accent, Enum.Material.Fabric, false)
        -- Low-emissive rings identify team courtyards; never tall neon columns.
        for index, skill in ipairs({"BEAST","WEAPON","MAGIC","ZOMBIE","VEHICLE","BUILDING"}) do
            local loc = Lobby.padPosition(side, skill)
            local ring = part(floor, side .. "_SKILL_FRAME_" .. tostring(index),
                Vector3.new(12.2, .16, 12.2),
                CFrame.new(loc.X, Y + .48, loc.Z), accent, Enum.Material.Slate, false)
            ring.Transparency = .3
        end
    end
    -- Boundary rails keep guests away from the 300+ stud stage separation.
    for _, x in ipairs({-112, 112}) do
        part(floor, "LOBBY_RAIL_WEST_EAST", Vector3.new(2, 8, 114),
            CFrame.new(x, Y + 4, Z), stone, Enum.Material.Cobblestone, true)
    end
    for _, z in ipairs({355, 467}) do
        part(floor, "LOBBY_RAIL_FRONT_BACK", Vector3.new(228, 8, 2),
            CFrame.new(0, Y + 4, z), stone, Enum.Material.Cobblestone, true)
    end
    floor:SetAttribute("PadCountExpected", 12)
    floor:SetAttribute("BattleZoneSeparate", true)
    return floor
end
return Lobby
