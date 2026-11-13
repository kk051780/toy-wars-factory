-- P0D WCS-F02+C03: Inverted Sky Lab + Sakasa-Fukuroru
-- An opt-in, S2+ isolated scenery/route candidate. No Game/Remote/score/HP/XP/Store writes.
-- Installing this source alone never alters official RC. #220 owns future admission.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local anchor = Workspace:FindFirstChild("P0D_InvertedSkyAnchor")
if not anchor or not anchor:IsA("BasePart") or anchor:GetAttribute("P0DWorldOptIn") ~= true then
    warn("[P0D/WCS-F02] opt-in anchor is absent; no world generated")
    return
end
if Workspace:FindFirstChild("P0D_WCS_InvertedSkyLab") then
    warn("[P0D/WCS-F02] already exists; refusing duplicate")
    return
end

local world = Instance.new("Model")
world.Name = "P0D_WCS_InvertedSkyLab"
world.Parent = Workspace

local clouds = Color3.fromRGB(224, 240, 255)
local blue = Color3.fromRGB(74, 160, 255)
local violet = Color3.fromRGB(153, 105, 245)
local gold = Color3.fromRGB(255, 210, 83)
local green = Color3.fromRGB(95, 220, 163)
local stone = Color3.fromRGB(87, 103, 143)

local function makePart(name, size, position, color, material)
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Anchored = true
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Material = material or Enum.Material.SmoothPlastic
    p.Color = color
    p.CFrame = anchor.CFrame * CFrame.new(position)
    p.Parent = world
    return p
end

-- Banks and the ALWAYS-OPEN alternative ground-level bridge prevent route lockout.
makePart("WestGround", Vector3.new(52, 4, 96), Vector3.new(-49, -2, 0), green, Enum.Material.Grass)
makePart("EastGround", Vector3.new(52, 4, 96), Vector3.new(49, -2, 0), green, Enum.Material.Grass)
makePart("AlwaysOpenGroundRoute", Vector3.new(48, 3, 12), Vector3.new(0, -1.5, 27), stone, Enum.Material.Slate)
makePart("SkyWalkway", Vector3.new(68, 2, 13), Vector3.new(0, 18, -11), clouds, Enum.Material.SmoothPlastic)
-- Two-sided rails: they cannot be used as a ladder to reach a one-team-only shortcut.
makePart("SkyRailFront", Vector3.new(68, 5, 1), Vector3.new(0, 21.5, -18), blue, Enum.Material.Glass)
makePart("SkyRailBack", Vector3.new(68, 5, 1), Vector3.new(0, 21.5, -4), blue, Enum.Material.Glass)

-- Stairs on BOTH shores make the raised route available even when the wind is off.
for i = 0, 12 do
    local y = 1.5 * i
    local inset = 2 * i
    makePart("WestSafeStair_" .. i, Vector3.new(3, 1.5, 10),
        Vector3.new(-55 + inset, y, -11), stone, Enum.Material.Slate)
    makePart("EastSafeStair_" .. i, Vector3.new(3, 1.5, 10),
        Vector3.new(55 - inset, y, -11), stone, Enum.Material.Slate)
end

local pads = {}
for _, spec in ipairs({
    {side = "West", x = -48},
    {side = "East", x = 48},
}) do
    local pad = makePart("AntiGravityPad" .. spec.side, Vector3.new(12, 1, 11),
        Vector3.new(spec.x, 0.5, -28), violet, Enum.Material.Neon)
    pad:SetAttribute("WCS_Active", false)
    table.insert(pads, {part = pad, side = spec.side, x = spec.x})
    local arrow = makePart("WindArrow" .. spec.side, Vector3.new(2, 0.25, 8),
        Vector3.new(spec.x, 1.2, -20), blue, Enum.Material.Neon)
    arrow.CanCollide = false
end
-- Visual lab landmarks, not load-heavy NPC combat or decorative high-poly geometry.
for i = 1, 5 do
    local dome = makePart("CloudLabTower_" .. i, Vector3.new(6, 7, 6),
        Vector3.new(-27 + i * 9, 23, -11), i % 2 == 0 and blue or violet,
        Enum.Material.Glass)
    dome.Shape = Enum.PartType.Ball
    dome.CanCollide = false
end

local WIND_SECONDS = 20
local REARM_SECONDS = 4
local PAD_COOLDOWN_SECONDS = 3
local windUntil = 0
local nextWind = 0
local lastLaunch = {}
local lastRecovery = {}

local function windActive()
    return os.clock() < windUntil
end

local function updatePads()
    local active = windActive()
    for _, spec in ipairs(pads) do
        spec.part.Color = active and green or violet
        spec.part:SetAttribute("WCS_Active", active)
    end
    world:SetAttribute("WCS_WindActive", active)
end

local function startWind()
    local now = os.clock()
    if now < windUntil or now < nextWind then
        return
    end
    windUntil = now + WIND_SECONDS
    nextWind = windUntil + REARM_SECONDS
    updatePads()
end

local function createOwl(name, x)
    local model = Instance.new("Model")
    model.Name = name
    model.Parent = world
    local body = makePart(name .. "_Body", Vector3.new(4, 4, 3),
        Vector3.new(x, 3, -31), clouds)
    body.Shape = Enum.PartType.Ball
    body.Parent = model
    for _, offset in ipairs({-2.5, 2.5}) do
        local wing = makePart(name .. "_Wing_" .. tostring(offset),
            Vector3.new(3, 1, 2), Vector3.new(x + offset, 3.4, -31), blue)
        wing.Parent = model
        wing.CanCollide = false
    end
    local beak = makePart(name .. "_Beak", Vector3.new(1.2, 1.2, 1.2),
        Vector3.new(x, 2.8, -33), gold)
    beak.Shape = Enum.PartType.Ball
    beak.Parent = model
    beak.CanCollide = false

    local prompt = Instance.new("ProximityPrompt")
    prompt.Name = "StartSkyWind"
    prompt.ActionText = "そらの風をおこす"
    prompt.ObjectText = "逆さフクロル"
    prompt.HoldDuration = 0.4
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt.Parent = body
    prompt.Triggered:Connect(function(player)
        local character = player and player.Character
        local root = character and character:FindFirstChild("HumanoidRootPart")
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if not root or not humanoid or humanoid.Health <= 0 then
            return
        end
        if (root.Position - body.Position).Magnitude > 13 then
            return
        end
        startWind()
    end)

    local billboard = Instance.new("BillboardGui")
    billboard.Name = "OwlHint"
    billboard.Size = UDim2.fromOffset(210, 70)
    billboard.StudsOffset = Vector3.new(0, 5, 0)
    billboard.MaxDistance = 50
    billboard.AlwaysOnTop = true
    billboard.Parent = body
    local label = Instance.new("TextLabel")
    label.Name = "HintText"
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundTransparency = 1
    label.TextScaled = true
    label.Text = "フクロル\n風をおこしてジャンプ！"
    label.TextColor3 = clouds
    label.TextStrokeTransparency = 0.15
    label.Font = Enum.Font.GothamBold
    label.Parent = billboard
end

createOwl("FukuroruWest", -62)
createOwl("FukuroruEast", 62)
updatePads()

for _, spec in ipairs(pads) do
    spec.part.Touched:Connect(function(hit)
        if not windActive() then
            return
        end
        local character = hit:FindFirstAncestorOfClass("Model")
        local player = character and Players:GetPlayerFromCharacter(character)
        if not player then
            return
        end
        local root = character:FindFirstChild("HumanoidRootPart")
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        if not root or not humanoid or humanoid.Health <= 0 or humanoid.Sit or root.Anchored then
            return
        end
        if (root.Position - spec.part.Position).Magnitude > 10 then
            return
        end
        local now = os.clock()
        if now - (lastLaunch[player.UserId] or -100) < PAD_COOLDOWN_SECONDS then
            return
        end
        lastLaunch[player.UserId] = now
        -- Aim inward toward the shared sky walkway; both teams have the same ability.
        local inward = spec.x < 0 and 1 or -1
        local vertical = math.clamp(math.sqrt(2 * Workspace.Gravity * 30), 80, 120)
        local horizontal = anchor.CFrame.RightVector * (inward * 36)
            - anchor.CFrame.LookVector * 15
        root.AssemblyLinearVelocity = horizontal + Vector3.new(0, vertical, 0)
    end)
end

-- Low-profile rescue floor. Dropping below the elevated route moves the player
-- back to the same shore, never to the enemy's goal or to a win/score location.
local catchFloor = makePart("FallRecoveryFloor", Vector3.new(60, 2, 60),
    Vector3.new(0, -14, -13), blue, Enum.Material.Glass)
catchFloor.Transparency = 0.5
catchFloor.Touched:Connect(function(hit)
    local character = hit:FindFirstAncestorOfClass("Model")
    local player = character and Players:GetPlayerFromCharacter(character)
    if not player then
        return
    end
    local root = character:FindFirstChild("HumanoidRootPart")
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if not root or not humanoid or humanoid.Health <= 0 then
        return
    end
    local now = os.clock()
    if now - (lastRecovery[player.UserId] or -100) < 3 then
        return
    end
    local localPosition = anchor.CFrame:PointToObjectSpace(root.Position)
    if localPosition.Y > -8 or math.abs(localPosition.X) > 33 then
        return
    end
    lastRecovery[player.UserId] = now
    root.AssemblyLinearVelocity = Vector3.zero
    root.CFrame = anchor.CFrame * CFrame.new(localPosition.X < 0 and -55 or 55, 5, -38)
end)

Players.PlayerRemoving:Connect(function(player)
    lastLaunch[player.UserId] = nil
    lastRecovery[player.UserId] = nil
end)

task.spawn(function()
    local lastState = false
    while world.Parent do
        local active = windActive()
        if active ~= lastState then
            lastState = active
            updatePads()
        end
        task.wait(0.25)
    end
end)

world:SetAttribute("WCS_FeatureId", "WCS-F02-C03")
world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")
