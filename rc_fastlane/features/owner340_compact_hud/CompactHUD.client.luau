--!strict
-- P0D OWNER #340: minimal HUD overlay for private Studio UX evaluation.
-- Client-side presentation only. Never creates game/score/HP/XP/Remote authority.
-- Omit this LocalScript to restore the exact previous 65-script game.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

if not RunService:IsStudio() then
    return
end

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui", 20)
if not playerGui then
    return
end

local TARGET_NAME = "TrapRaidersS1HUD"
local connected: {[Instance]: boolean} = {}

local function attach(screen: Instance)
    if not screen:IsA("ScreenGui") or screen.Name ~= TARGET_NAME or connected[screen] then
        return
    end
    local score = screen:FindFirstChild("Score")
    local status = screen:FindFirstChild("Status")
    local instructions = screen:FindFirstChild("Instructions")
    local attack = screen:FindFirstChild("Attack")
    -- Fail closed when the canonical HUD schema changes. Never hide arbitrary UI.
    if not (score and status and instructions and attack) then
        return
    end
    if not (score:IsA("TextLabel") and status:IsA("TextLabel")
        and instructions:IsA("TextLabel") and attack:IsA("GuiButton")) then
        return
    end
    connected[screen] = true

    local function relayout()
        if not screen.Parent then
            return
        end
        local camera = workspace.CurrentCamera
        local narrow = camera ~= nil and camera.ViewportSize.X <= 650
        local active = attack.Visible

        -- Full explanation is not persistent during play. Lobby retains one small hint.
        instructions.Visible = not active and not narrow
        instructions.TextWrapped = false
        instructions.TextTruncate = Enum.TextTruncate.AtEnd

        score.TextWrapped = false
        score.TextTruncate = Enum.TextTruncate.AtEnd
        score.TextSize = if narrow then 13 else 15
        score.Size = UDim2.new(if narrow then 0.94 else 0.72, 0, 0, if narrow then 27 else 34)
        score.Position = UDim2.new(if narrow then 0.03 else 0.14, 0, 0, 3)

        status.TextWrapped = false
        status.TextTruncate = Enum.TextTruncate.AtEnd
        status.TextSize = if narrow then 12 else 14
        status.Size = UDim2.new(if narrow then 0.94 else 0.72, 0, 0, 27)
        status.Position = UDim2.new(if narrow then 0.03 else 0.14, 0, 0, if narrow then 34 else 43)
        -- Never change movement, jump, attack button, HUD Remote, or its score contents.
    end

    attack:GetPropertyChangedSignal("Visible"):Connect(relayout)
    local viewportConnection: RBXScriptConnection? = nil
    local function bindCamera()
        if viewportConnection then
            viewportConnection:Disconnect()
            viewportConnection = nil
        end
        local camera = workspace.CurrentCamera
        if camera then
            viewportConnection = camera:GetPropertyChangedSignal("ViewportSize"):Connect(relayout)
        end
        relayout()
    end
    workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(bindCamera)
    bindCamera()
end

local function tryHUD(screen: Instance)
    if not screen:IsA("ScreenGui") or screen.Name ~= TARGET_NAME then
        return
    end
    attach(screen)
    screen.ChildAdded:Connect(function()
        attach(screen)
    end)
end

for _, child in playerGui:GetChildren() do
    tryHUD(child)
end
playerGui.ChildAdded:Connect(tryHUD)
