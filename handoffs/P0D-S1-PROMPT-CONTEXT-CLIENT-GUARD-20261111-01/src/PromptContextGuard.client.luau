--!strict
-- This optional LocalScript *only* changes the built-in prompt's local visual style.
-- It never changes Enabled, connects to Triggered, creates remotes, or sends intent.
-- Server ProximityPrompt.Enabled and Rules.canSteal/canScore remain in charge.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local player = Players.LocalPlayer
local Model = require(script.Parent:WaitForChild("TrapRaidersPromptPolicy"))
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote") :: RemoteEvent
local current = Model.new()
local managed: {[ProximityPrompt]: boolean} = {}

local function findObjectiveParts()
    local arena = workspace:FindFirstChild("TRAP_RAIDERS_S1")
    if not arena then return nil end
    local objects: {[string]: BasePart} = {}
    for _, team in ipairs({"RED", "BLUE"}) do
        local base = arena:FindFirstChild(team .. "_CASTLE")
        if not base then return nil end
        local egg = base:FindFirstChild(team .. "_EGG")
        local pad = base:FindFirstChild(team .. "_SCORE_PAD")
        if not egg or not egg:IsA("BasePart") or not pad or not pad:IsA("BasePart") then
            return nil
        end
        objects[team .. "_EGG"] = egg
        objects[team .. "_SCORE_PAD"] = pad
    end
    return objects
end

local function alive(): boolean
    local character = player.Character
    local humanoid = if character then character:FindFirstChildOfClass("Humanoid") else nil
    return humanoid ~= nil and humanoid.Health > 0
end

local function applyStyle(prompt: ProximityPrompt, allowed: boolean)
    -- Don't overtake an unknown Custom prompt/UI from another owner.
    if managed[prompt] == nil then
        if prompt.Style ~= Enum.ProximityPromptStyle.Default then return end
        managed[prompt] = true
    end
    local desired = if allowed then Enum.ProximityPromptStyle.Default else Enum.ProximityPromptStyle.Custom
    if prompt.Style ~= desired then prompt.Style = desired end
end

local function restoreOwned()
    for prompt in pairs(managed) do
        if prompt.Parent and prompt.Style == Enum.ProximityPromptStyle.Custom then
            prompt.Style = Enum.ProximityPromptStyle.Default
        end
        managed[prompt] = nil
    end
end

local function refresh()
    local parts = findObjectiveParts()
    if not parts then
        -- Map may not be replicated yet; fail closed until next snapshot.
        return
    end
    local ownEggVisible = false
    if current.team == "RED" or current.team == "BLUE" then
        local ownEgg = parts[current.team .. "_EGG"]
        -- Source S1 sets egg.Transparency to exactly 0 at home and 1 when stolen.
        ownEggVisible = ownEgg ~= nil and ownEgg.Transparency <= 0.05
    end
    local show = Model.view(current, ownEggVisible and alive())
    for key, part in pairs(parts) do
        local prompt = part:FindFirstChildOfClass("ProximityPrompt")
        if prompt and prompt:IsA("ProximityPrompt") then
            applyStyle(prompt, show[key] == true and alive())
        end
    end
end

remote.OnClientEvent:Connect(function(packet: any)
    Model.consume(current, packet)
    refresh()
end)

-- The same snapshot cadence will refresh current map on late replication.
-- Avoid periodic CPU loops and do not overwrite any other owned HUD or Remote.
player.CharacterAdded:Connect(function()
    current.valid = false
    refresh()
end)
script.Destroying:Connect(restoreOwned)
