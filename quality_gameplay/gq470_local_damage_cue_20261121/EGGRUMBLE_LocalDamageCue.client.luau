--!strict
-- EGGRUMBLE FB-015 local DEFENDER-only actual damage indication.
-- A isolated visual source: never modifies HP, score, combat, remotes, or the UI.
local Players = game:GetService("Players")
local Lighting = game:GetService("Lighting")
local TweenService = game:GetService("TweenService")

local PLAYER = Players.LocalPlayer
local FEATURE_ID = "GQ470_FB015_TRUE_LOCAL_DAMAGE_CUE_REAL69_20261121"
local EFFECT_NAME = "EGGRUMBLE_LocalTrueDamageCue"
local REDUCED_EFFECTS_ATTRIBUTE = "EGGRUMBLE_ReducedEffects"
local COOLDOWN_SECONDS = 0.30
local MAX_CUE_SECONDS = 0.24
local MAX_DAMAGE_TINT = 20

local existing = Lighting:FindFirstChild(EFFECT_NAME)
local effect: ColorCorrectionEffect
if existing and existing:IsA("ColorCorrectionEffect") then
    effect = existing
else
    effect = Instance.new("ColorCorrectionEffect")
    effect.Name = EFFECT_NAME
    effect.Parent = Lighting
end
effect:SetAttribute("FeatureID", FEATURE_ID)

local NORMAL_TINT = Color3.fromRGB(255, 255, 255)
local currentTween: Tween? = nil
local damageConnection: RBXScriptConnection? = nil
local diedConnection: RBXScriptConnection? = nil
local generation = 0
local pulseTicket = 0
local lastPulseAt = -math.huge

local function cancelPulse(): ()
    pulseTicket += 1
    if currentTween then
        currentTween:Cancel()
        currentTween = nil
    end
    effect.Enabled = false
    effect.TintColor = NORMAL_TINT
    effect.Saturation = 0
    effect.Brightness = 0
    effect.Contrast = 0
end

local function showDamageCue(loss: number, maxHealth: number): ()
    if PLAYER:GetAttribute(REDUCED_EFFECTS_ATTRIBUTE) == true then
        return
    end
    local now = os.clock()
    if now - lastPulseAt < COOLDOWN_SECONDS then
        return
    end
    lastPulseAt = now
    pulseTicket += 1
    local ticket = pulseTicket
    if currentTween then currentTween:Cancel() end

    -- Calm, subtle short true-damage warmth: never a red/white screen flash.
    local fraction = math.clamp(loss / math.max(1, maxHealth), 0, 0.3)
    local tintStrength = math.min(MAX_DAMAGE_TINT, math.floor(9 + fraction * 36))
    effect.Enabled = true
    effect.TintColor = Color3.fromRGB(255, 255 - tintStrength, 255 - tintStrength)
    effect.Saturation = -0.06
    effect.Brightness = -0.008
    effect.Contrast = 0
    currentTween = TweenService:Create(effect,
        TweenInfo.new(MAX_CUE_SECONDS, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
        {TintColor = NORMAL_TINT, Saturation = 0, Brightness = 0}
    )
    currentTween:Play()
    task.delay(MAX_CUE_SECONDS + 0.01, function()
        if ticket == pulseTicket then
            currentTween = nil
            effect.Enabled = false
        end
    end)
end

local function disconnectCharacter(): ()
    generation += 1
    if damageConnection then
        damageConnection:Disconnect()
        damageConnection = nil
    end
    if diedConnection then
        diedConnection:Disconnect()
        diedConnection = nil
    end
    cancelPulse()
end

local function bindCharacter(character: Model): ()
    disconnectCharacter()
    local token = generation
    local candidate = character:WaitForChild("Humanoid", 6)
    if token ~= generation or not candidate or not candidate:IsA("Humanoid") then
        return
    end
    local humanoid = candidate :: Humanoid
    local previousHealth = humanoid.Health
    damageConnection = humanoid.HealthChanged:Connect(function(currentHealth: number)
        local lost = previousHealth - currentHealth
        previousHealth = currentHealth
        -- SERVER-replicated genuine health loss only. Healing / 0 HP / respawn
        -- and repeated events never create synthetic hit confirmation.
        if token ~= generation or humanoid.Health <= 0 or currentHealth <= 0 then
            return
        end
        if lost > 0.25 then
            showDamageCue(lost, humanoid.MaxHealth)
        end
    end)
    diedConnection = humanoid.Died:Connect(disconnectCharacter)
end

PLAYER.CharacterRemoving:Connect(function()
    disconnectCharacter()
end)
PLAYER.CharacterAdded:Connect(bindCharacter)
PLAYER:GetAttributeChangedSignal(REDUCED_EFFECTS_ATTRIBUTE):Connect(function()
    if PLAYER:GetAttribute(REDUCED_EFFECTS_ATTRIBUTE) == true then
        cancelPulse()
    end
end)
if PLAYER.Character then
    task.defer(bindCharacter, PLAYER.Character)
end
