-- Optional CLIENT-only decorative 3D ghost renderer, requires owner-reviewed adapter.
-- No auto-run, no Remote listener, no cloning/mutation of real player avatars.
local Renderer = {}
Renderer.__index = Renderer

function Renderer.new()
    return setmetatable({model=nil, pieces={}}, Renderer)
end

function Renderer:clear()
    if self.model then self.model:Destroy() end
    self.model = nil
    self.pieces = {}
end

function Renderer:draw(frame, charactersByUser, camera)
    if type(frame) ~= "table" or frame.kind ~= "FRAME"
        or type(charactersByUser) ~= "table" or typeof(camera) ~= "Instance"
        or not camera:IsA("Camera") then
        self:clear()
        return {kind="CLEAR"}
    end
    if type(frame.users) ~= "table" or type(frame.max_parts_per_avatar) ~= "number" then
        self:clear()
        return {kind="CLEAR"}
    end
    if #frame.users > 8 or frame.max_parts_per_avatar > 18
        or frame.max_parts_per_avatar < 1
        or (frame.scale_factor ~= 1.6 and frame.scale_factor ~= 0.7) then
        self:clear()
        return {kind="CLEAR"}
    end
    if self.model and self.model.Parent ~= camera then
        self:clear()
    end
    if not self.model then
        self.model = Instance.new("Folder")
        self.model.Name = "D16ClientOnlyReplicaGhosts"
        self.model.Parent = camera
    end
    local needed = {}
    local total = 0
    for _, userId in ipairs(frame.users) do
        local character = charactersByUser[userId]
        if typeof(character) == "Instance" and character:IsA("Model") then
            local root = character:FindFirstChild("HumanoidRootPart")
            if root and root:IsA("BasePart") then
                local count = 0
                for _, source in ipairs(character:GetDescendants()) do
                    if count >= frame.max_parts_per_avatar or total >= 144 then break end
                    if source:IsA("BasePart") then
                        count += 1
                        total += 1
                        local key = tostring(userId) .. ":" .. tostring(count)
                        needed[key] = true
                        local ghost = self.pieces[key]
                        if not ghost then
                            ghost = Instance.new("Part")
                            ghost.Name = "ReplicaGhost_" .. key
                            ghost.Anchored = true
                            ghost.CanCollide = false
                            ghost.CanTouch = false
                            ghost.CanQuery = false
                            ghost.CastShadow = false
                            ghost.Material = Enum.Material.ForceField
                            ghost.Transparency = 0.72
                            ghost.Parent = self.model
                            self.pieces[key] = ghost
                        end
                        local scale = frame.scale_factor
                        local center = root.Position
                        local relative = source.Position - center
                        ghost.Size = source.Size * scale
                        ghost.CFrame = CFrame.new(center + relative * scale) * source.CFrame.Rotation
                    end
                end
            end
        end
    end
    for key, ghost in pairs(self.pieces) do
        if not needed[key] then
            ghost:Destroy()
            self.pieces[key] = nil
        end
    end
    return {kind="DRAWN", ghosts=total, noninteractive=true}
end

function Renderer:shutdown()
    self:clear()
end

return Renderer
