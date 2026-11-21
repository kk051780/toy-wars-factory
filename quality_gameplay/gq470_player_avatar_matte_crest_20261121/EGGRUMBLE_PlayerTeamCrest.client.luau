-- EGGRUMBLE player team shoulder crests (FB-015 visual-only A candidate)
-- Explicitly NOT a player-spawn repair. Safe to omit for exact REAL69 rollback.
-- One client-owned decoration. No server authority, combat, GUI, Remote or persistence.
local Players = game:GetService("Players")
local localPlayer = Players.LocalPlayer
if not localPlayer then return end

local CREST_NAME = "GQ470_PlayerTeamCrests"
local LOD_STUDS = 66
local LOD_POLL_SECONDS = 0.75
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

local function removeMounted(player)
    local rec = mounted[player]
    mounted[player] = nil
    if not rec then return end
    if rec.died then rec.died:Disconnect() end
    if rec.folder and rec.folder.Parent then rec.folder:Destroy() end
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

    -- CharacterAdded is only an observation: never call LoadCharacter or change spawn.
    local humanoid = character:WaitForChild("Humanoid", 8)
    local root = character:WaitForChild("HumanoidRootPart", 8)
    local torso
    for _ = 1, 24 do
        torso = character:FindFirstChild("UpperTorso") or character:FindFirstChild("Torso")
        if torso then break end
        task.wait(0.10)
    end
    if token ~= generations[player] or player.Character ~= character then return end
    if not humanoid or not root or not torso or humanoid.Health <= 0 then return end
    if not torso:IsA("BasePart") or not root:IsA("BasePart") then return end
    local color = teamColor(player)
    if not color then return end
    local isRed = player.Team ~= nil and player.Team.Name == "RED"

    local folder = Instance.new("Folder")
    folder.Name = CREST_NAME
    folder.Parent = character
    local pieces = {
        makeCrest(folder, torso, color, -1, isRed),
        makeCrest(folder, torso, color, 1, isRed),
    }
    local died = humanoid.Died:Connect(function()
        if generations[player] == token then
            removeMounted(player)
        end
    end)
    mounted[player] = {
        folder = folder,
        pieces = pieces,
        root = root,
        character = character,
        died = died,
    }
end

local function register(player)
    if subscriptions[player] then return end
    local conns = {}
    conns[#conns + 1] = player.CharacterAdded:Connect(function(character)
        task.spawn(attach, player, character)
    end)
    conns[#conns + 1] = player.CharacterRemoving:Connect(function()
        generations[player] = (generations[player] or 0) + 1
        removeMounted(player)
    end)
    conns[#conns + 1] = player:GetPropertyChangedSignal("Team"):Connect(function()
        -- Rebuild on actual team changes; never recolor an opponent with a stale team.
        local character = player.Character
        if character then task.spawn(attach, player, character) end
    end)
    subscriptions[player] = conns
    if player.Character then
        task.spawn(attach, player, player.Character)
    end
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
for _, player in ipairs(Players:GetPlayers()) do
    register(player)
end

-- Single low-frequency sweep; no Heartbeat/RenderStepped, particles or light sources.
task.spawn(function()
    while true do
        local camera = workspace.CurrentCamera
        local cameraPosition = camera and camera.CFrame.Position
        for player, rec in pairs(mounted) do
            if rec.character ~= player.Character or not rec.folder.Parent then
                removeMounted(player)
            else
                local near = player == localPlayer
                if not near and cameraPosition and rec.root.Parent then
                    near = (cameraPosition - rec.root.Position).Magnitude <= LOD_STUDS
                end
                for _, piece in ipairs(rec.pieces) do
                    piece.Transparency = near and 0.04 or 1
                end
            end
        end
        task.wait(LOD_POLL_SECONDS)
    end
end)
