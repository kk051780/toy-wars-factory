--!strict
-- Optional EGGRUMBLE V3 server-owned boss-counter lifecycle fence.
-- Runs in ServerScriptService in Studio AND in production ServerScriptService.
-- The original GAME preview still owns its own Studio-only activation gate.
-- No second Game, Remote, boss AI, reward or result implementation.
local Players = game:GetService("Players")
local Policy = require(script.Parent:WaitForChild("EGGRUMBLE_BossCreditPolicy"))
local MODE = "EGGRUMBLE_QueuedMode"
local COUNTER = "EGGRUMBLE_BossDefeats"
local previousModes: {[Player]: any} = {}
local listeners: {[Player]: RBXScriptConnection} = {}

local function unbind(player: Player)
    local connection = listeners[player]
    if connection then connection:Disconnect() end
    listeners[player] = nil
    previousModes[player] = nil
end

local function bind(player: Player)
    if listeners[player] then return end
    local initial = player:GetAttribute(MODE)
    previousModes[player] = initial
    listeners[player] = player:GetAttributeChangedSignal(MODE):Connect(function()
        if player.Parent ~= Players then return end
        local previous = previousModes[player]
        local current = player:GetAttribute(MODE)
        previousModes[player] = current
        if Policy.shouldReset(previous, current) then
            player:SetAttribute(COUNTER, 0)
        end
    end)
    -- Never clear an in-progress match when this optional Script starts late.
    if initial == nil and player.Parent == Players then
        player:SetAttribute(COUNTER, 0)
    end
end

Players.PlayerAdded:Connect(bind)
Players.PlayerRemoving:Connect(unbind)
for _, player in ipairs(Players:GetPlayers()) do
    bind(player)
end
