--!strict
-- Original child-visible egg/score/win feedback; private Studio preview ONLY.
-- Reads existing authoritative S1 SNAPSHOT. Never sends actions/rewards.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")

if not RunService:IsStudio() then return end

local player = Players.LocalPlayer
local Rules = require(script.Parent:WaitForChild("EggJoyRules"))
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent

local gui = Instance.new("ScreenGui")
gui.Name = "P0D_H1_EggJoy_ClientOnly"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.DisplayOrder = 14
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Parent = player:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.Name = "EggMoment"
panel.AnchorPoint = Vector2.new(0.5, 0)
panel.Position = UDim2.new(0.5, 0, 0, 186)
panel.Size = UDim2.new(0.66, 0, 0, 68)
panel.BackgroundColor3 = Color3.fromRGB(22, 38, 61)
panel.BackgroundTransparency = 0.15
panel.BorderSizePixel = 0
panel.Visible = false
panel.Active = false
panel.Parent = gui
local minMax = Instance.new("UISizeConstraint")
minMax.MinSize = Vector2.new(210, 59)
minMax.MaxSize = Vector2.new(420, 68)
minMax.Parent = panel
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 13)
corner.Parent = panel
local stroke = Instance.new("UIStroke")
stroke.Thickness = 2
stroke.Color = Color3.fromRGB(255, 206, 115)
stroke.Transparency = 0.28
stroke.Parent = panel

local headline = Instance.new("TextLabel")
headline.Name = "MomentTitle"
headline.BackgroundTransparency = 1
headline.Position = UDim2.fromOffset(12, 4)
headline.Size = UDim2.new(1, -24, 0, 33)
headline.TextColor3 = Color3.fromRGB(255, 239, 162)
headline.TextSize = 21
headline.Font = Enum.Font.GothamBold
headline.TextXAlignment = Enum.TextXAlignment.Center
headline.TextScaled = false
headline.TextTruncate = Enum.TextTruncate.AtEnd
headline.Parent = panel

local subline = Instance.new("TextLabel")
subline.Name = "MomentDirection"
subline.BackgroundTransparency = 1
subline.Position = UDim2.fromOffset(10, 39)
subline.Size = UDim2.new(1, -20, 0, 22)
subline.TextColor3 = Color3.fromRGB(234, 246, 255)
subline.TextSize = 13
subline.Font = Enum.Font.Gotham
subline.TextXAlignment = Enum.TextXAlignment.Center
subline.TextTruncate = Enum.TextTruncate.AtEnd
subline.Parent = panel

local wording = {
    PICKUP = {"🥚 お宝ゲット！", "じぶんの陣地へ持って帰ろう！"},
    TEAM_SCORE = {"✨ チーム得点！", "みんなで一歩リード！"},
    VICTORY = {"🏆 勝利！", "チームの大成功！"},
}
local colors = {
    Color3.fromRGB(255, 217, 85),
    Color3.fromRGB(101, 223, 246),
    Color3.fromRGB(244, 140, 219),
    Color3.fromRGB(169, 253, 145),
}
local state: any = nil
local generation = 0
local sparks: {Frame} = {}

local function removeSparks()
    for _, item in ipairs(sparks) do
        item:Destroy()
    end
    table.clear(sparks)
end

local function hide()
    generation += 1
    panel.Visible = false
    removeSparks()
end

local function showMoment(eventName: string)
    local copy = wording[eventName]
    if not copy then return end
    hide()
    local myGeneration = generation
    headline.Text = copy[1]
    subline.Text = copy[2]
    panel.BackgroundTransparency = 0.15
    headline.TextTransparency = 0
    subline.TextTransparency = 0
    stroke.Transparency = 0.28
    panel.Visible = true
    -- Bounded eight non-interactive original gem highlights. Not full-screen
    -- flashes or particles; controls remain visible/usable on small phones.
    for i = 1, 8 do
        local spark = Instance.new("Frame")
        spark.Name = "TinyGem"
        spark.Size = UDim2.fromOffset(7, 7)
        spark.AnchorPoint = Vector2.new(0.5, 0.5)
        spark.BackgroundColor3 = colors[(i - 1) % #colors + 1]
        spark.BorderSizePixel = 0
        spark.Rotation = 45
        spark.Active = false
        local x = (i - 1) / 7
        spark.Position = UDim2.new(x, 0, 0.50, 0)
        spark.Parent = panel
        table.insert(sparks, spark)
        TweenService:Create(spark,
            TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
            {Position = UDim2.new(x, 0, if i % 2 == 0 then 0.88 else 0.12, 0),
             BackgroundTransparency = 1}):Play()
    end
    task.delay(1.35, function()
        if myGeneration ~= generation then return end
        TweenService:Create(panel, TweenInfo.new(0.2),
            {BackgroundTransparency = 1}):Play()
        TweenService:Create(headline, TweenInfo.new(0.2),
            {TextTransparency = 1}):Play()
        TweenService:Create(subline, TweenInfo.new(0.2),
            {TextTransparency = 1}):Play()
        task.delay(0.22, function()
            if myGeneration == generation then hide() end
        end)
    end)
end

remote.OnClientEvent:Connect(function(snapshot: any)
    local previous = state
    local nextState, moment = Rules.accept(state, snapshot)
    state = nextState
    if nextState == previous then return end -- malformed/replayed snapshots
    if moment ~= nil then
        showMoment(moment)
    elseif state ~= nil and state.phase ~= "ACTIVE" and state.phase ~= "RESULTS" then
        hide()
    end
end)
