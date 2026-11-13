-- P0D World-Character Synergy F01+C01 (S2+ isolated candidate)
-- ServerScriptService only. Sole #220 integrator opts in with a placed anchor.
-- No Game, Remote, score, HP, XP, DataStore, or purchase authority.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")

local anchor = Workspace:FindFirstChild("P0D_CrystalCanyonAnchor")
if not anchor or not anchor:IsA("BasePart") or anchor:GetAttribute("P0DWorldOptIn") ~= true then
    warn("[P0D/WCS] Crystal Canyon not installed: opt-in anchor is absent")
    return
end
if Workspace:FindFirstChild("P0D_WCS_CrystalCanyon") then
    warn("[P0D/WCS] Crystal Canyon already exists; avoiding duplicate world")
    return
end

local world = Instance.new("Model")
world.Name = "P0D_WCS_CrystalCanyon"
world.Parent = Workspace

local function makePart(name, size, x, y, z, color, material, transparent)
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Anchored = true
    p.CanCollide = true
    p.CFrame = anchor.CFrame * CFrame.new(x, y, z)
    p.Color = color
    p.Material = material or Enum.Material.SmoothPlastic
    p.Transparency = transparent or 0
    p.TopSurface = Enum.SurfaceType.Smooth
    p.BottomSurface = Enum.SurfaceType.Smooth
    p.Parent = world
    return p
end

local slate = Color3.fromRGB(61, 66, 105)
local violet = Color3.fromRGB(169, 113, 255)
local gold = Color3.fromRGB(255, 211, 76)
local grass = Color3.fromRGB(76, 163, 113)

-- Fixed safe route at z=30; optional shortcut at z=0. Bridge never disappears.
makePart("WestBank", Vector3.new(50, 4, 85), -50, -2, 0, grass, Enum.Material.Grass)
makePart("EastBank", Vector3.new(50, 4, 85), 50, -2, 0, grass, Enum.Material.Grass)
makePart("AlwaysOpenSafeRoute", Vector3.new(50, 3, 12), 0, -1.5, 30, slate, Enum.Material.Slate)
makePart("ShortcutBridge", Vector3.new(50, 2, 12), 0, -1, 0, slate, Enum.Material.Slate)
makePart("CrystalCanyonBottom", Vector3.new(50, 2, 85), 0, -22, 0, slate, Enum.Material.Slate)

-- Prevent a fallen player from being stuck: visible staircase back to a bank.
for i = 0, 9 do
    local x = -20 - i * 3
    local y = -19 + i * 2
    makePart("ReturnStep_" .. tostring(i), Vector3.new(6, 1.5, 10), x, y, -28, slate, Enum.Material.Slate)
end
for i = 0, 9 do
    local x = 20 + i * 3
    local y = -19 + i * 2
    makePart("ReturnStepEast_" .. tostring(i), Vector3.new(6, 1.5, 10), x, y, -28, slate, Enum.Material.Slate)
end
for i = 1, 7 do
    local x = -22 + i * 6
    local crystal = makePart("Crystal_" .. tostring(i), Vector3.new(2, 8 + i % 3 * 3, 2), x, 3, -13, violet, Enum.Material.Neon, 0.12)
    crystal.CanCollide = false
end

-- All teams use the same gate. Keep it open only while a living avatar occupies the gate collision zone.
local gate = makePart("ShortcutGate", Vector3.new(3, 9, 12), 0, 4.5, 0, violet, Enum.Material.Neon, 0.15)
local gateOpen = false
local openUntil = 0
local nextOpenAllowed = 0
local OPEN_SECONDS = 14
local REOPEN_COOLDOWN = 4

local function playerIsInGateClosureZone()
    for _, player in ipairs(Players:GetPlayers()) do
        local character = player.Character
        local root = character and character:FindFirstChild("HumanoidRootPart")
        local humanoid = character and character:FindFirstChildOfClass("Humanoid")
        if root and humanoid and humanoid.Health > 0 then
            local localPoint = anchor.CFrame:PointToObjectSpace(root.Position)
            if math.abs(localPoint.X) <= 3.5 and math.abs(localPoint.Z) <= 8
                and localPoint.Y >= -3 and localPoint.Y <= 13 then
                return true
            end
        end
    end
    return false
end

local function setGateOpen(open)
    -- The cooldown begins when the gate ACTUALLY closes, including when
    -- a player delays closure beyond the nominal 14-second open period.
    if gateOpen and not open then
        nextOpenAllowed = os.clock() + REOPEN_COOLDOWN
    end
    gateOpen = open
    gate.CanCollide = not open
    gate.Transparency = open and 0.9 or 0.15
    gate.Color = open and grass or violet
    gate:SetAttribute("WCS_GateOpen", open)
end

local function openGate()
    local now = os.clock()
    if gateOpen or now < nextOpenAllowed then
        return
    end
    setGateOpen(true)
    openUntil = now + OPEN_SECONDS
    nextOpenAllowed = now + OPEN_SECONDS + REOPEN_COOLDOWN
end

local function makeMole(name, x)
    local mob = Instance.new("Model")
    mob.Name = name
    mob.Parent = world
    local torso = makePart(name .. "_Body", Vector3.new(4, 3, 4), x, 2.4, 0,
        Color3.fromRGB(158, 101, 65), Enum.Material.SmoothPlastic)
    torso.Shape = Enum.PartType.Ball
    torso.Parent = mob
    local nose = makePart(name .. "_Nose", Vector3.new(1.6, 1.2, 1.6), x, 2.7, -2,
        gold, Enum.Material.Neon)
    nose.Shape = Enum.PartType.Ball
    nose.CanCollide = false
    nose.Parent = mob

    local prompt = Instance.new("ProximityPrompt")
    prompt.Name = "OpenCrystalBridge"
    prompt.ActionText = "橋をひらく"
    prompt.ObjectText = "橋掘りモグロン"
    prompt.HoldDuration = 0.5
    prompt.MaxActivationDistance = 12
    prompt.RequiresLineOfSight = false
    prompt.Parent = torso
    prompt.Triggered:Connect(function(player)
        if not player or not player.Character then
            return
        end
        local root = player.Character:FindFirstChild("HumanoidRootPart")
        local humanoid = player.Character:FindFirstChildOfClass("Humanoid")
        if not root or not humanoid or humanoid.Health <= 0 then
            return
        end
        if (root.Position - torso.Position).Magnitude > 13 then
            return
        end
        openGate()
    end)

    local billboard = Instance.new("BillboardGui")
    billboard.Name = "WCSLabel"
    billboard.Size = UDim2.fromOffset(220, 64)
    billboard.StudsOffset = Vector3.new(0, 4, 0)
    billboard.AlwaysOnTop = true
    billboard.MaxDistance = 45
    billboard.Parent = torso
    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.BackgroundTransparency = 1
    label.Text = "モグロン\n橋をひらく！"
    label.TextColor3 = Color3.fromRGB(255, 255, 255)
    label.TextStrokeTransparency = 0.1
    label.TextScaled = true
    label.Font = Enum.Font.GothamBold
    label.Parent = billboard
end

-- One on each shore makes the opportunity symmetrical for red and blue.
makeMole("MoguronWest", -32)
makeMole("MoguronEast", 32)
setGateOpen(false)

task.spawn(function()
    while world.Parent do
        if gateOpen and os.clock() >= openUntil and not playerIsInGateClosureZone() then
            setGateOpen(false)
        end
        task.wait(0.5)
    end
end)

world:SetAttribute("WCS_FeatureId", "WCS-F01-C01")
world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")
