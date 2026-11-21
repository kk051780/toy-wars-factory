--!strict
-- GQ470 FB-015: distant coastal life, deliberately lightweight for Android.
-- Client-only matte silhouettes at the EXISTING PublicSeaDock. Not a creature/AI,
-- player-spawn fix, egg locator, navigation blocker, or gameplay authority.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local localPlayer = Players.LocalPlayer
local FEATURE_ID = "GQ470_FB015_SEA_GULLS_MATTE_20261121"
local BIRD_LIMIT = if UserInputService.TouchEnabled then 2 else 3
local PARTS_PER_BIRD = 3
local TOTAL_PART_BUDGET = BIRD_LIMIT * PARTS_PER_BIRD -- Android 6, PC 9.
local MAX_VIEW_DISTANCE = 165
local UPDATE_SECONDS = 2.8
local MATTE_IVORY = Color3.fromRGB(216, 219, 209)
local MATTE_SLATE = Color3.fromRGB(148, 159, 160)

type Bird = {parts: {BasePart}, offsets: {CFrame}, slot: number}
local docks: {[BasePart]: boolean} = {}
local activeDock: BasePart? = nil
local localFolder: Folder? = nil
local birds: {Bird} = {}
local activeTweens: {Tween} = {}
local phase = 0

local function validDock(obj: Instance): boolean
    return obj:IsA("BasePart") and obj.Name == "PublicSeaDock" and
        obj.Anchored and obj:IsDescendantOf(Workspace)
end

local function localPosition(): Vector3?
    local character = localPlayer.Character
    if not character then return nil end
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local root = character:FindFirstChild("HumanoidRootPart")
    if humanoid and humanoid.Health > 0 and root and root:IsA("BasePart") then
        return root.Position
    end
    return nil -- no camera-based fake effect while the avatar P0 is unresolved.
end

local function newPiece(parent: Folder, name: string, size: Vector3,
    base: CFrame, color: Color3, wedge: boolean): BasePart
    local part: BasePart = if wedge then Instance.new("WedgePart") else Instance.new("Part")
    part.Name = name
    part.Size = size
    part.CFrame = base
    part.Material = Enum.Material.SmoothPlastic
    part.Color = color
    part.Reflectance = 0
    part.Transparency = .04
    part.Anchored = true
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    if not wedge then (part :: Part).Shape = Enum.PartType.Ball end
    part.Parent = parent
    return part
end

local function clear()
    -- Never retain old-local-world Parts/Tweens across streams, respawn or
    -- reduced-effects changes; no server instances are edited.
    for _, tween in activeTweens do tween:Cancel() end
    table.clear(activeTweens)
    table.clear(birds)
    if localFolder then localFolder:Destroy() end
    localFolder = nil
    activeDock = nil
end

local function flightFrame(dock: BasePart, slot: number, t: number): CFrame
    local lateral = (slot - (BIRD_LIMIT + 1) / 2) * 12 + math.sin(t + slot) * 2.7
    local height = 17 + 2.5 * slot + math.cos(t * .72 + slot) * 1.8
    local seaward = -28 - 9 * slot + math.sin(t * .67 + slot) * 3.1
    return dock.CFrame * CFrame.new(lateral, height, seaward)
        * CFrame.Angles(0, math.rad((slot % 2 == 0) and -13 or 11), 0)
end

local function makeBird(dock: BasePart, folder: Folder, slot: number): Bird
    local base = flightFrame(dock, slot, phase)
    local offsets = {
        CFrame.new(),
        CFrame.new(-.87, .12, 0) * CFrame.Angles(0, 0, math.rad(12)),
        CFrame.new(.87, .12, 0) * CFrame.Angles(0, 0, math.rad(-12)),
    }
    local parts = {
        newPiece(folder, "BirdBody_" .. slot, Vector3.new(1.35, .28, .60),
            base * offsets[1], MATTE_SLATE, false),
        newPiece(folder, "LeftWing_" .. slot, Vector3.new(1.46, .16, .67),
            base * offsets[2], MATTE_IVORY, true),
        newPiece(folder, "RightWing_" .. slot, Vector3.new(1.46, .16, .67),
            base * offsets[3], MATTE_IVORY, true),
    }
    return {parts = parts, offsets = offsets, slot = slot}
end

local function discoverClosestDock(): BasePart?
    local eye = localPosition()
    if not eye or localPlayer:GetAttribute("EGGRUMBLE_ReducedEffects") == true then
        return nil
    end
    local best: BasePart? = nil
    local bestDistance = MAX_VIEW_DISTANCE
    for dock in docks do
        if validDock(dock) then
            local distance = (dock.Position - eye).Magnitude
            if distance < bestDistance then
                bestDistance = distance
                best = dock
            end
        end
    end
    return best
end

local function refresh()
    local dock = discoverClosestDock()
    if dock == nil then clear(); return end
    if dock ~= activeDock or localFolder == nil then
        clear()
        local folder = Instance.new("Folder")
        folder.Name = "EGGRUMBLE_SeaGulls_Local"
        folder:SetAttribute("FeatureID", FEATURE_ID)
        folder.Parent = Workspace
        activeDock = dock
        localFolder = folder
        for slot = 1, BIRD_LIMIT do
            table.insert(birds, makeBird(dock, folder, slot))
        end
    end
    local created = 0
    for _, bird in birds do created += #bird.parts end
    assert(created <= TOTAL_PART_BUDGET, "GQ470_SEA_GULLS_PART_BUDGET")
    -- Infrequent 2.8s stepped tweens, not RenderStepped/Heartbeat loops.
    for _, tween in activeTweens do tween:Cancel() end
    table.clear(activeTweens)
    phase += .85
    local style = TweenInfo.new(UPDATE_SECONDS, Enum.EasingStyle.Sine,
        Enum.EasingDirection.InOut, 0, false, 0)
    for _, bird in birds do
        local target = flightFrame(dock, bird.slot, phase)
        for i, part in bird.parts do
            local tween = TweenService:Create(part, style, {CFrame = target * bird.offsets[i]})
            table.insert(activeTweens, tween)
            tween:Play()
        end
    end
end

-- Register once; allow streaming to add/remove the actual dock later.
Workspace.DescendantAdded:Connect(function(obj)
    if obj:IsA("BasePart") and obj.Name == "PublicSeaDock" then
        docks[obj] = true
    end
end)
Workspace.DescendantRemoving:Connect(function(obj)
    if docks[obj :: any] then
        docks[obj :: BasePart] = nil
        if activeDock == obj then clear() end
    end
end)
for _, obj in Workspace:GetDescendants() do
    if obj:IsA("BasePart") and obj.Name == "PublicSeaDock" then
        docks[obj] = true
    end
end
localPlayer:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(function()
    if localPlayer:GetAttribute("EGGRUMBLE_ReducedEffects") == true then clear()
    else refresh() end
end)
localPlayer.CharacterRemoving:Connect(clear)
localPlayer.CharacterAdded:Connect(function()
    task.delay(.6, refresh)
end)
refresh()
task.spawn(function()
    while script.Parent ~= nil do
        task.wait(UPDATE_SECONDS)
        refresh()
    end
    clear()
end)
