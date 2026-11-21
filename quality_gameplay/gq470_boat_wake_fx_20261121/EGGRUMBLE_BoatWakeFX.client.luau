--!strict
-- GQ470 FB-015 A-only visual: shallow Terrain-water vehicle wake.
-- LOCAL ONLY; no damage, score, Remote, HUD, Store, collisions or gameplay writes.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")

local FEATURE_ID = "GQ470_FB015_BOAT_WAKE_MATTE_20261121"
local PLAYER = Players.LocalPlayer
local TOUCH = UserInputService.TouchEnabled
local PULSE_SECONDS = 0.28
local LIFE_SECONDS = 0.56
local MIN_HORIZONTAL_SPEED = 10
local MAX_LIVE_PARTS = 6
local MAX_PARTS_PER_PULSE = 2
local MOBILE_PARTS_PER_PULSE = 1
local CAMERA_FX_DISTANCE = 96
local WATER_RAY_LENGTH = 13

local folder = Instance.new("Folder")
folder.Name = "EGGRUMBLE_BoatWakeFX_Local"
folder:SetAttribute("FeatureID", FEATURE_ID)
folder:SetAttribute("PartBudget", MAX_LIVE_PARTS)
folder.Parent = Workspace

local generation = 0
local liveParts = 0
local seatedConnection: RBXScriptConnection? = nil
local diedConnection: RBXScriptConnection? = nil

local function clearVisuals(): ()
    folder:ClearAllChildren()
    liveParts = 0
end

local function emitWake(character: Model, seat: VehicleSeat): ()
    local velocity = seat.AssemblyLinearVelocity
    local flat = Vector3.new(velocity.X, 0, velocity.Z)
    if flat.Magnitude < MIN_HORIZONTAL_SPEED then return end
    local forward = flat.Unit
    local camera = Workspace.CurrentCamera
    if camera == nil or (camera.CFrame.Position - seat.Position).Magnitude > CAMERA_FX_DISTANCE then
        return
    end

    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = {character, seat.Parent, folder}
    params.IgnoreWater = false
    params.RespectCanCollide = false
    local origin = seat.Position + Vector3.new(0, 2, 0) - forward * 4
    local hit = Workspace:Raycast(origin, Vector3.new(0, -WATER_RAY_LENGTH, 0), params)
    -- No wake in air, on solid land, on decorative Water Part, or far from surface.
    if hit == nil or hit.Instance ~= Workspace.Terrain
        or hit.Material ~= Enum.Material.Water or hit.Normal.Y < 0.6 then
        return
    end
    local maxPerPulse = if TOUCH then MOBILE_PARTS_PER_PULSE else MAX_PARTS_PER_PULSE
    local allowed = math.min(maxPerPulse, MAX_LIVE_PARTS - liveParts)
    if allowed <= 0 then return end

    local right = Vector3.new(-forward.Z, 0, forward.X)
    local base = hit.Position + Vector3.new(0, 0.08, 0) - forward * 1.2
    for i = 1, allowed do
        local side = if allowed == 1 then 0 else (if i == 1 then -0.95 else 0.95)
        local part = Instance.new("WedgePart")
        part.Name = "MatteBoatWake"
        part.Size = Vector3.new(1.7, 0.055, 0.65)
        part.CFrame = CFrame.lookAt(base + right * side, base + right * side - forward)
        part.Color = Color3.fromRGB(189, 217, 222)
        part.Material = Enum.Material.SmoothPlastic
        part.Transparency = 0.54
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.CastShadow = false
        part.Parent = folder
        liveParts += 1
        TweenService:Create(part, TweenInfo.new(LIFE_SECONDS, Enum.EasingStyle.Quad),
            {Transparency = 1, Size = Vector3.new(2.5, 0.035, 0.85)}
        ):Play()
        Debris:AddItem(part, LIFE_SECONDS + 0.05)
        task.delay(LIFE_SECONDS + 0.08, function()
            liveParts = math.max(0, liveParts - 1)
        end)
    end
end

local function bindCharacter(character: Model): ()
    generation += 1
    local characterToken = generation
    if seatedConnection then seatedConnection:Disconnect() end
    if diedConnection then diedConnection:Disconnect() end
    clearVisuals()

    local humanoid = character:WaitForChild("Humanoid", 6)
    if characterToken ~= generation or humanoid == nil or not humanoid:IsA("Humanoid") then
        return
    end
    local function startWake(seatPart: BasePart?): ()
        generation += 1
        local seatToken = generation
        if seatPart == nil or not seatPart:IsA("VehicleSeat") then
            clearVisuals()
            return
        end
        local seat = seatPart :: VehicleSeat
        local function pulse(): ()
            if generation ~= seatToken or humanoid.Health <= 0 or not seat:IsDescendantOf(Workspace)
                or humanoid.SeatPart ~= seat then
                return
            end
            emitWake(character, seat)
            task.delay(PULSE_SECONDS, pulse)
        end
        pulse()
    end
    seatedConnection = humanoid.Seated:Connect(function(active: boolean, seat: BasePart?)
        startWake(if active then seat else nil)
    end)
    diedConnection = humanoid.Died:Connect(function()
        generation += 1
        clearVisuals()
        if seatedConnection then seatedConnection:Disconnect() end
    end)
    if humanoid.SeatPart then
        startWake(humanoid.SeatPart)
    end
end

PLAYER.CharacterRemoving:Connect(function()
    generation += 1
    if seatedConnection then seatedConnection:Disconnect() end
    if diedConnection then diedConnection:Disconnect() end
    clearVisuals()
end)
PLAYER.CharacterAdded:Connect(bindCharacter)
if PLAYER.Character then task.defer(bindCharacter, PLAYER.Character) end
