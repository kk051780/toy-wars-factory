--!nocheck
-- Talking NPC PREP: optional server-only observations; original Game/Store/Remote untouched.
-- ServerStorage P0D_RC_ENABLE_TALKING_NPC_V1 true only in Studio private build.
local RunService = game:GetService("RunService")
if not RunService:IsStudio() then return end
local ServerStorage = game:GetService("ServerStorage")
local FLAG = "P0D_RC_ENABLE_TALKING_NPC_V1"
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local PUBLIC_ENABLED = "P0D_TALKING_NPC_CLIENT_ENABLED"
ReplicatedStorage:SetAttribute(PUBLIC_ENABLED, false)

local directorModule = script.Parent:WaitForChild("TalkingNPCDirector", 20)
if not directorModule or not directorModule:IsA("ModuleScript") then
    warn("[P0D/TALK] missing TalkingNPCDirector; feature disabled")
    return
end
local directorOk, Director = pcall(require, directorModule)
if not directorOk or type(Director) ~= "table"
    or type(Director.Compose) ~= "function" or type(Director.CanSpeak) ~= "function" then
    warn("[P0D/TALK] dialogue module failed to load; feature disabled")
    return
end

local active = nil
local epoch = 0
local speechTimes = {}  -- [Player] = {[speaker] = os.clock()}
local lastAlertTarget = {} -- [Player] = enemy.UserId, only after ENEMY_ALERT is sent

local function aliveRoot(player)
    if not player or player.Parent ~= Players then return nil end
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    local root = character and character:FindFirstChild("HumanoidRootPart")
    if not humanoid or humanoid.Health <= 0 or not root or not root:IsA("BasePart") then
        return nil
    end
    return root
end
local function inTeam(player, team)
    return player.Team ~= nil and player.Team.Name == team
end
local function visibleEnemy(player)
    local root = aliveRoot(player)
    if not root or not player.Team then return nil end
    local name = player.Team.Name
    if name ~= "RED" and name ~= "BLUE" then return nil end
    local inspected = 0
    local raycasts = 0
    for _, enemy in ipairs(Players:GetPlayers()) do
        inspected += 1
        if inspected > 12 or raycasts >= 3 then break end -- bound whole-server scan
        if enemy ~= player and enemy.Team
            and (enemy.Team.Name == "RED" or enemy.Team.Name == "BLUE")
            and enemy.Team ~= player.Team then
            local other = aliveRoot(enemy)
            if other then
                local d = other.Position - root.Position
                if d.Magnitude <= 45 and d.Magnitude >= 0.1 then
                    local params = RaycastParams.new()
                    params.FilterType = Enum.RaycastFilterType.Exclude
                    params.FilterDescendantsInstances = {player.Character, enemy.Character}
                    raycasts += 1
                    local blocked = Workspace:Raycast(root.Position, d, params)
                    if blocked == nil then return enemy, other end
                end
            end
        end
    end
    return nil
end
local function areaFor(position)
    if position.X < -25 then return "west" end
    if position.X > 25 then return "east" end
    if position.Z < -22 then return "north" end
    if position.Z > 22 then return "south" end
    return "center"
end
local function carryingEgg(player)
    local head = player.Character and player.Character:FindFirstChild("Head")
    return head and head:FindFirstChild("S1_CARRIED_EGG") ~= nil
end

local function sourceFacts(player, speaker, mode, arena)
    local facts = {featureEnabled = true, speakerId = speaker, cooldownActive = false}
    if speaker == "NAVI" then
        -- Auto warnings use ENEMY_ALERT ONLY. Never mark the enemy as alerted
        -- after composing a carried-egg message or a HELLO.
        if mode ~= "AUTO_ENEMY_ALERT" and carryingEgg(player) then
            facts.signal = "EGG_RETURN"
            facts.ourEggCarrier = true
            facts.urgent = true
            return facts
        end
        -- The original Game alone owns round phase. No inferred phase from team
        -- or proximity: #220 must publish this read-only attribute in the host.
        local enemy, enemyRoot = nil, nil
        if arena:GetAttribute("P0D_AUTH_ROUND_PHASE") == "ACTIVE" then
            enemy, enemyRoot = visibleEnemy(player)
        end
        if enemy and enemyRoot then
            facts.signal = "ENEMY_ALERT"
            facts.areaCode = areaFor(enemyRoot.Position)
            facts.observedByTeam = true
            facts.urgent = true
            return facts
        end
        if mode == "AUTO_ENEMY_ALERT" then return nil end
        local starStage = Workspace:FindFirstChild("P0D_STARRY_PATH")
        local shardCount = player:GetAttribute("P0D_StarShardCount")
        if starStage and starStage:GetAttribute("PathOpen") == true
            and starStage:FindFirstChild("P0D_StarShardHunt")
            and type(shardCount) == "number" and shardCount < 6
            and player:GetAttribute("P0D_StarShardComplete") ~= true then
            facts.signal = "KNOWN_ITEM"
            facts.areaCode = "star_bridge"
            facts.itemCode = "star_shard"
            facts.itemKnownByTeam = true
            return facts
        end
        facts.signal = "HELLO"
        return facts
    elseif speaker == "TRICK" then
        facts.signal = mode == "TAUNT" and "TAUNT" or "TRICK_RUMOR"
        return facts
    elseif speaker == "ORACLE" then
        local realms = arena:FindFirstChild("P0D_REALM_HUNT_V1")
        if not realms or realms:GetAttribute("Enabled") ~= true then return nil end
        local discovered = player:GetAttribute("P0D_RealmHunt_Count")
        facts.signal = "SECRET_HINT"
        facts.hintUnlocked = type(discovered) == "number" and discovered >= 1
        facts.secretTier = type(discovered) == "number" and discovered >= 3 and 2 or 1
        if not facts.hintUnlocked then facts.signal = "INTRO" end
        return facts
    end
    return nil
end

local function speak(player, speaker, mode, arena)
    if ServerStorage:GetAttribute(FLAG) ~= true or not active
        or not aliveRoot(player) then return nil end
    local facts = sourceFacts(player, speaker, mode, arena)
    if not facts then return nil end
    local now = os.clock()
    local perSpeaker = speechTimes[player] or {}
    if not Director.CanSpeak(now, perSpeaker[speaker], facts.urgent) then return nil end
    local message = Director.Compose(facts)
    if not message or type(message.text) ~= "string" or #message.text > 270 then return nil end
    perSpeaker[speaker] = now
    speechTimes[player] = perSpeaker
    -- One existing Game-owned RemoteEvent. Private FireClient, never FireAllClients.
    active.remote:FireClient(player, {
        kind = "P0D_NPC_TALK_V1",
        speakerId = message.speakerId,
        displayName = message.displayName,
        text = message.text,
        voiceId = message.voiceId,
        suspicious = message.suspicious == true,
        automated = mode == "AUTO_ENEMY_ALERT",
    })
    return message.intent
end

local function createNPC(folder, arena, name, speaker, position, color, team, animated)
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
    core:SetAttribute("TalkRole", speaker)
    core:SetAttribute("Faction", team or "NEUTRAL")
    core.Parent = folder
    table.insert(animated, {core = core, base = core.CFrame, phase = #animated * 1.7})
    local light = Instance.new("PointLight")
    light.Range = 12
    light.Brightness = 1
    light.Color = color
    light.Parent = core
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
        if ServerStorage:GetAttribute(FLAG) ~= true or not active
            or active.folder ~= folder then return end
        local root = aliveRoot(player)
        if not root or (root.Position - core.Position).Magnitude > 13 then return end
        if team and not inTeam(player, team) then return end
        speak(player, speaker, nil, arena)
    end)
end

local function stop()
    epoch += 1
    local prior = active
    active = nil
    if prior and prior.folder.Parent then prior.folder:Destroy() end
    speechTimes = {}
    lastAlertTarget = {}
    ReplicatedStorage:SetAttribute(PUBLIC_ENABLED, false)
end
local function start()
    if active or ServerStorage:GetAttribute(FLAG) ~= true then return end
    local arena = Workspace:FindFirstChild("TRAP_RAIDERS_S1")
        or Workspace:WaitForChild("TRAP_RAIDERS_S1", 60)
    local remote = ReplicatedStorage:FindFirstChild("TrapRaidersS1Remote")
        or ReplicatedStorage:WaitForChild("TrapRaidersS1Remote", 60)
    if ServerStorage:GetAttribute(FLAG) ~= true then return end
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
    local animated = {}
    active = {folder = folder, remote = remote}
    createNPC(folder, arena, "ナビィ 赤チーム", "NAVI",
        Vector3.new(-69, 3.2, 11), Color3.fromRGB(254, 115, 153), "RED", animated)
    createNPC(folder, arena, "ナビィ 青チーム", "NAVI",
        Vector3.new(69, 3.2, 11), Color3.fromRGB(94, 193, 255), "BLUE", animated)
    createNPC(folder, arena, "マドロン あやしい噂", "TRICK",
        Vector3.new(0, 3.2, -40), Color3.fromRGB(202, 127, 249), nil, animated)
    createNPC(folder, arena, "オラクル 秘境のヒント", "ORACLE",
        Vector3.new(0, 3.2, 47), Color3.fromRGB(250, 213, 112), nil, animated)
    ReplicatedStorage:SetAttribute(PUBLIC_ENABLED, true)
    local generation = epoch
    task.spawn(function()
        -- Low-frequency ONE loop for all characters; sent only on real fresh enemy.
        while active and active.folder == folder and folder.Parent
            and epoch == generation and ServerStorage:GetAttribute(FLAG) == true do
            for _,player in ipairs(Players:GetPlayers()) do
                local enemy = nil
                if arena:GetAttribute("P0D_AUTH_ROUND_PHASE") == "ACTIVE" then
                    enemy = visibleEnemy(player)
                end
                if enemy and lastAlertTarget[player] ~= enemy.UserId then
                    if speak(player, "NAVI", "AUTO_ENEMY_ALERT", arena) == "ENEMY_ALERT" then
                        lastAlertTarget[player] = enemy.UserId
                    end
                elseif not enemy then
                    lastAlertTarget[player] = nil
                end
            end
            task.wait(8)
        end
    end)
    task.spawn(function()
        while active and active.folder == folder and folder.Parent
            and epoch == generation and ServerStorage:GetAttribute(FLAG) == true do
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
end
local reconcileBusy = false
local function reconcile()
    if reconcileBusy then return end
    reconcileBusy = true
    local ok, reason = pcall(function()
        if ServerStorage:GetAttribute(FLAG) == true then
            if not active then start() end
        else
            stop()
        end
    end)
    reconcileBusy = false -- reset even if the start() constructor throws
    if not ok then
        warn("[P0D/TALK] startup failure; cleaning up optional preview", reason)
        stop()
    end
end
Players.PlayerRemoving:Connect(function(player)
    speechTimes[player] = nil
    lastAlertTarget[player] = nil
end)
ServerStorage:GetAttributeChangedSignal(FLAG):Connect(reconcile)
Workspace.ChildAdded:Connect(function(child)
    if child.Name == "TRAP_RAIDERS_S1" then task.defer(reconcile) end
end)
ReplicatedStorage.ChildAdded:Connect(function(child)
    if child.Name == "TrapRaidersS1Remote" then task.defer(reconcile) end
end)
task.defer(reconcile)
print("[P0D/TALK] optional NPC layer configured; Studio/FUN NOT_TESTED")
