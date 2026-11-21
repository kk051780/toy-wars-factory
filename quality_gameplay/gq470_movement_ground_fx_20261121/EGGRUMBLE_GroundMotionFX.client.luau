--!strict
-- EGGRUMBLE FB-015: low-glare ground-contact FX, local player only.
-- A-PREP candidate; NEVER a replacement for combat/hit/castle/egg visuals.
-- No per-frame hooks. Ground parts are client-only, collision-free and short-lived.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")

local PLAYER = Players.LocalPlayer
local FOLDER_NAME = "EGGRUMBLE_GroundMotionFX_Local"
local FEATURE_ID = "GQ470_FB015_GROUND_MOTION_MATTE_20261121"
local STEP_SECONDS = 0.32
local MIN_SPEED = 9
local MAX_LIVE_PARTS = 6
local MAX_PARTS_PER_STEP = 2
local MOBILE_PARTS_PER_STEP = 1
local LIFE_SECONDS = 0.38
local TOUCH = UserInputService.TouchEnabled

local folder = Workspace:FindFirstChild(FOLDER_NAME)
if folder == nil then
    folder = Instance.new("Folder")
    folder.Name = FOLDER_NAME
    folder:SetAttribute("FeatureID", FEATURE_ID)
    folder:SetAttribute("PartBudget", MAX_LIVE_PARTS)
    folder:SetAttribute("TouchPartsPerStep", MOBILE_PARTS_PER_STEP)
    folder.Parent = Workspace
end

local liveParts = 0
local generation = 0
local runningConnection: RBXScriptConnection? = nil
local swimmingConnection: RBXScriptConnection? = nil
local diedConnection: RBXScriptConnection? = nil

local function tint(material: Enum.Material): Color3
    if material == Enum.Material.Water then
        return Color3.fromRGB(173, 211, 220)
    elseif material == Enum.Material.Grass or material == Enum.Material.LeafyGrass then
        return Color3.fromRGB(166, 170, 129)
    elseif material == Enum.Material.Sand or material == Enum.Material.Ground then
        return Color3.fromRGB(210, 184, 144)
    end
    return Color3.fromRGB(177, 174, 169)
end

local function emit(character: Model, root: BasePart, serial: number, waterOnly: boolean): ()
    local rayParams = RaycastParams.new()
    rayParams.FilterType = Enum.RaycastFilterType.Exclude
    rayParams.FilterDescendantsInstances = {character, folder :: Instance}
    rayParams.IgnoreWater = false
    rayParams.RespectCanCollide = not waterOnly
    local origin = if waterOnly then root.Position + Vector3.new(0, 6, 0) else root.Position
    local direction = if waterOnly then Vector3.new(0, -10.0, 0) else Vector3.new(0, -5.8, 0)
    local hit = Workspace:Raycast(origin, direction, rayParams)
    if hit == nil or hit.Normal.Y < 0.70 then
        return -- Never paint air, ceilings or steep walls.
    end
    if waterOnly and hit.Material ~= Enum.Material.Water then
        return -- No splash without a real Terrain-water surface hit.
    elseif not waterOnly and hit.Material == Enum.Material.Water then
        return -- Running dust never paints an uncertain water surface.
    end
    local allowed = math.min(
        if TOUCH then MOBILE_PARTS_PER_STEP else MAX_PARTS_PER_STEP,
        MAX_LIVE_PARTS - liveParts
    )
    if allowed <= 0 then
        return
    end

    local right = root.CFrame.RightVector
    local behind = -root.CFrame.LookVector
    local base = hit.Position + hit.Normal * 0.07 + behind * 0.22
    local color = tint(hit.Material)
    for i = 1, allowed do
        local side = if allowed == 1 then 0 else (if i == 1 then -0.32 else 0.32)
        local part = Instance.new("WedgePart")
        part.Name = "MatteGroundContact"
        part.Size = Vector3.new(0.52, 0.07, 0.28)
        part.CFrame = CFrame.new(base + right * side)
            * CFrame.Angles(0, math.rad((serial % 3) * 13 + i * 26), 0)
        part.Color = color
        part.Material = Enum.Material.SmoothPlastic
        part.Transparency = 0.42
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false
        part.Parent = folder
        liveParts += 1

        TweenService:Create(part, TweenInfo.new(LIFE_SECONDS, Enum.EasingStyle.Quad),
            {Transparency = 1, Size = Vector3.new(0.84, 0.05, 0.50)}
        ):Play()
        Debris:AddItem(part, LIFE_SECONDS + 0.08)
        task.delay(LIFE_SECONDS + 0.10, function()
            liveParts = math.max(0, liveParts - 1)
        end)
    end
end

local function bindCharacter(character: Model): ()
    generation += 1
    local token = generation
    if runningConnection then runningConnection:Disconnect() end
    if swimmingConnection then swimmingConnection:Disconnect() end
    if diedConnection then diedConnection:Disconnect() end

    local humanoid = character:WaitForChild("Humanoid", 6)
    local root = character:WaitForChild("HumanoidRootPart", 6)
    if generation ~= token or not humanoid or not root
        or not humanoid:IsA("Humanoid") or not root:IsA("BasePart") then
        return
    end

    local groundSpeed = 0
    local waterSpeed = 0
    local scheduled = false
    local serial = 0
    local function pulse(): ()
        local inWater = humanoid:GetState() == Enum.HumanoidStateType.Swimming
        local fastEnough = if inWater then waterSpeed >= 6 else groundSpeed >= MIN_SPEED
        if generation ~= token or humanoid.Health <= 0 or not fastEnough
            or humanoid.MoveDirection.Magnitude < 0.2 then
            scheduled = false
            return
        end
        if inWater or humanoid.FloorMaterial ~= Enum.Material.Air then
            serial += 1
            emit(character, root, serial, inWater)
        end
        task.delay(STEP_SECONDS, pulse)
    end

    runningConnection = humanoid.Running:Connect(function(speed: number)
        groundSpeed = speed
        if speed >= MIN_SPEED and humanoid:GetState() ~= Enum.HumanoidStateType.Swimming
            and not scheduled then
            scheduled = true
            pulse()
        end
    end)
    swimmingConnection = humanoid.Swimming:Connect(function(speed: number)
        waterSpeed = speed
        if speed >= 6 and humanoid:GetState() == Enum.HumanoidStateType.Swimming
            and not scheduled then
            scheduled = true
            pulse()
        end
    end)
    diedConnection = humanoid.Died:Connect(function()
        generation += 1
        scheduled = false
    end)
end

PLAYER.CharacterRemoving:Connect(function()
    generation += 1 -- invalidates every pending callback without running a loop.
    if runningConnection then runningConnection:Disconnect() end
    if diedConnection then diedConnection:Disconnect() end
end)
PLAYER.CharacterAdded:Connect(bindCharacter)
if PLAYER.Character then
    task.defer(bindCharacter, PLAYER.Character)
end
