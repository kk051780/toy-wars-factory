--!strict
-- GQ470_FB015_CASTLE_BANNER_WIND_20261121
-- Optional art-only LocalScript: never owns spawn, camera, HP, score, egg or UI.
-- The original 69 selected Luau routes are unchanged until authenticated B intake.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local player = Players.LocalPlayer
local MAX_BANNERS = 20
local RANGE_STUDS = 110
local MAX_SWAY_RADIANS = math.rad(3.5)
local TICK_SECONDS = if UserInputService.TouchEnabled then 0.32 else 0.18

type BannerState = {base: CFrame, phase: number, active: boolean}
local tracked: {[BasePart]: BannerState} = {}
local trackedCount = 0

local function isCastleBanner(inst: Instance): boolean
    if not inst:IsA("BasePart") then return false end
    local part = inst :: BasePart
    local name = string.lower(part.Name)
    if not (string.find(name, "banner", 1, true) or string.find(name, "pennant", 1, true)
        or string.find(name, "castleflag", 1, true)) then
        return false
    end
    -- Never alter physics, tools, hitboxes, personal avatars or neon FX.
    if not part.Anchored or part.CanCollide or part.Material == Enum.Material.Neon then
        return false
    end
    -- A castle StandardCore must be inside a nearby model ancestor.
    -- Scanning no higher than three ancestors prevents unrelated map signs.
    local ancestor: Instance? = part.Parent
    for _ = 1, 3 do
        if not ancestor or ancestor == Workspace then break end
        if ancestor:IsA("Model") then
            local core = ancestor:FindFirstChild("StandardCore", true)
            if core and core:IsA("BasePart") then return true end
        end
        ancestor = ancestor.Parent
    end
    return false
end

local function register(inst: Instance)
    if trackedCount >= MAX_BANNERS or not isCastleBanner(inst) then return end
    local part = inst :: BasePart
    if tracked[part] then return end
    local pos = part.Position
    tracked[part] = {base = part.CFrame, phase = (pos.X * 0.07 + pos.Z * 0.13), active = false}
    trackedCount += 1
end

local function stop(part: BasePart, state: BannerState)
    if state.active and part.Parent then
        part.CFrame = state.base
    end
    state.active = false
end

Workspace.DescendantRemoving:Connect(function(inst)
    if inst:IsA("BasePart") then
        local part = inst :: BasePart
        local state = tracked[part]
        if state then
            -- Destruction must not leave references to departed arenas.
            tracked[part] = nil
            trackedCount = math.max(0, trackedCount - 1)
        end
    end
end)

Workspace.DescendantAdded:Connect(function(inst)
    if not inst:IsA("BasePart") then return end
    local n = string.lower(inst.Name)
    if not (string.find(n, "banner", 1, true) or string.find(n, "pennant", 1, true)
        or string.find(n, "castleflag", 1, true)) then return end
    -- Castle core and optional decorations may arrive in different frames.
    task.defer(register, inst)
    task.delay(1, register, inst)
end)

-- One-time inventory. All later discoveries are event-driven; no per-frame map scan.
for _, inst in ipairs(Workspace:GetDescendants()) do
    register(inst)
end

local accumulator = 0
RunService.Heartbeat:Connect(function(delta: number)
    accumulator += math.min(delta, 0.5)
    if accumulator < TICK_SECONDS then return end
    accumulator = 0

    local camera = Workspace.CurrentCamera
    local reduced = player:GetAttribute("EGGRUMBLE_ReducedEffects") == true
        or Workspace:GetAttribute("EGGRUMBLE_ReducedEffects") == true
    local camPos = if camera then camera.CFrame.Position else nil
    local now = time()

    for part, state in pairs(tracked) do
        if not part.Parent then
            tracked[part] = nil
            trackedCount = math.max(0, trackedCount - 1)
        elseif reduced or not camPos or (part.Position - camPos).Magnitude > RANGE_STUDS then
            stop(part, state)
        else
            -- Only local, bounded art animation; no server replication or extra Parts.
            local wave = math.sin(now * 1.35 + state.phase) * MAX_SWAY_RADIANS
            local hinge = part.Size.Y * 0.5
            part.CFrame = state.base * CFrame.new(0, hinge, 0)
                * CFrame.Angles(0, 0, wave) * CFrame.new(0, -hinge, 0)
            state.active = true
        end
    end
end)
