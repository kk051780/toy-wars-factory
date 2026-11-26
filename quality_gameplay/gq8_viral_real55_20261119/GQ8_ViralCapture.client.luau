--!strict
-- GQ8_VIRAL_REAL56_20261119: optional local capture over REAL V3 server-committed Player attributes.
-- Pure client visual/capture; no network objects or mutations of match, egg, damage, score or store.
local Players = game:GetService("Players")
local CaptureService = game:GetService("CaptureService")
local TweenService = game:GetService("TweenService")
local RunService = game:GetService("RunService")
local user = Players.LocalPlayer
if not RunService:IsStudio() then return end -- this V3 preview is Studio-only; no public recording switch

local valid = {
    EGG_STEAL = {seconds = 15, tone = Color3.fromRGB(94, 215, 253)},
    EGG_DELIVER = {seconds = 9, tone = Color3.fromRGB(80, 255, 199)},
    CASTLE_DANGER = {seconds = 15, tone = Color3.fromRGB(210, 119, 255)},
    VICTORY = {seconds = 7, tone = Color3.fromRGB(250, 205, 93)},
    COMEBACK = {seconds = 7, tone = Color3.fromRGB(250, 205, 93)},
}
local armed = false
local starting = false
-- Keep the platform call occupied until its yielding start returns.
local startInFlight = false
local consentId = 0
local capturing = false
local captureId = 0
local previousEpoch = -1
local previousSeq = -1
local lastCueAt = -10000

local gui = Instance.new("ScreenGui")
gui.Name = "GQ8_ViralCaptureOptIn"
gui.ResetOnSpawn = false
gui.DisplayOrder = 10
gui.Parent = user:WaitForChild("PlayerGui")
local toggle = Instance.new("TextButton")
toggle.Name = "RecordingConsent"
toggle.Size = UDim2.fromOffset(99, 32)
toggle.AnchorPoint = Vector2.new(1, 0)
toggle.Position = UDim2.new(1, -9, 0, 95)
toggle.BackgroundColor3 = Color3.fromRGB(49, 63, 79)
toggle.BackgroundTransparency = .13
toggle.TextColor3 = Color3.fromRGB(250, 250, 252)
toggle.Font = Enum.Font.GothamBold
toggle.TextSize = 12
toggle.Text = "録画 OFF"
toggle.Parent = gui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 8)
corner.Parent = toggle

local function repaint()
    if capturing or starting then
        toggle.Text = "● 録画中"
        toggle.BackgroundColor3 = Color3.fromRGB(175, 72, 68)
    elseif armed then
        toggle.Text = "録画待機 ON"
        toggle.BackgroundColor3 = Color3.fromRGB(42, 137, 118)
    else
        toggle.Text = "録画 OFF"
        toggle.BackgroundColor3 = Color3.fromRGB(49, 63, 79)
    end
end

local function visual(kind: string)
    local cfg = valid[kind]
    if not cfg then return end
    local avatar = user.Character
    local root = avatar and avatar:FindFirstChild("HumanoidRootPart")
    if not root or not root:IsA("BasePart") then return end
    local center = root.Position
    for i = 1, 8 do
        local theta = i * math.pi / 4
        local glint = Instance.new("Part")
        glint.Name = "GQ8_ViralMomentLocalFX"
        glint.Shape = Enum.PartType.Ball
        glint.Material = Enum.Material.Neon
        glint.Color = cfg.tone
        glint.Size = Vector3.new(.5, .5, .5)
        glint.Anchored = true
        glint.CanCollide = false
        glint.CanTouch = false
        glint.CanQuery = false
        glint.CastShadow = false
        glint.Position = center + Vector3.new(3*math.cos(theta), 1.8, 3*math.sin(theta))
        glint.Parent = workspace
        local anim = TweenService:Create(glint, TweenInfo.new(2.2, Enum.EasingStyle.Quad),
            {Position = glint.Position + Vector3.new(0, 3.8, 0), Transparency = 1})
        anim:Play()
        task.delay(2.4, function()
            if glint.Parent then glint:Destroy() end
        end)
    end
end

local function stopCapture()
    if not capturing then return end
    capturing = false
    captureId += 1
    repaint()
    pcall(function() CaptureService:StopVideoCapture() end)
end

local function captureFor(kind: string, currentEpoch: number)
    local cfg = valid[kind]
    if not cfg or not armed or startInFlight or capturing then
        visual(kind)
        return
    end
    starting = true
    startInFlight = true
    captureId += 1
    local startId = captureId
    local startConsentId = consentId
    repaint()
    -- The platform's callback is the ONLY source of a real video to save.
    task.spawn(function()
        local completed = false
        local ok, result = pcall(function()
            return CaptureService:StartVideoCaptureAsync(function(outcome, capture)
                completed = true
                -- A terminal callback may arrive before our duration timer.
                if captureId == startId then
                    starting = false
                    capturing = false
                    repaint()
                end
                if not armed or currentEpoch ~= previousEpoch
                    or consentId ~= startConsentId then return end
                if (outcome == Enum.VideoCaptureResult.Success
                    or outcome == Enum.VideoCaptureResult.TimeLimitReached)
                    and capture ~= nil then
                    pcall(function()
                        CaptureService:PromptSaveCapturesToGallery({capture}, function(_answers) end)
                    end)
                end
            end, {})
        end)
        starting = false
        if captureId ~= startId or not armed or currentEpoch ~= previousEpoch then
            if ok and result == Enum.VideoCaptureStartedResult.Success and not completed then
                pcall(function() CaptureService:StopVideoCapture() end)
            end
            startInFlight = false
            repaint()
            return
        end
        startInFlight = false
        if not ok or result ~= Enum.VideoCaptureStartedResult.Success then
            repaint()
            visual(kind)
            return
        end
        if completed then
            repaint()
            visual(kind)
            return
        end
        capturing = true
        repaint()
        visual(kind) -- after recorder starts, not before
        task.delay(cfg.seconds, function()
            if capturing and captureId == startId then stopCapture() end
        end)
    end)
end

toggle.Activated:Connect(function()
    armed = not armed
    consentId += 1 -- a later ON does not re-authorize an old clip
    if not armed then
        captureId += 1 -- invalidate the result, not the still-running platform call
        if capturing then
            capturing = false
            pcall(function() CaptureService:StopVideoCapture() end)
        end
        starting = false
    end
    repaint()
end)

local function consume()
    local epoch = user:GetAttribute("EGGRUMBLE_ViralEpoch")
    local seq = user:GetAttribute("EGGRUMBLE_ViralSeq")
    local kind = user:GetAttribute("EGGRUMBLE_ViralKind")
    if type(epoch) ~= "number" or epoch % 1 ~= 0 or epoch < 1
        or type(seq) ~= "number" or seq % 1 ~= 0 or seq < 1
        or type(kind) ~= "string" or valid[kind] == nil then return end
    if epoch < previousEpoch or (epoch == previousEpoch and seq <= previousSeq) then return end
    if epoch > previousEpoch then
        previousEpoch = epoch -- fence callbacks before Stop can complete a clip
        previousSeq = -1
        lastCueAt = -10000
        captureId += 1
        starting = false
        if capturing then stopCapture() end
        repaint()
    end
    previousSeq = seq
    local now = time()
    if now - lastCueAt < 2 then return end
    lastCueAt = now
    captureFor(kind, epoch)
end
user:GetAttributeChangedSignal("EGGRUMBLE_ViralSeq"):Connect(consume)
repaint()
