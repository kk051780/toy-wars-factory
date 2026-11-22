--!strict
-- GQ470 FB-015: visual wake for actual LSS server-pivot SEA craft.
-- CLIENT-ONLY; does not change gameplay, character velocity, collisions or GUI.
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
local MAX_SEAT_WATER_HEIGHT = 12
local WATER_NAMES = {"COASTAL_WATER_VISUAL_ONLY", "OFFSHORE_NAVIGABLE_SEA_LANE"}

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

local function isSeaCraft(seat: BasePart?): boolean
    if seat == nil or not seat:IsA("VehicleSeat") or seat.Name ~= "PilotSeat" then
        return false
    end
    local craft = seat.Parent
    if not craft or not craft:IsA("Model") then return false end
    -- Exact current source: makeRide() names BUILDER_SEA_BOAT_<userid> /
    -- BEAST_SEA_BEAST_<userid>. This intentionally excludes AIRSHIP/SKY_BEAST.
    return craft.Name:match("^BUILDER_SEA_BOAT_%d+$") ~= nil
        or craft.Name:match("^BEAST_SEA_BEAST_%d+$") ~= nil
end

local function waterSurface(craft: Model, sample: Vector3): Vector3?
    local scene = craft.Parent
    if scene == nil or not scene:IsDescendantOf(Workspace) then return nil end
    -- LSS sea is NON-COLLIDING, anchored GLASS Parts; there is NO Terrain water.
    -- Use exact scene-owned geometry, never a generic ray through solid ground.
    for _, name in WATER_NAMES do
        local water = scene:FindFirstChild(name)
        if water and water:IsA("BasePart") then
            local localPos = water.CFrame:PointToObjectSpace(sample)
            local maxX = water.Size.X * 0.5 - 1
            local maxZ = water.Size.Z * 0.5 - 1
            local top = water.Size.Y * 0.5
            if maxX > 0 and maxZ > 0
                and math.abs(localPos.X) <= maxX and math.abs(localPos.Z) <= maxZ
                and localPos.Y >= top and localPos.Y <= top + MAX_SEAT_WATER_HEIGHT then
                return water.CFrame:PointToWorldSpace(Vector3.new(
                    localPos.X, top + 0.10, localPos.Z))
            end
        end
    end
    return nil
end

local function emitWake(seat: VehicleSeat, motion: Vector3, serial: number): ()
    local horizontal = Vector3.new(motion.X, 0, motion.Z)
    if horizontal.Magnitude < MIN_HORIZONTAL_SPEED then return end
    local forward = horizontal.Unit
    local camera = Workspace.CurrentCamera
    if camera == nil or (camera.CFrame.Position - seat.Position).Magnitude > CAMERA_FX_DISTANCE then
        return
    end
    local craft = seat.Parent
    if not craft or not craft:IsA("Model") then return end
    -- Original sea hull is 13 studs long, so a wake only four studs behind
    -- the pilot is hidden INSIDE the boat. Sample the visible stern instead.
    local stern = seat.Position - forward * 9.0
    if waterSurface(craft, stern) == nil then return end
    local maxPerPulse = if TOUCH then MOBILE_PARTS_PER_PULSE else MAX_PARTS_PER_PULSE
    local allowed = math.min(maxPerPulse, MAX_LIVE_PARTS - liveParts)
    if allowed <= 0 then return end

    local right = Vector3.new(-forward.Z, 0, forward.X)
    for i = 1, allowed do
        -- Desktop: two angled V-shaped ribbons aft of the pontoons.
        -- Touch: alternate one flank each pulse rather than spawning two.
        local sideSign = if allowed == 1 then (if serial % 2 == 0 then 1 else -1)
            else (if i == 1 then -1 else 1)
        local position = waterSurface(craft, stern + right * (sideSign * 4.1))
        if position then
            local part = Instance.new("WedgePart")
            part.Name = "MatteBoatWake"
            part.Size = Vector3.new(1.7, 0.055, 0.65)
            part.CFrame = CFrame.lookAt(position, position - forward)
                * CFrame.Angles(0, math.rad(sideSign * 18), 0)
            part.Color = Color3.fromRGB(189, 217, 222)
            part.Material = Enum.Material.SmoothPlastic
            part.Transparency = 0.54
            part.Anchored = true
            part.CanCollide = false
            part.CanTouch = false
            part.CanQuery = false
            part.CastShadow = false
            liveParts += 1
            part.Destroying:Connect(function()
                liveParts = math.max(0, liveParts - 1)
            end)
            part.Parent = folder
            TweenService:Create(part, TweenInfo.new(LIFE_SECONDS, Enum.EasingStyle.Quad),
                {Transparency = 1, Size = Vector3.new(2.5, 0.035, 0.85)}
            ):Play()
            Debris:AddItem(part, LIFE_SECONDS + 0.05)
        end
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
        clearVisuals()
        if not isSeaCraft(seatPart) then return end
        local seat = seatPart :: VehicleSeat
        -- The existing LSS server moves ANCHORED craft with Model:PivotTo.
        -- AssemblyLinearVelocity may remain zero. Use real replicated displacement.
        local lastPosition = seat.Position
        local pulseSerial = 0
        local function pulse(): ()
            if generation ~= seatToken or humanoid.Health <= 0 or not seat:IsDescendantOf(Workspace)
                or humanoid.SeatPart ~= seat then
                return
            end
            local position = seat.Position
            local moved = position - lastPosition
            lastPosition = position
            pulseSerial += 1
            emitWake(seat, moved / PULSE_SECONDS, pulseSerial)
            task.delay(PULSE_SECONDS, pulse)
        end
        task.delay(PULSE_SECONDS, pulse)
    end
    seatedConnection = humanoid.Seated:Connect(function(active: boolean, seat: BasePart?)
        startWake(if active then seat else nil)
    end)
    diedConnection = humanoid.Died:Connect(function()
        generation += 1
        clearVisuals()
        if seatedConnection then seatedConnection:Disconnect() end
    end)
    if humanoid.SeatPart then startWake(humanoid.SeatPart) end
end

PLAYER.CharacterRemoving:Connect(function()
    generation += 1
    if seatedConnection then seatedConnection:Disconnect() end
    if diedConnection then diedConnection:Disconnect() end
    clearVisuals()
end)
PLAYER.CharacterAdded:Connect(bindCharacter)
if PLAYER.Character then task.defer(bindCharacter, PLAYER.Character) end
