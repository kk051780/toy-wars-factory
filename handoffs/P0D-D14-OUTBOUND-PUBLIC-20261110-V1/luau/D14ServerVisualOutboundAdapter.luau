--!strict
-- Server-only optional adapter. Disabled until the OWNER PC explicitly reviews
-- real seat+motion callbacks. Delivers visual-only frames; never accepts Remote input.
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local Core = require(script.Parent:WaitForChild("D14VisualPublisherCore"))
local Adapter = {}
Adapter.__index = Adapter

function Adapter.new(opts)
    if not RunService:IsServer() then return nil, "SERVER_ONLY" end
    if type(opts) ~= "table" or opts.enabled ~= true then
        return nil, "DISABLED_BY_DEFAULT"
    end
    if typeof(opts.remote) ~= "Instance" or not opts.remote:IsA("RemoteEvent")
        or type(opts.authority) ~= "table"
        or type(opts.authority.getSnapshot) ~= "function"
        or type(opts.authority.getRecipients) ~= "function"
        or type(opts.authority.isTrustedRound) ~= "function"
        or type(opts.authority.encodeVisual) ~= "function" then
        return nil, "MISSING_SERVER_DEPENDENCY"
    end
    return setmetatable({core=Core.new(),opts=opts,active=false},Adapter), "OK"
end
function Adapter:beginRound(roundId, now)
    if self.active then return false, "ALREADY_RUNNING" end
    if not self.opts.authority.isTrustedRound(roundId) then return false,"UNTRUSTED_ROUND" end
    local ok,reason=Core.beginRound(self.core,roundId,now)
    if ok then self.active=true end
    return ok,reason
end
function Adapter:publishFromServer(vehicleId)
    if not self.active then return false,"INACTIVE" end
    -- API accepts ONLY canonical server-owned vehicleId, never a Player/Remote payload.
    local a=self.opts.authority
    local snapshot=a.getSnapshot(vehicleId)
    if type(snapshot) ~= "table" or not a.isTrustedRound(snapshot.roundId) then
        return false,"UNTRUSTED_SNAPSHOT"
    end
    -- The OWNER PC must compute these booleans from genuine live server systems.
    if snapshot.authorizedServer ~= true or snapshot.seatVerified ~= true then
        return false,"NO_SERVER_RECEIPTS"
    end
    local frame,reason=Core.publish(self.core,snapshot)
    if frame == nil then return false,reason end
    local encoded=a.encodeVisual(frame) -- Must map to actual D14 client visual schema in PC.
    if type(encoded) ~= "table" then return false,"ENCODER_REJECTED" end
    local people=a.getRecipients(frame)
    if type(people) ~= "table" or #people > 4 then return false,"RECIPIENT_LIMIT" end
    for _, player in ipairs(people) do
        if typeof(player) ~= "Instance" or not player:IsA("Player") or player.Parent ~= Players then
            return false,"UNTRUSTED_RECIPIENT"
        end
    end
    -- FireClient is deliberately OUTBOUND only. No inbound event subscriptions.
    for _,player in ipairs(people) do self.opts.remote:FireClient(player,encoded) end
    return true,"SENT"
end
function Adapter:stop()
    self.active=false
    Core.stop(self.core)
    return true
end
return Adapter
