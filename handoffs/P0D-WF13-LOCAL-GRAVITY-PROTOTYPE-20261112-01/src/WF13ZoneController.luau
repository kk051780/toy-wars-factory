--!strict
-- WF13ZoneController: opt-in, original, isolated server-side low gravity.
-- No network messages, prizes, egg authority, global gravity change, or auto-start.
local Policy = require(script.Parent.WF13Policy)

local Controller = {}
Controller.__index = Controller

local OWNER_ATTRIBUTE = "WF13GravityOwner"
local FORCE_NAME = "WF13ServerVectorForce"
local ATTACHMENT_NAME = "WF13ServerAttachment"

local function liveCharacter(player: Player): (Model?, BasePart?, Humanoid?)
    local char = player.Character
    if not char or not char.Parent then return nil, nil, nil end
    local root = char:FindFirstChild("HumanoidRootPart")
    local humanoid = char:FindFirstChildOfClass("Humanoid")
    if not root or not root:IsA("BasePart") or root.Anchored then return nil, nil, nil end
    if not humanoid or humanoid.Health <= 0 then return nil, nil, nil end
    return char, root, humanoid
end

local function restoreOwnership(entry)
    local root = entry.root
    if not root or not root.Parent or not entry.ownsNetwork then return end
    pcall(function()
        if root:CanSetNetworkOwnership() then
            if entry.oldAuto then
                root:SetNetworkOwnershipAuto()
            elseif entry.oldOwner and entry.oldOwner.Parent then
                root:SetNetworkOwner(entry.oldOwner)
            else
                root:SetNetworkOwnershipAuto()
            end
        end
    end)
end

function Controller.new(deps)
    assert(deps and deps.players and deps.runService and deps.workspace and deps.zone, "WF13 dependencies missing")
    assert(deps.zone:IsA("BasePart"), "WF13 zone must be a BasePart")
    assert(deps.safePad and deps.safePad:IsA("BasePart"), "WF13 safe fallback pad is required")
    local self = setmetatable({}, Controller)
    self.players = deps.players
    self.runService = deps.runService
    self.workspace = deps.workspace
    self.zone = deps.zone
    self.safePad = deps.safePad
    self.records = {}
    self.blockedUntilExit = {}
    self.conns = {}
    self.playerConns = {}
    self.running = false
    self.destroyed = false
    self.accumulated = 0
    self.token = "WF13-" .. tostring(self)
    return self
end

function Controller:_inside(root: BasePart): boolean
    if not self.zone.Parent or not self.zone:IsDescendantOf(self.workspace) then return false end
    local localPos = self.zone.CFrame:PointToObjectSpace(root.Position)
    local size = self.zone.Size
    return Policy.insideEllipsoid(localPos.X, localPos.Y, localPos.Z, size.X, size.Y, size.Z)
end

function Controller:_clear(player: Player)
    local entry = self.records[player]
    if not entry then return end
    self.records[player] = nil
    local root = entry.root
    if entry.force then pcall(function() entry.force.Enabled = false end) end
    if entry.force then pcall(function() entry.force:Destroy() end) end
    if entry.attachment then pcall(function() entry.attachment:Destroy() end) end
    if root and root.Parent then
        pcall(function()
            if root:GetAttribute(OWNER_ATTRIBUTE) == self.token then
                root:SetAttribute(OWNER_ATTRIBUTE, nil)
            end
        end)
    end
    restoreOwnership(entry)
end

function Controller:_enter(player: Player, char: Model, root: BasePart)
    if self.records[player] or self.blockedUntilExit[player] then return end
    if root:GetAttribute(OWNER_ATTRIBUTE) ~= nil then return end
    if root:FindFirstChild(FORCE_NAME) or root:FindFirstChild(ATTACHMENT_NAME) then return end

    local canRead, canSet = pcall(function() return root:CanSetNetworkOwnership() end)
    if not canRead or not canSet then return end
    local oldAuto, oldOwner
    local readOk = pcall(function()
        oldAuto = root:GetNetworkOwnershipAuto()
        oldOwner = root:GetNetworkOwner()
    end)
    if not readOk then return end
    local locked = pcall(function() root:SetNetworkOwner(nil) end)
    if not locked then return end

    local attachment = Instance.new("Attachment")
    attachment.Name = ATTACHMENT_NAME
    attachment.Parent = root
    local force = Instance.new("VectorForce")
    force.Name = FORCE_NAME
    force.Attachment0 = attachment
    force.ApplyAtCenterOfMass = true
    force.RelativeTo = Enum.ActuatorRelativeTo.World
    force.Force = Vector3.zero
    force.Enabled = true
    force.Parent = root

    root:SetAttribute(OWNER_ATTRIBUTE, self.token)
    self.records[player] = {
        char = char,
        root = root,
        attachment = attachment,
        force = force,
        oldAuto = oldAuto,
        oldOwner = oldOwner,
        ownsNetwork = true,
        mode = "active",
        dwell = 0,
        landingElapsed = 0,
    }
end

function Controller:_recover(entry)
    local root = entry.root
    if not root or not root.Parent or not self.safePad.Parent then return end
    local bottom = self.zone.Position.Y - self.zone.Size.Y * 0.5
    if root.Position.Y >= bottom - Policy.SAFETY_DEPTH then return end
    local char = entry.char
    if not char or not char.Parent then return end
    char:PivotTo(CFrame.new(self.safePad.Position + Vector3.new(0, 5, 0)))
    root.AssemblyLinearVelocity = Vector3.zero
end

function Controller:_landing(entry, dt)
    entry.mode = "landing"
    entry.landingElapsed += dt
    if not entry.force or not entry.force.Parent or not entry.root.Parent then return false end
    local newForce = Policy.landingForce(entry.root.AssemblyMass, self.workspace.Gravity, entry.landingElapsed)
    entry.force.Force = Vector3.new(0, newForce, 0)
    return entry.landingElapsed < Policy.LANDING_SECONDS
end

function Controller:_samplePlayer(player: Player, dt: number)
    local char, root = liveCharacter(player)
    local entry = self.records[player]
    if not char or not root then
        self:_clear(player)
        self.blockedUntilExit[player] = nil
        return
    end
    if entry and (entry.char ~= char or entry.root ~= root
        or not entry.force or not entry.force.Parent
        or not entry.attachment or not entry.attachment.Parent
        or root:GetAttribute(OWNER_ATTRIBUTE) ~= self.token) then
        self:_clear(player)
        self.blockedUntilExit[player] = true
        return
    end

    local inside = self:_inside(root)
    if not inside then self.blockedUntilExit[player] = nil end
    if inside and not entry and not self.blockedUntilExit[player] then
        self:_enter(player, char, root)
        entry = self.records[player]
    end
    if not entry then return end

    self:_recover(entry)
    -- If recovery teleports outside, clear and leave player's physics untouched.
    inside = self:_inside(root)
    if not inside then self.blockedUntilExit[player] = nil end

    if entry.mode == "active" and inside then
        entry.dwell += dt
        if entry.dwell >= Policy.MAX_DWELL then
            self.blockedUntilExit[player] = true
            entry.mode = "landing"
            entry.landingElapsed = 0
        else
            local mass = root.AssemblyMass
            entry.force.Force = Vector3.new(0,
                Policy.upwardForce(mass, self.workspace.Gravity, Policy.GRAVITY_RATIO), 0)
            local v = root.AssemblyLinearVelocity
            local vx, vy, vz = Policy.clampVelocity(v.X, v.Y, v.Z)
            if vx ~= v.X or vy ~= v.Y or vz ~= v.Z then
                root.AssemblyLinearVelocity = Vector3.new(vx, vy, vz)
            end
            return
        end
    end
    -- On exit, timed dwell limit or brief loss of a valid zone: fade assistance 2 seconds.
    if entry.mode ~= "landing" then
        entry.mode = "landing"
        entry.landingElapsed = 0
        local v = root.AssemblyLinearVelocity
        if v.Y < -Policy.MAX_FALL then
            root.AssemblyLinearVelocity = Vector3.new(v.X, -Policy.MAX_FALL, v.Z)
        end
    end
    if not self:_landing(entry, dt) then
        self:_clear(player)
        if inside then self.blockedUntilExit[player] = true end
    end
end

function Controller:_bindPlayer(player: Player)
    if self.playerConns[player] then return end
    self.playerConns[player] = player.CharacterRemoving:Connect(function(oldChar)
        local entry = self.records[player]
        if entry and entry.char == oldChar then self:_clear(player) end
        self.blockedUntilExit[player] = nil
    end)
end

function Controller:start()
    assert(not self.destroyed, "WF13 controller has been destroyed")
    if self.running then return end
    self.running = true
    for _, player in ipairs(self.players:GetPlayers()) do self:_bindPlayer(player) end
    table.insert(self.conns, self.players.PlayerAdded:Connect(function(player)
        self:_bindPlayer(player)
    end))
    table.insert(self.conns, self.players.PlayerRemoving:Connect(function(player)
        self:_clear(player)
        self.blockedUntilExit[player] = nil
        local conn = self.playerConns[player]
        if conn then conn:Disconnect(); self.playerConns[player] = nil end
    end))
    table.insert(self.conns, self.runService.Heartbeat:Connect(function(dt)
        if not self.running or self.destroyed then return end
        self.accumulated += math.min(math.max(dt, 0), 0.25)
        if self.accumulated < Policy.SAMPLE_SECONDS then return end
        local elapsed = self.accumulated
        self.accumulated = 0
        for _, player in ipairs(self.players:GetPlayers()) do
            self:_samplePlayer(player, elapsed)
        end
    end))
end

function Controller:stop()
    self.running = false
    for _, conn in ipairs(self.conns) do conn:Disconnect() end
    table.clear(self.conns)
    for player, conn in pairs(self.playerConns) do
        conn:Disconnect()
        self.playerConns[player] = nil
    end
    for player in pairs(self.records) do self:_clear(player) end
    table.clear(self.blockedUntilExit)
    self.destroyed = true
end

return Controller
