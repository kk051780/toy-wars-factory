--!strict
-- EGGRUMBLE: opt-in 15s gameplay moment capture; source-only until formal RC adoption.
-- Existing Game/HUD/remote stay authoritative. No recording or publishing without opt-in.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CaptureService = game:GetService("CaptureService")
local TweenService = game:GetService("TweenService")
local player = Players.LocalPlayer
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent
local Policy = require(ReplicatedStorage:WaitForChild("TrapRaidersShared"):WaitForChild("ViralMomentPolicy"))

local state = Policy.new()
local armed = false -- default OFF, session-local, no hidden capture
local pending = false
local recording = false
local token = 0
local captureSequence = 0
local latestTitle = ""
local playerGui = player:WaitForChild("PlayerGui")

local gui = Instance.new("ScreenGui")
gui.Name = "EGGRUMBLE_ViralMomentOptIn"
gui.DisplayOrder = 5
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.Parent = playerGui

local control = Instance.new("TextButton")
control.Name = "CaptureConsentToggle"
control.AnchorPoint = Vector2.new(1, 0)
control.Position = UDim2.new(1, -10, 0, 110)
control.Size = UDim2.fromOffset(100, 37)
control.BackgroundColor3 = Color3.fromRGB(33, 47, 69)
control.BackgroundTransparency = 0.14
control.TextColor3 = Color3.fromRGB(242, 245, 255)
control.TextSize = 13
control.Font = Enum.Font.GothamBold
control.Text = "録画 OFF"
control.AutoButtonColor = true
control.Parent = gui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 9)
corner.Parent = control

local info = Instance.new("TextLabel")
info.Name = "CaptureNotice"
info.AnchorPoint = Vector2.new(1, 0)
info.Position = UDim2.new(1, -10, 0, 150)
info.Size = UDim2.fromOffset(192, 48)
info.BackgroundColor3 = Color3.fromRGB(23, 36, 55)
info.BackgroundTransparency = .18
info.BorderSizePixel = 0
info.TextColor3 = Color3.fromRGB(229, 236, 252)
info.TextSize = 12
info.TextWrapped = true
info.Font = Enum.Font.Gotham
info.Visible = false
info.Parent = gui
local infoCorner = Instance.new("UICorner")
infoCorner.CornerRadius = UDim.new(0, 8)
infoCorner.Parent = info

local function status(message: string, seconds: number)
    info.Text = message
    info.Visible = true
    token += 1
    local mine = token
    task.delay(seconds, function()
        if token == mine then info.Visible = false end
    end)
end

local function repaint()
    if recording or pending then
        control.Text = "録画中 ■"
        control.BackgroundColor3 = Color3.fromRGB(174, 69, 61)
    elseif armed then
        control.Text = "録画待機 ON"
        control.BackgroundColor3 = Color3.fromRGB(38, 132, 115)
    else
        control.Text = "録画 OFF"
        control.BackgroundColor3 = Color3.fromRGB(33, 47, 69)
    end
end

-- All visible effects are disposable local scenery, not hitboxes or game effects.
-- World Parts are used because Roblox video captures may omit ScreenGui.
local function showWorldMoment(cue)
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root or not root:IsA("BasePart") then return end
    local base = if cue.tint == "GOLD" then Color3.fromRGB(255, 205, 53)
        elseif cue.tint == "VIOLET" then Color3.fromRGB(192, 94, 255)
        else Color3.fromRGB(72, 221, 248)
    local origin = root.Position
    local particleCount = 6
    for i = 1, particleCount do
        local angle = (i - 1) * math.pi * 2 / particleCount
        local center = origin + Vector3.new(math.cos(angle) * 3, 1.5, math.sin(angle) * 3)
        local glow = Instance.new("Part")
        glow.Name = "EGGRUMBLE_MomentGlint"
        glow.Shape = Enum.PartType.Ball
        glow.Material = Enum.Material.Neon
        glow.Color = base
        glow.Anchored = true
        glow.CanCollide = false
        glow.CanTouch = false
        glow.CanQuery = false
        glow.CastShadow = false
        glow.Size = Vector3.new(.45, .45, .45)
        glow.Position = center
        glow.Parent = workspace
        local target = {Position = center + Vector3.new(0, 5, 0),
            Transparency = 1, Size = Vector3.new(.12, .12, .12)}
        TweenService:Create(glow, TweenInfo.new(2.2, Enum.EasingStyle.Quad,
            Enum.EasingDirection.Out), target):Play()
        task.delay(2.4, function()
            if glow.Parent then glow:Destroy() end
        end)
    end
end

local function stopRecording()
    if not recording then return end
    recording = false
    captureSequence += 1 -- invalidate every delayed timer from the old clip
    repaint()
    pcall(function() CaptureService:StopVideoCapture() end)
end

local function beginRecording(cue)
    if not armed or pending or recording then return end
    pending = true
    repaint()
    captureSequence += 1
    local thisCapture = captureSequence
    task.spawn(function()
        local ok, result = pcall(function()
            return CaptureService:StartVideoCaptureAsync(function(outcome, capture)
                -- The platform controls capture eligibility and final save permission.
                if not armed then return end
                if (outcome == Enum.VideoCaptureResult.Success
                    or outcome == Enum.VideoCaptureResult.TimeLimitReached) and capture then
                    pcall(function()
                        CaptureService:PromptSaveCapturesToGallery({capture}, function() end)
                    end)
                end
            end, {})
        end)
        pending = false
        if not ok or result ~= Enum.VideoCaptureStartedResult.Success then
            recording = false
            repaint()
            status("この端末では録画できません。Robloxの撮影メニューも確認してください。", 5)
            return
        end
        if not armed then
            recording = true
            stopRecording()
            return
        end
        recording = true
        repaint()
        status(latestTitle .. "  ｜  最大" .. tostring(cue.recordSeconds) .. "秒録画", 3)
        task.delay(cue.recordSeconds, function()
            -- No perpetual capture; never stop a subsequent clip with an old timer.
            if thisCapture == captureSequence and recording then stopRecording() end
        end)
    end)
end

control.Activated:Connect(function()
    armed = not armed
    if not armed then
        if recording then stopRecording() end
        status("録画待機をOFFにしました。SNSへ自動投稿されません。", 4)
    else
        status("卵奪取・城の危機・勝利で最大15秒撮影。保存は確認画面で選べます。", 5)
    end
    repaint()
end)

remote.OnClientEvent:Connect(function(packet)
    local cue = Policy.consume(state, packet, time())
    if not cue then return end
    -- Gameplay happens even when recording is disabled: every player gets the
    -- moment visuals, but never an unsolicited capture or external call.
    showWorldMoment(cue)
    latestTitle = cue.title
    if armed then beginRecording(cue) end
end)

repaint()
