--!strict
-- EGGRUMBLE | GQ470 FB-015 | A-only visual candidate
-- Low-glare bevel stones at the edges of the EXISTING GQ646 lobby floor.
-- Does not create/change floor, SpawnLocation, Character, Camera, GUI or gameplay authority.
local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer
local FEATURE_ID = "GQ470_FB015_LOBBY_EDGE_MASONRY_20261121"
local FLOOR_NAME = "GQ646_LOBBY_SAFE_GROUND"
local LOBBY_NAME = "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"
local REFRESH_SECONDS = 2.5
local MAX_DISTANCE = if UserInputService.TouchEnabled then 115 else 175
local PARTS_PER_FLOOR = 8
local MAX_FLOORS = 1
local MAX_EXTRA_PARTS = PARTS_PER_FLOOR * MAX_FLOORS
local STONE_A = Color3.fromRGB(112, 106, 95)
local STONE_B = Color3.fromRGB(155, 137, 115)

type Decor = {
    folder: Folder,
    parts: {BasePart},
    lastPose: CFrame,
    lastSize: Vector3,
}
local candidates: {[BasePart]: boolean} = {}
local active: {[BasePart]: Decor} = {}

local function validFloor(part: Instance): boolean
    if not part:IsA("BasePart") or part.Name ~= FLOOR_NAME or not part.Anchored then
        return false
    end
    local ancestor: Instance? = part.Parent
    while ancestor and ancestor ~= Workspace do
        if ancestor.Name == LOBBY_NAME and ancestor:IsA("Folder") then
            return true
        end
        ancestor = ancestor.Parent
    end
    return false
end

local function viewPosition(): Vector3?
    local character = player.Character
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    if root and root:IsA("BasePart") then
        return root.Position
    end
    local camera = Workspace.CurrentCamera
    return if camera then camera.CFrame.Position else nil
end

local function dispose(floor: BasePart)
    local found = active[floor]
    if found then
        active[floor] = nil
        found.folder:Destroy()
    end
end

local function positionStones(floor: BasePart, decor: Decor)
    -- Each side uses two short wedges in the floor's local coordinates.
    -- Wedges sit just BELOW the walkable top; collisions/queries stay disabled.
    for side = 1, 4 do
        local yaw = (side - 1) * math.pi / 2
        local along = if side % 2 == 1 then floor.Size.X else floor.Size.Z
        local across = if side % 2 == 1 then floor.Size.Z else floor.Size.X
        local span = math.clamp(along * .21, 1.4, 11.0)
        for section = 1, 2 do
            local index = (side - 1) * 2 + section
            local lateral = (if section == 1 then -.27 else .27) * along
            local edge = across * .5 + .17
            local stone = decor.parts[index]
            stone.Size = Vector3.new(span, .85, .7)
            stone.CFrame = floor.CFrame * CFrame.Angles(0, yaw, 0)
                * CFrame.new(lateral, floor.Size.Y * .5 - .46, edge)
            stone.Color = if (side + section) % 2 == 0 then STONE_A else STONE_B
        end
    end
    decor.lastPose = floor.CFrame
    decor.lastSize = floor.Size
end

local function addFloor(floor: BasePart)
    if active[floor] or not validFloor(floor) then return end
    local folder = Instance.new("Folder")
    folder.Name = "EGGRUMBLE_LobbyEdgeMasonry_Local"
    folder:SetAttribute("FeatureID", FEATURE_ID)
    folder.Parent = floor
    local parts: {BasePart} = {}
    for index = 1, PARTS_PER_FLOOR do
        local stone = Instance.new("WedgePart")
        stone.Name = "MatteEdgeStone_" .. index
        stone.Anchored = true
        stone.Material = Enum.Material.Slate
        stone.Reflectance = 0
        stone.CanCollide = false
        stone.CanTouch = false
        stone.CanQuery = false
        stone.CastShadow = false
        stone.Parent = folder
        table.insert(parts, stone)
    end
    active[floor] = {
        folder = folder, parts = parts,
        lastPose = floor.CFrame, lastSize = floor.Size,
    }
    positionStones(floor, active[floor])
end

local function refresh()
    local view = viewPosition()
    local chosen: BasePart? = nil
    local best = MAX_DISTANCE
    if view and player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true then
        for floor in pairs(candidates) do
            if validFloor(floor) and floor:IsDescendantOf(Workspace) then
                local distance = (view - floor.Position).Magnitude
                if distance < best then
                    best, chosen = distance, floor
                end
            end
        end
    end
    for floor in pairs(active) do
        if floor ~= chosen or not validFloor(floor) then
            dispose(floor)
        end
    end
    if chosen then
        if not active[chosen] then addFloor(chosen) end
        local decor = active[chosen]
        if decor and (decor.lastPose ~= chosen.CFrame or decor.lastSize ~= chosen.Size) then
            positionStones(chosen, decor)
        end
    end
    local floors = 0
    for _ in pairs(active) do floors += 1 end
    assert(floors * PARTS_PER_FLOOR <= MAX_EXTRA_PARTS)
end

-- Handle delayed Host construction and StreamingEnabled removal without leaks.
Workspace.DescendantAdded:Connect(function(obj)
    if obj:IsA("BasePart") and obj.Name == FLOOR_NAME then
        candidates[obj] = true
    end
end)
Workspace.DescendantRemoving:Connect(function(obj)
    if obj:IsA("BasePart") and candidates[obj] then
        candidates[obj] = nil
        dispose(obj)
    end
end)
for _, obj in Workspace:GetDescendants() do
    if obj:IsA("BasePart") and obj.Name == FLOOR_NAME then
        candidates[obj] = true
    end
end
player:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(refresh)
player.CharacterAdded:Connect(function()
    task.delay(.5, refresh)
end)
refresh()
task.spawn(function()
    while script.Parent do
        task.wait(REFRESH_SECONDS)
        refresh()
    end
end)
