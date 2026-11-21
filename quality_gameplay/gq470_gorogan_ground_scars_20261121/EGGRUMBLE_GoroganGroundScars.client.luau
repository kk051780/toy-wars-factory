--!strict
-- GQ470 / FB-015: Gorogan ground-fracture matte accent (A-only visual candidate).
-- Studio/private preview only. No damage, scoring, movement, collision or replication authority.
-- Distinct from #930's actual Gorogan shoulders/crown and #968's human footstep FX.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

if not RunService:IsStudio() then return end

local player = Players.LocalPlayer
if not player then return end

local LOW_TOUCH = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
local MAX_PARTS = if LOW_TOUCH then 4 else 6
local MAX_DISTANCE = if LOW_TOUCH then 100 else 140
local UPDATE_SECONDS = 0.40
local MODEL_NAME = "Gorogan_ServerRig"
local FEATURE_ID = "GQ470_FB015_GOROGAN_GROUND_SCARS_REAL69_20261121"

type Entry = {
    model: Model,
    humanoid: Humanoid,
    parts: {BasePart},
    deathConnection: RBXScriptConnection?,
    destroyConnection: RBXScriptConnection?,
}
local tracked: {[Model]: Entry} = {}
-- Retain only already-observed real boss rigs. DescendantAdded may precede
-- assembly of Humanoid/Torso, and replacement can appear before old rig dies.
local candidates: {[Model]: boolean} = {}
local ownerModel: Model? = nil
local folder = Instance.new("Folder")
folder.Name = "GQ470_GoroganGroundScars_ClientOnly"
folder:SetAttribute("VisualOnly", true)
folder:SetAttribute("FeatureId", FEATURE_ID)
folder.Parent = Workspace

local function clearParts(entry: Entry)
    for _, piece in ipairs(entry.parts) do
        if piece.Parent then piece:Destroy() end
    end
    table.clear(entry.parts)
end

local function release(model: Model)
    local entry = tracked[model]
    if not entry then return end
    tracked[model] = nil
    if ownerModel == model then ownerModel = nil end
    if entry.deathConnection then entry.deathConnection:Disconnect() end
    if entry.destroyConnection then entry.destroyConnection:Disconnect() end
    clearParts(entry)
end

local function track(instance: Instance)
    if not instance:IsA("Model") or instance.Name ~= MODEL_NAME then return end
    local model = instance :: Model
    if ownerModel or tracked[model] then return end
    local humanoid = model:FindFirstChildOfClass("Humanoid")
    local torso = model:FindFirstChild("Torso")
    if not humanoid or not torso or not torso:IsA("BasePart")
        or humanoid.Health <= 0 then return end
    local entry: Entry = {
        model = model, humanoid = humanoid, parts = {},
        deathConnection = nil, destroyConnection = nil,
    }
    tracked[model] = entry
    ownerModel = model
    entry.deathConnection = humanoid.Died:Connect(function() release(model) end)
    entry.destroyConnection = model.Destroying:Connect(function() release(model) end)
end

local function makePiece(index: number): BasePart
    local piece = Instance.new("WedgePart")
    piece.Name = "BasaltGroundScar_" .. tostring(index)
    piece.Anchored = true
    piece.CanCollide = false
    piece.CanTouch = false
    piece.CanQuery = false
    piece.CastShadow = false
    piece.Material = Enum.Material.Slate
    piece.Color = if index % 2 == 0
        then Color3.fromRGB(92, 104, 111)
        else Color3.fromRGB(66, 76, 83)
    piece.Transparency = 0.16
    piece.Size = Vector3.new(1.6, 0.20, 3.4)
    piece.Parent = folder
    return piece
end

local function hide(entry: Entry)
    for _, piece in ipairs(entry.parts) do
        piece.Transparency = 1
    end
end

local ray = RaycastParams.new()
ray.FilterType = Enum.RaycastFilterType.Exclude
ray.IgnoreWater = true

local function update(entry: Entry)
    local model = entry.model
    if not model:IsDescendantOf(Workspace) or entry.humanoid.Health <= 0 then
        release(model)
        return
    end
    -- Do not reveal invisible opponents or render when the local avatar is absent.
    local character = player.Character
    local root = character and character:FindFirstChild("HumanoidRootPart")
    local torso = model:FindFirstChild("Torso")
    if player:GetAttribute("EGGRUMBLE_ReducedEffects") == true
        or not root or not root:IsA("BasePart")
        or not torso or not torso:IsA("BasePart")
        or (root.Position - torso.Position).Magnitude > MAX_DISTANCE then
        hide(entry)
        return
    end
    ray.FilterDescendantsInstances = {model, folder}
    local hit = Workspace:Raycast(torso.Position + Vector3.new(0, 4, 0),
        Vector3.new(0, -40, 0), ray)
    if not hit or hit.Material == Enum.Material.Water or hit.Normal.Y < 0.82 then
        hide(entry)
        return
    end
    local bodyRadius = math.clamp(math.max(torso.Size.X, torso.Size.Z) * 0.8, 3.9, 6.5)
    for i = 1, MAX_PARTS do
        local piece = entry.parts[i]
        if not piece then
            piece = makePiece(i)
            table.insert(entry.parts, piece)
        end
        local radians = ((i - 1) / MAX_PARTS) * math.pi * 2
        local radial = Vector3.new(math.cos(radians), 0, math.sin(radians))
        local center = hit.Position + radial * bodyRadius + hit.Normal * 0.12
        piece.CFrame = CFrame.lookAt(center, center + radial, hit.Normal)
        piece.Transparency = 0.16
    end
end

for _, candidate in ipairs(Workspace:GetDescendants()) do
    if candidate:IsA("Model") and candidate.Name == MODEL_NAME then
        candidates[candidate] = true
        track(candidate)
    end
end
local addedConnection = Workspace.DescendantAdded:Connect(function(instance)
    if instance:IsA("Model") and instance.Name == MODEL_NAME then
        candidates[instance] = true
        task.defer(track, instance)
    end
end)
local removingConnection = Workspace.DescendantRemoving:Connect(function(instance)
    if instance:IsA("Model") and candidates[instance] then
        candidates[instance] = nil
        release(instance)
    end
end)

local alive = true
script.Destroying:Connect(function()
    alive = false
    addedConnection:Disconnect()
    removingConnection:Disconnect()
    for model in pairs(tracked) do release(model) end
    table.clear(candidates)
    folder:Destroy()
end)
task.spawn(function()
    while alive do
        -- Do not scan the whole Workspace on every frame. Retry only actual
        -- observed boss models that may have arrived before their children,
        -- or appeared as the outgoing boss was still alive.
        if not ownerModel then
            for model in pairs(candidates) do
                if model:IsDescendantOf(Workspace) then
                    track(model)
                    if ownerModel then break end
                else
                    candidates[model] = nil
                end
            end
        end
        for _, entry in pairs(tracked) do update(entry) end
        task.wait(UPDATE_SECONDS)
    end
end)
