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

local UserInputService = game:GetService("UserInputService")
local MAX_REMOTE_CRESTS = if UserInputService.TouchEnabled then 2 else 3
local STEALTH_FLAGS = { "Stealthed", "IsInvisible", "AssassinCloaked", "EGGRUMBLE_Stealthed" }
local PART_TRANSPARENCY_LIMIT = 0.35

local mounted = {}
local subscriptions = {}
local generations = {}

local function teamColor(player)
    local team = player.Team
    if not team then return nil end
    return OFFICIAL_TEAM_COLORS[team.Name]
end

local function hiddenAvatar(player, character)
    -- Never add an opaque shoulder silhouette to an invisible R6/R15 avatar.
    for _, flag in ipairs(STEALTH_FLAGS) do
        if player:GetAttribute(flag) == true or character:GetAttribute(flag) == true then
            return true
        end
    end
    local bodyCount = 0
    for _, child in ipairs(character:GetChildren()) do
        if child:IsA("BasePart") and child.Name ~= "HumanoidRootPart" then
            bodyCount += 1
            if child.Transparency >= PART_TRANSPARENCY_LIMIT
                or child.LocalTransparencyModifier >= PART_TRANSPARENCY_LIMIT then
                return true
            end
        end
    end
    -- Character still streaming or a rig with no visible body: fail closed.
    return bodyCount == 0
end

local function clearPieces(rec)
    if rec.watchers then
        for _, conn in ipairs(rec.watchers) do conn:Disconnect() end
        rec.watchers = nil
    end
    if rec.folder then rec.folder:Destroy() end
    rec.folder = nil
    rec.pieces = nil
end

local function removeMounted(player)
    local rec = mounted[player]
    mounted[player] = nil
    if not rec then return end
    if rec.died then rec.died:Disconnect() end
    clearPieces(rec)
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

    -- Observe the existing avatar; never alter spawn, camera or its Humanoid.
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

    -- Merely register the rig. No WedgePart exists until this player is
    -- actually selected by the distance/visibility/part-budget sweep.
    local rec = {
        humanoid = humanoid, root = root, torso = torso,
        character = character, folder = nil, pieces = nil, watchers = nil,
    }
    rec.died = humanoid.Died:Connect(function()
        if generations[player] == token then removeMounted(player) end
    end)
    mounted[player] = rec
end

local function watchActiveVisibility(player, rec)
    local function dropIfHidden()
        if mounted[player] == rec and
            (hiddenAvatar(player, rec.character) or not teamColor(player)) then
            clearPieces(rec)
        end
    end
    rec.watchers = {}
    -- Only the 2/3 closest drawn remotes (plus self) have these watchers.
    -- Character/Player flag changes remove a crest immediately, not 0.75s later.
    for _, owner in ipairs({player, rec.character}) do
        for _, flag in ipairs(STEALTH_FLAGS) do
            table.insert(rec.watchers, owner:GetAttributeChangedSignal(flag):Connect(dropIfHidden))
        end
    end
    -- Both R6 and R15 partial-limb invisibility must not leave crests visible.
    for _, limb in ipairs(rec.character:GetChildren()) do
        if limb:IsA("BasePart") and limb.Name ~= "HumanoidRootPart" then
            table.insert(rec.watchers,
                limb:GetPropertyChangedSignal("Transparency"):Connect(dropIfHidden))
            table.insert(rec.watchers,
                limb:GetPropertyChangedSignal("LocalTransparencyModifier"):Connect(dropIfHidden))
        end
    end
    dropIfHidden() -- close the tiny gap between eligibility test and listeners
end

local function showPieces(player, rec)
    if rec.pieces then return end
    if rec.character ~= player.Character or not teamColor(player) then return end
    if hiddenAvatar(player, rec.character) then return end
    local folder = Instance.new("Folder")
    folder.Name = CREST_NAME
    folder.Parent = rec.character
    local color = teamColor(player)
    local isRed = player.Team ~= nil and player.Team.Name == "RED"
    rec.folder = folder
    rec.pieces = {
        makeCrest(folder, rec.torso, color, -1, isRed),
        makeCrest(folder, rec.torso, color, 1, isRed),
    }
    watchActiveVisibility(player, rec)
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
        -- Team changes clear old colors immediately, before async reattach.
        removeMounted(player)
        local character = player.Character
        if character then task.spawn(attach, player, character) end
    end)
    subscriptions[player] = conns
    if player.Character then task.spawn(attach, player, player.Character) end
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
for _, player in ipairs(Players:GetPlayers()) do register(player) end

localPlayer:GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(function()
    if localPlayer:GetAttribute("EGGRUMBLE_ReducedEffects") == true then
        for _, rec in pairs(mounted) do clearPieces(rec) end
    end
end)

-- One throttled camera-distance sweep. Create actual Parts for no more than
-- 2 remote avatars on touch or 3 on desktop, plus at most the local avatar.
-- Far/stealthed characters have ZERO invisible retained WedgeParts.
task.spawn(function()
    while true do
        local camera = workspace.CurrentCamera
        local cameraPosition = camera and camera.CFrame.Position
        local candidates = {}
        for player, rec in pairs(mounted) do
            if rec.character ~= player.Character or not rec.character.Parent
                or not rec.root.Parent or not rec.torso.Parent
                or rec.humanoid.Health <= 0 then
                removeMounted(player)
            else
                local valid = cameraPosition ~= nil and teamColor(player) ~= nil
                    and localPlayer:GetAttribute("EGGRUMBLE_ReducedEffects") ~= true
                local distance = math.huge
                if valid then
                    distance = (cameraPosition - rec.root.Position).Magnitude
                    valid = distance <= LOD_STUDS
                end
                if valid then valid = not hiddenAvatar(player, rec.character) end
                if valid then
                    table.insert(candidates, {player = player, rec = rec, distance = distance})
                else
                    clearPieces(rec)
                end
            end
        end
        table.sort(candidates, function(a, b)
            if (a.player == localPlayer) ~= (b.player == localPlayer) then
                return a.player == localPlayer
            end
            if a.distance ~= b.distance then return a.distance < b.distance end
            return a.player.UserId < b.player.UserId
        end)
        local remotesDrawn = 0
        for _, candidate in ipairs(candidates) do
            local player, rec = candidate.player, candidate.rec
            if player == localPlayer then
                showPieces(player, rec)
            elseif remotesDrawn < MAX_REMOTE_CRESTS then
                showPieces(player, rec)
                if rec.pieces then remotesDrawn += 1 end
            else
                clearPieces(rec)
            end
        end
        task.wait(LOD_POLL_SECONDS)
    end
end)
