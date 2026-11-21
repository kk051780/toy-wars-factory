--!strict
-- FB-015 / ART-420: matte ground waystones outside castle foundations.
-- Cosmetic-only candidate: no terrain, collision, HUD, camera or game authority.
local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local player = Players.LocalPlayer

local FEATURE_ID = "GQ470_FB015_CASTLE_APPROACH_MATTE_20261121"
local MAX_CASTLES = if UserInputService.TouchEnabled then 2 else 3
local PIECES_PER_CASTLE = 8
local MAX_PARTS = MAX_CASTLES * PIECES_PER_CASTLE
local MAX_DISTANCE = 155
local REFRESH_SECONDS = 2.5
local SLATE = Color3.fromRGB(93, 105, 108)
local SANDSTONE = Color3.fromRGB(171, 152, 120)

type Decor = { folder: Folder, pieces: {BasePart}, lastPose: CFrame, lastSize: Vector3 }
local candidates: {[BasePart]: boolean} = {}
local active: {[BasePart]: Decor} = {}

local function validCore(core: Instance): boolean
    if not core:IsA("BasePart") or core.Name ~= "StandardCore" or not core.Anchored then
        return false
    end
    -- Fail closed for map revisions where shallow stones would fall inside a keep.
    if core.Size.X > 126 or core.Size.Z > 126 or core.Size.Y > 150 then
        return false
    end
    local ancestor = core.Parent
    if not ancestor or not ancestor:IsA("Model") then return false end
    while ancestor and ancestor ~= Workspace do
        if ancestor.Name == "TacticalBattlefield" then return true end
        ancestor = ancestor.Parent
    end
    return false
end

local function playerPosition(): Vector3?
    local character = player.Character
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    if not root or not root:IsA("BasePart") then return nil end
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if not humanoid or humanoid.Health <= 0 then return nil end
    return root.Position
end

local function makePiece(parent: Folder, name: string, tint: Color3): BasePart
    local p = Instance.new("WedgePart")
    p.Name = name
    p.Size = Vector3.new(1.7, .22, 3.8)
    p.CFrame = CFrame.new()
    p.Color = tint
    p.Material = Enum.Material.Slate
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Reflectance = 0
    p.Parent = parent
    return p
end

local function clear(core: BasePart)
    local old = active[core]
    if not old then return end
    active[core] = nil
    old.folder:Destroy()
end

local function updatePieces(core: BasePart, decor: Decor)
    -- Four pairs of split, shallow path-edge keystones, NOT foundation blocks.
    -- The inset is farther away than #982 foundation (core face + >=8 studs).
    local base = core.CFrame * CFrame.new(0, -core.Size.Y * .5 + .14, 0)
    -- Place approach stones relative to the correct local castle face.
    -- A single max(X,Z) radius pushes stones far from the short faces of
    -- long rectangular keeps, so compute two clamped face offsets instead.
    local offsetX = math.clamp(core.Size.X * .5 + 9, 12, 72)
    local offsetZ = math.clamp(core.Size.Z * .5 + 9, 12, 72)
    for side = 0, 3 do
        local angle = side * math.pi * .5
        local toward = base * CFrame.new(
            math.sin(angle) * offsetX, 0, math.cos(angle) * offsetZ)
            * CFrame.Angles(0, angle, 0)
        local first = side * 2 + 1
        decor.pieces[first].CFrame =
            toward * CFrame.new(-1.12, 0, 0) * CFrame.Angles(0, math.rad(28), 0)
        decor.pieces[first + 1].CFrame =
            toward * CFrame.new(1.12, 0, 0) * CFrame.Angles(0, math.rad(-28), 0)
    end
    decor.lastPose = core.CFrame
    decor.lastSize = core.Size
end

local function makeApproach(core: BasePart)
    if active[core] or not validCore(core) then return end
    local folder = Instance.new("Folder")
    folder.Name = "EGGRUMBLE_CastleApproach_Local"
    folder:SetAttribute("FeatureID", FEATURE_ID)
    folder.Parent = core
    local pieces: {BasePart} = {}
    for side = 1, 4 do
        table.insert(pieces, makePiece(folder, "SlatePathEdge_" .. side, SLATE))
        table.insert(pieces, makePiece(folder, "SandstonePathEdge_" .. side, SANDSTONE))
    end
    assert(#pieces == PIECES_PER_CASTLE)
    local decor: Decor = {
        folder = folder, pieces = pieces,
        lastPose = core.CFrame, lastSize = core.Size,
    }
    active[core] = decor
    updatePieces(core, decor)
end

local function refresh()
    local pos = playerPosition()
    local ranked: {{core: BasePart, distance: number}} = {}
    if pos and player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true
        and player:GetAttribute("EGGRUMBLE_CastleApproachOff") ~= true then
        for core in candidates do
            if validCore(core) and core:IsDescendantOf(Workspace) then
                local distance = (core.Position - pos).Magnitude
                if distance <= MAX_DISTANCE then
                    table.insert(ranked, {core = core, distance = distance})
                end
            end
        end
    end
    table.sort(ranked, function(a, b)
        if a.distance ~= b.distance then return a.distance < b.distance end
        if a.core.Position.X ~= b.core.Position.X then
            return a.core.Position.X < b.core.Position.X
        end
        return a.core.Position.Z < b.core.Position.Z
    end)
    local wanted: {[BasePart]: boolean} = {}
    for i = 1, math.min(MAX_CASTLES, #ranked) do
        wanted[ranked[i].core] = true
    end
    for core in active do
        if not wanted[core] or not validCore(core) then clear(core) end
    end
    for core in wanted do
        if not active[core] then makeApproach(core) end
        local decor = active[core]
        if decor and (decor.lastPose ~= core.CFrame or decor.lastSize ~= core.Size) then
            updatePieces(core, decor)
        end
    end
    local actual = 0
    for _ in active do actual += 1 end
    assert(actual * PIECES_PER_CASTLE <= MAX_PARTS)
end

-- StreamingEnabled and round teardown remove decorations immediately.
Workspace.DescendantAdded:Connect(function(obj)
    if obj:IsA("BasePart") and obj.Name == "StandardCore" then
        candidates[obj] = true
    end
end)
Workspace.DescendantRemoving:Connect(function(obj)
    if candidates[obj :: any] then
        candidates[obj :: BasePart] = nil
        clear(obj :: BasePart)
    end
end)
for _, obj in Workspace:GetDescendants() do
    if obj:IsA("BasePart") and obj.Name == "StandardCore" then
        candidates[obj] = true
    end
end
player:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(refresh)
player:GetAttributeChangedSignal("EGGRUMBLE_CastleApproachOff"):Connect(refresh)
player.CharacterAdded:Connect(function()
    task.delay(.5, refresh)
end)
player.CharacterRemoving:Connect(function()
    task.defer(refresh)
end)
refresh()
task.spawn(function()
    while script.Parent do
        task.wait(REFRESH_SECONDS)
        refresh()
    end
end)
