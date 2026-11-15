--!strict
-- P0D-031 / FB item+flight: in-world, usable flight pickup (one server Script).
-- Non-public preview only. No new Remote, Game owner, combat, score or save mutation.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

if not RunService:IsServer() then return end
if not RunService:IsStudio() then
    if game.PrivateServerId == "" or script:GetAttribute("EnablePrivatePreview") ~= true then
        return
    end
end

local world = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not world then warn("P0D031_WORLD_MISSING") return end
local grass = world:WaitForChild("GrassArena", 12)
if not grass or not grass:IsA("BasePart") then
    warn("P0D031_GRASS_ANCHOR_MISSING")
    return
end
if world:FindFirstChild("P0D031_SKY_FEATHER_ITEMS") then return end

local ITEM_NAME = "飛行羽｜8秒飛行"
local ITEM_ID = "P0D031_SKY_FEATHER_V1"
local FLIGHT_SECONDS = 8
local RESPAWN_SECONDS = 14
local MAX_ALTITUDE = 48
local MAX_HORIZ_SPEED = 31
local folder = Instance.new("Folder")
folder.Name = "P0D031_SKY_FEATHER_ITEMS"
folder.Parent = world
folder:SetAttribute("FeatureId", "P0D-031")
folder:SetAttribute("EngineQA", "NOT_TESTED")

local active: {[Player]: {cleanup: () -> ()}} = {}

local function insideArena(pos: Vector3): boolean
    local localPos = grass.CFrame:PointToObjectSpace(pos)
    return math.abs(localPos.X) <= grass.Size.X * .5 - 4
        and math.abs(localPos.Z) <= grass.Size.Z * .5 - 4
        and localPos.Y >= -12 and localPos.Y <= MAX_ALTITUDE + grass.Size.Y * .5
end

local function hasFeather(player: Player): boolean
    for _, home in ipairs({player:FindFirstChildOfClass("Backpack"), player.Character}) do
        if home then
            for _, child in ipairs(home:GetChildren()) do
                if child:IsA("Tool") and child:GetAttribute("P0DItemId") == ITEM_ID then
                    return true
                end
            end
        end
    end
    return false
end

local function createTool(player: Player): boolean
    local backpack = player:FindFirstChildOfClass("Backpack")
    if not backpack or hasFeather(player) or active[player] then return false end
    local tool = Instance.new("Tool")
    tool.Name = ITEM_NAME
    tool.ToolTip = "装備してタップ／クリックで上昇・滑空（8秒）"
    tool.CanBeDropped = false
    tool.RequiresHandle = true
    tool:SetAttribute("P0DItemId", ITEM_ID)
    local handle = Instance.new("Part")
    handle.Name = "Handle"
    handle.Size = Vector3.new(.75, 1.3, .32)
    handle.Material = Enum.Material.Neon
    handle.Color = Color3.fromRGB(120, 235, 255)
    handle.Shape = Enum.PartType.Ball
    handle.CanCollide = false
    handle.Massless = true
    handle.Parent = tool
    local used = false
    tool.Activated:Connect(function()
        if used or active[player] or tool.Parent ~= player.Character then return end
        local character = player.Character
        if not character then return end
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        local root = character:FindFirstChild("HumanoidRootPart")
        if not humanoid or humanoid.Health <= 0
            or not root or not root:IsA("BasePart") or not insideArena(root.Position) then
            return
        end
        used = true
        tool.Enabled = false
        local a = Instance.new("Attachment")
        a.Name = "P0D031_FlightAttachment"
        a.Parent = root
        local velocity = Instance.new("LinearVelocity")
        velocity.Name = "P0D031_FlightVelocity"
        velocity.Attachment0 = a
        velocity.RelativeTo = Enum.ActuatorRelativeTo.World
        velocity.VelocityConstraintMode = Enum.VelocityConstraintMode.Vector
        velocity.ForceLimitsEnabled = false
        velocity.VectorVelocity = Vector3.new(0, 12, 0)
        velocity.Parent = root
        local trailA = Instance.new("Attachment")
        trailA.Position = Vector3.new(-.75, -.4, 0)
        trailA.Parent = root
        local trailB = Instance.new("Attachment")
        trailB.Position = Vector3.new(.75, -.4, 0)
        trailB.Parent = root
        local trail = Instance.new("Trail")
        trail.Name = "P0D031_WingTrail"
        trail.Attachment0 = trailA
        trail.Attachment1 = trailB
        trail.Color = ColorSequence.new(Color3.fromRGB(105, 231, 255), Color3.fromRGB(193, 163, 255))
        trail.Lifetime = .25
        trail.MinLength = .1
        trail.Parent = root
        local running = true
        local connection: RBXScriptConnection? = nil
        local function cleanup()
            if not running then return end
            running = false
            if connection then connection:Disconnect() end
            trail:Destroy()
            trailA:Destroy()
            trailB:Destroy()
            velocity:Destroy()
            a:Destroy()
            tool:Destroy()
            active[player] = nil
        end
        active[player] = {cleanup = cleanup}
        local started = os.clock()
        local altitudeLimit = math.min(grass.Position.Y + grass.Size.Y * .5 + MAX_ALTITUDE,
            root.Position.Y + MAX_ALTITUDE)
        connection = RunService.Heartbeat:Connect(function()
            if not running then return end
            local elapsed = os.clock() - started
            if elapsed >= FLIGHT_SECONDS or player.Character ~= character or humanoid.Health <= 0
                or not root:IsDescendantOf(workspace) or not insideArena(root.Position) then
                cleanup()
                return
            end
            local move = humanoid.MoveDirection
            local horizontal = Vector3.new(move.X, 0, move.Z)
            if horizontal.Magnitude > 1 then horizontal = horizontal.Unit end
            local ascent = if elapsed < 2.7 then 12 elseif elapsed < 5.8 then 2 else -6
            if root.Position.Y >= altitudeLimit then ascent = math.min(0, ascent) end
            velocity.VectorVelocity = horizontal * MAX_HORIZ_SPEED + Vector3.new(0, ascent, 0)
        end)
    end)
    -- The standard Roblox inventory Tool button works on mobile; no permanent HUD.
    tool.Parent = backpack
    return true
end

local offsets = {
    Vector2.new(-.20, -.18), Vector2.new(.20, -.18),
    Vector2.new(-.20, .18), Vector2.new(.20, .18),
}
for i, xy in ipairs(offsets) do
    local location = grass.CFrame:PointToWorldSpace(Vector3.new(
        grass.Size.X * xy.X, grass.Size.Y * .5 + 2.6, grass.Size.Z * xy.Y))
    local orb = Instance.new("Part")
    orb.Name = "SKY_FEATHER_PICKUP_" .. i
    orb.Size = Vector3.new(2.6, 2.6, 2.6)
    orb.Shape = Enum.PartType.Ball
    orb.Material = Enum.Material.Neon
    orb.Color = Color3.fromRGB(106, 224, 249)
    orb.Position = location
    orb.Anchored = true
    orb.CanCollide = false
    orb.CanTouch = false
    orb.CanQuery = false
    orb.CastShadow = false
    orb.Parent = folder
    local prompt = Instance.new("ProximityPrompt")
    prompt.Name = "PickUpSkyFeather"
    prompt.ActionText = "拾う"
    prompt.ObjectText = "飛行羽"
    prompt.HoldDuration = .15
    prompt.MaxActivationDistance = 9
    prompt.RequiresLineOfSight = false
    prompt.Parent = orb
    local ready = true
    prompt.Triggered:Connect(function(player: Player)
        if not ready then return end
        local character = player.Character
        local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
        local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
        if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then return end
        if (root.Position - orb.Position).Magnitude > 12 or not insideArena(root.Position) then return end
        if not createTool(player) then return end
        ready = false
        prompt.Enabled = false
        orb.Transparency = .78
        task.delay(RESPAWN_SECONDS, function()
            if not prompt:IsDescendantOf(game) then return end
            ready = true
            prompt.Enabled = true
            orb.Transparency = 0
        end)
    end)
end

Players.PlayerRemoving:Connect(function(player)
    local flight = active[player]
    if flight then flight.cleanup() end
end)
print("P0D031_SKY_FEATHER_PRIVATE_PICKUP_READY", #offsets)
