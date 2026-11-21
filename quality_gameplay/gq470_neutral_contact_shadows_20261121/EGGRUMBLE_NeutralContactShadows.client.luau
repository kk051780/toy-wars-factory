--!strict
-- GQ470_FB015_NEUTRAL_CONTACT_SHADOWS_REAL69_20261121
-- LOCAL ART ONLY: low-glare ground contacts for truly replicated neutral NPCs.
-- Does not touch server HP/KO/movement/egg/score/remote/Store or player visibility.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local UserInputService = game:GetService("UserInputService")

local PLAYER = Players.LocalPlayer
local TOUCH = UserInputService.TouchEnabled
local MAX_SHADOWS = if TOUCH then 6 else 10
local MAX_DISTANCE = if TOUCH then 55 else 72
local UPDATE_SECONDS = if TOUCH then 0.95 else 0.75
local RESCAN_SECONDS = 3.8
local MIN_GROUND_NORMAL = 0.72
local SHADOW_TRANSPARENCY = 0.73
local FEATURE_OFF = "EGGRUMBLE_NeutralContactShadowsOff"
local REDUCED_EFFECTS = "EGGRUMBLE_ReducedEffects"
local SPECIES_ATTRIBUTE = "EGGRUMBLE_NeutralSpecies"

local folder = Instance.new("Folder")
folder.Name = "EGGRUMBLE_LocalNeutralContactShadows"
folder.Parent = Workspace

local active: {[Model]: Part} = {}
local discovered: {Model} = {}
local lastScan = -math.huge
local running = true

local function clearAll()
    for model, disc in pairs(active) do
        active[model] = nil
        disc:Destroy()
    end
end

local function effectsDisabled(): boolean
    return PLAYER:GetAttribute(REDUCED_EFFECTS) == true
        or PLAYER:GetAttribute(FEATURE_OFF) == true
end

local function rescan()
    table.clear(discovered)
    for _, descendant in ipairs(Workspace:GetDescendants()) do
        if descendant:IsA("Model") then
            local species = descendant:GetAttribute(SPECIES_ATTRIBUTE)
            if typeof(species) == "string" and #species > 0
                and descendant:FindFirstChild("HumanoidRootPart")
                and descendant:FindFirstChildOfClass("Humanoid") then
                table.insert(discovered, descendant)
            end
        end
    end
end

local function newDisc(): Part
    local disc = Instance.new("Part")
    disc.Name = "MatteContactDisc"
    disc.Shape = Enum.PartType.Cylinder
    disc.Material = Enum.Material.SmoothPlastic
    disc.Color = Color3.fromRGB(21, 30, 43)
    disc.Transparency = SHADOW_TRANSPARENCY
    disc.Anchored = true
    disc.CanCollide = false
    disc.CanTouch = false
    disc.CanQuery = false
    disc.CastShadow = false
    disc.Parent = folder
    return disc
end

local function contact(model: Model, root: BasePart): RaycastResult?
    local ray = RaycastParams.new()
    ray.FilterType = Enum.RaycastFilterType.Exclude
    ray.FilterDescendantsInstances = {model, folder, PLAYER.Character}
    ray.IgnoreWater = false
    ray.RespectCanCollide = true
    local hit = Workspace:Raycast(root.Position + Vector3.new(0, 0.4, 0),
        Vector3.new(0, -8, 0), ray)
    if not hit or hit.Normal.Y < MIN_GROUND_NORMAL
        or hit.Material == Enum.Material.Water or not hit.Instance.CanCollide then
        return nil
    end
    local groundModel = hit.Instance:FindFirstAncestorOfClass("Model")
    if groundModel and groundModel:GetAttribute(SPECIES_ATTRIBUTE) ~= nil then
        return nil
    end
    return hit
end

local function tick()
    if not running or not script:IsDescendantOf(game) then
        clearAll()
        return
    end
    if effectsDisabled() then
        clearAll()
        task.delay(UPDATE_SECONDS, tick)
        return
    end
    local camera = Workspace.CurrentCamera
    if not camera then
        clearAll()
        task.delay(UPDATE_SECONDS, tick)
        return
    end
    local now = os.clock()
    if now - lastScan > RESCAN_SECONDS then
        rescan()
        lastScan = now
    end

    local nearby: {{model: Model, root: BasePart, distance: number}} = {}
    for _, model in ipairs(discovered) do
        if model:IsDescendantOf(Workspace) then
            local root = model:FindFirstChild("HumanoidRootPart")
            local humanoid = model:FindFirstChildOfClass("Humanoid")
            if root and root:IsA("BasePart") and humanoid and humanoid.Health > 0 then
                local distance = (camera.CFrame.Position - root.Position).Magnitude
                if distance <= MAX_DISTANCE then
                    table.insert(nearby, {model = model, root = root, distance = distance})
                end
            end
        end
    end
    table.sort(nearby, function(a, b) return a.distance < b.distance end)
    -- GQ470_CONTACT_SHADOW_HARD_PART_BUDGET_V2:
    -- Decide the full surviving set BEFORE allocating new Parts. Otherwise,
    -- replacing ten old shadows with ten new shadows briefly doubles the budget.
    local chosen: {{model: Model, root: BasePart, hit: RaycastResult}} = {}
    local selected: {[Model]: boolean} = {}
    local limit = math.min(MAX_SHADOWS, #nearby)
    for i = 1, limit do
        local entry = nearby[i]
        local hit = contact(entry.model, entry.root)
        if hit then
            selected[entry.model] = true
            table.insert(chosen, {model = entry.model, root = entry.root, hit = hit})
        end
    end
    -- Phase 1: reclaim stale discs; phase 2: allocate only needed replacements.
    for model, disc in pairs(active) do
        if not selected[model] then
            active[model] = nil
            disc:Destroy()
        end
    end
    for _, entry in ipairs(chosen) do
        local disc = active[entry.model]
        if not disc then
            disc = newDisc()
            active[entry.model] = disc
        end
        local radius = math.clamp(math.max(entry.root.Size.X, entry.root.Size.Z) * 1.28, 1.3, 3.0)
        disc.Size = Vector3.new(0.055, radius, radius)
        -- A cylinder is thin along its local X axis. Align that axis with the
        -- true solid-ground normal so the matte footprint hugs slopes, not a
        -- horizontal plane that intersects or floats above the ground.
        -- Normal.Y >= 0.72 makes world Z cross Normal safely non-degenerate.
        local groundNormal = entry.hit.Normal
        local tangent = Vector3.new(0, 0, 1):Cross(groundNormal).Unit
        disc.CFrame = CFrame.fromMatrix(
            entry.hit.Position + groundNormal * 0.035, groundNormal, tangent)
    end
    task.delay(UPDATE_SECONDS, tick)
end

script.Destroying:Connect(function()
    running = false
    clearAll()
    folder:Destroy()
end)
PLAYER:GetAttributeChangedSignal(FEATURE_OFF):Connect(function()
    if effectsDisabled() then clearAll() end
end)
PLAYER:GetAttributeChangedSignal(REDUCED_EFFECTS):Connect(function()
    if effectsDisabled() then clearAll() end
end)
task.defer(tick)
