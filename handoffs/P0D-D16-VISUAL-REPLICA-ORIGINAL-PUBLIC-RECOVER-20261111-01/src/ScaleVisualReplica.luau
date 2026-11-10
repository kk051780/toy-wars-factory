-- Local-only visual replicas: no live Character scaling, RemoteEvent send, physics or server damage.
-- Studio/PC must review client FPS and avatar compatibility before enabling.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")
local Policy = require(script.Parent.ScaleFxClientPolicy)
local Replica = {}
Replica.__index = Replica
local MAX_VISIBLE_PLAYERS = 8
local MAX_PARTS_PER_PLAYER = 18
local MAX_DISTANCE = 90

local function playerForId(id)
    for _, player in ipairs(Players:GetPlayers()) do
        if tostring(player.UserId) == id then return player end
    end
    return nil
end
local function safePartClone(source, parent, ratio)
    local ok, clone = pcall(function() return source:Clone() end)
    if not ok or clone == nil or not clone:IsA("BasePart") then return nil end
    -- No cloned scripts, constraints, attachments, sounds, particles or arbitrary descendants.
    for _, descendant in ipairs(clone:GetDescendants()) do
        if not descendant:IsA("SpecialMesh") and not descendant:IsA("Decal")
            and not descendant:IsA("Texture") and not descendant:IsA("SurfaceAppearance") then
            descendant:Destroy()
        end
    end
    clone.Anchored = true
    clone.CanCollide, clone.CanTouch, clone.CanQuery = false, false, false
    clone.CastShadow = false
    clone.Massless = true
    clone.Transparency = math.max(source.Transparency, 0.42)
    clone.Size = source.Size * ratio
    clone.Parent = parent
    return clone
end
local function destroyGhost(ghost)
    if ghost and ghost.folder then ghost.folder:Destroy() end
end
function Replica.new(remote, currentMatchId)
    assert(remote and remote:IsA("RemoteEvent"), "SERVER_REMOTE_REQUIRED")
    assert(type(currentMatchId) == "function", "MATCH_ID_CALLBACK_REQUIRED")
    local self = setmetatable({}, Replica)
    self.remote, self.getMatchId, self.policy = remote, currentMatchId, nil
    self.folder = Instance.new("Folder")
    self.folder.Name = "TrapRaidersD16VisualOnly"
    self.folder.Parent = Workspace
    self.ghosts = {}
    self.closed = false
    self.connections = {
        remote.OnClientEvent:Connect(function(packet) self:_onPacket(packet) end),
        RunService.RenderStepped:Connect(function() self:_frame() end),
        Players.PlayerRemoving:Connect(function(player)
            self:_remove(tostring(player.UserId))
        end)
    }
    return self
end
function Replica:_remove(id)
    destroyGhost(self.ghosts[id])
    self.ghosts[id] = nil
end
function Replica:_clear()
    for id, _ in pairs(self.ghosts) do self:_remove(id) end
end
function Replica:_onPacket(packet)
    if self.closed then return end
    local matchId = self.getMatchId()
    if type(matchId) ~= "string" or #matchId == 0 then
        self:_clear(); self.policy = nil; return
    end
    if self.policy == nil or self.policy.matchId ~= matchId then
        self:_clear(); self.policy = Policy.new(matchId)
    end
    local accepted = Policy.accept(self.policy, packet, matchId, os.clock())
    if accepted and self.policy.status ~= "ACTIVE" then self:_clear() end
end
function Replica:_build(id, player, ratio)
    if self.ghosts[id] then return end
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not root or not root:IsA("BasePart") then return end
    local folder = Instance.new("Folder")
    folder.Name = "CosmeticReplica_" .. id
    folder.Parent = self.folder
    local parts = {}
    for _, source in ipairs(character:GetDescendants()) do
        if #parts >= MAX_PARTS_PER_PLAYER then break end
        if source:IsA("BasePart") and source ~= root and source.Transparency < 1 then
            local clone = safePartClone(source, folder, ratio)
            if clone then parts[#parts + 1] = {original = source, clone = clone} end
        end
    end
    if #parts == 0 then folder:Destroy(); return end
    self.ghosts[id] = {folder = folder, character = character, root = root, parts = parts}
end
function Replica:_frame()
    if self.closed then return end
    local currentMatch = self.getMatchId()
    if self.policy == nil then return end
    local status = Policy.tick(self.policy, currentMatch, os.clock())
    if status ~= "ACTIVE" then self:_clear(); return end
    local ratio = self.policy.scaleMilli / 1000
    local desired, displayed = {}, 0
    for _, id in ipairs(self.policy.targets) do
        desired[id] = true
        local player = playerForId(id)
        local root = player and player.Character and player.Character:FindFirstChild("HumanoidRootPart")
        local me = Players.LocalPlayer.Character
        local myRoot = me and me:FindFirstChild("HumanoidRootPart")
        local near = root and myRoot and (root.Position - myRoot.Position).Magnitude <= MAX_DISTANCE
        if near and displayed < MAX_VISIBLE_PLAYERS then
            displayed += 1
            local old = self.ghosts[id]
            if old and old.character ~= player.Character then self:_remove(id) end
            self:_build(id, player, ratio)
            local ghost = self.ghosts[id]
            if ghost and ghost.root.Parent then
                local rootCFrame = ghost.root.CFrame
                for _, pair in ipairs(ghost.parts) do
                    if pair.original.Parent then
                        local localCFrame = rootCFrame:ToObjectSpace(pair.original.CFrame)
                        local rotation = localCFrame - localCFrame.Position
                        pair.clone.CFrame = rootCFrame * CFrame.new(localCFrame.Position * ratio) * rotation
                    else
                        self:_remove(id)
                        break
                    end
                end
            end
        else
            self:_remove(id)
        end
    end
    for id, _ in pairs(self.ghosts) do
        if not desired[id] then self:_remove(id) end
    end
end
function Replica:destroy()
    if self.closed then return end
    self.closed = true
    for _, c in ipairs(self.connections) do c:Disconnect() end
    self:_clear()
    self.folder:Destroy()
end
return Replica
