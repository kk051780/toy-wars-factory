-- P0D-WEATHER-METEOR-SHORTCUT-V1: neutral, reversible route event.
-- Isolated original feature code; only #220 may wire into official RC.
-- No Remote, Game, Store, HP, score, XP, damage or purchase authority.
local ServerStorage = game:GetService("ServerStorage")
local Workspace = game:GetService("Workspace")
local TweenService = game:GetService("TweenService")

local ENABLE_FLAG = "P0D_ENABLE_METEOR_SHORTCUT_V1"
local ANCHOR_FOLDER = "P0D_MeteorShortcutAnchors"
local RUNTIME_FOLDER = "P0D_MeteorShortcutRuntime"
local QUIET_SECONDS = 55
local WARNING_SECONDS = 5
local ACTIVE_SECONDS = 22
local MAX_BRIDGE_PARTS = 12
local MIN_LENGTH = 14
local MAX_LENGTH = 90
local MAX_HEIGHT_DIFFERENCE = 5

local function isEnabled(): boolean
    local flag = ServerStorage:FindFirstChild(ENABLE_FLAG)
    return flag ~= nil and flag:IsA("BoolValue") and flag.Value == true
end

local function getAnchors(): (BasePart?, BasePart?)
    local folder = Workspace:FindFirstChild(ANCHOR_FOLDER)
    if not folder then
        return nil, nil
    end
    local a = folder:FindFirstChild("A")
    local b = folder:FindFirstChild("B")
    if not (a and b and a:IsA("BasePart") and b:IsA("BasePart")) then
        return nil, nil
    end
    local offset = b.Position - a.Position
    local flat = Vector3.new(offset.X, 0, offset.Z)
    local span = flat.Magnitude
    if span < MIN_LENGTH or span > MAX_LENGTH or math.abs(offset.Y) > MAX_HEIGHT_DIFFERENCE then
        return nil, nil
    end
    return a, b
end

-- Each segment is a real temporary walking surface. Both teams can use it.
local function buildRoute(parent: Folder, a: BasePart, b: BasePart): {BasePart}
    local flat = Vector3.new(b.Position.X - a.Position.X, 0, b.Position.Z - a.Position.Z)
    local span = flat.Magnitude
    local count = math.min(MAX_BRIDGE_PARTS, math.ceil(span / 7))
    local direction = flat.Unit
    local segments = {}
    for i = 1, count do
        local t = (i - 0.5) / count
        local center = a.Position:Lerp(b.Position, t) - Vector3.new(0, 0.65, 0)
        local part = Instance.new("Part")
        part.Name = string.format("MeteorBridge_%02d", i)
        part.Anchored = true
        part.CanCollide = false
        part.CanTouch = false
        part.CanQuery = false
        part.Size = Vector3.new(9, 1.2, span / count + 0.6)
        part.CFrame = CFrame.lookAt(center, center + direction)
        part.Material = Enum.Material.Neon
        part.Color = Color3.fromRGB(85, 201, 255)
        part.Transparency = 1
        part.CastShadow = false
        part.Parent = parent
        table.insert(segments, part)
    end
    return segments
end

local function announce(parent: Folder, at: Vector3): BillboardGui
    local pedestal = Instance.new("Part")
    pedestal.Name = "MeteorWarningAnchor"
    pedestal.Size = Vector3.new(1, 1, 1)
    pedestal.Position = at + Vector3.new(0, 8, 0)
    pedestal.Anchored = true
    pedestal.CanCollide = false
    pedestal.CanQuery = false
    pedestal.CanTouch = false
    pedestal.Transparency = 1
    pedestal.Parent = parent
    local gui = Instance.new("BillboardGui")
    gui.Name = "MeteorRouteSignal"
    gui.AlwaysOnTop = true
    gui.Size = UDim2.fromOffset(310, 72)
    gui.MaxDistance = 280
    gui.Adornee = pedestal
    gui.Parent = pedestal
    local label = Instance.new("TextLabel")
    label.Name = "Message"
    label.BackgroundColor3 = Color3.fromRGB(16, 28, 48)
    label.BackgroundTransparency = 0.2
    label.BorderSizePixel = 0
    label.Size = UDim2.fromScale(1, 1)
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.TextColor3 = Color3.fromRGB(255, 241, 157)
    label.Text = "☄️ 流星の道がまもなく出現!"
    label.Parent = gui
    return gui
end

local function isBridgeOccupied(segments: {BasePart}): boolean
    for _, bridge in ipairs(segments) do
        local queryBox = bridge.Size + Vector3.new(0, 8, 0)
        for _, hit in ipairs(Workspace:GetPartBoundsInBox(bridge.CFrame, queryBox)) do
            local character = hit:FindFirstAncestorOfClass("Model")
            local humanoid = character and character:FindFirstChildOfClass("Humanoid")
            if humanoid and humanoid.Health > 0 then
                return true
            end
        end
    end
    return false
end

local function setRoute(segments: {BasePart}, open: boolean)
    for _, part in ipairs(segments) do
        if open then
            part.CanCollide = true
            TweenService:Create(part, TweenInfo.new(0.45), {Transparency = 0.08}):Play()
        else
            -- Fade only after collision is disabled; no hidden solid platforms.
            part.CanCollide = false
            part.Transparency = 1
        end
    end
end

if not isEnabled() then
    return -- missing/nil/false flag: fail-closed, even in Studio
end

local a, b = getAnchors()
if not a or not b then
    warn("[P0D_METEOR] Disabled: anchor A/B missing or distance/height outside safe bounds")
    return
end
if Workspace:FindFirstChild(RUNTIME_FOLDER) then
    warn("[P0D_METEOR] Duplicate runtime detected, no second owner")
    return
end

local runtime = Instance.new("Folder")
runtime.Name = RUNTIME_FOLDER
runtime.Parent = Workspace
local segments = buildRoute(runtime, a, b)
local midpoint = a.Position:Lerp(b.Position, 0.5)
local gui = announce(runtime, midpoint)
local label = gui:FindFirstChild("Message")
if label then
    label.Text = ""
end

while isEnabled() and runtime.Parent ~= nil do
    task.wait(QUIET_SECONDS)
    if not isEnabled() then break end
    if label then label.Text = "☄️ 5秒後、流星の道が開く!" end
    task.wait(WARNING_SECONDS)
    if not isEnabled() then break end
    setRoute(segments, true)
    if label then label.Text = "🌠 流星ショートカット! 22秒間!" end
    task.wait(ACTIVE_SECONDS)
    -- Never remove the floor from under a living player. Late players may extend the event.
    if label then label.Text = "🌠 道を閉じるまで安全を確認中" end
    while runtime.Parent ~= nil and isBridgeOccupied(segments) do
        task.wait(0.5)
    end
    setRoute(segments, false)
    if label then label.Text = "" end
end
-- A feature-off during an active event must also wait for the bridge to empty.
while runtime.Parent ~= nil and isBridgeOccupied(segments) do
    task.wait(0.5)
end
setRoute(segments, false)
runtime:Destroy()
