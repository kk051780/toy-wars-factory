-- P0D-WEATHER-METEOR-SHORTCUT-V1: neutral, reversible route event.
-- Isolated original feature code; only #220 may wire into official RC.
-- No Remote, Game, Store, HP, score, XP, damage or purchase authority.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
    return -- unpublished Studio-only until owner approves release
end
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

local function validRoute(a: Vector3, b: Vector3): boolean
    local delta = b - a
    local planar = Vector3.new(delta.X, 0, delta.Z).Magnitude
    return planar >= MIN_LENGTH and planar <= MAX_LENGTH
        and math.abs(delta.Y) <= MAX_HEIGHT_DIFFERENCE
        and math.abs(a.X) <= 120 and math.abs(b.X) <= 120
        and math.abs(a.Z) <= 68 and math.abs(b.Z) <= 68
end

-- Priority: explicit author anchors; fallback only to verified original WCS banks.
-- The WCS stage is made by another server Script, so allow bounded boot ordering.
local function getAnchors(): (Vector3?, Vector3?)
    local folder = Workspace:FindFirstChild(ANCHOR_FOLDER)
    if folder then
        local a = folder:FindFirstChild("A")
        local b = folder:FindFirstChild("B")
        if a and b and a:IsA("BasePart") and b:IsA("BasePart") then
            if a.Anchored and b.Anchored and validRoute(a.Position, b.Position) then
                return a.Position, b.Position
            end
            warn("[P0D_METEOR] Explicit A/B anchors invalid; not auto-overriding")
            return nil, nil
        end
        warn("[P0D_METEOR] Partial explicit anchor folder; refusing WCS fallback")
        return nil, nil
    end

    if ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01") ~= true then
        return nil, nil
    end
    local world = Workspace:FindFirstChild("P0D_WCS_CrystalCanyon")
        or Workspace:WaitForChild("P0D_WCS_CrystalCanyon", 12)
    if not world or not world:IsA("Model") then
        return nil, nil
    end
    local west = world:FindFirstChild("WestBank") or world:WaitForChild("WestBank", 5)
    local east = world:FindFirstChild("EastBank") or world:WaitForChild("EastBank", 5)
    if not (west and east and west:IsA("BasePart") and east:IsA("BasePart")
        and west.Anchored and east.Anchored and west.CanCollide and east.CanCollide) then
        return nil, nil
    end
    -- WCS has safe fixed crossing at local z=+30 and Moguron gate at z=0.
    -- A second crossing at bank's far z edge +8 does not replace either.
    local z = math.max(west.Position.Z - west.Size.Z * 0.5,
        east.Position.Z - east.Size.Z * 0.5) + 8
    local y = math.min(west.Position.Y + west.Size.Y * 0.5,
        east.Position.Y + east.Size.Y * 0.5) + 0.6
    local a = Vector3.new(west.Position.X + west.Size.X * 0.5 - 1.5, y, z)
    local b = Vector3.new(east.Position.X - east.Size.X * 0.5 + 1.5, y, z)
    if not validRoute(a, b) then
        return nil, nil
    end
    return a, b
end

-- Each segment is a real temporary walking surface. Both teams can use it.
local function buildRoute(parent: Folder, a: Vector3, b: Vector3): {BasePart}
    local flat = Vector3.new(b.X - a.X, 0, b.Z - a.Z)
    local span = flat.Magnitude
    local count = math.min(MAX_BRIDGE_PARTS, math.ceil(span / 7))
    local direction = flat.Unit
    local segments = {}
    for i = 1, count do
        local t = (i - 0.5) / count
        local center = a:Lerp(b, t) - Vector3.new(0, 0.65, 0)
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
local midpoint = a:Lerp(b, 0.5)
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
