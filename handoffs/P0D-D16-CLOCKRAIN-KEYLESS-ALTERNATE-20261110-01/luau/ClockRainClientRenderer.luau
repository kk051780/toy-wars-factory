-- Optional owner-controlled client visual adapter. No auto-run or remote listeners.
-- Geometry is decorative: anchored, noncollidable, nonqueryable, no Humanoid.
local Policy = require(script.Parent.ClockRainVisualPolicy)
local Renderer = {}
Renderer.__index = Renderer

function Renderer.new()
    return setmetatable({policy = Policy.new(), model = nil, parts = {}}, Renderer)
end

function Renderer:clear()
    if self.model then
        self.model:Destroy()
    end
    self.model = nil
    self.parts = {}
    self.policy:stop()
end

function Renderer:begin(trustedEvent)
    if self.model then
        return {kind = "REJECTED", reason = "already showing"}
    end
    local result = self.policy:start(trustedEvent)
    if result.kind ~= "STARTED" then
        return result
    end
    local camera = workspace.CurrentCamera
    if not camera then
        self.policy:stop()
        return {kind = "REJECTED", reason = "camera missing"}
    end
    local model = Instance.new("Model")
    model.Name = "ClockRainClientFX"
    model.Parent = camera
    self.model = model
    for i = 1, result.parts do
        local p = Instance.new("Part")
        p.Name = "ClockMarker_" .. tostring(i)
        p.Shape = Enum.PartType.Cylinder
        p.Size = Vector3.new(0.18, 1.4, 1.4)
        p.Anchored = true
        p.CanCollide = false
        p.CanTouch = false
        p.CanQuery = false
        p.CastShadow = false
        p.Material = Enum.Material.SmoothPlastic
        p.Color = Color3.fromRGB(200, 220, 238)
        p.Transparency = 0.25
        p.Parent = model
        self.parts[i] = p
    end
    return result
end

function Renderer:step(now, matchId, epoch, anchorCFrame)
    if not self.model then
        return {kind = "IDLE"}
    end
    if typeof(anchorCFrame) ~= "CFrame" then
        self:clear()
        return {kind = "CLEARED", reason = "invalid anchor"}
    end
    local frame = self.policy:step(now, matchId, epoch)
    if frame.kind ~= "FRAME" then
        self:clear()
        return frame
    end
    for i, marker in ipairs(frame.markers) do
        local part = self.parts[i]
        if not part then
            self:clear()
            return {kind = "CLEARED", reason = "marker missing"}
        end
        part.CFrame = anchorCFrame
            * CFrame.new(marker.x, marker.y, marker.z)
            * CFrame.Angles(0, marker.yaw, math.rad(90))
        part.Transparency = 1 - 0.75 * marker.opacity
    end
    return {kind = "FRAME", parts = #self.parts}
end

function Renderer:shutdown()
    self:clear()
end

return Renderer
