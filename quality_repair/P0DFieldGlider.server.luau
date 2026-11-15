--!strict
-- FB-020 / FB-021: collectible field glider. Server-owned pickup, real Tool use.
-- PRIVATE SOURCE ONLY. Does not own damage/egg/score/Store/Remote.
-- Staged as one additional Script under ServerScriptService by the authorized RC integrator.
-- Live mode remains OFF unless explicitly server-enabled; Studio test is allowed.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local Debris = game:GetService("Debris")

if not RunService:IsStudio()
    and ServerStorage:GetAttribute("P0D_FIELD_GLIDER_ENABLED") ~= true then
    return
end

local world = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not world then
    warn("FB020_FIELD_GLIDER_MISSING_WORLD")
    return
end
local grass = world:WaitForChild("GrassArena", 10)
if not grass or not grass:IsA("BasePart") or not grass.Anchored then
    warn("FB020_FIELD_GLIDER_MISSING_GROUND")
    return
end
if world:FindFirstChild("P0D_FIELD_GLIDER_V1") then return end

local ROOT_NAME = "P0D_FIELD_GLIDER_V1"
local TOOL_NAME = "風の翼"
local TOOL_ID = "P0D_FIELD_GLIDER_TOOL"
local MAX_FLIGHT_SECONDS = 4.0
local RESTOCK_SECONDS = 30
local TRAVEL_SPEED = 40
local active: {[Player]: boolean} = {}
local rootFolder = Instance.new("Folder")
rootFolder.Name = ROOT_NAME
rootFolder.Parent = world

local function makePart(parent: Instance, name: string, size: Vector3,
    color: Color3, material: Enum.Material): Part
    local part = Instance.new("Part")
    part.Name = name
    part.Size = size
    part.Color = color
    part.Material = material
    part.Anchored = false
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.Massless = true
    part.Parent = parent
    return part
end

local function hasGlider(player: Player): boolean
    local character = player.Character
    local backpack = player:FindFirstChildOfClass("Backpack")
    for _, container in ipairs({character, backpack}) do
        if container then
            for _, child in ipairs(container:GetChildren()) do
                if child:IsA("Tool") and child:GetAttribute(TOOL_ID) == true then
                    return true
                end
            end
        end
    end
    return active[player] == true
end

local function makeGlider(player: Player): Tool
    local tool = Instance.new("Tool")
    tool.Name = TOOL_NAME
    tool.ToolTip = "タップ/クリックで4秒間の滑空"
    tool.CanBeDropped = false
    tool.RequiresHandle = true
    tool:SetAttribute(TOOL_ID, true)
    local handle = makePart(tool, "Handle", Vector3.new(1, 0.3, 2),
        Color3.fromRGB(207, 178, 110), Enum.Material.Wood)
    handle.Shape = Enum.PartType.Block
    for _, side in ipairs({-1, 1}) do
        local wing = makePart(tool, "FeatherWing", Vector3.new(0.4, 0.18, 2.2),
            Color3.fromRGB(120, 213, 220), Enum.Material.SmoothPlastic)
        wing.Shape = Enum.PartType.Wedge
        wing.CFrame = handle.CFrame * CFrame.new(side * 0.7, 0, 0)
            * CFrame.Angles(0, side * 0.6, 0)
        local weld = Instance.new("WeldConstraint")
        weld.Part0 = handle
        weld.Part1 = wing
        weld.Parent = wing
    end

    local consumed = false
    tool.Activated:Connect(function()
        if consumed or active[player] then return end
        local character = player.Character
        if not character or tool.Parent ~= character then return end
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        local hrp = character:FindFirstChild("HumanoidRootPart")
        if not humanoid or not hrp or not hrp:IsA("BasePart")
            or humanoid.Health <= 0 then return end
        -- This prototype never writes egg, HP, score, KO or round state.
        -- The integrator must bind canonical egg-carry restrictions before live enable.
        if math.abs(hrp.Position.X) > grass.Size.X * 0.5 - 6
            or math.abs(hrp.Position.Z) > grass.Size.Z * 0.5 - 6
            or hrp.Position.Z > 300 then return end
        consumed = true
        active[player] = true
        tool.Enabled = false

        local attachment = Instance.new("Attachment")
        attachment.Name = "P0D_GliderFlight"
        attachment.Parent = hrp
        local force = Instance.new("LinearVelocity")
        force.Name = "P0D_GliderMotion"
        force.Attachment0 = attachment
        force.RelativeTo = Enum.ActuatorRelativeTo.World
        force.VectorVelocity = Vector3.new(0, 2, 0)
        force.MaxForce = 22000
        force.ForceLimitsEnabled = false
        force.Parent = hrp
        local move = humanoid.MoveDirection
        hrp.AssemblyLinearVelocity = move * 28 + Vector3.new(0, 30, 0)
        local expires = os.clock() + MAX_FLIGHT_SECONDS
        local connection: RBXScriptConnection?
        local function finish()
            if connection then connection:Disconnect(); connection = nil end
            if force.Parent then force:Destroy() end
            if attachment.Parent then attachment:Destroy() end
            active[player] = nil
            if tool.Parent then tool:Destroy() end
        end
        connection = RunService.Heartbeat:Connect(function()
            if os.clock() >= expires or player.Character ~= character
                or humanoid.Health <= 0 or not hrp.Parent then
                finish()
                return
            end
            local direction = humanoid.MoveDirection
            if direction.Magnitude > 1 then direction = direction.Unit end
            local pos = hrp.Position
            if math.abs(pos.X) >= grass.Size.X * 0.5 - 8
                or math.abs(pos.Z) >= grass.Size.Z * 0.5 - 8 then
                direction = Vector3.zero
            end
            -- Genuine movement on server; move direction follows keyboard / touch joystick.
            force.VectorVelocity = direction * TRAVEL_SPEED + Vector3.new(0, -4, 0)
        end)
        Debris:AddItem(tool, MAX_FLIGHT_SECONDS + 2)
    end)
    return tool
end

local stations = {
    Vector2.new(-54, -43), Vector2.new(54, -43),
    Vector2.new(-54, 43), Vector2.new(54, 43),
}
for index, coords in ipairs(stations) do
    local stand = Instance.new("Part")
    stand.Name = "GliderPickup_" .. index
    stand.Shape = Enum.PartType.Cylinder
    stand.Size = Vector3.new(1.1, 2.8, 2.8)
    stand.Material = Enum.Material.Slate
    stand.Color = Color3.fromRGB(110, 149, 163)
    stand.CFrame = CFrame.new(coords.X, grass.Position.Y + grass.Size.Y * .5 + 1.5, coords.Y)
        * CFrame.Angles(0, 0, math.pi / 2)
    stand.Anchored = true
    stand.CanCollide = false
    stand.CanTouch = false
    stand.Parent = rootFolder

    local prompt = Instance.new("ProximityPrompt")
    prompt.ActionText = "拾う"
    prompt.ObjectText = TOOL_NAME
    prompt.HoldDuration = 0.15
    prompt.KeyboardKeyCode = Enum.KeyCode.E
    prompt.MaxActivationDistance = 8
    prompt.RequiresLineOfSight = true
    prompt.Parent = stand
    local available = true
    prompt.Triggered:Connect(function(player: Player)
        if not available or hasGlider(player) then return end
        local character = player.Character
        local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
        local hrp = if character then character:FindFirstChild("HumanoidRootPart") else nil
        local backpack = player:FindFirstChildOfClass("Backpack")
        if not humanoid or humanoid.Health <= 0 or not hrp
            or not hrp:IsA("BasePart") or not backpack then return end
        if (hrp.Position - stand.Position).Magnitude > 10 then return end
        available = false
        prompt.Enabled = false
        stand.Transparency = .65
        local tool = makeGlider(player)
        tool.Parent = backpack
        task.delay(RESTOCK_SECONDS, function()
            if stand.Parent then
                available = true
                prompt.Enabled = true
                stand.Transparency = 0
            end
        end)
    end)
end
Players.PlayerRemoving:Connect(function(player)
    active[player] = nil
end)
