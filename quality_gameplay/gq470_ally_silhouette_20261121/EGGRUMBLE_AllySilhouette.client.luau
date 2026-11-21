-- GQ470_FB015_ALLY_SILHOUETTE_REAL69_20261121
-- Private A-only client visual. Never marks a player, score, health or team on the server.
-- Visible nearby TEAM allies only; never enemies, neutral players, or cloaked allies.
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local LOCAL_PLAYER = Players.LocalPlayer
if not LOCAL_PLAYER then
    return
end

local MAX_ALLIES = 3
local TOUCH_MAX_ALLIES = 2
local MAX_DISTANCE = 45
local SCAN_INTERVAL = 0.75
local OUTLINE_TRANSPARENCY = 0.68
local EFFECT_NAME = "GQ470_AllySilhouette"
local REDUCED_EFFECTS_ATTRIBUTE = "EGGRUMBLE_ReducedEffects"
local DISABLE_ATTRIBUTE = "GQ470_DisableAllyOutline"
local active = {}

local function clear(player)
    local effect = active[player]
    if effect then
        active[player] = nil
        effect:Destroy()
    end
end

local function clearAll()
    for player in pairs(active) do
        clear(player)
    end
end

local function isVisibleAlly(player, localRoot, localTeam)
    if player == LOCAL_PLAYER or player.Team ~= localTeam or player.Neutral then
        return nil
    end
    local character = player.Character
    if not character then
        return nil
    end
    if character:GetAttribute("Stealthed") == true
        or character:GetAttribute("IsInvisible") == true
        or character:GetAttribute("AssassinCloaked") == true
        or character:GetAttribute("EGGRUMBLE_Stealthed") == true then
        return nil
    end
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local root = character:FindFirstChild("HumanoidRootPart")
    local head = character:FindFirstChild("Head")
    local torso = character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")
    if not humanoid or humanoid.Health <= 0 or not root or not head or not torso
        or head.Transparency >= 0.35
        or head.LocalTransparencyModifier >= 0.35
        or torso.Transparency >= 0.35
        or torso.LocalTransparencyModifier >= 0.35 then
        return nil
    end
    -- Fail closed on partial-body stealth. A cloak may fade individual R6/R15 limbs
    -- without setting a character-wide stealth attribute or hiding Head/Torso.
    -- Only inspect direct body parts: equipped Tool parts live in descendants.
    for _, bodyPart in ipairs(character:GetChildren()) do
        if bodyPart:IsA("BasePart") and bodyPart.Name ~= "HumanoidRootPart"
            and (bodyPart.Transparency >= 0.35 or bodyPart.LocalTransparencyModifier >= 0.35) then
            return nil
        end
    end
    local distance = (root.Position - localRoot.Position).Magnitude
    if distance > MAX_DISTANCE then
        return nil
    end
    return {player = player, character = character, distance = distance}
end

local function present(candidate)
    local player = candidate.player
    local effect = active[player]
    if effect and effect.Adornee ~= candidate.character then
        clear(player)
        effect = nil
    end
    if not effect or not effect.Parent then
        effect = Instance.new("Highlight")
        effect.Name = EFFECT_NAME
        effect.DepthMode = Enum.HighlightDepthMode.Occluded
        effect.FillTransparency = 1
        effect.OutlineTransparency = OUTLINE_TRANSPARENCY
        effect.Adornee = candidate.character
        effect.Parent = candidate.character
        active[player] = effect
    end
    -- Retain team hue but desaturate the rim; avoid saturated neon overlays.
    effect.OutlineColor = player.TeamColor.Color:Lerp(Color3.fromRGB(202, 218, 219), 0.48)
    effect.Enabled = true
end

Players.PlayerRemoving:Connect(clear)
LOCAL_PLAYER.CharacterRemoving:Connect(clearAll)
-- Effect switches must remove already-visible outlines immediately, not after 0.75s.
LOCAL_PLAYER:GetAttributeChangedSignal(REDUCED_EFFECTS_ATTRIBUTE):Connect(function()
    if LOCAL_PLAYER:GetAttribute(REDUCED_EFFECTS_ATTRIBUTE) == true then
        clearAll()
    end
end)
LOCAL_PLAYER:GetAttributeChangedSignal(DISABLE_ATTRIBUTE):Connect(function()
    if LOCAL_PLAYER:GetAttribute(DISABLE_ATTRIBUTE) == true then
        clearAll()
    end
end)

while true do
    task.wait(SCAN_INTERVAL)
    if LOCAL_PLAYER.Parent ~= Players then
        clearAll()
        break
    end
    local character = LOCAL_PLAYER.Character
    local localRoot = character and character:FindFirstChild("HumanoidRootPart")
    local localHumanoid = character and character:FindFirstChildOfClass("Humanoid")
    local localTeam = LOCAL_PLAYER.Team
    if not localRoot or not localHumanoid or localHumanoid.Health <= 0
        or not localTeam or LOCAL_PLAYER.Neutral
        or LOCAL_PLAYER:GetAttribute(REDUCED_EFFECTS_ATTRIBUTE) == true
        or LOCAL_PLAYER:GetAttribute(DISABLE_ATTRIBUTE) == true then
        clearAll()
        continue
    end

    local candidates = {}
    for _, player in ipairs(Players:GetPlayers()) do
        local ally = isVisibleAlly(player, localRoot, localTeam)
        if ally then
            table.insert(candidates, ally)
        end
    end
    table.sort(candidates, function(a, b)
        return a.distance < b.distance
    end)

    local keep = {}
    for i = 1, math.min(UserInputService.TouchEnabled and TOUCH_MAX_ALLIES or MAX_ALLIES, #candidates) do
        local ally = candidates[i]
        keep[ally.player] = true
        present(ally)
    end
    for player in pairs(active) do
        if not keep[player] then
            clear(player)
        end
    end
end
