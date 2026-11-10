--!strict
-- Example integration ONLY. Do not enable in shipped game before PC validates existing RoundCoordinator contracts.
-- Three sibling modules under script.Parent: GoroganVisualPolicy, GoroganVisualPrefab and this LocalScript.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Policy = require(script.Parent:WaitForChild("GoroganVisualPolicy"))
local Prefab = require(script.Parent:WaitForChild("GoroganVisualPrefab"))
local player = Players.LocalPlayer
local remote = ReplicatedStorage:FindFirstChild("TRAP_BossVisualEvent")
if not remote or not remote:IsA("RemoteEvent") then
    warn("D07 Gorogan visual adapter inert: no approved server RemoteEvent")
    return
end

local state = nil
local handle = nil
local activeMatchId = ""
local tickBudget = 0

local function clear()
    Prefab.destroy(handle)
    handle = nil
end

local function resetForAuthoritativeRound()
    clear()
    -- This example uses replicated player attributes written by server code.
    -- PC integrator must verify the real source and replace names if necessary.
    local roundId = player:GetAttribute("TRAP_ActiveMatchId")
    local stage = player:GetAttribute("TRAP_ActiveStage")
    if type(roundId) == "string" and #roundId <= 64
        and (stage == "S1" or stage == "S3") then
        local ok, policy = pcall(Policy.new, roundId, stage)
        state = if ok then policy else nil
        activeMatchId = if state then roundId else ""
    else
        state = nil
        activeMatchId = ""
    end
end

resetForAuthoritativeRound()
local attributeA = player:GetAttributeChangedSignal("TRAP_ActiveMatchId"):Connect(resetForAuthoritativeRound)
local attributeB = player:GetAttributeChangedSignal("TRAP_ActiveStage"):Connect(resetForAuthoritativeRound)
local eventConnection = remote.OnClientEvent:Connect(function(snapshot)
    if not state or player:GetAttribute("TRAP_ActiveMatchId") ~= activeMatchId then return end
    local now = os.clock()
    local result = Policy.apply(state, snapshot, now)
    if result == "STARTED" then
        clear()
        local pos = state.position
        if pos then
            local lowDetail = player:GetAttribute("TRAP_LowDetail") == true
            handle = Prefab.create(workspace, Vector3.new(pos.x,pos.y,pos.z), lowDetail)
        end
    elseif result == "STOMP_STARTED" then
        -- Visible warning only, never deal damage here.
    elseif result == "ENDED" or result == "EXPIRED" then
        clear()
    end
end)
local heartbeat = RunService.Heartbeat:Connect(function(dt)
    tickBudget += math.max(0, dt)
    if tickBudget < .1 then return end
    tickBudget = 0
    if not state then return end
    local status = Policy.expire(state, os.clock())
    if status == "EXPIRED" then clear() end
    if state.active and handle then
        Prefab.render(handle, state.phase, os.clock(), player:GetAttribute("TRAP_ReducedMotion") == true)
    end
end)
script.Destroying:Connect(function()
    eventConnection:Disconnect()
    heartbeat:Disconnect()
    attributeA:Disconnect()
    attributeB:Disconnect()
    clear()
end)
