--!strict
-- Optional private Studio-only addon. Adds no Game, Remote, event reward or scoreboard.
-- Original 21-source V3 and its lobby/round service are immutable inputs.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local Fence = require(script.Parent:WaitForChild("EGGRUMBLE_RoundAttributeFence"))
local connections: {[Player]: RBXScriptConnection} = {}

local function bind(player: Player)
    if connections[player] then return end
    local previous = player:GetAttribute("EGGRUMBLE_QueuedMode")
    connections[player] = player:GetAttributeChangedSignal("EGGRUMBLE_QueuedMode"):Connect(function()
        local current = player:GetAttribute("EGGRUMBLE_QueuedMode")
        if Fence.shouldClear(previous, current) then
            -- A finished/abandoned match returns to a clean lobby. The source
            -- of authority for egg/KO/round results remains the original Game.
            Fence.clear(player)
        end
        previous = current
    end)
end

for _, player in ipairs(Players:GetPlayers()) do bind(player) end
Players.PlayerAdded:Connect(bind)
Players.PlayerRemoving:Connect(function(player)
    local connection = connections[player]
    if connection then connection:Disconnect() end
    connections[player] = nil
end)
