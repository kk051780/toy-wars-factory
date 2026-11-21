--!strict
-- EGGRUMBLE GQ470 FB-015 | A-only optional visual source.
-- Matte nonblocking dune grass beside EXISTING LandSeaSky public dock.
-- Does not create a spawn, ground, prompt, gameplay or server authority.
local Workspace = game:GetService("Workspace")
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer
local FEATURE_ID = "GQ470_FB015_COASTAL_DUNE_GRASS_20261121"
local SCENE_NAME = "EGGRUMBLE_LAND_SEA_SKY_20261117"
local DOCK_NAME = "PublicSeaDock"
local FLOOR_NAME = "TacticalBattlefield"
local LOD_DISTANCE = if UserInputService.TouchEnabled then 115 else 175
local CLUMPS = if UserInputService.TouchEnabled then 4 else 6
local BLADES_PER_CLUMP = 3
local MAX_PARTS = CLUMPS * BLADES_PER_CLUMP -- touch 12 / PC 18
local REFRESH_SECONDS = 3.2
local COLORS = {
    Color3.fromRGB(107, 124, 74),
    Color3.fromRGB(134, 140, 79),
    Color3.fromRGB(172, 155, 93),
}
-- Leave the 50-stud central dock shuttle lane unobstructed.
-- Landward local -Z is grounded by the original unrotated dock CFrame.
local OFFSETS = {
    Vector2.new(-50, -19), Vector2.new(50, -19),
    Vector2.new(-37, -30), Vector2.new(37, -30),
    Vector2.new(-27, -43), Vector2.new(27, -43),
}

type Grass = {
    folder: Folder,
    pose: CFrame,
    floor: BasePart,
    floorPose: CFrame,
    floorSize: Vector3,
    count: number,
}
local candidates: {[BasePart]: boolean} = {}
local selected: BasePart? = nil
local active: Grass? = nil

local function sceneAndFloor(dock: BasePart): (Folder?, BasePart?)
    if dock.Name ~= DOCK_NAME or not dock.Anchored
        or not dock:IsDescendantOf(Workspace) then
        return nil, nil
    end
    local scene = dock.Parent
    if not scene or not scene:IsA("Folder") or scene.Name ~= SCENE_NAME then
        return nil, nil
    end
    local arena = scene.Parent
    if not arena or not arena:IsA("Folder")
        or (arena.Name ~= "TEAM_Arena" and arena.Name ~= "BATTLE_ROYALE_Arena") then
        return nil, nil
    end
    local floor = arena:FindFirstChild(FLOOR_NAME)
    if not floor or not floor:IsA("BasePart") or not floor.Anchored
        or floor.Size.X < 600 or floor.Size.Z < 700 then
        return nil, nil
    end
    return scene, floor
end

local function eyePosition(): Vector3?
    local camera = Workspace.CurrentCamera
    if camera then return camera.CFrame.Position end
    local character = player.Character
    local root = if character then character:FindFirstChild("HumanoidRootPart") else nil
    return if root and root:IsA("BasePart") then root.Position else nil
end

local function clear()
    if active then
        active.folder:Destroy()
        active = nil
    end
    selected = nil
end

local function makeGrass(dock: BasePart, floor: BasePart): Grass?
    -- Include ONLY the authentic battlefield. Ignore translucent water,
    -- prompts, sea craft, avatars and all other cosmetic layers.
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Include
    params.FilterDescendantsInstances = {floor}
    params.IgnoreWater = true

    local folder = Instance.new("Folder")
    folder.Name = "EGGRUMBLE_CoastalDuneGrass_Local"
    folder:SetAttribute("FeatureID", FEATURE_ID)
    folder.Parent = dock

    local count = 0
    for slot = 1, CLUMPS do
        local offset = OFFSETS[slot]
        local world = dock.CFrame:PointToWorldSpace(Vector3.new(offset.X, 0, offset.Y))
        local rayOrigin = Vector3.new(
            world.X, floor.Position.Y + floor.Size.Y * 0.5 + 40, world.Z
        )
        local hit = Workspace:Raycast(rayOrigin, Vector3.new(0, -110, 0), params)
        if hit and hit.Instance == floor and hit.Normal.Y >= 0.91 then
            for blade = 1, BLADES_PER_CLUMP do
                local height = 2.0 + 0.42 * ((slot + blade) % 3)
                local dx = (blade - 2) * 0.76
                local dz = ((slot + blade) % 2 == 0) and -0.33 or 0.33
                local wedge = Instance.new("WedgePart")
                wedge.Name = "MatteDuneBlade_" .. tostring(slot) .. "_" .. tostring(blade)
                wedge.Size = Vector3.new(0.38, height, 0.72)
                wedge.CFrame = CFrame.new(
                    hit.Position + Vector3.new(dx, height * 0.50, dz)
                ) * CFrame.Angles(
                    0, math.rad((slot * 43 + blade * 59) % 160),
                    math.rad((blade - 2) * 11)
                )
                wedge.Material = Enum.Material.SmoothPlastic
                wedge.Color = COLORS[(slot + blade - 2) % #COLORS + 1]
                wedge.Reflectance = 0
                wedge.Transparency = 0.08
                wedge.Anchored = true
                wedge.CanCollide = false
                wedge.CanTouch = false
                wedge.CanQuery = false
                wedge.CastShadow = false
                wedge.Parent = folder
                count += 1
            end
        end
    end
    if count == 0 or count > MAX_PARTS then
        folder:Destroy() -- missing streamed terrain never yields floating grass
        return nil
    end
    return {
        folder = folder, pose = dock.CFrame, floor = floor,
        floorPose = floor.CFrame, floorSize = floor.Size,
        count = count,
    }
end

local function refresh()
    if player:GetAttribute("EGGRUMBLE_ReducedEffects") == true then
        clear()
        return
    end
    local eye = eyePosition()
    if not eye then
        clear()
        return
    end
    local best: BasePart? = nil
    local bestFloor: BasePart? = nil
    local nearest = LOD_DISTANCE
    for dock in pairs(candidates) do
        local _, floor = sceneAndFloor(dock)
        if floor then
            local distance = (eye - dock.Position).Magnitude
            if distance < nearest then
                best, bestFloor, nearest = dock, floor, distance
            end
        end
    end
    if not best or not bestFloor then
        clear()
        return
    end
    if selected ~= best or not active or active.floor ~= bestFloor
        or active.pose ~= best.CFrame or active.floorPose ~= bestFloor.CFrame
        or active.floorSize ~= bestFloor.Size then
        clear()
        selected = best
        active = makeGrass(best, bestFloor)
    end
end

Workspace.DescendantAdded:Connect(function(obj)
    if obj:IsA("BasePart") and obj.Name == DOCK_NAME then
        candidates[obj] = true
    end
end)
Workspace.DescendantRemoving:Connect(function(obj)
    if obj:IsA("BasePart") and candidates[obj] then
        candidates[obj] = nil
        if selected == obj then clear() end
    end
end)
for _, obj in Workspace:GetDescendants() do
    if obj:IsA("BasePart") and obj.Name == DOCK_NAME then
        candidates[obj] = true
    end
end
player:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(refresh)
player.CharacterAdded:Connect(function()
    task.delay(0.5, refresh)
end)
refresh()
task.spawn(function()
    while script.Parent do
        task.wait(REFRESH_SECONDS)
        refresh()
    end
    clear()
end)
