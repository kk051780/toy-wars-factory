-- EGGRUMBLE player team shoulder crests (FB-015 visual-only A candidate)
-- Explicitly NOT a player-spawn repair. Safe to omit for exact REAL69 rollback.
-- One client-owned decoration. No server authority, combat, GUI, Remote or persistence.
local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")
local localPlayer = Players.LocalPlayer
if not localPlayer then return end

local CREST_NAME = "GQ470_PlayerTeamCrests"
local LOD_STUDS = 66
local LOD_POLL_SECONDS = 0.75
-- Budget counts ACTUAL instantiated crests, not only transparent hidden ones.
local MAX_REMOTE_CRESTS = if UserInputService.TouchEnabled then 2 else 3
local STEALTH_FLAGS = { "Stealthed", "IsInvisible", "AssassinCloaked", "EGGRUMBLE_Stealthed" }
local BODY_PARTS = {
    Head = true, Torso = true, UpperTorso = true, LowerTorso = true,
    ["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true,
    LeftUpperArm = true, RightUpperArm = true, LeftLowerArm = true, RightLowerArm = true,
    LeftHand = true, RightHand = true, LeftUpperLeg = true, RightUpperLeg = true,
    LeftLowerLeg = true, RightLowerLeg = true, LeftFoot = true, RightFoot = true,
}
local OFFICIAL_TEAM_COLORS = {
    RED = Color3.fromRGB(174, 79, 73),
    BLUE = Color3.fromRGB(70, 122, 176),
}

local mounted = {}
local subscriptions = {}
local generations = {}

local function teamColor(player)
    local team = player.Team
    if not team then return nil end
    return OFFICIAL_TEAM_COLORS[team.Name]
end

local function visualsDisabled()
    return localPlayer:GetAttribute("ReducedEffects") == true
        or localPlayer:GetAttribute("EGGRUMBLE_TeamCrestsOff") == true
end

local function removeMounted(player)
    local rec = mounted[player]
    mounted[player] = nil
    if not rec then return end
    if rec.died then rec.died:Disconnect() end
    for _, connection in ipairs(rec.watchers or {}) do connection:Disconnect() end
    if rec.folder and rec.folder.Parent then rec.folder:Destroy() end
end

local function isConcealed(player, character)
    -- Cosmetic crests must not reveal Assassin/invisible players, including R6/R15 limbs.
    for _, flag in ipairs(STEALTH_FLAGS) do
        if player:GetAttribute(flag) == true or character:GetAttribute(flag) == true then
            return true
        end
    end
    for _, part in ipairs(character:GetDescendants()) do
        if part:IsA("BasePart") and BODY_PARTS[part.Name] then
            if part.Transparency >= 0.5 or part.LocalTransparencyModifier >= 0.5 then
                return true
            end
        end
    end
    return false
end

local function cameraDistance(player, character, cameraPosition)
    if player == localPlayer or not cameraPosition or not character or visualsDisabled() then return nil end
    local root = character:FindFirstChild("HumanoidRootPart")
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
        return nil
    end
    if not root.Parent or not teamColor(player) or isConcealed(player, character) then return nil end
    local distance = (cameraPosition - root.Position).Magnitude
    return if distance <= LOD_STUDS then distance else nil
end

local function makeCrest(folder, torso, color, side, isRed)
    -- Wedge silhouette is more legible than a neon orb or oversized billboard.
    local crest = Instance.new("WedgePart")
    crest.Name = side < 0 and "LeftShoulderMatte" or "RightShoulderMatte"
    -- Red: broader horizontal spear shoulders; blue: taller vertical fins.
    -- Different silhouette, not color alone, for color-vision accessibility.
    crest.Size = if isRed then Vector3.new(0.52, 0.20, 0.66)
        else Vector3.new(0.35, 0.31, 0.63)
    crest.Material = Enum.Material.SmoothPlastic
    crest.Color = color
    crest.Reflectance = 0.025
    crest.Transparency = 0.04
    crest.Anchored = false
    crest.Massless = true
    crest.CanCollide = false
    crest.CanTouch = false
    crest.CanQuery = false
    crest.CastShadow = false
    crest.CFrame = torso.CFrame
        * CFrame.new(side * 0.92, 0.48, -0.07)
        * CFrame.Angles(0, if isRed then 0.22 else -0.22,
            side * (if isRed then 0.14 else -0.22))
    crest.Parent = folder
    local join = Instance.new("WeldConstraint")
    join.Name = "ClientOnlyShoulderWeld"
    join.Part0 = torso
    join.Part1 = crest
    join.Parent = crest
    return crest
end

local function attach(player, character)
    local token = (generations[player] or 0) + 1
    generations[player] = token
    removeMounted(player)
    -- No WaitForChild loops: only nearby, fully streamed-in bodies can instantiate parts.
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    local root = character:FindFirstChild("HumanoidRootPart")
    local torso = character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")
    if token ~= generations[player] or player.Character ~= character then return end
    if not humanoid or not root or not torso or humanoid.Health <= 0 then return end
    if not torso:IsA("BasePart") or not root:IsA("BasePart") then return end
    local color = teamColor(player)
    if not color then return end
    local camera = workspace.CurrentCamera
    if not cameraDistance(player, character, camera and camera.CFrame.Position) then return end
    local isRed = player.Team ~= nil and player.Team.Name == "RED"

    local folder = Instance.new("Folder")
    folder.Name = CREST_NAME
    folder.Parent = character
    local pieces = {
        makeCrest(folder, torso, color, -1, isRed),
        makeCrest(folder, torso, color, 1, isRed),
    }
    local watchers = {}
    local function rejectConcealment()
        if generations[player] == token and (isConcealed(player, character)
            or player.Character ~= character or humanoid.Health <= 0) then
            removeMounted(player)
        end
    end
    -- Immediate cleanup when true cloak/partial-body transparency changes.
    for _, flag in ipairs(STEALTH_FLAGS) do
        watchers[#watchers + 1] = player:GetAttributeChangedSignal(flag):Connect(rejectConcealment)
        watchers[#watchers + 1] = character:GetAttributeChangedSignal(flag):Connect(rejectConcealment)
    end
    for _, part in ipairs(character:GetDescendants()) do
        if part:IsA("BasePart") and BODY_PARTS[part.Name] then
            watchers[#watchers + 1] = part:GetPropertyChangedSignal("Transparency"):Connect(rejectConcealment)
            watchers[#watchers + 1] = part:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(rejectConcealment)
        end
    end
    -- Only active near-avatar crests have watchers. A streamed R6/R15 limb
    -- invalidates the old part listener set and is removed immediately.
    watchers[#watchers + 1] = character.DescendantAdded:Connect(function(part)
        if part:IsA("BasePart") and BODY_PARTS[part.Name]
            and generations[player] == token then
            removeMounted(player)
        end
    end)
    watchers[#watchers + 1] = character.DescendantRemoving:Connect(function(part)
        if part:IsA("BasePart") and BODY_PARTS[part.Name]
            and generations[player] == token then
            removeMounted(player)
        end
    end)
    local died = humanoid.Died:Connect(function()
        if generations[player] == token then removeMounted(player) end
    end)
    mounted[player] = {
        folder = folder, pieces = pieces, root = root, character = character,
        died = died, watchers = watchers,
    }
    rejectConcealment()
end

local function register(player)
    if subscriptions[player] then return end
    local conns = {}
    conns[#conns + 1] = player.CharacterAdded:Connect(function()
        generations[player] = (generations[player] or 0) + 1
        removeMounted(player)
        -- Next LOD sweep creates cosmetics only when genuinely in camera range.
    end)
    conns[#conns + 1] = player.CharacterRemoving:Connect(function()
        generations[player] = (generations[player] or 0) + 1
        removeMounted(player)
    end)
    conns[#conns + 1] = player:GetPropertyChangedSignal("Team"):Connect(function()
        generations[player] = (generations[player] or 0) + 1
        removeMounted(player)
    end)
    subscriptions[player] = conns
end

local function unregister(player)
    generations[player] = (generations[player] or 0) + 1
    removeMounted(player)
    local conns = subscriptions[player]
    subscriptions[player] = nil
    if conns then
        for _, connection in ipairs(conns) do connection:Disconnect() end
    end
    generations[player] = nil
end

Players.PlayerAdded:Connect(register)
Players.PlayerRemoving:Connect(unregister)
-- Local accessibility and fast rollback: tear down instantly, without waiting for the LOD scan.
for _, attr in ipairs({ "ReducedEffects", "EGGRUMBLE_TeamCrestsOff" }) do
    localPlayer:GetAttributeChangedSignal(attr):Connect(function()
        if visualsDisabled() then
            for player in pairs(mounted) do removeMounted(player) end
        end
    end)
end
for _, player in ipairs(Players:GetPlayers()) do
    register(player)
end

-- Low-frequency, actual-part budget: closest remote avatars only.
-- A distant/hidden/streamed-out avatar owns ZERO crest parts.
task.spawn(function()
    while true do
        local camera = workspace.CurrentCamera
        local cameraPosition = camera and camera.CFrame.Position
        local nearby = {}
        if cameraPosition and not visualsDisabled() then
            for _, player in ipairs(Players:GetPlayers()) do
                local character = player.Character
                local distance = cameraDistance(player, character, cameraPosition)
                if distance then
                    nearby[#nearby + 1] = { player = player, character = character, distance = distance }
                end
            end
        end
        table.sort(nearby, function(a, b)
            if a.distance == b.distance then return a.player.UserId < b.player.UserId end
            return a.distance < b.distance
        end)
        local selected = {}
        for index = 1, math.min(MAX_REMOTE_CRESTS, #nearby) do
            local entry = nearby[index]
            selected[entry.player] = entry.character
        end
        for player, rec in pairs(mounted) do
            if selected[player] ~= rec.character or not rec.folder.Parent
                or isConcealed(player, rec.character) then
                removeMounted(player)
            end
        end
        for player, character in pairs(selected) do
            if not mounted[player] then attach(player, character) end
        end
        task.wait(LOD_POLL_SECONDS)
    end
end)
