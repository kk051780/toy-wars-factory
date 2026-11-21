--!strict
-- GQ470 FB-015: ground-level, faceted matte castle foundation shoulders.
-- Visual-only on the local client; no siege, egg, spawn or combat authority.
local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer
local FEATURE_ID = "GQ470_FB015_CASTLE_FOUNDATION_MATTE_20261121"
local MAX_CASTLES = if UserInputService.TouchEnabled then 2 else 3
local PARTS_PER_CASTLE = 8
local MAX_TOTAL_EXTRA_PARTS = MAX_CASTLES * PARTS_PER_CASTLE
local MAX_DISTANCE_STUDS = 190
local REFRESH_INTERVAL = 2.5
local STONE = Color3.fromRGB(103, 102, 99)
local EDGE = Color3.fromRGB(171, 151, 118)

type Decor = { folder: Folder, parts: {BasePart}, lastPose: CFrame, lastSize: Vector3 }
local candidates: {[BasePart]: boolean} = {}
local active: {[BasePart]: Decor} = {}

-- Local-only geometry must not outlive its LocalScript on reload or teardown.
local disposed = false
local connections: {RBXScriptConnection} = {}
local function track(connection: RBXScriptConnection)
    table.insert(connections, connection)
end

local function validCore(obj: Instance): boolean
    if not obj:IsA("BasePart") or obj.Name ~= "StandardCore" or not obj.Anchored then
        return false
    end
    local ancestor = obj.Parent
    if not ancestor or not ancestor:IsA("Model") then return false end
    while ancestor and ancestor ~= Workspace do
        if ancestor.Name == "TacticalBattlefield" then return true end
        ancestor = ancestor.Parent
    end
    return false
end

local function eyePosition(): Vector3?
    -- Visual LOD follows the camera, not the player's remote physical root.
    -- Spectator/cutscene/locked comparison cameras must see nearby castle
    -- architecture even if the avatar is far away or not yet spawned.
    local camera = Workspace.CurrentCamera
    if camera then return camera.CFrame.Position end
    -- Before CurrentCamera exists, fall back to a real character position.
    local character = player.Character
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    return if root and root:IsA("BasePart") then root.Position else nil
end

local function makeStone(parent: Folder, name: string, size: Vector3,
    pose: CFrame, color: Color3, material: Enum.Material): BasePart
    local stone = Instance.new("WedgePart")
    stone.Name = name
    stone.Size = size
    stone.CFrame = pose
    stone.Color = color
    stone.Material = material
    stone.Reflectance = 0
    stone.Anchored = true
    stone.CanCollide = false
    stone.CanTouch = false
    stone.CanQuery = false
    stone.CastShadow = false
    stone.Parent = parent
    return stone
end

local function clear(core: BasePart)
    local current = active[core]
    if not current then return end
    active[core] = nil
    current.folder:Destroy()
end

local function updatePoses(core: BasePart, decoration: Decor)
    local base = core.CFrame * CFrame.new(0, -core.Size.Y * .5 + .6, 0)
    -- Proportions follow actual castle-core dimensions; do not assume teams
    -- or invent a gate/hitbox location. All geometry is nonblocking.
    local radiusX = math.clamp(core.Size.X * .5 + .75, 2.0, 64.0)
    local radiusZ = math.clamp(core.Size.Z * .5 + .75, 2.0, 64.0)
    for side = 0, 3 do
        local angle = side * math.pi * .5
        local alongX = math.sin(angle) * radiusX
        local alongZ = math.cos(angle) * radiusZ
        local outward = base * CFrame.new(alongX, 0, alongZ)
            * CFrame.Angles(0, angle, 0)
        local first = side * 2 + 1
        decoration.parts[first].CFrame = outward * CFrame.new(0, 0, .18)
        decoration.parts[first + 1].CFrame = outward
            * CFrame.new(0, .85, -.22) * CFrame.Angles(0, math.pi, 0)
    end
    decoration.lastPose = core.CFrame
    decoration.lastSize = core.Size
end

local function makeFoundation(core: BasePart)
    if active[core] or not validCore(core) then return end
    local folder = Instance.new("Folder")
    folder.Name = "EGGRUMBLE_CastleFoundation_Local"
    folder:SetAttribute("FeatureID", FEATURE_ID)
    folder.Parent = core
    local stones: {BasePart} = {}
    for side = 1, 4 do
        table.insert(stones, makeStone(folder, "StoneShoulder_" .. side,
            Vector3.new(2.4, 1.45, 1.35), CFrame.new(), STONE, Enum.Material.Slate))
        table.insert(stones, makeStone(folder, "BevelInset_" .. side,
            Vector3.new(1.55, .42, .82), CFrame.new(), EDGE, Enum.Material.SmoothPlastic))
    end
    assert(#stones == PARTS_PER_CASTLE)
    local decoration: Decor = {folder = folder, parts = stones, lastPose = core.CFrame, lastSize = core.Size}
    active[core] = decoration
    updatePoses(core, decoration)
end

local function refresh()
    if disposed then return end
    local eye = eyePosition()
    local ranked: {{core: BasePart, distance: number}} = {}
    if player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true and eye then
        for core in candidates do
            if validCore(core) and core:IsDescendantOf(Workspace) then
                local dist = (core.Position - eye).Magnitude
                if dist <= MAX_DISTANCE_STUDS then
                    table.insert(ranked, {core = core, distance = dist})
                end
            end
        end
    end
    table.sort(ranked, function(a, b)
        if a.distance == b.distance then return a.core.Name < b.core.Name end
        return a.distance < b.distance
    end)
    local wanted: {[BasePart]: boolean} = {}
    for i = 1, math.min(MAX_CASTLES, #ranked) do
        wanted[ranked[i].core] = true
    end
    for core in active do
        if not wanted[core] or not validCore(core) then clear(core) end
    end
    for core in wanted do
        if not active[core] then makeFoundation(core) end
        local decoration = active[core]
        if decoration and (decoration.lastPose ~= core.CFrame or
            decoration.lastSize ~= core.Size or #decoration.parts ~= PARTS_PER_CASTLE) then
            updatePoses(core, decoration)
        end
    end
    -- Directly enforced touch/desktop budget; no per-frame update hook.
    local count = 0
    for _ in active do count += 1 end
    assert(count * PARTS_PER_CASTLE <= MAX_TOTAL_EXTRA_PARTS)
end

-- DescendantAdded may fire while streamed castle properties/ancestry are still
-- being assigned. Record named BaseParts first, validate after 2.5s refresh.
track(Workspace.DescendantAdded:Connect(function(obj)
    if not disposed and obj:IsA("BasePart") and obj.Name == "StandardCore" then
        candidates[obj] = true
    end
end))
track(Workspace.DescendantRemoving:Connect(function(obj)
    if not disposed and candidates[obj :: any] then
        candidates[obj :: BasePart] = nil
        clear(obj :: BasePart)
    end
end))
for _, obj in Workspace:GetDescendants() do
    if obj:IsA("BasePart") and obj.Name == "StandardCore" then
        candidates[obj] = true
    end
end
track(player:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(refresh))
track(player.CharacterAdded:Connect(function()
    task.delay(.5, refresh)
end))
refresh()
task.spawn(function()
    while not disposed and script.Parent do
        task.wait(REFRESH_INTERVAL)
        refresh()
    end
end)

script.Destroying:Connect(function()
    disposed = true
    for _, connection in ipairs(connections) do
        connection:Disconnect()
    end
    table.clear(connections)
    for core in active do
        clear(core)
    end
    table.clear(candidates)
end)
