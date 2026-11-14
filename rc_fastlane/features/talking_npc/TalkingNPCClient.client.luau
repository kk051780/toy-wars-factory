--!nocheck
-- Talking NPC PREP: client captions always, best-effort Japanese TTS only on demand.
-- One existing Game-owned Remote is reused; never client-chosen enemy location.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local player = Players.LocalPlayer
if not player then return end
local playerGui = player:WaitForChild("PlayerGui", 30)
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 60)
if not playerGui or not remote or not remote:IsA("RemoteEvent") then return end
if playerGui:FindFirstChild("P0DTalkingNPCUI") then return end
local PUBLIC_ENABLED = "P0D_TALKING_NPC_CLIENT_ENABLED"

local gui = Instance.new("ScreenGui")
gui.Name = "P0DTalkingNPCUI"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.DisplayOrder = 16
gui.Enabled = ReplicatedStorage:GetAttribute(PUBLIC_ENABLED) == true
gui.Parent = playerGui

local card = Instance.new("Frame")
card.Name = "SpeechBubble"
card.AnchorPoint = Vector2.new(0.5, 0)
card.Position = UDim2.new(0.5, 0, 0.69, 0)
card.Size = UDim2.new(0.72, 0, 0, 94)
card.BackgroundColor3 = Color3.fromRGB(24, 30, 53)
card.BackgroundTransparency = 0.08
card.BorderSizePixel = 0
card.Visible = false
card.Parent = gui
local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 12)
corner.Parent = card

local label = Instance.new("TextLabel")
label.Name = "Speaker"
label.Position = UDim2.fromOffset(12, 5)
label.Size = UDim2.new(1, -24, 0, 26)
label.BackgroundTransparency = 1
label.TextSize = 16
label.Font = Enum.Font.GothamBold
label.TextColor3 = Color3.fromRGB(140, 229, 255)
label.TextXAlignment = Enum.TextXAlignment.Left
label.Parent = card
local message = Instance.new("TextLabel")
message.Name = "Message"
message.Position = UDim2.fromOffset(12, 32)
message.Size = UDim2.new(1, -24, 1, -38)
message.BackgroundTransparency = 1
message.TextWrapped = true
message.TextScaled = true
message.Font = Enum.Font.GothamBold
message.TextColor3 = Color3.fromRGB(255, 251, 238)
message.TextXAlignment = Enum.TextXAlignment.Left
message.Parent = card

local voiceToggle = Instance.new("TextButton")
voiceToggle.Name = "VoiceToggle"
voiceToggle.Size = UDim2.fromOffset(100, 29)
voiceToggle.AnchorPoint = Vector2.new(1, 0)
voiceToggle.Position = UDim2.new(1, -10, 0, 125)
voiceToggle.BorderSizePixel = 0
voiceToggle.BackgroundColor3 = Color3.fromRGB(27, 37, 59)
voiceToggle.TextColor3 = Color3.new(1, 1, 1)
voiceToggle.Font = Enum.Font.GothamBold
voiceToggle.TextSize = 13
voiceToggle.Text = "音声: ON"
voiceToggle.Parent = gui
local toggleCorner = Instance.new("UICorner")
toggleCorner.CornerRadius = UDim.new(0, 8)
toggleCorner.Parent = voiceToggle

local audioEnabled = true
local speechSerial = 0
local audioNode = nil
local audioOut = nil
local wire = nil
local audioUnsupported = false
local audioBusy = false
local audioPending = nil
local lastAudioAt = -math.huge
local TTS_GAP = 20 -- seconds: per-client quota guard; also never request automated alerts.

local function stopVoice()
    audioPending = nil
    if audioNode then pcall(function() audioNode:Pause() end) end
end
voiceToggle.Activated:Connect(function()
    audioEnabled = not audioEnabled
    voiceToggle.Text = audioEnabled and "音声: ON" or "音声: OFF"
    if not audioEnabled then stopVoice() end
end)

local function initializeAudio()
    if audioNode then return true end
    if audioUnsupported then return false end
    local staged = {}
    local ok, obj, output, link = pcall(function()
        local tts = Instance.new("AudioTextToSpeech")
        table.insert(staged, tts)
        tts.Name = "P0D_NPC_TTS"
        tts.AutoLocalize = true
        tts.Looping = false
        tts.Volume = 0.65
        tts.Parent = SoundService
        local device = Instance.new("AudioDeviceOutput")
        table.insert(staged, device)
        device.Name = "P0D_NPC_Output"
        device.Parent = SoundService
        local w = Instance.new("Wire")
        table.insert(staged, w)
        w.Name = "P0D_NPC_Wire"
        w.SourceInstance = tts
        w.TargetInstance = device
        w.Parent = SoundService
        return tts, device, w
    end)
    if not ok then
        for _, item in ipairs(staged) do
            pcall(function() item:Destroy() end)
        end
        audioUnsupported = true
        warn("[P0D/TALK] audio initialization unsupported; subtitles remain visible")
        return false
    end
    audioNode, audioOut, wire = obj, output, link
    return true
end

-- Exactly ONE asynchronous worker can mutate AudioTextToSpeech.Text / VoiceId.
-- A new message replaces any queued stale one, and old completed playback is
-- refused by nonce. No concurrent LoadAsync on the same AudioTextToSpeech node.
local function pumpAudio()
    if audioBusy then return end
    audioBusy = true
    task.spawn(function()
        while audioPending do
            local request = audioPending
            audioPending = nil
            if request.nonce == speechSerial and audioEnabled and gui.Enabled
                and (os.clock() - lastAudioAt) >= TTS_GAP
                and initializeAudio() then
                lastAudioAt = os.clock() -- count attempts, including failed loads
                local tts = audioNode
                local ok, status = pcall(function()
                    tts:Pause()
                    tts.TimePosition = 0
                    tts.Text = request.text
                    tts.VoiceId = request.voiceId
                    return tts:LoadAsync()
                end)
                if not ok or status ~= Enum.AssetFetchStatus.Success then
                    warn("[P0D/TALK] TTS unavailable; subtitles still visible")
                elseif request.nonce == speechSerial and audioEnabled and gui.Enabled then
                    pcall(function() tts:Play() end)
                end
            end
        end
        audioBusy = false
        if audioPending then pumpAudio() end
    end)
end
local function playSpeech(text, voiceId, nonce)
    if not audioEnabled or not gui.Enabled then return end
    audioPending = {text = text, voiceId = voiceId, nonce = nonce}
    pumpAudio()
end

local function setEnabled()
    gui.Enabled = ReplicatedStorage:GetAttribute(PUBLIC_ENABLED) == true
    if not gui.Enabled then
        speechSerial += 1
        card.Visible = false
        stopVoice()
    end
end
ReplicatedStorage:GetAttributeChangedSignal(PUBLIC_ENABLED):Connect(setEnabled)
setEnabled()

local allowSpeaker = {NAVI = true, TRICK = true, ORACLE = true}
local allowVoices = {["701"] = true, ["702"] = true}
local function receive(packet)
    if not gui.Enabled then return end
    if type(packet) ~= "table" or packet.kind ~= "P0D_NPC_TALK_V1" then return end
    if not allowSpeaker[packet.speakerId] then return end
    if type(packet.text) ~= "string" or #packet.text > 270 then return end
    if type(packet.displayName) ~= "string" or #packet.displayName > 65 then return end
    if not allowVoices[packet.voiceId] then return end
    speechSerial += 1
    local seq = speechSerial
    label.Text = packet.displayName .. (packet.suspicious == true and "　※敵のうわさ" or "")
    label.TextColor3 = packet.suspicious == true
        and Color3.fromRGB(255, 172, 237) or Color3.fromRGB(146, 228, 255)
    message.Text = packet.text
    card.Visible = true -- Must show captions even if TTS is unsupported/muted.
    if packet.automated ~= true then
        playSpeech(packet.text, packet.voiceId, seq)
    end
    task.delay(7, function()
        if seq == speechSerial and card.Parent then card.Visible = false end
    end)
end
remote.OnClientEvent:Connect(receive)
print("[P0D/TALK] subtitles enabled by server; mobile/TTS engine NOT_TESTED")
