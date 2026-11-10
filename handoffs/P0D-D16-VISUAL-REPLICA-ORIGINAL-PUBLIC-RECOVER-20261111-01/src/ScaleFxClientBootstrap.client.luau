-- Optional client integration example. Do not enable until PC Codex verifies genuine v37 round ID.
-- Only trusted RoundCoordinator broadcasts validated visual snapshots to clients.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local root = ReplicatedStorage:FindFirstChild("TrapRaiders")
if not root then return end
local remote = root:FindFirstChild("ScaleFxDisplay")
if not remote or not remote:IsA("RemoteEvent") then return end
local Replica = require(script.Parent.ScaleVisualReplica)
local controller = Replica.new(remote, function()
    -- Round ID must be a server-replicated attribute, not derived from client claim.
    return root:GetAttribute("ActiveRoundId")
end)
script.Destroying:Connect(function() controller:destroy() end)
