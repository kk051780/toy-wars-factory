--!strict
-- P0D HUD-CLEAN P0: Studio-only presentation correction, NOT another game authority.
-- Existing HUD keeps all attack/touch controls, Game retains HP/egg/score authority.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 30)
if not remote or not remote:IsA("RemoteEvent") then return end
local coreGui = playerGui:WaitForChild("TrapRaidersS1HUD", 30)
if not coreGui or not coreGui:IsA("ScreenGui") then return end
local marker = coreGui:FindFirstChild("P0D_HUD_CLEAN_GOVERNOR")
if marker then return end
marker = Instance.new("BoolValue")
marker.Name = "P0D_HUD_CLEAN_GOVERNOR"
marker.Parent = coreGui

local score = coreGui:FindFirstChild("Score")
local status = coreGui:FindFirstChild("Status")
local instructions = coreGui:FindFirstChild("Instructions")
if not (score and score:IsA("TextLabel")
    and status and status:IsA("TextLabel")
    and instructions and instructions:IsA("TextLabel")) then
    marker:Destroy()
    return -- fail closed if author changes GUI structure
end
local scoreLabel = score :: TextLabel
local statusLabel = status :: TextLabel
local instructionLabel = instructions :: TextLabel
-- Restore the author's lobby/results layout after every match; never let the
-- compact ACTIVE overlay permanently corrupt the existing HUD.
local originalScoreLayout = {
    Size = scoreLabel.Size,
    Position = scoreLabel.Position,
    BackgroundTransparency = scoreLabel.BackgroundTransparency,
    TextScaled = scoreLabel.TextScaled,
    TextSize = scoreLabel.TextSize,
    TextWrapped = scoreLabel.TextWrapped,
}

local hp = Instance.new("TextLabel")
hp.Name = "BattleSelfHPNumerical"
hp.Size = UDim2.fromOffset(120, 28)
hp.Position = UDim2.new(0, 12, 1, -193) -- clear of native mobile thumbstick
hp.BackgroundColor3 = Color3.fromRGB(18, 26, 32)
hp.BackgroundTransparency = 0.55
hp.TextColor3 = Color3.new(1, 1, 1)
hp.TextSize = 15
hp.Font = Enum.Font.GothamBold
hp.Text = "HP --/--"
hp.Visible = false
hp.Parent = coreGui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 6)
corner.Parent = hp

local active = false
local compactScore: string? = nil
local savedEnabled: {[ScreenGui]: boolean} = {}
local OPTIONAL = {
    V4TrialOverlay = true,
    EggJoy = true,
    TrapRaidersCoach = true,
    RealmHuntHUD = true,
    ResultNextStep = true,
    P0DStudioTrialAudit = true,
}
local function updateOptional(gui: Instance)
    if not gui:IsA("ScreenGui") or not OPTIONAL[gui.Name] then return end
    if active then
        if savedEnabled[gui] == nil then savedEnabled[gui] = gui.Enabled end
        gui.Enabled = false
    elseif savedEnabled[gui] ~= nil then
        gui.Enabled = savedEnabled[gui]
        savedEnabled[gui] = nil
    end
end
local function updateOptionalAll()
    for _, child in ipairs(playerGui:GetChildren()) do updateOptional(child) end
end
playerGui.ChildAdded:Connect(function(child)
    task.defer(updateOptional, child)
end)

-- Big world labels were hiding the player/goal. ProximityPrompts are untouched.
local function reduceWorldBillboard(obj: Instance)
    if not obj:IsA("BillboardGui") or obj.Name == "S1_CARRIED_EGG" then return end
    if obj.MaxDistance == 0 or obj.MaxDistance > 36 then
        obj.MaxDistance = 36
    end
    obj.AlwaysOnTop = false
end
for _, instance in ipairs(workspace:GetDescendants()) do reduceWorldBillboard(instance) end
workspace.DescendantAdded:Connect(reduceWorldBillboard)

local humConnection: RBXScriptConnection? = nil
local maxConnection: RBXScriptConnection? = nil
local currentHum: Humanoid? = nil
local function refreshHp()
    local hum = currentHum
    if not hum then hp.Text = "HP --/--" return end
    hp.Text = string.format("HP %d/%d", math.ceil(math.max(0, hum.Health)),
        math.ceil(math.max(0, hum.MaxHealth)))
end
local function bindCharacter(char: Model)
    if humConnection then humConnection:Disconnect() end
    if maxConnection then maxConnection:Disconnect() end
    local hum = char:WaitForChild("Humanoid", 10)
    if hum and hum:IsA("Humanoid") then
        currentHum = hum
        humConnection = hum.HealthChanged:Connect(refreshHp)
        maxConnection = hum:GetPropertyChangedSignal("MaxHealth"):Connect(refreshHp)
    else
        currentHum = nil
    end
    refreshHp()
end
player.CharacterAdded:Connect(bindCharacter)
if player.Character then task.spawn(bindCharacter, player.Character) end

-- The original HUD may receive SNAPSHOT in any listener order. These guards
-- keep extra text hidden even when its older listener changes visibility.
statusLabel:GetPropertyChangedSignal("Visible"):Connect(function()
    if active and statusLabel.Visible then statusLabel.Visible = false end
end)
instructionLabel:GetPropertyChangedSignal("Visible"):Connect(function()
    if active and instructionLabel.Visible then instructionLabel.Visible = false end
end)
scoreLabel:GetPropertyChangedSignal("Text"):Connect(function()
    if active and compactScore and scoreLabel.Text ~= compactScore then
        scoreLabel.Text = compactScore
    end
end)
local function bounded(value: any): number
    if type(value) ~= "number" or value ~= value then return 0 end
    return math.clamp(math.floor(value), 0, 99999)
end
remote.OnClientEvent:Connect(function(packet: any)
    if type(packet) ~= "table" or packet.kind ~= "SNAPSHOT" then return end
    active = packet.phase == "ACTIVE"
    hp.Visible = active
    if active then
        local castle = if type(packet.hp) == "table" then packet.hp else {}
        local scores = if type(packet.scores) == "table" then packet.scores else {}
        local maximum = bounded(packet.maxHp)
        local remaining = bounded(packet.time)
        compactScore = string.format("🔴城 %d/%d  🔵城 %d/%d   🥚 %d-%d   ⏱ %02d:%02d",
            bounded(castle.RED), maximum, bounded(castle.BLUE), maximum,
            bounded(scores.RED), bounded(scores.BLUE), math.floor(remaining / 60), remaining % 60)
        scoreLabel.Size = UDim2.new(0.94, 0, 0, 28)
        scoreLabel.Position = UDim2.new(0.03, 0, 0, 4)
        scoreLabel.BackgroundTransparency = 0.7
        scoreLabel.TextScaled = false
        scoreLabel.TextSize = 13
        scoreLabel.TextWrapped = false
        scoreLabel.Text = compactScore
        statusLabel.Visible = false
        instructionLabel.Visible = false
    else
        compactScore = nil
        scoreLabel.Size = originalScoreLayout.Size
        scoreLabel.Position = originalScoreLayout.Position
        scoreLabel.BackgroundTransparency = originalScoreLayout.BackgroundTransparency
        scoreLabel.TextScaled = originalScoreLayout.TextScaled
        scoreLabel.TextSize = originalScoreLayout.TextSize
        scoreLabel.TextWrapped = originalScoreLayout.TextWrapped
        statusLabel.Visible = true
        instructionLabel.Visible = true
    end
    updateOptionalAll()
end)
