--!strict
-- GQ470 FB-015: matte castle banners for spatial RED/BLUE wayfinding.
-- Client-only decorative geometry. No character, match, health or egg authority.
local Workspace = game:GetService("Workspace")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Players = game:GetService("Players")

local player = Players.LocalPlayer
local FEATURE_ID = "GQ470_FB015_CASTLE_BANNER_MATTE_20261121"
local MAX_PER_TEAM = if UserInputService.TouchEnabled then 2 else 3
local MAX_PARTS_PER_TOWER = 4
local MAX_NEUTRAL_CASTLES = 2
local NEARER_MARGIN_STUDS = 8
local MAX_TOTAL_EXTRA_PARTS = (MAX_PER_TEAM * 2 + MAX_NEUTRAL_CASTLES) * MAX_PARTS_PER_TOWER
local PALETTE = {
    RED = Color3.fromRGB(166, 69, 75),
    BLUE = Color3.fromRGB(60, 113, 164),
    NEUTRAL = Color3.fromRGB(165, 148, 113),
}
local trim = Color3.fromRGB(194, 173, 137)
local counts = { RED = 0, BLUE = 0, NEUTRAL = 0 }
type Entry = { root: Folder, connections: {RBXScriptConnection}, tweens: {Tween}, team: string }
local tracked: {[BasePart]: Entry} = {}

local function cameraDistance(tower: BasePart): number
    local character = player.Character
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    local camera = Workspace.CurrentCamera
    local viewpoint = if root and root:IsA("BasePart") then root.Position
        elseif camera then camera.CFrame.Position else Vector3.zero
    return (tower.Position - viewpoint).Magnitude
end

local function castleTeam(tower: Instance): string?
    if not tower:IsA("BasePart") or not tower.Anchored then return nil end
    local name = tower.Name
    local team = if name == "RED_TOWER" then "RED" elseif name == "BLUE_TOWER" then "BLUE" else nil
    local ancestor = tower.Parent
    if team then
        while ancestor and ancestor ~= Workspace do
            if ancestor.Name == team .. "_CASTLE" then return team end
            ancestor = ancestor.Parent
        end
        return nil
    end
    -- REAL69's genuine 16-castle battlefield uses StandardCore under a castle Model.
    -- Do not invent a RED/BLUE allegiance when the server has not supplied one:
    -- the neutral stone pennant is aesthetic only.
    if name == "StandardCore" and ancestor and ancestor:IsA("Model") then
        local parent = ancestor.Parent
        while parent and parent ~= Workspace do
            if parent.Name == "TacticalBattlefield" then return "NEUTRAL" end
            parent = parent.Parent
        end
    end
    return nil
end

local function part(folder: Folder, name: string, size: Vector3, pose: CFrame, color: Color3, wedge: boolean): BasePart
    local p: BasePart = if wedge then Instance.new("WedgePart") else Instance.new("Part")
    p.Name = name
    p.Size = size
    p.CFrame = pose
    p.Color = color
    p.Material = if name == "MatteFlagstaff" then Enum.Material.SmoothPlastic else Enum.Material.Fabric
    p.Reflectance = 0
    p.Anchored = true
    p.CanCollide = false
    p.CanTouch = false
    p.CanQuery = false
    p.CastShadow = false
    p.Parent = folder
    return p
end

local function stop(tower: BasePart)
    local entry = tracked[tower]
    if not entry then return end
    tracked[tower] = nil
    counts[entry.team] = math.max(0, counts[entry.team] - 1)
    for _, conn in entry.connections do conn:Disconnect() end
    for _, tween in entry.tweens do tween:Cancel() end
    entry.root:Destroy()
end

local function attach(tower: Instance)
    local team = castleTeam(tower)
    if not team or not tower:IsA("BasePart") or tracked[tower] then return end
    local limit = if team == "NEUTRAL" then MAX_NEUTRAL_CASTLES else MAX_PER_TEAM
    if team == "NEUTRAL" and counts[team] >= limit then
        -- Streaming/arrival order must not reserve all banners for faraway
        -- castles. Replace only an existing farther neutral decoration.
        local farthest: BasePart? = nil
        local farthestDistance = -1
        for candidate, current in tracked do
            if current.team == "NEUTRAL" then
                local distance = cameraDistance(candidate)
                if distance > farthestDistance then
                    farthest, farthestDistance = candidate, distance
                end
            end
        end
        if farthest and cameraDistance(tower) + NEARER_MARGIN_STUDS < farthestDistance then
            stop(farthest)
        end
    end
    if counts[team] >= limit then return end
    counts[team] += 1
    local folder = Instance.new("Folder")
    folder.Name = "EGGRUMBLE_CastleBanner_Local"
    folder:SetAttribute("FeatureID", FEATURE_ID)
    folder.Parent = tower

    local rootPose = tower.CFrame * CFrame.new(0, tower.Size.Y / 2, 0)
    local pole = part(folder, "MatteFlagstaff", Vector3.new(0.22, 5.3, 0.22),
        rootPose * CFrame.new(0, 2.6, 0), trim, false)
    local clothBase = rootPose * CFrame.new(2.12, 3.65, 0)
    local cloth = part(folder, "TeamClothBody", Vector3.new(4, 2.15, 0.15),
        clothBase, PALETTE[team], false)
    local fly: {BasePart} = {cloth}
    if team == "RED" then
        -- Two separated triangular pennants: recognizable even without color.
        table.insert(fly, part(folder, "SplitTailUpper", Vector3.new(1.5, 0.92, 0.15),
            clothBase * CFrame.new(2.75, 0.57, 0), PALETTE.RED, true))
        table.insert(fly, part(folder, "SplitTailLower", Vector3.new(1.5, 0.92, 0.15),
            clothBase * CFrame.new(2.75, -0.57, 0) * CFrame.Angles(0, 0, math.pi),
            PALETTE.RED, true))
    else
        table.insert(fly, part(folder, "SinglePointTail", Vector3.new(1.65, 2.1, 0.15),
            clothBase * CFrame.new(2.83, 0, 0), PALETTE[team], true))
    end
    local entry: Entry = {root = folder, connections = {}, tweens = {}, team = team}
    tracked[tower] = entry
    -- Keep the original panel poses. Re-toggling accessibility must not
    -- accumulate yaw or permanently displace the pennant.
    local restingPose: {[BasePart]: CFrame} = {}
    for _, panel in fly do restingPose[panel] = panel.CFrame end
    local function refreshMotion()
        for _, tween in entry.tweens do tween:Cancel() end
        table.clear(entry.tweens)
        for _, panel in fly do
            if not panel.Parent then continue end
            local base = restingPose[panel]
            panel.CFrame = base
            if player:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true then
                local tween = TweenService:Create(panel,
                    TweenInfo.new(2.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
                    {CFrame = base * CFrame.Angles(0, math.rad(3), 0)})
                table.insert(entry.tweens, tween)
                tween:Play()
            end
        end
    end
    -- A removed castle can leave an empty neutral/team slot with already-
    -- present skipped castles. Rescan only after actual removal, never per frame.
    local function refillVacantSlots()
        task.defer(function()
            for _, other in Workspace:GetDescendants() do
                if other.Name == "StandardCore" or other.Name == "RED_TOWER"
                    or other.Name == "BLUE_TOWER" then attach(other) end
            end
        end)
    end
    table.insert(entry.connections, player:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(refreshMotion))
    table.insert(entry.connections, tower.Destroying:Connect(function()
        stop(tower)
        refillVacantSlots()
    end))
    table.insert(entry.connections, tower.AncestryChanged:Connect(function()
        if not tower:IsDescendantOf(Workspace) or castleTeam(tower) ~= team then
            stop(tower)
            refillVacantSlots()
        end
    end))
    refreshMotion()
    assert(#fly + 1 <= MAX_PARTS_PER_TOWER and pole.Parent == folder)
end

-- Connect before scanning so late-spawned castles also get their banners.
Workspace.DescendantAdded:Connect(attach)
for _, descendant in Workspace:GetDescendants() do
    attach(descendant)
end
-- Re-rank the small neutral castle set once after a real player respawn.
-- No per-frame or repeated background loop; new streamed cores use the
-- same nearest-selection logic via DescendantAdded.
player.CharacterAdded:Connect(function()
    task.delay(0.8, function()
        for _, descendant in Workspace:GetDescendants() do
            if descendant.Name == "StandardCore" then attach(descendant) end
        end
    end)
end)
-- Maximum decorative part budget: MAX_TOTAL_EXTRA_PARTS; no per-frame Lua loop.
