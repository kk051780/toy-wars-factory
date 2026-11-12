--!strict
-- TRAP RAIDERS S1 Chat build: exactly one match/event/combat/objective authority.
-- This source is not a patched copy of the OWNER's newest Windows Place.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TeamsService = game:GetService("Teams")
local Config = require(ReplicatedStorage:WaitForChild("TrapRaidersShared"):WaitForChild("Config"))
local Rules = require(script.Parent:WaitForChild("S1Rules"))
local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))
local LobbyTeamRecovery = require(script.Parent:WaitForChild("LobbyTeamRecovery"))
local TrapRules = require(script.Parent:WaitForChild("S1TrapRules"))
-- The existing Game is the ONLY match/event/HP/egg owner.
local CanonicalHost = require(script.Parent:WaitForChild("S1CanonicalRoundHost"))
local BossBinding = require(script.Parent:WaitForChild("S1GoroganLiveBindings"))
local CANONICAL_S1_ENABLED = false -- explicit #220 sole-integrator decision
local D07_D08_RELEASE_REVIEW_APPROVED = false -- distinct owner safety gate
local canonicalHost: any = nil
local bossBinding: any = nil

if ReplicatedStorage:FindFirstChild("TrapRaidersS1Remote") then
    error("DUPLICATE_S1_RUNTIME: refused second authoritative remote")
end
local remote = Instance.new("RemoteEvent")
remote.Name = "TrapRaidersS1Remote"
remote.Parent = ReplicatedStorage

local function setupTeam(name: string, color: Color3): Team
    local existing = TeamsService:FindFirstChild(name)
    assert(existing == nil, "TEAM_NAME_COLLISION: do not modify another game")
    local team = Instance.new("Team")
    team.Name = name
    team.TeamColor = BrickColor.new(color)
    team.AutoAssignable = false
    team.Parent = TeamsService
    return team
end
local teamInstances = {
    RED = setupTeam("RED", Config.TeamColors.RED),
    BLUE = setupTeam("BLUE", Config.TeamColors.BLUE),
}
local map = MapBuilder.build(Config)
local trapFolder = Instance.new("Folder")
trapFolder.Name = "S1_GUARDIAN_TRAPS"
trapFolder.Parent = map.model
local roles: {[Player]: string} = {}
local lastSeq: {[Player]: number} = {}
local lastAttack: {[Player]: number} = {}
local lastRoleChange: {[Player]: number} = {}
local lastTrap: {[Player]: number} = {}
local slowed: {[Player]: any} = {}
local traps: {any} = {}
local trapSerial = 0
local invulnUntil: {[Player]: number} = {}
local carry: {[Player]: string} = {}
local carryVisuals: {[Player]: Instance} = {}
local match = {
    serial = 0,
    phase = "LOBBY",
    phaseUntil = 0,
    startedAt = 0,
    deadline = 0,
    winner = "",
    reason = "",
    scores = {RED = 0, BLUE = 0},
    hp = {RED = Config.CastleMaxHp, BLUE = Config.CastleMaxHp},
    eggOwners = {} :: {[string]: Player?},
    alarm = "IDLE",
    alarmUntil = 0,
}

local function serverNow(): number
    return workspace:GetServerTimeNow()
end
local function getTeamName(player: Player): string
    if player.Team == teamInstances.RED then return "RED" end
    if player.Team == teamInstances.BLUE then return "BLUE" end
    return "NONE"
end
local function healthy(player: Player): (boolean, BasePart?, Humanoid?)
    local character = player.Character
    if not character then return false, nil, nil end
    local root = character:FindFirstChild("HumanoidRootPart")
    local hum = character:FindFirstChildOfClass("Humanoid")
    if root == nil or not root:IsA("BasePart") or not hum or hum.Health <= 0 then
        return false, nil, nil
    end
    return true, root, hum
end
local function within(player: Player, world: Vector3, dist: number): boolean
    local ok, root = healthy(player)
    return ok and root ~= nil and (root.Position - world).Magnitude <= dist
end
local function teamCount(name: string): number
    local n = 0
    for _, p in ipairs(Players:GetPlayers()) do
        if getTeamName(p) == name then n += 1 end
    end
    return n
end
local function removeCarrierVisual(player: Player)
    local v = carryVisuals[player]
    carryVisuals[player] = nil
    if v then v:Destroy() end
end
local function resetEgg(team: string)
    match.eggOwners[team] = nil
    map.teams[team].egg.Transparency = 0
    map.teams[team].eggPrompt.Enabled = match.phase == "ACTIVE"
end
local function dropEgg(player: Player)
    local egg = carry[player]
    if egg == nil then return end
    carry[player] = nil
    removeCarrierVisual(player)
    if match.eggOwners[egg] == player then resetEgg(egg) end
end
local function giveEggVisual(player: Player)
    removeCarrierVisual(player)
    local character = player.Character
    local head = character and character:FindFirstChild("Head")
    if not head or not head:IsA("BasePart") then return end
    local b = Instance.new("BillboardGui")
    b.Name = "S1_CARRIED_EGG"
    b.Size = UDim2.fromOffset(100, 80)
    b.StudsOffsetWorldSpace = Vector3.new(0, 3.8, 0)
    b.AlwaysOnTop = true
    b.Parent = head
    local txt = Instance.new("TextLabel")
    txt.Size = UDim2.fromScale(1, 1)
    txt.BackgroundTransparency = 1
    txt.Text = "🥚"
    txt.TextScaled = true
    txt.TextColor3 = Color3.fromRGB(255, 229, 98)
    txt.Parent = b
    carryVisuals[player] = b
end
-- Guardian traps stay inside the EXISTING Game.server round/combat authority.
-- No second Remote, scheduler, damage owner, client position or monetization.
local function restoreSlow(player: Player)
    local record = slowed[player]
    slowed[player] = nil
    if record and record.hum and record.hum.Parent and record.hum.Health > 0 then
        record.hum.WalkSpeed = Config.RoleWalkSpeed[roles[player] or "RAIDER"]
    end
end
local function clearTraps()
    for _, rec in ipairs(traps) do
        if rec.part then rec.part:Destroy() end
    end
    table.clear(traps)
    for player, _ in pairs(slowed) do restoreSlow(player) end
end
local function countTraps(team: string): number
    local count = 0
    for _, rec in ipairs(traps) do
        if rec.team == team then count += 1 end
    end
    return count
end
local function placeTrap(player: Player, data)
    if type(data) ~= "table" or data.action ~= "PLACE_TRAP" then return end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq -- consume even invalid intent, same server authority as ATTACK
    local team = getTeamName(player)
    local alive, root = healthy(player)
    if not alive or not root or (team ~= "RED" and team ~= "BLUE") then return end
    local now = serverNow()
    local side = map.teams[team]
    local avoid = {}
    for _, pt in ipairs({side.egg.Position, side.scorePad.Position,
        side.core.Position, side.spawn.Position}) do
        table.insert(avoid, {x = pt.X, z = pt.Z})
    end
    if not TrapRules.canPlace({
        phase = match.phase, team = team, role = roles[player] or "RAIDER",
        alive = alive, carrying = carry[player] ~= nil,
        now = now, lastAt = lastTrap[player] or -math.huge,
        x = root.Position.X, y = root.Position.Y, z = root.Position.Z,
        count = countTraps(team), avoid = avoid,
    }) then return end
    lastTrap[player] = now
    trapSerial += 1
    local disc = Instance.new("Part")
    disc.Name = "S1_VISIBLE_TRAP_" .. team .. "_" .. tostring(trapSerial)
    disc.Anchored = true
    disc.CanCollide = false
    disc.CanTouch = false
    disc.CanQuery = false -- traps never obstruct melee raycast or castle aim
    disc.Size = Vector3.new(9, 0.25, 9)
    disc.Position = Vector3.new(root.Position.X, -0.72, root.Position.Z)
    disc.Material = Enum.Material.Neon
    disc.Color = Config.TeamColors[team]
    disc.Transparency = 0.18
    disc.Parent = trapFolder
    local label = Instance.new("BillboardGui")
    label.Size = UDim2.fromOffset(160, 48)
    label.StudsOffsetWorldSpace = Vector3.new(0, 2, 0)
    label.AlwaysOnTop = true
    label.Parent = disc
    local text = Instance.new("TextLabel")
    text.Size = UDim2.fromScale(1, 1)
    text.BackgroundTransparency = 0.25
    text.TextScaled = true
    text.Text = "🪤 ふむとスロー！　ジャンプで回避"
    text.TextColor3 = Color3.new(1, 1, 1)
    text.Parent = label
    table.insert(traps, {team = team, owner = player,
        x = root.Position.X, z = root.Position.Z,
        expiresAt = now + TrapRules.LIFETIME, part = disc})
    -- Existing authoritative tick broadcasts the next snapshot.
end
local function tickTraps(now: number)
    for player, record in pairs(slowed) do
        local alive, _, hum = healthy(player)
        if not alive or hum ~= record.hum or now >= record.untilAt then
            restoreSlow(player)
        end
    end
    for i = #traps, 1, -1 do
        local rec = traps[i]
        local triggered: Player? = nil
        if match.phase == "ACTIVE" and now < rec.expiresAt then
            for _, player in ipairs(Players:GetPlayers()) do
                local team = getTeamName(player)
                local alive, root, hum = healthy(player)
                if alive and root and hum and TrapRules.shouldTrigger({
                    phase = match.phase, healthy = alive,
                    trapTeam = rec.team, enemyTeam = team,
                    invulnerable = now < (invulnUntil[player] or 0),
                    now = now, expiresAt = rec.expiresAt,
                    x = rec.x, z = rec.z,
                    enemyX = root.Position.X, enemyY = root.Position.Y,
                    enemyZ = root.Position.Z,
                }) then
                    local slow = TrapRules.slowSpeed(Config.RoleWalkSpeed[roles[player] or "RAIDER"])
                    if slow then
                        local current = slowed[player]
                        slowed[player] = {hum = hum,
                            untilAt = math.max(now + TrapRules.SLOW_SECONDS,
                                if current then current.untilAt else 0)}
                        hum.WalkSpeed = slow
                        triggered = player
                        break
                    end
                end
            end
        end
        if triggered or now >= rec.expiresAt or match.phase ~= "ACTIVE" then
            rec.part:Destroy()
            table.remove(traps, i)
        end
    end
end

local function snapshotFor(player: Player)
    local now = serverNow()
    local seconds = 0
    if match.phase == "ACTIVE" then
        seconds = math.max(0, math.ceil(match.deadline - now))
    elseif match.phase == "COUNTDOWN" or match.phase == "RESULTS" then
        seconds = math.max(0, math.ceil(match.phaseUntil - now))
    end
    return {
        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,
        time = seconds, scores = {RED = match.scores.RED, BLUE = match.scores.BLUE},
        hp = {RED = match.hp.RED, BLUE = match.hp.BLUE},
        maxHp = Config.CastleMaxHp,
        team = getTeamName(player), role = roles[player] or "RAIDER",
        carrying = carry[player] or "", winner = match.winner,
        reason = match.reason, alarm = match.alarm,
        alarmTime = math.max(0, math.ceil(match.alarmUntil - now)),
        redPlayers = teamCount("RED"), bluePlayers = teamCount("BLUE"),
        trapCooldown = math.max(0, math.ceil((lastTrap[player] or -math.huge)
            + TrapRules.COOLDOWN - now)),
        trapRole = (roles[player] or "RAIDER") == "GUARDIAN",
    }
end
local function broadcast()
    for _, p in ipairs(Players:GetPlayers()) do
        remote:FireClient(p, snapshotFor(p))
    end
end
-- The original S1 Remote remains the sole player network endpoint.
-- Only the SERVER emits a bounded boss visual record; never an activation intent.
local function sendBossVisual(packet)
    if type(packet) ~= "table" or match.phase ~= "ACTIVE"
        or packet.matchId ~= "S1_" .. tostring(match.serial)
        or packet.stageId ~= "S1" or packet.bossId ~= "GOROGAN"
        or packet.eventId ~= "G07_" .. tostring(match.serial)
        or (packet.kind ~= "START" and packet.kind ~= "STOMP"
            and packet.kind ~= "END")
        or type(packet.seq) ~= "number" or packet.seq % 1 ~= 0
        or packet.seq < 1 or packet.seq > 10000 then
        return false
    end
    -- Original CombinedRuntime emits the true server attack center for
    -- START / STOMP. Never invent a client target or silently drop it.
    local position = nil
    if packet.kind == "START" or packet.kind == "STOMP" then
        local p = packet.position
        if type(p) ~= "table"
            or type(p.x) ~= "number" or type(p.y) ~= "number"
            or type(p.z) ~= "number" or p.x ~= p.x
            or p.y ~= p.y or p.z ~= p.z
            or math.abs(p.x) > 2048 or p.y < -100 or p.y > 700
            or math.abs(p.z) > 2048 then
            return false -- never show a false attack center
        end
        position = {x = p.x, y = p.y, z = p.z}
    end
    local emittedAt = serverNow()
    for _, player in ipairs(Players:GetPlayers()) do
        remote:FireClient(player, {
            kind = "BOSS_VISUAL", visualKind = packet.kind,
            bossId = packet.bossId, eventId = packet.eventId,
            serial = match.serial, seq = packet.seq,
            stageId = "S1", position = position,
            serverSentAt = emittedAt,
        })
    end
    return true
end

local function stopCanonical(reason: string)
    -- Disarm while the OLD epoch is still active; clear before next serial.
    local oldHost, oldBinding = canonicalHost, bossBinding
    canonicalHost, bossBinding = nil, nil
    if oldHost then
        local ok, result = pcall(function() return oldHost:stop(reason) end)
        if not ok or result ~= true then warn("S1_D08_STOP_UNCONFIRMED") end
    end
    if oldBinding then
        local ok, result = pcall(function()
            return oldBinding:abort("S1_" .. tostring(match.serial))
        end)
        if not ok or result ~= true then warn("S1_D07_PHYSICAL_ABORT_UNCONFIRMED") end
    end
end

local function startCanonical()
    if not CANONICAL_S1_ENABLED or not D07_D08_RELEASE_REVIEW_APPROVED then
        return -- no unsupported event is promised in initial S1
    end
    local ok, why = pcall(function()
        local binding = BossBinding.new({
            approvedByOwner = true, readMatch = function() return match end,
            serverTime = serverNow, map = map,
            getPlayerTeam = getTeamName,
            getInvulnerableUntil = function(player)
                return invulnUntil[player] or 0
            end,
            sendBossVisual = sendBossVisual,
        })
        bossBinding = binding -- set before constructing Host to permit failed-init abort
        local host = CanonicalHost.new({
            approvedByOwner = true, enableCanonicalS1 = true,
            readMatch = function() return match end,
            serverTime = serverNow,
            serverRoll = function(_matchId, _epoch)
                return math.random(0, 99) -- exactly one trusted D08 invocation
            end,
            makeCombined = function(mapper)
                return binding:makeCombined(mapper)
            end,
            abortCombined = function(roundId)
                return binding:abort(roundId)
            end,
            setAlarm = function(state, untilAt, epoch)
                if match.serial ~= epoch then return true end
                if state ~= "IDLE" and state ~= "WARNING"
                    and state ~= "SIGNAL" then return false end
                match.alarm, match.alarmUntil = state, untilAt
                return true
            end,
            broadcast = broadcast,
        })
        if host:status().enabled ~= true then error("S1_CANONICAL_NOT_ENABLED") end
        canonicalHost = host
    end)
    if not ok then
        warn("S1_D08_D07_INIT_FAILED", why)
        stopCanonical("INIT_FAILED")
        match.alarm, match.alarmUntil = "IDLE", 0
    end
end

local function setObjectiveEnabled(enabled: boolean)
    for _, name in ipairs({"RED", "BLUE"}) do
        map.teams[name].eggPrompt.Enabled = enabled and match.eggOwners[name] == nil
        map.teams[name].scorePrompt.Enabled = enabled
    end
end
local function stopRound(winner: string, reason: string)
    if match.phase ~= "ACTIVE" then return end
    stopCanonical("ROUND_END")
    match.phase = "RESULTS"
    match.phaseUntil = serverNow() + Config.ResultsSeconds
    match.winner = winner
    match.reason = reason
    match.alarm = "IDLE"
    match.alarmUntil = 0
    setObjectiveEnabled(false)
    clearTraps()
    for _, p in ipairs(Players:GetPlayers()) do dropEgg(p) end
    broadcast()
end
local function resetRound()
    stopCanonical("ROUND_RESET")
    clearTraps()
    match.serial += 1
    match.phase = "ACTIVE"
    match.startedAt = serverNow()
    match.deadline = match.startedAt + Config.MatchSeconds
    match.scores = {RED = 0, BLUE = 0}
    match.hp = {RED = Config.CastleMaxHp, BLUE = Config.CastleMaxHp}
    match.eggOwners = {}
    match.winner = ""
    match.reason = ""
    match.alarm = "IDLE"
    match.alarmUntil = 0
    for _, p in ipairs(Players:GetPlayers()) do
        dropEgg(p)
        lastAttack[p] = -math.huge
        lastTrap[p] = -math.huge
        -- Player seq stays monotonic across round transitions; never rewind replay ceiling.
        p:LoadCharacter()
    end
    for _, team in ipairs({"RED", "BLUE"}) do resetEgg(team) end
    setObjectiveEnabled(true)
    startCanonical()
    broadcast()
end
local function chooseTeam(player: Player)
    local name = if teamCount("RED") <= teamCount("BLUE") then "RED" else "BLUE"
    player.Team = teamInstances[name]
    player.Neutral = false
end
-- Only LOBBY may correct team balance; never touch a live round or countdown.
-- This is a small attachment to the existing server controller, not another authority.
local function rebalanceLobbyTeams()
    if match.phase ~= "LOBBY" then return end
    local online = Players:GetPlayers()
    if #online < Config.MinPlayers then return end
    local roster = {}
    local byUserId = {}
    for _, player in ipairs(online) do
        table.insert(roster, {userId = player.UserId, team = getTeamName(player)})
        byUserId[player.UserId] = player
    end
    local planned = LobbyTeamRecovery.plan(roster)
    if planned == nil then return end
    for _, move in ipairs(planned) do
        local player = byUserId[move.userId]
        if player and player.Parent == Players and getTeamName(player) == move.from then
            -- Defensive cleanup: no carried egg survives a lobby team move.
            dropEgg(player)
            player.Team = teamInstances[move.to]
            player.Neutral = false
            local alive, root = healthy(player)
            if alive and root then
                root.CFrame = map.teams[move.to].spawn + Vector3.new(0, 2, 0)
            end
        end
    end
end

local function assignSpawn(player: Player, character: Model)
    local root = character:WaitForChild("HumanoidRootPart", 10)
    local hum = character:WaitForChild("Humanoid", 10)
    if root and root:IsA("BasePart") and hum and hum:IsA("Humanoid") then
        local team = getTeamName(player)
        if team == "RED" or team == "BLUE" then
            root.CFrame = map.teams[team].spawn + Vector3.new(0, 2, 0)
        end
        local role = roles[player] or "RAIDER"
        hum.MaxHealth = Config.RoleHealth[role]
        hum.Health = hum.MaxHealth
        hum.WalkSpeed = Config.RoleWalkSpeed[role]
        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability
        hum.Died:Connect(function()
            restoreSlow(player)
            dropEgg(player)
            invulnUntil[player] = 0
        end)
    end
end

for _, team in ipairs({"RED", "BLUE"}) do
    map.teams[team].eggPrompt.Triggered:Connect(function(player: Player)
        local thiefTeam = getTeamName(player)
        local alive = healthy(player)
        local free = match.eggOwners[team] == nil
        if not Rules.canSteal(match.phase, thiefTeam, team,
            if within(player, map.teams[team].egg.Position, Config.InteractDistance)
                then 0 else 1e8, alive, carry[player] ~= nil, free,
            Config.InteractDistance) then return end
        match.eggOwners[team] = player
        carry[player] = team
        map.teams[team].egg.Transparency = 1
        map.teams[team].eggPrompt.Enabled = false
        giveEggVisual(player)
        broadcast()
    end)
    map.teams[team].scorePrompt.Triggered:Connect(function(player: Player)
        local alive = healthy(player)
        local playerTeam = getTeamName(player)
        local ownEggHome = match.eggOwners[team] == nil
        if not Rules.canScore(match.phase, playerTeam, team,
            if within(player, map.teams[team].scorePad.Position, Config.InteractDistance)
                then 0 else 1e8, alive, carry[player], ownEggHome,
            Config.InteractDistance) then return end
        local stolenTeam = carry[player]
        if not stolenTeam or match.eggOwners[stolenTeam] ~= player then return end
        dropEgg(player)
        match.scores[team] += 1
        local winner = Rules.winner(match.scores, match.hp, Config.CapturesToWin)
        if winner then stopRound(winner, "EGG_CAPTURE") else broadcast() end
    end)
end

local function applyAttack(player: Player, data)
    if type(data) ~= "table" or data.action ~= "ATTACK" then return end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq
    local team = getTeamName(player)
    if team ~= "RED" and team ~= "BLUE" then return end
    local alive, root = healthy(player)
    if not alive or root == nil then return end
    local now = serverNow()
    if not Rules.canAttack(now, lastAttack[player] or -math.huge, match.phase,
        alive, Config.AttackCooldown) then return end
    lastAttack[player] = now
    local look = root.CFrame.LookVector
    local chosen = nil
    local best = Config.AttackReach + 0.001
    for _, other in ipairs(Players:GetPlayers()) do
        if other ~= player and getTeamName(other) == Rules.opponent(team) then
            local enemyAlive, enemyRoot = healthy(other)
            if enemyAlive and enemyRoot and now >= (invulnUntil[other] or 0) then
                local displacement = enemyRoot.Position - root.Position
                local dist = displacement.Magnitude
                local dot = if dist > 0.0001 then look:Dot(displacement.Unit) else 1
                if Rules.damageCandidate(dist, dot, Config.AttackReach) and dist < best then
                    -- Reject hits through solid parts; whitelist target's character only.
                    local params = RaycastParams.new()
                    params.FilterType = Enum.RaycastFilterType.Exclude
                    params.FilterDescendantsInstances = {player.Character :: Model}
                    local hit = workspace:Raycast(root.Position, displacement, params)
                    if hit == nil or (other.Character and hit.Instance:IsDescendantOf(other.Character)) then
                        chosen = other
                        best = dist
                    end
                end
            end
        end
    end
    if chosen then
        local ok, _, hum = healthy(chosen)
        if ok and hum then hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"]) end
        return
    end
    local enemy = Rules.opponent(team)
    local core = map.teams[enemy].core
    local distance = (core.Position - root.Position).Magnitude
    local aim = if distance > 0.001 then look:Dot((core.Position - root.Position).Unit) else 1
    if not Rules.damageCandidate(distance, aim, Config.CastleReach) then return end
    -- Fail closed when a map wall or solid decoration occludes the castle core.
    local params = RaycastParams.new()
    params.FilterType = Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances = {player.Character :: Model}
    local hit = workspace:Raycast(root.Position, core.Position - root.Position, params)
    if hit and hit.Instance ~= core then return end
    -- Castle damage is server-owned; client never sends its preferred damage/target.
    match.hp[enemy] = math.max(0, match.hp[enemy] - Config.CastleAttackDamage[roles[player] or "RAIDER"])
    local winner = Rules.winner(match.scores, match.hp, Config.CapturesToWin)
    if winner then stopRound(winner, "CASTLE_DESTROYED") else broadcast() end
end

local function applyRole(player: Player, data)
    if type(data) ~= "table" or data.action ~= "ROLE" then return end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq
    local role = data.role
    if role ~= "RAIDER" and role ~= "GUARDIAN" then return end
    -- Prevent role-change healing in combat.
    if match.phase == "ACTIVE" then return end
    local now = serverNow()
    if now - (lastRoleChange[player] or -math.huge) < Config.RoleSelectCooldown then return end
    lastRoleChange[player] = now
    roles[player] = role
    remote:FireClient(player, snapshotFor(player))
end

remote.OnServerEvent:Connect(function(player: Player, data)
    if type(data) ~= "table" then return end
    if data.action == "ATTACK" then applyAttack(player, data)
    elseif data.action == "ROLE" then applyRole(player, data)
    elseif data.action == "PLACE_TRAP" then placeTrap(player, data)
    end
end)

local function onJoin(player: Player)
    chooseTeam(player)
    roles[player] = "RAIDER"
    lastSeq[player] = 0
    lastAttack[player] = -math.huge
    lastRoleChange[player] = -math.huge
    lastTrap[player] = -math.huge
    invulnUntil[player] = 0
    player.CharacterAdded:Connect(function(character)
        dropEgg(player)
        task.spawn(assignSpawn, player, character)
    end)
    if player.Character then task.spawn(assignSpawn, player, player.Character) end
    remote:FireClient(player, snapshotFor(player))
end
Players.PlayerAdded:Connect(onJoin)
for _, player in ipairs(Players:GetPlayers()) do onJoin(player) end
Players.PlayerRemoving:Connect(function(player)
    local side = getTeamName(player)
    dropEgg(player)
    restoreSlow(player)
    for i = #traps, 1, -1 do
        if traps[i].owner == player then
            traps[i].part:Destroy()
            table.remove(traps, i)
        end
    end
    roles[player] = nil
    lastSeq[player] = nil
    lastAttack[player] = nil
    lastRoleChange[player] = nil
    lastTrap[player] = nil
    invulnUntil[player] = nil
    if match.phase == "ACTIVE" and side ~= "NONE" then
        -- Robust to PlayerRemoving before OR after GetPlayers() drops the leaver.
        -- Count only distinct teammates, never the player being removed.
        local teammates = 0
        for _, other in ipairs(Players:GetPlayers()) do
            if other ~= player and getTeamName(other) == side then
                teammates += 1
            end
        end
        if teammates == 0 then
            stopRound(Rules.opponent(side), "OPPONENT_LEFT")
        end
    end
end)

local function tickRound()
    local now = serverNow()
    tickTraps(now)
    local count = #Players:GetPlayers()
    if match.phase == "LOBBY" then
        rebalanceLobbyTeams()
        if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then
            match.phase = "COUNTDOWN"
            match.phaseUntil = now + Config.IntermissionSeconds
        end
    elseif match.phase == "COUNTDOWN" then
        -- Players can leave during countdown; do not start a one-sided game.
        if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then
            match.phase = "LOBBY"
        elseif now >= match.phaseUntil then resetRound() end
    elseif match.phase == "ACTIVE" then
        if teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")
        elseif teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")
        elseif now >= match.deadline then
            local red = match.scores.RED * 1000 + match.hp.RED
            local blue = match.scores.BLUE * 1000 + match.hp.BLUE
            stopRound(if red == blue then "DRAW" else (if red > blue then "RED" else "BLUE"), "TIME_LIMIT")
        else
            -- D08 only advances within this already-existing authoritative tick.
            if canonicalHost then
                local ok, success, reason = pcall(function()
                    return canonicalHost:tick()
                end)
                if not ok or success ~= true then
                    warn("S1_D08_TICK_FAIL_CLOSED", reason)
                    stopCanonical("TICK_FAILED")
                    match.alarm, match.alarmUntil = "IDLE", 0
                end
            end
        end
    elseif match.phase == "RESULTS" then
        if now >= match.phaseUntil then
            match.phase = "LOBBY"
            match.winner = ""
            match.reason = ""
            match.alarm = "IDLE"
        end
    end
    -- Recovery uses the existing server-only authoritative tick. Exact current
    -- S1 GrassArena is 250 x 142 studs; five studs outside is no longer playable.
    -- No client request or egg carry can choose a free teleport destination.
    for _, player in ipairs(Players:GetPlayers()) do
        local alive, root = healthy(player)
        if alive and root then
            local position = root.Position
            if position.Y < -30 or math.abs(position.X) > 130
                or math.abs(position.Z) > 76 then
                local team = getTeamName(player)
                if team == "RED" or team == "BLUE" then
                    dropEgg(player)
                    restoreSlow(player)
                    root.AssemblyLinearVelocity = Vector3.zero
                    root.AssemblyAngularVelocity = Vector3.zero
                    root.CFrame = map.teams[team].spawn + Vector3.new(0, 4, 0)
                    invulnUntil[player] = now + Config.RespawnInvulnerability
                end
            end
        end
    end
end

task.spawn(function()
    while true do
        tickRound()
        broadcast()
        task.wait(Config.SnapshotInterval)
    end
end)
