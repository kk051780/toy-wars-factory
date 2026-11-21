--!strict
-- EGGRUMBLE / GQ470 / FB-015: matte airborne landing silhouette.
-- Client-owned visual only. Never moves the avatar, awards points, marks enemies,
-- or writes match/egg/castle/Remote state. Entire feature can be removed as one LocalScript.
-- ART_GATE=SOURCE_PREP_ONLY; actual Studio/Android comparisons remain mandatory.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local player = Players.LocalPlayer
if not player then
    return
end

-- At most three local, non-interactive matte Parts. One raycast / 0.12 sec.
local SAMPLE_INTERVAL = 0.12
local MAX_GROUND_DEPTH = 48
local MIN_AIR_HEIGHT = 4.5
local MAX_SLOPE_COS = 0.78
local MIN_FALL_SPEED = -2
local MAX_VISUAL_PARTS = 3
-- These are purely presentation flags; never grant gameplay effects.
local VISUAL_OFF_FLAGS = {
    "EGGRUMBLE_ReducedEffects",
    "ReducedEffects",
    "EGGRUMBLE_LandingShadowOff",
}

local function visualDisabled(character: Model?): boolean
    for _, flag in ipairs(VISUAL_OFF_FLAGS) do
        if player:GetAttribute(flag) == true then
            return true
        end
        if character and character:GetAttribute(flag) == true then
            return true
        end
    end
    return false
end

local effects = Instance.new("Folder")
effects.Name = "EGGRUMBLE_LandingShadow_LocalOnly"

local function visualPart(name: string, color: Color3, shape: Enum.PartType?): Part
    local part = Instance.new("Part")
    part.Name = name
    part.Anchored = true
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Material = Enum.Material.SmoothPlastic -- no Neon, lights or particles
    part.Color = color
    part.Transparency = 1
    part.Size = Vector3.new(0.1, 0.1, 0.1)
    part.TopSurface = Enum.SurfaceType.Smooth
    part.BottomSurface = Enum.SurfaceType.Smooth
    if shape then
        part.Shape = shape
    end
    part.Parent = effects
    return part
end

local disc = visualPart("LandingMatteDisc", Color3.fromRGB(36, 47, 59), Enum.PartType.Cylinder)
local left = visualPart("LandingChevronLeft", Color3.fromRGB(244, 210, 139), nil)
local right = visualPart("LandingChevronRight", Color3.fromRGB(244, 210, 139), nil)
assert(#effects:GetChildren() == MAX_VISUAL_PARTS, "landing effect exceeds local Part budget")

local humanoid: Humanoid? = nil
local root: BasePart? = nil

local function hide()
    disc.Transparency = 1
    left.Transparency = 1
    right.Transparency = 1
end

local globalConnections: {RBXScriptConnection} = {}
local characterConnections: {RBXScriptConnection} = {}
local function clearCharacterConnections()
    for _, connection in ipairs(characterConnections) do
        connection:Disconnect()
    end
    table.clear(characterConnections)
end

local function trackCharacter(character: Model)
    clearCharacterConnections()
    for _, flag in ipairs(VISUAL_OFF_FLAGS) do
        table.insert(characterConnections, character:GetAttributeChangedSignal(flag):Connect(function()
            -- Hide immediately on OFF; the regular bounded sampler handles ON.
            if visualDisabled(character) then
                hide()
            end
        end))
    end
    -- Never wait indefinitely for an avatar. This is a visual affordance only.
    humanoid = character:FindFirstChildOfClass("Humanoid")
    root = character:FindFirstChild("HumanoidRootPart") :: BasePart?
    hide()
end

table.insert(globalConnections, player.CharacterAdded:Connect(trackCharacter))
table.insert(globalConnections, player.CharacterRemoving:Connect(function()
    clearCharacterConnections()
    humanoid = nil
    root = nil
    hide()
end))
for _, flag in ipairs(VISUAL_OFF_FLAGS) do
    table.insert(globalConnections, player:GetAttributeChangedSignal(flag):Connect(function()
        if visualDisabled(player.Character) then
            hide()
        end
    end))
end
if player.Character then
    trackCharacter(player.Character)
end

local elapsed = 0
local heartbeatConnection: RBXScriptConnection? = nil
heartbeatConnection = RunService.Heartbeat:Connect(function(dt: number)
    elapsed += dt
    if elapsed < SAMPLE_INTERVAL then
        return
    end
    elapsed = 0

    local camera = Workspace.CurrentCamera
    local character = player.Character
    if visualDisabled(character) then
        hide()
        return
    end
    if not camera or not character then
        hide()
        return
    end
    if effects.Parent ~= camera then
        effects.Parent = camera
    end

    local currentHumanoid = character:FindFirstChildOfClass("Humanoid")
    local currentRoot = character:FindFirstChild("HumanoidRootPart")
    if not currentHumanoid or not currentRoot or not currentRoot:IsA("BasePart") then
        humanoid = nil
        root = nil
        hide()
        return
    end
    humanoid = currentHumanoid
    root = currentRoot

    -- Don't show through spectator cameras, seats, swimming or during death.
    if currentHumanoid.Health <= 0
        or currentHumanoid.SeatPart ~= nil
        or currentHumanoid:GetState() ~= Enum.HumanoidStateType.Freefall
        or currentHumanoid.FloorMaterial ~= Enum.Material.Air
        or currentRoot.AssemblyLinearVelocity.Y >= MIN_FALL_SPEED
        or (camera.CameraSubject ~= currentHumanoid and camera.CameraSubject ~= currentRoot)
    then
        hide()
        return
    end

    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = {character, effects}
    params.IgnoreWater = false

    local hit = Workspace:Raycast(currentRoot.Position, Vector3.new(0, -MAX_GROUND_DEPTH, 0), params)
    if not hit or hit.Material == Enum.Material.Water or hit.Normal.Y < MAX_SLOPE_COS then
        hide()
        return
    end
    -- A standing player or humanoid NPC is not ground. Nested accessories
    -- may be several Models deep, so check the complete ancestry locally.
    local ancestor: Instance? = hit.Instance.Parent
    while ancestor do
        if ancestor:IsA("Model") and ancestor:FindFirstChildOfClass("Humanoid") then
            hide()
            return
        end
        ancestor = ancestor.Parent
    end

    -- Only show a real landing surface. Noncolliding decor and synthetic
    -- translucent Glass seas may be queryable but cannot carry an avatar.
    if hit.Instance:IsA("BasePart") then
        if not hit.Instance.CanCollide
            or hit.Instance.Transparency >= 0.95
            or hit.Instance.LocalTransparencyModifier >= 0.95
            or (hit.Instance.Material == Enum.Material.Glass and hit.Instance.Transparency >= 0.35)
        then
            hide()
            return
        end
    end
    local height = currentRoot.Position.Y - hit.Position.Y
    if height < MIN_AIR_HEIGHT or height > MAX_GROUND_DEPTH then
        hide()
        return
    end

    -- Ground-aligned chevron tells the player where they can land; color is
    -- supplementary to its shape, so the signal survives color-vision differences.
    local normal = hit.Normal
    local heading = currentRoot.CFrame.LookVector
    local tangent = heading - normal * heading:Dot(normal)
    if tangent.Magnitude < 0.05 then
        tangent = Vector3.new(0, 0, -1) - normal * Vector3.new(0, 0, -1):Dot(normal)
    end
    tangent = tangent.Unit
    local frame = CFrame.lookAt(hit.Position + normal * 0.10, hit.Position + normal * 0.10 + tangent, normal)
    local diameter = math.clamp(1.45 + height * 0.034, 1.6, 2.9)
    local fade = math.clamp((height - MIN_AIR_HEIGHT) / 12, 0, 1)

    disc.Size = Vector3.new(0.065, diameter, diameter)
    disc.CFrame = frame * CFrame.Angles(0, 0, math.pi / 2)
    disc.Transparency = 0.60 + 0.13 * fade
    left.Size = Vector3.new(0.17, 0.045, 0.88)
    right.Size = left.Size
    left.CFrame = frame * CFrame.new(-0.35, 0.045, 0.12) * CFrame.Angles(0, math.rad(-37), 0)
    right.CFrame = frame * CFrame.new(0.35, 0.045, 0.12) * CFrame.Angles(0, math.rad(37), 0)
    left.Transparency = 0.22 + 0.24 * fade
    right.Transparency = left.Transparency
end)
-- Prevent abandoned camera-local Parts or callbacks when a candidate script is
-- removed/reloaded. The official 69-script game remains completely untouched.
script.Destroying:Connect(function()
    if heartbeatConnection then
        heartbeatConnection:Disconnect()
        heartbeatConnection = nil
    end
    clearCharacterConnections()
    for _, connection in ipairs(globalConnections) do
        connection:Disconnect()
    end
    table.clear(globalConnections)
    hide()
    effects:Destroy()
end)
