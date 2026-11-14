--!strict
-- P0 #431 LIVE-ART: first production-safe stylized castle silhouette pass.
-- The base MapBuilder, not the Studio-only Owner361 3-route expansion, is
-- the only dependency. No movement, physics, objectives, HIT/HP, remote or
-- persistent state is mutated. This does NOT solve sea/beast/forest parity.
local RunService = game:GetService("RunService")
if not RunService:IsServer() then return end
-- Studio preview remains unchanged by default. For a privately authorized
-- production-like Studio preview, enable this SCRIPT attribute explicitly.
if RunService:IsStudio() and script:GetAttribute("EnablePrivatePreview") ~= true then
    return
end

local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then
    warn("P0D_LIVE_CASTLE_BASE_MAP_MISSING_NO_ART")
    return
end
if arena:FindFirstChild("P0D_LIVE_SAFE_CASTLE_ART_V1") then return end

local sides = {}
for _, name in ipairs({"RED", "BLUE"}) do
    local castle = arena:FindFirstChild(name .. "_CASTLE")
    if not castle or not castle:IsA("Folder") then
        warn("P0D_LIVE_CASTLE_TEAM_ANCHOR_MISSING", name)
        return
    end
    local core = castle:FindFirstChild(name .. "_CASTLE_CORE")
    local towers = {}
    for _, child in ipairs(castle:GetChildren()) do
        if child.Name == name .. "_TOWER" and child:IsA("BasePart") then
            table.insert(towers, child)
        end
    end
    if not core or not core:IsA("BasePart") or #towers ~= 2 then
        warn("P0D_LIVE_CASTLE_TOWER_ANCHOR_MISSING", name)
        return
    end
    table.sort(towers, function(a, b) return a.Position.Z < b.Position.Z end)
    table.insert(sides, {name = name, core = core, towers = towers})
end
-- All anchors validated before creating one decorative part.
local art = Instance.new("Folder")
art.Name = "P0D_LIVE_SAFE_CASTLE_ART_V1"
art.Parent = arena
local BUDGET = 36
local created = 0
local stone = Color3.fromRGB(133, 145, 158)
local slate = Color3.fromRGB(56, 68, 83)
local gold = Color3.fromRGB(209, 173, 108)
local bronze = Color3.fromRGB(145, 123, 98)

local function deco(parent: Instance, name: string, size: Vector3, cf: CFrame,
        color: Color3, material: Enum.Material, wedge: boolean): BasePart
    assert(created < BUDGET, "P0D_LIVE_CASTLE_ART_BUDGET_EXCEEDED")
    local p: BasePart = if wedge then Instance.new("WedgePart") else Instance.new("Part")
    p.Name = name
    p.Size = size
    p.CFrame = cf
    p.Color = color
    p.Material = material
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Parent = parent
    created += 1
    return p
end

for _, side in ipairs(sides) do
    local team = side.name
    local accent = if team == "RED" then Color3.fromRGB(199, 88, 91)
        else Color3.fromRGB(77, 141, 202)
    local group = Instance.new("Folder")
    group.Name = team .. "_CASTLE_SILHOUETTE"
    group.Parent = art
    for index, tower in ipairs(side.towers) do
        local p = tower.Position
        -- Existing tower is 19 studs tall (top y=19); all new geometry starts
        -- above it. Four pitched planes give a strong roof silhouette with
        -- few large shapes even at a mobile screen resolution.
        for _, quarter in ipairs({
            {Vector3.new(-2.4, 12.5, 0), math.pi},
            {Vector3.new(2.4, 12.5, 0), 0},
            {Vector3.new(0, 12.5, -2.4), math.pi / 2},
            {Vector3.new(0, 12.5, 2.4), -math.pi / 2},
        }) do
            local q = quarter[2]
            deco(group, "ROOF_PANEL_" .. index .. "_" .. tostring(q),
                Vector3.new(6.1, 6.4, 10.8),
                CFrame.new(p + quarter[1]) * CFrame.Angles(0, q, 0),
                slate, Enum.Material.Slate, true)
        end
        for _, z in ipairs({-1, 1}) do
            deco(group, "ROOF_TRIM_" .. index .. "_" .. z,
                Vector3.new(11.2, 1.1, 1.8),
                CFrame.new(p + Vector3.new(0, 10.0, z * 5.2)),
                stone, Enum.Material.Cobblestone, false)
        end
        deco(group, "ROOF_FINIAL_" .. index,
            Vector3.new(2, 3.2, 2),
            CFrame.new(p + Vector3.new(0, 18.1, 0)),
            gold, Enum.Material.Metal, false)
        -- One colored cloth standard + relief emblem on each actual tower.
        -- Keep all team labels geometric instead of creating BillboardGui.
        deco(group, "TEAM_STANDARD_" .. index,
            Vector3.new(.4, 6, 4.2),
            CFrame.new(p + Vector3.new(6.2, 14, 0)),
            accent, Enum.Material.Fabric, false)
        deco(group, "TEAM_MEDALLION_" .. index,
            Vector3.new(.6, 2.8, 2.8),
            CFrame.new(p + Vector3.new(6.55, 13.2, 0)),
            bronze, Enum.Material.Metal, false)
    end
end

assert(created == BUDGET, "P0D_LIVE_CASTLE_COUNT_INVARIANT")
art:SetAttribute("VisualOnly", true)
art:SetAttribute("MobileStaticPartBudget", BUDGET)
art:SetAttribute("ActualArtPartCount", created)
art:SetAttribute("AdditionalLightCount", 0)
art:SetAttribute("AdditionalParticleCount", 0)
art:SetAttribute("AdditionalCollisionCount", 0)
art:SetAttribute("StudioAuthorPreviewReplaced", false)
art:SetAttribute("SourceQAOnly", true)
art:SetAttribute("OwnerAccepted", false)
print("P0D_LIVE_CASTLE_VISUAL_ONLY_RUNTIME_CANDIDATE", created)
