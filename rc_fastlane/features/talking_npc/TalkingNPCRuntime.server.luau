--!nocheck
-- P0D-TALKING-NPC-V1 / PREP only. ONE existing Game remains match/egg/combat authority.
-- Install as ServerScriptService/TrapRaidersS1/TalkingNPCRuntime after real integration.
-- Requires sibling TalkingNPCDirector ModuleScript and existing TrapRaidersS1Remote.
-- No new Remote, Store, round, HP, score, XP, rewards or paid services.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local ServerStorage = game:GetService("ServerStorage")
local FLAG = "P0D_RC_ENABLE_TALKING_NPC_V1"
if ServerStorage:GetAttribute(FLAG) ~= true then return end

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Director = require(script.Parent:WaitForChild("TalkingNPCDirector", 20))
if type(Director) ~= "table" or type(Director.Compose) ~= "function" then return end
local arena = Workspace:WaitForChild("TRAP_RAIDERS_S1", 60)
local remote = ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 60)
if not arena or not arena:IsA("Folder") or not remote or not remote:IsA("RemoteEvent") then
    warn("[P0D/TALK] original arena or Remote missing; fail closed")
    return
end
if arena:FindFirstChild("P0D_TalkingNPCs") then
    warn("[P0D/TALK] duplicate runtime refused")
    return
end

local folder = Instance.new("Folder")
folder.Name = "P0D_TalkingNPCs"
folder:SetAttribute("FeatureId", "P0D-TALKING-NPC-V1")
folder:SetAttribute("PrivateStudioOnly", true)
folder:SetAttribute("NoGameplayAuthority", true)
folder.Parent = arena

local lastSpeech = {}
local lastAlertTarget = {}
local animated = {}
local function aliveRoot(player)
    if not player or player.Parent ~= Players then return nil end
    local char = player.Character
    local hum = char and char:FindFirstChildOfClass("Humanoid")
    local root = char and char:FindFirstChild("HumanoidRootPart")
    if not hum or hum.Health <= 0 or not root or not root:IsA("BasePart") then return nil end
    return root
end
local function inTeam(player, team)
    return player.Team ~= nil and player.Team.Name == team
end
local function visibleEnemy(player)
    local root = aliveRoot(player)
    if not root or not player.Team then return nil end
    local ourTeam = player.Team.Name
    if ourTeam ~= "RED" and ourTeam ~= "BLUE" then return nil end
    for _, enemy in ipairs(Players:GetPlayers()) do
        if enemy ~= player and enemy.Team and enemy.Team ~= player.Team then
            local other = aliveRoot(enemy)
            if other then
                local d = other.Position - root.Position
                if d.Magnitude <= 45 and d.Magnitude >= 0.1 then
                    local params = RaycastParams.new()
                    params.FilterType = Enum.RaycastFilterType.Exclude
                    params.FilterDescendantsInstances = {player.Character, enemy.Character}
                    local blocked = Workspace:Raycast(root.Position, d, params)
                    if blocked == nil then
                        return enemy, other
                    end
                end
            end
        end
    end
    return nil
end
local function areaFor(worldPosition)
    if worldPosition.X < -25 then return "west" end
    if worldPosition.X > 25 then return "east" end
    if worldPosition.Z < -22 then return "north" end
    if worldPosition.Z > 22 then return "south" end
    return "center"
end
local function sourceFacts(player, speaker, selected)
    local facts = {featureEnabled = true, speakerId = speaker, cooldownActive = false}
    if speaker == "NAVI" then
        if player.Character and player.Character:FindFirstChild("S1_CARRIED_EGG") then
            facts.signal = "EGG_RETURN"
            facts.ourEggCarrier = true
            facts.urgent = true
            return facts
        end
        local enemy, enemyRoot = visibleEnemy(player)
        if enemy and enemyRoot then
            -- LOS+45 studs confirmed on the server for this player only.
            facts.signal = "ENEMY_ALERT"
            facts.areaCode = areaFor(enemyRoot.Position)
            facts.observedByTeam = true
            facts.urgent = true
            return facts
        end
        local starStage = Workspace:FindFirstChild("P0D_STARRY_PATH")
        if starStage and starStage:GetAttribute("PathOpen") == true
            and starStage:FindFirstChild("P0D_StarShardHunt") then
            facts.signal = "KNOWN_ITEM"
            facts.areaCode = "sky"
            facts.itemCode = "star_shard"
            facts.itemKnownByTeam = true
            return facts
        end
        facts.signal = "HELLO"
        return facts
    elseif speaker == "TRICK" then
        facts.signal = selected == "TAUNT" and "TAUNT" or "TRICK_RUMOR"
        return facts
    elseif speaker == "ORACLE" then
        local realms = arena:FindFirstChild("P0D_REALM_HUNT_V1")
        if not realms then return nil end
        local discovered = player:GetAttribute("P0D_RealmHunt_Count")
        facts.signal = "SECRET_HINT"
        facts.hintUnlocked = type(discovered) == "number" and discovered >= 1
        facts.secretTier = (type(discovered) == "number" and discovered >= 3) and 2 or 1
        if not facts.hintUnlocked then facts.signal = "INTRO" end
        return facts
    end
    return nil
end

local function speak(player, speaker, selected)
    if ServerStorage:GetAttribute(FLAG) ~= true then return false end
    if not aliveRoot(player) then return false end
    local facts = sourceFacts(player, speaker, selected)
    if not facts then return false end
    local now = os.clock()
    if not Director.CanSpeak(now, lastSpeech[player], facts.urgent) then return false end
    local message = Director.Compose(facts)
    if not message then return false end
    if type(message.text) ~= "string" or #message.text > 270 then return false end
    lastSpeech[player] = now
    -- This is an existing server-owned Remote. FireClient is private to ONE player.
    -- Other clients never receive this location, hint, or nearby enemy observation.
    remote:FireClient(player, {
        kind = "P0D_NPC_TALK_V1",
        speakerId = message.speakerId,
        displayName = message.displayName,
        text = message.text,
        voiceId = message.voiceId,
        suspicious = message.suspicious == true,
    })
    return true
end

local function npc(name, speaker, position, color, team)
    local core = Instance.new("Part")
    core.Name = name
    core.Shape = Enum.PartType.Ball
    core.Size = Vector3.new(3.3, 3.3, 3.3)
    core.Position = position
    core.Anchored = true
    core.CanCollide = false
    core.CanTouch = false
    core.CanQuery = false
    core.Material = Enum.Material.Neon
    core.Color = color
    core.Parent = folder
    core:SetAttribute("TalkRole", speaker)
    core:SetAttribute("Faction", team or "NEUTRAL")
    table.insert(animated, {core = core, base = core.CFrame, phase = #animated * 1.7})
    local light = Instance.new("PointLight")
    light.Range = 12
    light.Brightness = 1
    light.Color = color
    light.Parent = core
    local eye = Instance.new("Decal")
    eye.Name = "Eyes"
    eye.Face = Enum.NormalId.Front
    eye.Texture = "rbxasset://textures/face.png"
    eye.Parent = core
    local bb = Instance.new("BillboardGui")
    bb.Size = UDim2.fromOffset(160, 38)
    bb.StudsOffsetWorldSpace = Vector3.new(0, 3, 0)
    bb.MaxDistance = 65
    bb.AlwaysOnTop = true
    bb.Parent = core
    local label = Instance.new("TextLabel")
    label.Size = UDim2.fromScale(1, 1)
    label.TextScaled = true
    label.BackgroundColor3 = Color3.fromRGB(20, 26, 42)
    label.BackgroundTransparency = 0.2
    label.TextColor3 = Color3.fromRGB(248, 250, 255)
    label.Font = Enum.Font.GothamBold
    label.Text = name
    label.Parent = bb
    local prompt = Instance.new("ProximityPrompt")
    prompt.Name = "Ask" .. speaker
    prompt.ActionText = "話を聞く"
    prompt.ObjectText = name
    prompt.HoldDuration = 0.2
    prompt.MaxActivationDistance = 10
    prompt.RequiresLineOfSight = false
    prompt.Parent = core
    prompt.Triggered:Connect(function(player)
        local root = aliveRoot(player)
        if not root or (root.Position - core.Position).Magnitude > 13 then return end
        if team and not inTeam(player, team) then return end
        speak(player, speaker, nil)
    end)
    return core
end

-- Both teams get the same ally, while the trickster and Oracle are neutral locations.
npc("ナビィ 赤チーム", "NAVI", Vector3.new(-69, 3.2, 11), Color3.fromRGB(254, 115, 153), "RED")
npc("ナビィ 青チーム", "NAVI", Vector3.new(69, 3.2, 11), Color3.fromRGB(94, 193, 255), "BLUE")
npc("マドロン あやしい噂", "TRICK", Vector3.new(0, 3.2, -40), Color3.fromRGB(202, 127, 249), nil)
npc("オラクル 秘境のヒント", "ORACLE", Vector3.new(0, 3.2, 47), Color3.fromRGB(250, 213, 112), nil)

Players.PlayerRemoving:Connect(function(p)
    lastSpeech[p] = nil
    lastAlertTarget[p] = nil
end)

-- Optional automatic companion warning. Never transmit a hidden enemy.
-- One low-frequency scan; no Heartbeat loop per character.
task.spawn(function()
    while folder.Parent and ServerStorage:GetAttribute(FLAG) == true do
        for _, player in ipairs(Players:GetPlayers()) do
            local enemy = visibleEnemy(player)
            if enemy ~= nil and lastAlertTarget[player] ~= enemy.UserId then
                if speak(player, "NAVI", nil) then
                    lastAlertTarget[player] = enemy.UserId
                end
            elseif enemy == nil then
                lastAlertTarget[player] = nil
            end
        end
        task.wait(8)
    end
end)
task.spawn(function()
    -- One shared lightweight animation loop, 4 decorative nonblocking orbs only.
    while folder.Parent and ServerStorage:GetAttribute(FLAG) == true do
        local t = os.clock()
        for _, entry in ipairs(animated) do
            if entry.core.Parent then
                entry.core.CFrame = entry.base
                    * CFrame.new(0, math.sin(t * 1.4 + entry.phase) * 0.33, 0)
                    * CFrame.Angles(0, math.sin(t * 0.7 + entry.phase) * 0.25, 0)
            end
        end
        task.wait(0.12)
    end
end)
print("[P0D/TALK] optional NPC layer ready; original Game untouched, Studio/FUN NOT_TESTED")
