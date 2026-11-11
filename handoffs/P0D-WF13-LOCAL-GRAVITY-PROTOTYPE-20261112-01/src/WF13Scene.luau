--!strict
-- WF13Scene: original low-poly, no external meshes/assets, map-only proof.
-- Provides free safe walking stairs AND optional gravity bubble. No enemy/egg data.
local Scene = {}

local function part(parent: Instance, name: string, size: Vector3, pos: Vector3,
    color: Color3, material: Enum.Material, collidable: boolean): Part
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Position = pos
    p.Color = color
    p.Material = material
    p.Anchored = true
    p.CanCollide = collidable
    p.CanTouch = collidable
    p.CanQuery = collidable
    p.Parent = parent
    return p
end

function Scene.build(parent: Instance)
    assert(parent and parent:IsA("Workspace"), "WF13 scene only accepts Workspace")
    assert(parent:FindFirstChild("WF13IsolatedScene") == nil, "WF13 duplicate scene")
    local folder = Instance.new("Folder")
    folder.Name = "WF13IsolatedScene"
    folder.Parent = parent

    local blue = Color3.fromRGB(63, 205, 255)
    local purple = Color3.fromRGB(154, 86, 254)
    local white = Color3.fromRGB(231, 242, 255)
    local gold = Color3.fromRGB(255, 224, 107)

    part(folder, "NoPayFreeGround", Vector3.new(166, 2, 118), Vector3.new(0, -1, 0),
        Color3.fromRGB(37, 53, 94), Enum.Material.SmoothPlastic, true)
    local safePad = part(folder, "WF13SafeRecoveryPad", Vector3.new(14, 1, 14),
        Vector3.new(-58, 1, 0), blue, Enum.Material.Neon, true)

    local zone = part(folder, "WF13LocalGravityBubble", Vector3.new(82, 58, 82),
        Vector3.new(0, 27, 0), purple, Enum.Material.Neon, false)
    zone.Shape = Enum.PartType.Ball
    zone.Transparency = 0.83
    zone.CastShadow = false
    zone:SetAttribute("WF13Effect", "LocalizedLowGravity")
    -- Not based on Touched from client: server controller checks actual root position.

    -- The stairs are a free alternative accessible to EVERY class without using gravity.
    for i = 1, 15 do
        local step = part(folder, string.format("FreeStair%02d", i),
            Vector3.new(5, 1.5 + i * 1.5, 16),
            Vector3.new(-55 + i * 4.3, (1.5 + i * 1.5) * 0.5, -25),
            Color3.fromRGB(89 + (i % 3) * 14, 132, 184), Enum.Material.SmoothPlastic, true)
        step.CastShadow = true
    end
    local bridge = part(folder, "FreeWalkingBridge", Vector3.new(25, 2, 16),
        Vector3.new(23, 25, -25), white, Enum.Material.SmoothPlastic, true)
    bridge.CanTouch = true
    part(folder, "SkyCastleDeck", Vector3.new(30, 2, 34), Vector3.new(42, 25, -16),
        Color3.fromRGB(87, 106, 202), Enum.Material.SmoothPlastic, true)
    for _, x in ipairs({30, 55}) do
        part(folder, "CastleTower", Vector3.new(6, 26, 6), Vector3.new(x, 37, -31),
            Color3.fromRGB(191, 205, 246), Enum.Material.SmoothPlastic, true)
        part(folder, "CastleCrown", Vector3.new(9, 3, 9), Vector3.new(x, 51, -31), gold,
            Enum.Material.Neon, false)
    end

    -- Visible rings are all cosmetic and noncolliding; no hidden gameplay cost.
    for i = 1, 18 do
        local angle = i * math.pi * 2 / 18
        local p = part(folder, string.format("OrbitSign%02d", i),
            Vector3.new(3, 1, 7),
            Vector3.new(math.cos(angle) * 43, 27, math.sin(angle) * 43),
            (i % 2 == 0) and blue or purple, Enum.Material.Neon, false)
        p.CFrame = CFrame.new(p.Position) * CFrame.Angles(0, -angle, 0)
        p.Transparency = 0.2
    end
    for i = 1, 26 do
        local angle = i * math.pi * 2 * 0.61803398875
        local radius = 58 + i % 8 * 4
        local p = part(folder, string.format("DistantStar%02d", i),
            Vector3.new(1.5, 1.5, 1.5),
            Vector3.new(math.cos(angle) * radius, 40 + (i * 13) % 43,
                math.sin(angle) * radius),
            (i % 3 == 0) and gold or white, Enum.Material.Neon, false)
        p.Shape = Enum.PartType.Ball
        p.CastShadow = false
    end

    local signPost = part(folder, "WF13EntranceSign", Vector3.new(1, 9, 1),
        Vector3.new(-41, 6, 21), gold, Enum.Material.Neon, false)
    local billboard = Instance.new("BillboardGui")
    billboard.Name = "WF13HelpSign"
    billboard.Size = UDim2.fromOffset(192, 60)
    billboard.StudsOffset = Vector3.new(0, 6, 0)
    billboard.AlwaysOnTop = true
    billboard.MaxDistance = 105
    billboard.Parent = signPost
    local text = Instance.new("TextLabel")
    text.Name = "KidReadableCue"
    text.Text = "↑ ふわっと宇宙!\n紫のドームへ"
    text.Font = Enum.Font.GothamBold
    text.TextScaled = true
    text.TextColor3 = Color3.fromRGB(255, 255, 255)
    text.BackgroundColor3 = Color3.fromRGB(69, 42, 145)
    text.BackgroundTransparency = 0.15
    text.Size = UDim2.fromScale(1, 1)
    text.Parent = billboard

    return {folder = folder, zone = zone, safePad = safePad, bridge = bridge}
end

return Scene
