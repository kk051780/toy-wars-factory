--!nocheck
-- FB-008 / FB-015 ART-COMBAT: server-CONFIRMED neutral hits -> short
-- original client-local slash arcs. Pure appearance, never hit authority.
-- This private candidate is intentionally Studio-only pending OWNER visual QA.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end

local Players = game:GetService("Players")
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local localPlayer = Players.LocalPlayer
if not localPlayer then return end

local arena = workspace:WaitForChild("TRAP_RAIDERS_S1", 45)
if not arena then warn("ART_COMBAT_NO_ARENA"); return end
local mobs = arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)
if not mobs then warn("ART_COMBAT_NO_HORDE"); return end

local FEATURE = "ART_COMBAT_SLASH_READONLY_V1"
local MAX_LIVE = 8
local MAX_BURSTS_PER_SECOND = 9
local live = 0
local times = {}
local bound = {}
local folderConnection
local destroyed = false

local function isOriginalMob(model)
    return model:IsA("Model")
        and (model.Name:match("^MUSOU_MINION_%d+$") ~= nil
            or model.Name == "MUSOU_ELITE_TELEGRAPH")
end

local function makeArc(hitPos, toward, isKO)
    if live >= MAX_LIVE then return end
    local dx = Vector3.new(toward.X - hitPos.X, 0, toward.Z - hitPos.Z)
    if dx.Magnitude < .1 then dx = Vector3.new(0, 0, -1) end
    local holder = Instance.new("Part")
    holder.Name = "P0D_ART_COMBAT_SLASH_FX"
    holder.Anchored = true
    holder.Size = Vector3.new(.12, .12, .12)
    holder.Transparency = 1
    holder.CanCollide = false
    holder.CanTouch = false
    holder.CanQuery = false
    holder.CastShadow = false
    holder.CFrame = CFrame.lookAt(hitPos + Vector3.new(0, 1.35, 0), hitPos + dx)
    holder.Parent = workspace
    live += 1
    holder.Destroying:Connect(function() live = math.max(0, live - 1) end)

    local count = if UserInputService.TouchEnabled then 1 else 2
    local extent = if isKO then 3.2 else 2.25
    for i = 1, count do
        local a = Instance.new("Attachment")
        a.Name = "FX_START_" .. i
        a.Position = Vector3.new(-extent, (i - 1) * .24, -.25)
        a.Parent = holder
        local b = Instance.new("Attachment")
        b.Name = "FX_END_" .. i
        b.Position = Vector3.new(extent, .35 + (i - 1) * .3, -.25)
        b.Parent = holder
        local beam = Instance.new("Beam")
        beam.Name = "P0D_SERVER_HIT_CONFIRMED_ARC"
        beam.Attachment0 = a
        beam.Attachment1 = b
        beam.Segments = 10
        beam.CurveSize0 = if i == 1 then 2.7 else -2.1
        beam.CurveSize1 = if i == 1 then -2.0 else 1.8
        beam.Width0 = if isKO then .48 else .32
        beam.Width1 = .11
        beam.FaceCamera = true
        beam.LightEmission = .7
        beam.Color = if isKO
            then ColorSequence.new(Color3.fromRGB(255, 186, 63), Color3.fromRGB(255, 246, 207))
            else ColorSequence.new(Color3.fromRGB(139, 235, 255), Color3.fromRGB(255, 250, 210))
        beam.Transparency = NumberSequence.new({
            NumberSequenceKeypoint.new(0, .12),
            NumberSequenceKeypoint.new(.55, .04),
            NumberSequenceKeypoint.new(1, 1),
        })
        beam.Parent = holder
    end
    TweenService:Create(holder, TweenInfo.new(.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
        CFrame = holder.CFrame * CFrame.Angles(0, 0, math.rad(if isKO then 52 else 32))
    }):Play()
    Debris:AddItem(holder, .22)
end

local function onConfirmedHit(core, popup, textLabel, state)
    if destroyed or not core.Parent or not popup.Parent or not popup.Enabled then return end
    local cue = textLabel.Text
    local isKO = string.find(cue, "撃破", 1, true) ~= nil
    local isDamage = string.find(cue, "−", 1, true) == 1
    if not isKO and not isDamage then return end

    local root = localPlayer.Character and localPlayer.Character:FindFirstChild("HumanoidRootPart")
    if not root or (root.Position - core.Position).Magnitude > 64 then return end
    local now = os.clock()
    if now - state.last < .13 then return end
    while #times > 0 and now - times[1] >= 1 do table.remove(times, 1) end
    if #times >= MAX_BURSTS_PER_SECOND then return end

    state.last = now
    table.insert(times, now)
    makeArc(core.Position, root.Position, isKO)
end

local function detach(model)
    local state = bound[model]
    if not state then return end
    bound[model] = nil
    for _,connection in ipairs(state.connections) do connection:Disconnect() end
end

local function attach(model)
    if destroyed or not model.Parent or not isOriginalMob(model) or bound[model] then return end
    local core = model:FindFirstChild("Core")
    local popup = core and core:FindFirstChild("RealDamagePopup")
    local label = popup and popup:FindFirstChildOfClass("TextLabel")
    if not (core and core:IsA("BasePart") and popup
        and popup:IsA("BillboardGui") and label and label:IsA("TextLabel")) then return end
    local state = {last = -100, connections = {}}
    bound[model] = state
    table.insert(state.connections, popup:GetPropertyChangedSignal("Enabled"):Connect(function()
        onConfirmedHit(core, popup, label, state)
    end))
    table.insert(state.connections, label:GetPropertyChangedSignal("Text"):Connect(function()
        onConfirmedHit(core, popup, label, state)
    end))
    table.insert(state.connections, model.Destroying:Connect(function() detach(model) end))
end

-- Original MusouHorde destroys and recreates up to 9 models each round.
for _,child in ipairs(mobs:GetChildren()) do task.defer(attach, child) end
folderConnection = mobs.ChildAdded:Connect(function(child) task.defer(attach, child) end)

script.Destroying:Connect(function()
    destroyed = true
    if folderConnection then folderConnection:Disconnect() end
    for model in pairs(bound) do detach(model) end
end)
print(FEATURE .. "_SOURCE_WIP_STUDIO_PRIVATE_ONLY")
