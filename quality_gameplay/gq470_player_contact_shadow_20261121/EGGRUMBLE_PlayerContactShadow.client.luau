--!strict
-- GQ470_FB015_PLAYER_CONTACT_SHADOW_REAL69_20261121
-- A-only optional visual: one matte shadow for LOCAL GROUNDED avatar.
-- Distinct from #968 footsteps, #993 airborne landing, #997 neutral shadows.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local UserInputService = game:GetService("UserInputService")

local PLAYER = Players.LocalPlayer
local INTERVAL = if UserInputService.TouchEnabled then 0.16 else 0.10
local MAX_CAMERA_DISTANCE = if UserInputService.TouchEnabled then 55 else 75
local MIN_GROUND_NORMAL = 0.78
local FADE_START_FRACTION = 0.72
local SHADOW_ALPHA = 0.76
local FEATURE_OFF = "EGGRUMBLE_PlayerContactShadowOff"
local REDUCED_EFFECTS = "EGGRUMBLE_ReducedEffects"

local folder = Instance.new("Folder")
folder.Name = "EGGRUMBLE_PlayerContactShadow_Local"
folder.Parent = Workspace
local disc: Part? = nil
local running = true
local disabledConnection: RBXScriptConnection? = nil
local reducedConnection: RBXScriptConnection? = nil
local removingConnection: RBXScriptConnection? = nil

local function clearDisc()
    if disc then
        disc:Destroy()
        disc = nil
    end
end

local function off(): boolean
    return PLAYER:GetAttribute(FEATURE_OFF) == true
        or PLAYER:GetAttribute(REDUCED_EFFECTS) == true
end

local function characterVisible(character: Model, humanoid: Humanoid): boolean
    if humanoid.Health <= 0 or humanoid.FloorMaterial == Enum.Material.Air then
        return false
    end
    local state = humanoid:GetState()
    if state == Enum.HumanoidStateType.Dead
        or state == Enum.HumanoidStateType.Swimming
        or state == Enum.HumanoidStateType.Climbing
        or state == Enum.HumanoidStateType.Freefall
        or state == Enum.HumanoidStateType.Seated then
        return false
    end
    if character:GetAttribute("Invisible") == true
        or character:GetAttribute("StealthActive") == true
        or character:GetAttribute("IsInvisible") == true then
        return false
    end
    local head = character:FindFirstChild("Head")
    if not head or not head:IsA("BasePart")
        or head.Transparency >= 0.95 or head.LocalTransparencyModifier >= 0.95 then
        return false
    end
    return true
end

local function ensureDisc(): Part
    if disc then return disc end
    local part = Instance.new("Part")
    part.Name = "MatteAvatarContactDisc"
    part.Shape = Enum.PartType.Cylinder
    part.Size = Vector3.new(0.05, 2.8, 2.3)
    part.Material = Enum.Material.SmoothPlastic
    part.Color = Color3.fromRGB(24, 34, 45)
    part.Transparency = SHADOW_ALPHA
    part.Reflectance = 0
    part.Anchored = true
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Parent = folder
    disc = part
    return part
end

local function update()
    if not running or not script:IsDescendantOf(game) then
        clearDisc()
        return
    end
    if off() then
        clearDisc()
        task.delay(INTERVAL, update)
        return
    end
    local character = PLAYER.Character
    local camera = Workspace.CurrentCamera
    local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    local cameraDistance = if camera and root and root:IsA("BasePart")
        then (camera.CFrame.Position - root.Position).Magnitude else math.huge
    if not character or not humanoid or not root or not root:IsA("BasePart")
        or not root:IsDescendantOf(Workspace) or not camera
        or not characterVisible(character, humanoid)
        or cameraDistance > MAX_CAMERA_DISTANCE then
        clearDisc()
        task.delay(INTERVAL, update)
        return
    end
    -- Hide during spectator or another character's camera.
    local subject = camera.CameraSubject
    if subject ~= humanoid and subject ~= root
        and (not subject or not subject:IsDescendantOf(character)) then
        clearDisc()
        task.delay(INTERVAL, update)
        return
    end
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = {character, folder}
    params.IgnoreWater = false
    params.RespectCanCollide = true
    local hit = Workspace:Raycast(root.Position + Vector3.new(0, 0.35, 0),
        Vector3.new(0, -7.5, 0), params)
    if not hit or hit.Normal.Y < MIN_GROUND_NORMAL
        or hit.Material == Enum.Material.Water
        or not hit.Instance.CanCollide then
        clearDisc()
        task.delay(INTERVAL, update)
        return
    end
    local ancestor = hit.Instance:FindFirstAncestorOfClass("Model")
    if ancestor and (ancestor:FindFirstChildOfClass("Humanoid")
        or ancestor:GetAttribute("EGGRUMBLE_NeutralSpecies") ~= nil) then
        clearDisc()
        task.delay(INTERVAL, update)
        return
    end
    local part = ensureDisc()
    -- Ease toward invisible before leaving LOD. One Part, no additional raycasts.
    local fade = math.clamp(
        (cameraDistance / MAX_CAMERA_DISTANCE - FADE_START_FRACTION)
            / (1 - FADE_START_FRACTION), 0, 1)
    part.Transparency = SHADOW_ALPHA + (1 - SHADOW_ALPHA) * fade
    local radius = math.clamp(math.max(root.Size.X, root.Size.Z), 1.6, 3)
    part.Size = Vector3.new(0.05, radius * 1.46, radius * 1.19)
    local normal = hit.Normal
    local tangent = Vector3.new(0, 0, 1):Cross(normal).Unit
    -- Thin cylinder local X axis aligned to the dry ground normal.
    part.CFrame = CFrame.fromMatrix(hit.Position + normal * 0.045, normal, tangent)
    task.delay(INTERVAL, update)
end

disabledConnection = PLAYER:GetAttributeChangedSignal(FEATURE_OFF):Connect(function()
    if off() then clearDisc() end
end)
reducedConnection = PLAYER:GetAttributeChangedSignal(REDUCED_EFFECTS):Connect(function()
    if off() then clearDisc() end
end)
removingConnection = PLAYER.CharacterRemoving:Connect(clearDisc)
script.Destroying:Connect(function()
    running = false
    if disabledConnection then disabledConnection:Disconnect() end
    if reducedConnection then reducedConnection:Disconnect() end
    if removingConnection then removingConnection:Disconnect() end
    clearDisc()
    folder:Destroy()
end)
task.defer(update)
