-- Reference LocalScript module. Disabled by default until PC source / RemoteEvent provenance audit.
local Policy = require(script.Parent.VehicleVisualPolicy)
local Models = require(script.Parent.VehicleVisualModels)
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Client = {}
Client.__index = Client

function Client.new(serverRemote, roundId, options)
    options = options or {}
    if options.enabled ~= true then return nil, "EXPLICIT_OPT_IN_REQUIRED" end
    if typeof(serverRemote) ~= "Instance" or not serverRemote:IsA("RemoteEvent") then
        return nil, "TRUSTED_REMOTE_REQUIRED"
    end
    local state = Policy.new(roundId)
    local folder = Instance.new("Folder")
    folder.Name = "P0D_D14_VisualOnly"
    folder.Parent = Workspace -- Only local instances from this client module.
    local self = setmetatable({ state = state, folder = folder, views = {}, deadlines = {},
        lowDetail = options.lowDetail == true, closed = false, clock = os.clock() }, Client)
    self.remoteConn = serverRemote.OnClientEvent:Connect(function(packet)
        if self.closed then return end
        local actions = Policy.ingest(self.state, packet)
        for _, action in ipairs(actions) do
            if action.op == "CLEAR" then
                for _, view in pairs(self.views) do Models.destroy(view) end
                self.views = {}
                self.deadlines = {}
            elseif action.op == "REMOVE" then
                Models.destroy(self.views[action.vehicleId])
                self.views[action.vehicleId] = nil
                self.deadlines[action.vehicleId] = nil
            elseif action.op == "SPAWN" or action.op == "MOVE" then
                local p = action.presentation
                local view = self.views[action.vehicleId]
                if not view then
                    view = Models.create(action.vehicleId, p.vehicleType, p.team, self.lowDetail, self.folder)
                    self.views[action.vehicleId] = view
                end
                Models.update(view, p)
                self.deadlines[action.vehicleId] = os.clock() + p.remainingMs / 1000
            end
        end
        if self.state.closed then self:close() end
    end)
    self.heartbeatConn = RunService.Heartbeat:Connect(function()
        if self.closed then return end
        local now = os.clock()
        if now - self.clock < 0.25 then return end
        self.clock = now
        for id, deadline in pairs(self.deadlines) do
            if now >= deadline then
                Models.destroy(self.views[id])
                self.views[id] = nil
                self.deadlines[id] = nil
                self.state.items[id] = nil
                -- Avoid MOVE respawning without a fresh START; policy requires it.
            end
        end
    end)
    return self
end

function Client:close()
    if self.closed then return end
    self.closed = true
    if self.remoteConn then self.remoteConn:Disconnect() end
    if self.heartbeatConn then self.heartbeatConn:Disconnect() end
    Policy.close(self.state)
    for _, view in pairs(self.views) do Models.destroy(view) end
    self.views = {}
    self.deadlines = {}
    if self.folder then self.folder:Destroy() end
end

return Client
