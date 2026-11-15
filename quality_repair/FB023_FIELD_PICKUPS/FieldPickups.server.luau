-- P0D FB023 / private-source candidate.
-- Standalone ServerScriptService Script: actual world pickups -> real Tool -> server effect.
-- Deliberately does not own HP, egg, KO, inventory persistence or Game remotes.
-- Public servers stay OFF until the official RC writer explicitly adopts/authorizes.
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")

local enabled = RunService:IsStudio()
    or (game.PrivateServerId ~= "" and workspace:GetAttribute("P0D_PRIVATE_FIELD_ITEMS") == true)
if not enabled then
    return
end

local RESPAWN_SECONDS = 18
local MAX_PICKUP_DISTANCE = 11
local MAX_EQUIPPED_SAME_ITEM = 1
local PREFIX = "P0D_FB023_"
local stations = {
    { id = "HAMMER", label = "衝撃ハンマー", pos = Vector3.new(0, 0, -38), tint = Color3.fromRGB(255, 145, 57) },
    { id = "SWIFT", label = "疾風の羽根", pos = Vector3.new(-33, 0, 8), tint = Color3.fromRGB(85, 219, 245) },
    { id = "SHIELD", label = "守護の護符", pos = Vector3.new(33, 0, 8), tint = Color3.fromRGB(138, 245, 151) },
}

local folder = workspace:FindFirstChild("P0D_FieldPickups_FB023")
if folder then
    -- Do not create duplicate prompts/items if another copy is installed by accident.
    return
end
folder = Instance.new("Folder")
folder.Name = "P0D_FieldPickups_FB023"
folder.Parent = workspace

local function livingCharacter(player)
    local char = player.Character
    local root = char and char:FindFirstChild("HumanoidRootPart")
    local hum = char and char:FindFirstChildOfClass("Humanoid")
    if not (root and hum and hum.Health > 0) then
        return nil, nil, nil
    end
    return char, root, hum
end

local function getGroundPosition(position)
    local filter = RaycastParams.new()
    filter.FilterType = Enum.RaycastFilterType.Exclude
    filter.FilterDescendantsInstances = { folder }
    local hit = workspace:Raycast(Vector3.new(position.X, 170, position.Z), Vector3.new(0, -340, 0), filter)
    if not hit then
        return nil
    end
    return Vector3.new(position.X, hit.Position.Y + 2.1, position.Z)
end

local function flash(center, color, size)
    local ring = Instance.new("Part")
    ring.Name = "PickupEffect"
    ring.Anchored = true
    ring.CanCollide = false
    ring.CanTouch = false
    ring.CanQuery = false
    ring.Shape = Enum.PartType.Ball
    ring.Material = Enum.Material.Neon
    ring.Color = color
    ring.Transparency = 0.45
    ring.Size = Vector3.new(1, 1, 1)
    ring.CFrame = CFrame.new(center)
    ring.Parent = folder
    local tween = TweenService:Create(ring, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        Size = Vector3.new(size, size, size), Transparency = 1,
    })
    tween:Play()
    Debris:AddItem(ring, 0.4)
end

local function knockbackEnemies(player, root)
    -- Server physics only. No Health subtraction or score mutation: central Game keeps authority.
    local overlap = OverlapParams.new()
    overlap.FilterType = Enum.RaycastFilterType.Exclude
    overlap.FilterDescendantsInstances = { player.Character, folder }
    overlap.MaxParts = 120
    local seen = {}
    local hits = 0
    for _, part in ipairs(workspace:GetPartBoundsInRadius(root.Position, 17, overlap)) do
        local model = part:FindFirstAncestorOfClass("Model")
        local hum = model and model:FindFirstChildOfClass("Humanoid")
        local otherRoot = model and model:FindFirstChild("HumanoidRootPart")
        if hum and otherRoot and hum.Health > 0 and not seen[model] and not otherRoot.Anchored then
            seen[model] = true
            local opponent = Players:GetPlayerFromCharacter(model)
            if not (opponent and opponent.Team ~= nil and opponent.Team == player.Team) then
                local direction = otherRoot.Position - root.Position
                if direction.Magnitude > 0.5 then
                    local mass = otherRoot.AssemblyMass
                    otherRoot:ApplyImpulse((direction.Unit * 44 + Vector3.new(0, 15, 0)) * mass)
                    hits += 1
                    if hits >= 8 then break end
                end
            end
        end
    end
    flash(root.Position, Color3.fromRGB(255, 160, 60), 16)
end

local function applySwift(hum, root)
    -- Do not overwrite newer job/wind movement changes on expiry.
    local before = hum.WalkSpeed
    local boosted = math.max(before, math.min(before + 8, 34))
    hum.WalkSpeed = boosted
    flash(root.Position, Color3.fromRGB(85, 219, 245), 7)
    task.delay(7, function()
        if hum.Parent and math.abs(hum.WalkSpeed - boosted) < 0.01 then
            hum.WalkSpeed = before
        end
    end)
end

local function applyShield(char, root)
    local forceField = Instance.new("ForceField")
    forceField.Name = PREFIX .. "Shield"
    forceField.Visible = true
    forceField.Parent = char
    flash(root.Position, Color3.fromRGB(138, 245, 151), 8)
    Debris:AddItem(forceField, 4)
end

local function makeTool(station, player)
    local tool = Instance.new("Tool")
    tool.Name = station.label
    tool.ToolTip = "装備してタップ/クリックで使う (使い切り)"
    tool.CanBeDropped = false
    tool.RequiresHandle = true
    tool:SetAttribute("P0D_FB023_Type", station.id)
    local grip = Instance.new("Part")
    grip.Name = "Handle"
    grip.Shape = Enum.PartType.Cylinder
    grip.Size = Vector3.new(0.55, 2.1, 0.55)
    grip.Color = station.tint
    grip.Material = Enum.Material.Metal
    grip.Massless = true
    grip.CanCollide = false
    grip.CanTouch = false
    grip.CanQuery = false
    grip.Parent = tool
    if station.id == "HAMMER" then
        local head = Instance.new("Part")
        head.Name = "HammerHead"
        head.Size = Vector3.new(2.2, 0.75, 0.9)
        head.Color = Color3.fromRGB(244, 210, 103)
        head.Material = Enum.Material.Metal
        head.CanCollide = false
        head.CanTouch = false
        head.CanQuery = false
        head.Massless = true
        head.CFrame = grip.CFrame * CFrame.new(0, 0.9, 0)
        head.Parent = tool
        local weld = Instance.new("WeldConstraint")
        weld.Part0 = grip
        weld.Part1 = head
        weld.Parent = head
    end
    local used = false
    tool.Activated:Connect(function()
        if used or not tool.Enabled then return end
        local char, root, hum = livingCharacter(player)
        if not char or tool.Parent ~= char then return end
        used = true
        tool.Enabled = false
        if station.id == "HAMMER" then
            knockbackEnemies(player, root)
        elseif station.id == "SWIFT" then
            applySwift(hum, root)
        elseif station.id == "SHIELD" then
            applyShield(char, root)
        end
        tool:Destroy()
    end)
    return tool
end

local function ownsItem(player, itemName)
    local char = player.Character
    local backpack = player:FindFirstChildOfClass("Backpack")
    return (char and char:FindFirstChild(itemName) ~= nil)
        or (backpack and backpack:FindFirstChild(itemName) ~= nil)
end

for _, station in ipairs(stations) do
    local position = getGroundPosition(station.pos)
    if position then
        local pad = Instance.new("Part")
        pad.Name = PREFIX .. station.id
        pad.Shape = Enum.PartType.Ball
        pad.Size = Vector3.new(2.5, 2.5, 2.5)
        pad.Anchored = true
        pad.CanCollide = false -- never block egg raiders/solo bots
        pad.CanTouch = false
        pad.CanQuery = false
        pad.Material = Enum.Material.Neon
        pad.Color = station.tint
        pad.Position = position
        pad.Parent = folder
        local prompt = Instance.new("ProximityPrompt")
        prompt.ActionText = "拾う"
        prompt.ObjectText = station.label
        prompt.HoldDuration = 0.15
        prompt.MaxActivationDistance = 10
        prompt.RequiresLineOfSight = false
        prompt.Parent = pad
        local available = true
        prompt.Triggered:Connect(function(player)
            if not available or not player or not player:IsDescendantOf(Players) then return end
            local _, root = livingCharacter(player)
            if not root or (root.Position - pad.Position).Magnitude > MAX_PICKUP_DISTANCE then return end
            if MAX_EQUIPPED_SAME_ITEM == 1 and ownsItem(player, station.label) then return end
            local backpack = player:FindFirstChildOfClass("Backpack")
            if not backpack then return end
            available = false -- atomic server-side claim BEFORE handing Tool
            prompt.Enabled = false
            pad.Transparency = 0.82
            local tool = makeTool(station, player)
            tool.Parent = backpack
            task.delay(RESPAWN_SECONDS, function()
                if pad.Parent then
                    available = true
                    pad.Transparency = 0
                    prompt.Enabled = true
                end
            end)
        end)
    end
end
