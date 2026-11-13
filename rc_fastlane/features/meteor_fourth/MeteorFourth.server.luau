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
-- PRIVATE62: Starfall is already a separate third bridge near canyon local z=-35.
-- Put this timed meteor route at local z=-17, not at the old auto z=-34.5.
-- Only real WCS banks + original Starfall world allow installation.
-- 140s WCS and 160s Star budgets exceed WCS 45+45+12s and the Star120s
-- startup guard; each prerequisite Part also has a bounded 12s wait.
local function getAnchors(): (Vector3?, Vector3?)
    if ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01") ~= true
        or ServerStorage:GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1") ~= true then
        return nil, nil
    end
    local world = Workspace:FindFirstChild("P0D_WCS_CrystalCanyon")
        or Workspace:WaitForChild("P0D_WCS_CrystalCanyon", 140)
    local star = Workspace:FindFirstChild("P0D_STARRY_PATH")
        or Workspace:WaitForChild("P0D_STARRY_PATH", 160)
    if not world or not world:IsA("Model") or not star or not star:IsA("Model") then
        return nil, nil
    end
    local west = world:WaitForChild("WestBank", 12)
    local east = world:WaitForChild("EastBank", 12)
    local gate = world:WaitForChild("ShortcutGate", 12)
    local safe = world:WaitForChild("AlwaysOpenSafeRoute", 12)
    local starStep = star:WaitForChild("StarStep_01", 12)
    if not (west and east and gate and safe and starStep
        and west:IsA("BasePart") and east:IsA("BasePart")
        and gate:IsA("BasePart") and safe:IsA("BasePart")
        and starStep:IsA("BasePart")) then
        return nil, nil
    end
    if not (west.Anchored and east.Anchored and west.CanCollide and east.CanCollide
        and gate.Anchored and safe.Anchored and starStep.Anchored) then
        return nil, nil
    end
    if math.abs(west.Position.Z-east.Position.Z)>2 then
        return nil, nil
    end
    local z = (west.Position.Z + east.Position.Z) * 0.5 - 17
    local width = 9
    local buffer = 3
    local function clearOf(existing: BasePart): boolean
        -- Same-axis WCS/Starfall bridges must leave at least 3 studs between edges.
        return math.abs(z-existing.Position.Z) > (width+existing.Size.Z)*0.5+buffer
    end
    if not (clearOf(gate) and clearOf(safe) and clearOf(starStep)) then
        warn("[P0D_METEOR] Not enough clearance from Starfall/WCS gate")
        return nil, nil
    end
    if math.abs(z-west.Position.Z) > west.Size.Z*0.5-width*0.5
        or math.abs(z-east.Position.Z) > east.Size.Z*0.5-width*0.5 then
        return nil, nil
    end
    local y = math.min(west.Position.Y+west.Size.Y*0.5,
        east.Position.Y+east.Size.Y*0.5) + 0.6
    local a = Vector3.new(west.Position.X+west.Size.X*0.5-1.5,y,z)
    local b = Vector3.new(east.Position.X-east.Size.X*0.5+1.5,y,z)
    if not validRoute(a,b) then
        return nil, nil
    end
    return a,b
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
    warn("[P0D_METEOR] Disabled: separate canyon lane or Starfall/WCS unavailable")
    return
end
if Workspace:FindFirstChild(RUNTIME_FOLDER) then
    warn("[P0D_METEOR] Duplicate runtime detected, no second owner")
    return
end

local runtime = Instance.new("Folder")
runtime.Name = RUNTIME_FOLDER
runtime:SetAttribute("RouteRole","FOURTH_CANYON_LANE")
runtime:SetAttribute("DistinctFromStarfall",true)
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
