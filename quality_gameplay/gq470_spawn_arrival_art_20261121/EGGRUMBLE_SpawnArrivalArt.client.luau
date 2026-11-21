--!strict
-- EGGRUMBLE_SpawnArrivalArt: #470 FB-015 local-only short matte arrival.
-- Not a fix for absent Player.Character; no Game/HP/egg/store/AI authority.
local Players = game:GetService("Players")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")
local UserInputService = game:GetService("UserInputService")
local player = Players.LocalPlayer
local FEATURE_ID = "GQ470_FB015_SPAWN_ARRIVAL_MATTE_20261121"
local MAX_EMIT_TOUCH = 5
local MAX_EMIT_DESKTOP = 9
local EFFECT_SECONDS = 0.82
local ROOT_TIMEOUT_SECONDS = 5
local generation = 0
local activeFolder: Folder? = nil
local activeAttachment: Attachment? = nil

local function clearTransient()
    if activeAttachment then activeAttachment:Destroy(); activeAttachment = nil end
    if activeFolder then activeFolder:Destroy(); activeFolder = nil end
end

local function onCharacter(character: Model)
    generation += 1
    local token = generation
    clearTransient()
    task.spawn(function()
        local root = character:WaitForChild("HumanoidRootPart", ROOT_TIMEOUT_SECONDS)
        local human = character:WaitForChild("Humanoid", ROOT_TIMEOUT_SECONDS)
        if generation ~= token or player.Character ~= character then return end
        if not root or not root:IsA("BasePart") then return end
        if not human or not human:IsA("Humanoid") or human.Health <= 0 then return end

        local tint = if player.Neutral then Color3.fromRGB(175, 190, 193)
            else player.TeamColor.Color
        local folder = Instance.new("Folder")
        folder.Name = "EGGRUMBLE_SpawnArrival_Local"
        folder:SetAttribute("FeatureID", FEATURE_ID)
        folder.Parent = character
        activeFolder = folder

        local glow = Instance.new("Highlight")
        glow.Name = "ArrivalSilhouette"
        glow.Adornee = character
        glow.DepthMode = Enum.HighlightDepthMode.Occluded
        glow.FillColor = tint:Lerp(Color3.fromRGB(223, 226, 213), 0.55)
        glow.OutlineColor = tint
        glow.FillTransparency = 0.84
        glow.OutlineTransparency = 0.46
        glow.Parent = folder

        local foot = Instance.new("Attachment")
        foot.Name = "ArrivalAtFeet"
        foot.Position = Vector3.new(0, -math.clamp(human.HipHeight + root.Size.Y * 0.5, 1.5, 4), 0)
        foot.Parent = root
        activeAttachment = foot
        local sparks = Instance.new("ParticleEmitter")
        sparks.Name = "MatteArrivalDust"
        sparks.Texture = "rbxasset://textures/particles/sparkles_main.dds"
        sparks.Color = ColorSequence.new(tint:Lerp(Color3.fromRGB(220, 218, 197), 0.65))
        sparks.LightEmission = 0
        sparks.LightInfluence = 1
        sparks.Rate = 0
        sparks.Lifetime = NumberRange.new(0.24, 0.52)
        sparks.Speed = NumberRange.new(1.2, 2.8)
        sparks.Drag = 5
        sparks.SpreadAngle = Vector2.new(180, 180)
        sparks.Size = NumberSequence.new({
            NumberSequenceKeypoint.new(0, 0.22),
            NumberSequenceKeypoint.new(0.6, 0.14),
            NumberSequenceKeypoint.new(1, 0),
        })
        sparks.Transparency = NumberSequence.new({
            NumberSequenceKeypoint.new(0, 0.42),
            NumberSequenceKeypoint.new(1, 1),
        })
        sparks.Parent = foot
        sparks:Emit(if UserInputService.TouchEnabled then MAX_EMIT_TOUCH else MAX_EMIT_DESKTOP)

        TweenService:Create(glow, TweenInfo.new(0.66, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            FillTransparency = 1,
            OutlineTransparency = 1,
        }):Play()
        Debris:AddItem(foot, EFFECT_SECONDS)
        Debris:AddItem(folder, EFFECT_SECONDS)
        task.delay(EFFECT_SECONDS + 0.05, function()
            if generation ~= token then return end
            if activeAttachment == foot then activeAttachment = nil end
            if activeFolder == folder then activeFolder = nil end
        end)
    end)
end

player.CharacterRemoving:Connect(function()
    generation += 1
    clearTransient()
end)
player.CharacterAdded:Connect(onCharacter)
if player.Character then onCharacter(player.Character) end
