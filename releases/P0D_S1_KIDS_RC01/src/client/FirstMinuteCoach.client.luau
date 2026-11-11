--!strict
-- Optional independent S1 client overlay; subscribes to the EXISTING snapshot RemoteEvent.
-- No new remotes, no server writes. Add to StarterPlayerScripts as a separate script.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local shared = ReplicatedStorage:WaitForChild("TrapRaidersShared")
local Model = require(shared:WaitForChild("FirstMinuteModel"))
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent

local gui = Instance.new("ScreenGui")
gui.Name = "TR_S1_FirstMinuteCoach"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.DisplayOrder = 8
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Parent = player:WaitForChild("PlayerGui")

local panel = Instance.new("Frame")
panel.Name = "CoachPanel"
panel.AnchorPoint = Vector2.new(0.5, 0)
panel.Position = UDim2.new(0.5, 0, 0, 108)
panel.Size = UDim2.new(0.62, 0, 0, 67)
panel.BackgroundColor3 = Color3.fromRGB(18, 35, 52)
panel.BackgroundTransparency = 0.10
panel.BorderSizePixel = 0
panel.Visible = false
panel.Parent = gui
local panelCorner = Instance.new("UICorner")
panelCorner.CornerRadius = UDim.new(0, 9)
panelCorner.Parent = panel
local constraint = Instance.new("UISizeConstraint")
constraint.MaxSize = Vector2.new(530, 74)
constraint.MinSize = Vector2.new(220, 63)
constraint.Parent = panel

local title = Instance.new("TextLabel")
title.Name = "CoachTitle"
title.BackgroundTransparency = 1
title.Position = UDim2.fromOffset(10, 3)
title.Size = UDim2.new(1, -45, 0, 23)
title.Font = Enum.Font.GothamBold
title.TextColor3 = Color3.fromRGB(255, 222, 113)
title.TextSize = 15
title.TextXAlignment = Enum.TextXAlignment.Left
title.TextTruncate = Enum.TextTruncate.AtEnd
title.Parent = panel

local detail = Instance.new("TextLabel")
detail.Name = "CoachDetail"
detail.BackgroundTransparency = 1
detail.Position = UDim2.fromOffset(10, 27)
detail.Size = UDim2.new(1, -20, 1, -30)
detail.Font = Enum.Font.Gotham
detail.TextColor3 = Color3.fromRGB(241, 246, 255)
detail.TextSize = 12
detail.TextXAlignment = Enum.TextXAlignment.Left
detail.TextYAlignment = Enum.TextYAlignment.Top
detail.TextWrapped = true
detail.Parent = panel

local close = Instance.new("TextButton")
close.Name = "HideHelp"
close.Position = UDim2.new(1, -33, 0, 3)
close.Size = UDim2.fromOffset(29, 29)
close.Text = "×"
close.TextSize = 19
close.Font = Enum.Font.GothamBold
close.BackgroundColor3 = Color3.fromRGB(49, 65, 82)
close.TextColor3 = Color3.new(1, 1, 1)
close.Parent = panel
local closeCorner = Instance.new("UICorner")
closeCorner.CornerRadius = UDim.new(0, 7)
closeCorner.Parent = close

local help = Instance.new("TextButton")
help.Name = "ShowHelp"
help.Position = UDim2.new(1, -38, 0, 105)
help.Size = UDim2.fromOffset(31, 31)
help.Text = "?"
help.TextSize = 19
help.Font = Enum.Font.GothamBold
help.BackgroundColor3 = Color3.fromRGB(22, 50, 73)
help.TextColor3 = Color3.fromRGB(255, 233, 135)
help.Visible = false
help.Parent = gui
local helpCorner = Instance.new("UICorner")
helpCorner.CornerRadius = UDim.new(0, 9)
helpCorner.Parent = help

local state = Model.new()
local function repaint()
    local v = Model.view(state, time())
    panel.Visible = v ~= nil and v.visible
    help.Visible = state.latest ~= nil and not panel.Visible
    if not v or not v.visible then return end
    title.Text = v.title
    detail.Text = v.detail
    title.TextColor3 = if v.tone == "success" then Color3.fromRGB(156, 252, 178)
        else Color3.fromRGB(255, 222, 113)
end

close.MouseButton1Click:Connect(function()
    Model.setHidden(state, true)
    repaint()
end)
help.MouseButton1Click:Connect(function()
    Model.setHidden(state, false)
    repaint()
end)
remote.OnClientEvent:Connect(function(snapshot)
    if Model.consume(state, snapshot, time()) then repaint() end
end)