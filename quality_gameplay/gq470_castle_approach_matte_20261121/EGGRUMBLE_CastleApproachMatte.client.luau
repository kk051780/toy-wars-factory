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
-- Matte stones gradually disappear at the outer LOD edge.
local FADE_START = 125
local REFRESH_SECONDS = 2.5
local OPACITY_SECONDS = 0.2 -- cheap local alpha only; no new raycasts
local SLATE = Color3.fromRGB(93, 105, 108)
local SANDSTONE = Color3.fromRGB(171, 152, 120)

type Decor = { folder: Folder, pieces: {BasePart}, grounded: {[BasePart]: boolean} }
local candidates: {[BasePart]: boolean} = {}
local active: {[BasePart]: Decor} = {}

-- A-only lifecycle fence: destroy all camera-local castle visual objects on
-- Script reload and disconnect every Workspace/Player listener we create.
local disposed = false
local trackedConnections: {RBXScriptConnection} = {}
local function keep(connection: RBXScriptConnection)
    table.insert(trackedConnections, connection)
end

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

local function decorIntact(core: BasePart, decor: Decor): boolean
    if decor.folder.Parent ~= core or #decor.pieces ~= PIECES_PER_CASTLE then return false end
    for _, stone in ipairs(decor.pieces) do
        if stone.Parent ~= decor.folder then return false end
    end
    return true
end

local function placeOnGround(piece: BasePart, pose: CFrame, filter: RaycastParams): boolean
    -- Never place floating/underwater ornaments on streamed or absent floors.
    local hit = Workspace:Raycast(pose.Position + Vector3.new(0, 6, 0),
        Vector3.new(0, -14, 0), filter)
    if not hit or hit.Material == Enum.Material.Water or hit.Normal.Y < .7
        or math.abs(hit.Position.Y - pose.Position.Y) > 2.75 then
        piece.Transparency = 1
        return false
    end
    local surface = hit.Instance
    -- A moving NPC/player is not the ground, even if its body is collidable.
    local ancestor: Instance? = surface.Parent
    local actorSurface = false
    while ancestor do
        if ancestor:IsA("Model") and ancestor:FindFirstChildOfClass("Humanoid") then
            actorSurface = true
            break
        end
        ancestor = ancestor.Parent
    end
    if actorSurface or (surface:IsA("BasePart") and (
        not surface.CanCollide
        or surface.Transparency >= .95
        or surface.LocalTransparencyModifier >= .95
        or (surface.Material == Enum.Material.Glass and surface.Transparency >= .35)
    )) then
        piece.Transparency = 1
        return false
    end
    piece.CFrame = pose + Vector3.new(0,
        hit.Position.Y + piece.Size.Y * .5 - pose.Position.Y, 0)
    piece.Transparency = 0
    return true
end

local function updatePieces(core: BasePart, decor: Decor, distance: number)
    -- Four shallow split path-edge pairs, outside the foundation.
    local base = core.CFrame * CFrame.new(0, -core.Size.Y * .5 + .14, 0)
    local offsetX = math.clamp(core.Size.X * .5 + 9, 12, 72)
    local offsetZ = math.clamp(core.Size.Z * .5 + 9, 12, 72)
    local filter = RaycastParams.new()
    filter.FilterType = Enum.RaycastFilterType.Exclude
    filter.IgnoreWater = false
    -- Other actual castle floor Parts remain raycastable.
    local ignore: {Instance} = {core}
    if player.Character then table.insert(ignore, player.Character) end
    filter.FilterDescendantsInstances = ignore
    for side = 0, 3 do
        local angle = side * math.pi * .5
        local toward = base * CFrame.new(math.sin(angle) * offsetX, 0, math.cos(angle) * offsetZ)
            * CFrame.Angles(0, angle, 0)
        local first = side * 2 + 1
        decor.grounded[decor.pieces[first]] = placeOnGround(decor.pieces[first],
            toward * CFrame.new(-1.12, 0, 0) * CFrame.Angles(0, math.rad(28), 0),
            filter)
        decor.grounded[decor.pieces[first + 1]] = placeOnGround(decor.pieces[first + 1],
            toward * CFrame.new(1.12, 0, 0) * CFrame.Angles(0, math.rad(-28), 0),
            filter)
    end
    -- Rejected ground remains invisible; accepted stone edges blend in.
    local fade = math.clamp((distance - FADE_START) / (MAX_DISTANCE - FADE_START), 0, 1)
    for _, stone in ipairs(decor.pieces) do
        stone.Transparency = if decor.grounded[stone] then fade else 1
    end
end

-- 5Hz alpha-only visibility refresh: walking speed crosses the 30-stud LOD
-- zone in under the 2.5s ground-ray period. Do not re-raycast here.
local function refreshOpacity()
    if disposed then return end
    local pos = playerPosition()
    for core, decor in active do
        local distance = if pos then (core.Position - pos).Magnitude else MAX_DISTANCE
        local fade = math.clamp((distance - FADE_START) / (MAX_DISTANCE - FADE_START), 0, 1)
        for _, stone in ipairs(decor.pieces) do
            if stone.Parent == decor.folder then
                stone.Transparency = if decor.grounded[stone] then fade else 1
            end
        end
    end
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
    local decor: Decor = { folder = folder, pieces = pieces, grounded = {} }
    active[core] = decor
end

local function refresh()
    if disposed then return end
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
    local wanted: {[BasePart]: number} = {}
    for i = 1, math.min(MAX_CASTLES, #ranked) do
        wanted[ranked[i].core] = ranked[i].distance
    end
    for core in active do
        if not wanted[core] or not validCore(core) then clear(core) end
    end
    for core in wanted do
        if not active[core] then makeApproach(core) end
        local decor = active[core]
        if decor and not decorIntact(core, decor) then
            -- Streamed-away wedges must not leave a half-built path.
            clear(core)
            makeApproach(core)
            decor = active[core]
        end
        if decor then
            updatePieces(core, decor, wanted[core])
        end
    end
    local actual = 0
    for _ in active do actual += 1 end
    assert(actual * PIECES_PER_CASTLE <= MAX_PARTS)
end

-- StreamingEnabled and round teardown remove decorations immediately.
keep(Workspace.DescendantAdded:Connect(function(obj)
    if not disposed and obj:IsA("BasePart") and obj.Name == "StandardCore" then
        candidates[obj] = true
    end
end))
keep(Workspace.DescendantRemoving:Connect(function(obj)
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
keep(player:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(refresh))
keep(player:GetAttributeChangedSignal("EGGRUMBLE_CastleApproachOff"):Connect(refresh))
keep(player.CharacterAdded:Connect(function()
    task.delay(.5, refresh)
end))
keep(player.CharacterRemoving:Connect(function()
    -- Do not leave a ghost castle trail while the avatar respawns.
    for core in active do clear(core) end
end))
refresh()
task.spawn(function()
    while not disposed and script.Parent do
        task.wait(REFRESH_SECONDS)
        refresh()
    end
end)
task.spawn(function()
    while not disposed and script.Parent do
        task.wait(OPACITY_SECONDS)
        refreshOpacity()
    end
end)

-- Script.Destroying is distinct from CharacterRemoving. Hot reload/replacement
-- must not retain stale geometry or closures in other clients/rounds.
local function shutdown()
    if disposed then return end
    disposed = true
    for _, connection in ipairs(trackedConnections) do
        connection:Disconnect()
    end
    table.clear(trackedConnections)
    for core in active do
        clear(core)
    end
    table.clear(candidates)
end
script.Destroying:Connect(shutdown)
script.AncestryChanged:Connect(function(_, parent)
    if parent == nil then shutdown() end
end)
