--!strict
-- TRAP RAIDERS S1 Chat build: exactly one match/event/combat/objective authority.
-- This source is not a patched copy of the OWNER's newest Windows Place.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TeamsService = game:GetService("Teams")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local DataStoreService = game:GetService("DataStoreService")
-- EGG RAID RUMBLE: H2 5-egg alternative is private Studio only.
-- Normal runtime / published Game remains the original unchanged one-egg mode.
local EXPERIMENTAL_FIVE_EGG_MODE = false -- selected per round; 5 eggs Studio-only for this private build
local H2Score = require(script.Parent:WaitForChild("H2FiveEggRules"))
local ModeVote = require(script.Parent:WaitForChild("ModeVoteRules"))
-- Exact original #275 free-hatch entitlement module, no duplicate rewards authority.
local RewardRules = require(script.Parent:WaitForChild("RewardEquipRules"))
local PersistentHatch = require(script.Parent:WaitForChild("PersistentHatchStore"))
local Progression = require(script.Parent:WaitForChild("ProgressionRules")) -- exact #281 original source
-- Original #285 server-only earned power rules, byte-identical import.
local Power = require(script.Parent:WaitForChild("PowerFantasyRules"))
-- Byte-identical #287 EvolutionRules; stored by the SAME original hatch profile.
local Evolution = require(script.Parent:WaitForChild("EvolutionRules"))
-- One read-only FIRST90 guide; no separate gameplay authority.
local First90Guide = require(script.Parent:WaitForChild("First90GuideRules"))
local First90Waypoint = require(script.Parent:WaitForChild("First90WaypointRules"))
-- #288 experimental helpers only. Original Game remains sole server combat/egg authority.
local MusouHorde = require(script.Parent:WaitForChild("MusouHorde"))
local MusouBind = require(script.Parent:WaitForChild("MusouBindRules"))
local Config = require(ReplicatedStorage:WaitForChild("TrapRaidersShared"):WaitForChild("Config"))
local Rules = require(script.Parent:WaitForChild("S1Rules"))
local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))
local LobbyTeamRecovery = require(script.Parent:WaitForChild("LobbyTeamRecovery"))
local TrapRules = require(script.Parent:WaitForChild("S1TrapRules"))
local WindRules = require(script.Parent:WaitForChild("S1RaiderWindRules"))
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
local lastNet: {[Player]: number} = {}
local netImmuneUntil: {[Player]: number} = {}
local mobCombo: {[Player]: number} = {}
local mobComboUntil: {[Player]: number} = {}
local mobImpactSeq: {[Player]: number} = {}
local mobLastHits: {[Player]: number} = {}
local mobLastKOs: {[Player]: number} = {}
local lastWind: {[Player]: number} = {}
local windUntil: {[Player]: number} = {}
local windHighlight: {[Player]: Instance} = {}
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

-- Only the ORIGINAL Game.server owns the H2 match, egg interactions and scoring.
-- Additional physical eggs/score Parts are children of the existing MapBuilder arena.
local h2ScoreState: any = nil
local h2Eggs: {[string]: any} = {}
local h2Ids: {[Player]: number} = {}
local h2NextId = 0
-- One server owns both game modes. Votes never cause a mid-round toggle.
local modeVotes: {[Player]: string} = {}
local lastModeVote: {[Player]: number} = {}
-- Private Studio session only: no DataStore or reconnect persistence claimed.
local rewardState = RewardRules.new()
local rewardRng = Random.new()
local roundEligible: {[number]: boolean} = {}
local lastFreeHatch: {[Player]: string} = {}
-- Studio QA uses ONLY a dedicated DEV DataStore, never the experience's live profile.
-- A datastore handle does NOT imply Studio API access; GetAsync must succeed first.
local studioHatchStore: any=nil
local hatchSessionGUID=HttpService:GenerateGUID(false)
if RunService:IsStudio() then
    local ok,result=pcall(function()
        return DataStoreService:GetDataStore("EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1")
    end)
    if ok then studioHatchStore=result end
end
local persistenceState: {[Player]: string} = {}
local persistentProfiles: {[Player]: any} = {}
-- Actual ORIGINAL Game holds server-validated action logs, one per match epoch.
local progressionProfile: {[Player]: any}={}
local progressionRound: {[Player]: any}={}
local progressionEvents: {[Player]: {any}}={}
local progressionStatus: {[Player]: string}={}
local progressionLastAward: {[Player]: number}={}
local progressionEventSerial=0
-- Isolated H1: server-side earned power is one state per player/match.
local earnedPower: {[Player]: any} = {}
local earnedPowerVisual: {[Player]: Highlight} = {}
local evolutionPending: {[Player]: boolean} = {}
local guideProgress: {[Player]: any} = {}
local function progressUid(player: Player): number?
    return if player.UserId>0 then PersistentHatch.policyUserId(player.UserId)
        else h2Ids[player]
end
local delayedRestore: {[Player]: boolean} = {}
local outstandingWrites=0
-- Forward-declared view helper: async persistence completion must not call a nil global.
local snapshotFor: (Player) -> any
local function canWriteProfile(player: Player): boolean
    return RunService:IsStudio() and player.UserId>0
        and studioHatchStore~=nil and persistenceState[player]=="SAVED"
end
local function savedEvolutionForm(player: Player): any?
    local raw=persistentProfiles[player]
    if not raw or persistenceState[player]~="SAVED" or player.UserId<=0 then
        return nil
    end
    local evo=PersistentHatch.toEvolutionProfile(raw,player.UserId)
    if not evo then return nil end
    return Evolution.form(evo,raw.equipped,raw.owned)
end
local function restoreSavedProfile(player: Player)
    local profile=persistentProfiles[player]
    local uid=h2Ids[player]
    if not profile or not uid or player.Parent~=Players then return end
    if rewardState.phase~="LOBBY" then
        delayedRestore[player]=true
        return
    end
    local canonical=PersistentHatch.toRulesRecord(profile)
    if canonical==nil then
        persistenceState[player]="SAVE_FAILED"
        return
    end
    local ok=RewardRules.restore(rewardState,uid,canonical)
    if ok then delayedRestore[player]=nil
    else persistenceState[player]="SAVE_FAILED" end
end
-- DataStore UpdateAsync may commit despite a failed caller response.
-- Retry the SAME server-certified immutable receipt, NEVER reroll or change item.
local function commitFreeReward(player: Player,receipt: string,item: string)
    outstandingWrites+=1
    task.spawn(function()
        local waitn=0
        while persistenceState[player]=="LOADING" and waitn<15 do
            task.wait(.25)
            waitn+=.25
        end
        local confirmed=false
        local record=nil
        if canWriteProfile(player) then
            for attempt=1,4 do
                local ok,newProfile=PersistentHatch.grant(
                    studioHatchStore,player.UserId,receipt,item)
                if ok then confirmed=true;record=newProfile;break end
                if attempt<4 then task.wait(attempt*.65) end
            end
        end
        if confirmed and record then
            local prior=persistentProfiles[player]
            if not prior or record.revision>=prior.revision then
                persistentProfiles[player]=record
            end
            persistenceState[player]="SAVED"
            local grantedItem=record.receipts[receipt]
            if grantedItem then lastFreeHatch[player]=grantedItem end
            restoreSavedProfile(player)
        else
            -- Not a saved reward: game still offers LOCAL_ONLY testing,
            -- but UI explicitly warns. Never tell children it is persisted.
            persistenceState[player]="SAVE_FAILED"
            lastFreeHatch[player]=item
            warn("EGG_RUMBLE_REWARD_SAVE_UNCONFIRMED",player.UserId)
        end
        if player.Parent==Players then
            remote:FireClient(player,snapshotFor(player))
        end
        outstandingWrites-=1
    end)
end
local function loadHatchProfile(player: Player)
    persistenceState[player]="LOADING"
    local uid=h2Ids[player]
    task.spawn(function()
        if not RunService:IsStudio() or player.UserId<=0 or not studioHatchStore then
            persistenceState[player]="LOCAL_ONLY"
            progressionStatus[player]="LOCAL_ONLY"
        else
            -- Bypass GetAsync cache where supported. This isolated test store
            -- never shares its namespace with live user data.
            local option=nil
            pcall(function()
                option=DataStoreGetOptions.new()
                option.UseCache=false
            end)
            local ok,profile=PersistentHatch.load(studioHatchStore,player.UserId,option)
            if ok then
                persistentProfiles[player]=profile
                persistenceState[player]="SAVED"
                local progressed=PersistentHatch.toProgressProfile(profile,player.UserId)
                if progressed then
                    progressionProfile[player]=progressed
                    progressionStatus[player]="SAVED"
                end
                restoreSavedProfile(player)
            else
                persistenceState[player]="LOCAL_ONLY"
                progressionStatus[player]="LOCAL_ONLY"
                warn("EGG_RUMBLE_DEV_DATASTORE_LOAD_FAILED_LOCAL_ONLY",player.UserId)
            end
        end
        if player.Parent==Players and h2Ids[player]==uid then
            remote:FireClient(player,snapshotFor(player))
        end
    end)
end
local scoutModels: {[Player]: Model} = {}
-- GUARD forms protect real teammates from actual neutral mob impacts, not PvP.
local evolutionGuards: {[Player]: {untilAt: number,hits: number}} = {}
local scoutActivitySerial: {[Player]: number} = {}
local SCOUT_DURATION=5
local SCOUT_MAX_TEAM=3
local SCOUT_MAX_LOS_DISTANCE=90

local function modeVoteSnapshot()
    local selected,classic,five=ModeVote.tally(modeVotes,Players:GetPlayers())
    return selected,classic,five
end

local function serverNow(): number
    return workspace:GetServerTimeNow()
end
-- #285 policy accepts INTEGER in [0, 1e9]. Workspace serverNow is Unix seconds
-- (>1e9 in 2026), so policy receives trusted elapsed match time, never Unix time.
local function powerSecond(): number
    return math.max(0,math.floor(serverNow()-match.startedAt))
end
local function clearEarnedPowerVisual(player: Player)
    local old=earnedPowerVisual[player]
    earnedPowerVisual[player]=nil
    if old then old:Destroy() end
end
local function earnedDamageMultiplier(player: Player,targetType: string): number
    if not RunService:IsStudio() or match.phase~="ACTIVE"
        or carry[player]~=nil then return 1 end
    local state=earnedPower[player]
    if not state then return 1 end
    local combat=Power.combat(state,targetType,powerSecond())
    if not combat then return 1 end
    -- Additional server clamp protects base Game against malformed state and upgrades.
    return math.clamp(combat.damage,1,if targetType=="MINION" then 3.8 else 1.4)
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

-- ONLY Server Game confirms objective events. Incoming Remote does NOT accept
-- XP values, objective event names, arbitrary timestamps or match receipt IDs.
local function recordServerProgress(player: Player,kind: string)
    if not RunService:IsStudio() or match.phase~="ACTIVE" then return end
    local round=progressionRound[player]
    if not round or round.closed or not progressionEvents[player] then return end
    progressionEventSerial+=1
    local eventId=tostring(match.serial)..":E"..tostring(progressionEventSerial)
    if Progression.recordEvent(round,eventId,kind,true) then
        table.insert(progressionEvents[player],{id=eventId,kind=kind})
        -- Actual committed server objective only: never client-generated tutorial progress.
        First90Guide.mark(guideProgress[player],match.serial,kind,true)
        -- EXACT SAME certified server objective and receipt: no paid/kill/AFK charge.
        local state=earnedPower[player]
        if state then Power.recordObjective(state,eventId,kind,true) end
    end
end
local function beginProgressRounds(mode: string)
    for _,player in ipairs(Players:GetPlayers()) do
        local uid=progressUid(player)
        local localProfile=if uid then progressionProfile[player] else nil
        if uid and not localProfile then
            localProfile=Progression.newProfile(uid)
            progressionProfile[player]=localProfile
        end
        local rewardUid=h2Ids[player]
        local inv=if rewardUid and rewardState.players[rewardUid]
            then RewardRules.export(rewardState,rewardUid) else nil
        local equipped=if inv and inv.equipped and inv.owned[inv.equipped]
            then inv.equipped else nil
        local id=PersistentHatch.makeReceipt(hatchSessionGUID,match.serial)
        if uid and id and getTeamName(player)~="NONE" then
            progressionRound[player]=Progression.newRound(id,uid,mode,
                equipped,equipped~=nil)
            progressionEvents[player]={}
            progressionLastAward[player]=0
            local mastered=if localProfile and localProfile.mastery and equipped
                then localProfile.mastery[equipped] else nil
            local level=if localProfile and type(localProfile.level)=="number"
                then localProfile.level else 1
            local mastery=if mastered and type(mastered.level)=="number"
                then mastered.level else 1
            earnedPower[player]=Power.makeRound(id,uid,level,mastery,
                if mode=="SCORE" then "SCORE_5" else "CLASSIC")
        else
            progressionRound[player]=nil
            progressionEvents[player]=nil
            earnedPower[player]=nil
        end
    end
end
local function settleProgressAtRealEnd(winner: string)
    if not RunService:IsStudio() then return end
    local duration=math.floor(serverNow()-match.startedAt)
    for _,player in ipairs(Players:GetPlayers()) do
        local round=progressionRound[player]
        local profile=progressionProfile[player]
        local events=progressionEvents[player]
        if round and profile and events and getTeamName(player)~="NONE" then
            local outcome=if winner=="DRAW" then "DRAW"
                elseif getTeamName(player)==winner then "WIN" else "LOSS"
            local proposal=Progression.previewXp(round,outcome,duration,true)
            if proposal>0 then
                -- Frozen original round summary; DataStore recomputes reward
                -- from server action LOG within its own pure UpdateAsync callback.
                local immutable={id=round.id,mode=round.mode,
                    itemId=round.equippedItemId,outcome=outcome,
                    duration=duration,events={}}
                for _,ev in ipairs(events) do
                    table.insert(immutable.events,{id=ev.id,kind=ev.kind})
                end
                local reward=Progression.commit(profile,round,outcome,duration,true)
                if reward and reward.grantedXp<=Progression.XP_CAP_PER_ROUND then
                    progressionLastAward[player]=reward.grantedXp
                    progressionStatus[player]="LOCAL_ONLY"
                    if canWriteProfile(player) and player.Parent==Players then
                        progressionStatus[player]="SAVING"
                        outstandingWrites+=1
                        task.spawn(function()
                            local success=false
                            local updated=nil
                            for attempt=1,4 do
                                local good,record=PersistentHatch.settleProgress(
                                    studioHatchStore,player.UserId,immutable)
                                if good then success=true;updated=record;break end
                                if attempt<4 then task.wait(attempt*.65) end
                            end
                            if success and updated and player.Parent==Players then
                                local prior=persistentProfiles[player]
                                if not prior or updated.revision>=prior.revision then
                                    persistentProfiles[player]=updated
                                end
                                local progress=PersistentHatch.toProgressProfile(
                                    persistentProfiles[player],player.UserId)
                                if progress then progressionProfile[player]=progress end
                                progressionStatus[player]="SAVED"
                            elseif player.Parent==Players then
                                progressionStatus[player]="SAVE_FAILED"
                                warn("EGG_RUMBLE_PROGRESS_SAVE_NOT_CONFIRMED",player.UserId)
                            end
                            if player.Parent==Players then
                                remote:FireClient(player,snapshotFor(player))
                            end
                            outstandingWrites-=1
                        end)
                    end
                end
            end
            progressionRound[player]=nil -- match XP is finalized once, not tick-farmed
            progressionEvents[player]=nil
        end
    end
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
    if EXPERIMENTAL_FIVE_EGG_MODE then
        local def=h2Eggs[egg]
        local uid=h2Ids[player]
        if h2ScoreState and uid and h2ScoreState.active then
            H2Score.drop(h2ScoreState,uid)
        end
        carry[player]=nil
        removeCarrierVisual(player)
        if def then
            local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
            local pos=if root and root:IsA("BasePart")
                then Vector3.new(math.clamp(root.Position.X,-116,116),3,
                                 math.clamp(root.Position.Z,-65,65))
                else def.home
            def.part.CFrame=CFrame.new(pos)
            def.part.Transparency=0
            def.prompt.Enabled=match.phase=="ACTIVE" and h2ScoreState~=nil
                and h2ScoreState.active==true
        end
        return
    end
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
-- Wind burst is a mobility-only extension of the SAME server/Remote/seq authority.
local function stopWind(player: Player)
    windUntil[player] = nil
    local old = windHighlight[player]
    windHighlight[player] = nil
    if old then old:Destroy() end
    local alive, _, hum = healthy(player)
    if alive and hum and slowed[player] == nil then
        hum.WalkSpeed = Config.RoleWalkSpeed[roles[player] or "RAIDER"]
    end
end
-- Guardian traps stay inside the EXISTING Game.server round/combat authority.
-- No second Remote, scheduler, damage owner, client position or monetization.
local function restoreSlow(player: Player)
    local record = slowed[player]
    slowed[player] = nil
    -- Early ally/self release must remove the bind outline immediately.
    if record and record.highlight and record.highlight.Parent then
        record.highlight:Destroy()
    end
    if record and record.hum and record.hum.Parent and record.hum.Health > 0 then
        record.hum.WalkSpeed = Config.RoleWalkSpeed[roles[player] or "RAIDER"]
        -- Existing trap records have no jump state; only short NET binds restore it.
        if record.jumpPower ~= nil then record.hum.JumpPower=record.jumpPower end
        if record.jumpHeight ~= nil then record.hum.JumpHeight=record.jumpHeight end
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
                if alive and root and hum
                    and not (slowed[player] and slowed[player].kind=="NET")
                    and TrapRules.shouldTrigger({
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
                        stopWind(player) -- Guardian trap always cancels Raider wind.
                        local current = slowed[player]
                        slowed[player] = {hum = hum,
                            untilAt = math.max(now + TrapRules.SLOW_SECONDS,
                                if current then current.untilAt else 0)}
                        hum.WalkSpeed = slow
                        triggered = player
                        if carry[player]~=nil and rec.owner~=nil then
                            recordServerProgress(rec.owner,"DEFEND")
                        end
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

-- #288 H1 experimental horde is a bounded server-ticked helper, NOT a second Game.
local broadcast: () -> () = function() end -- forward-bound to original sole snapshot publisher
local horde=MusouHorde.new(map.model)
local function hasBoundAllyNearby(player: Player): boolean
    local ok,root=healthy(player)
    if not ok or not root or match.phase~="ACTIVE" then return false end
    local team=getTeamName(player)
    for _,other in ipairs(Players:GetPlayers()) do
        if other~=player and getTeamName(other)==team then
            local rec=slowed[other]
            local targetOk,targetRoot=healthy(other)
            if rec and rec.kind=="NET" and targetOk and targetRoot then
                local delta=targetRoot.Position-root.Position
                if delta.Magnitude<=MusouBind.RESCUE_RANGE then
                    local params=RaycastParams.new()
                    params.FilterType=Enum.RaycastFilterType.Exclude
                    params.FilterDescendantsInstances={player.Character :: Model,horde.folder}
                    local hit=workspace:Raycast(root.Position,delta,params)
                    if hit==nil or (other.Character~=nil
                        and hit.Instance:IsDescendantOf(other.Character)) then
                        return true
                    end
                end
            end
        end
    end
    return false
end
-- No target, position, duration, speed or damage is trusted from the client.
local function applyNet(player: Player,data)
    if not RunService:IsStudio() or type(data)~="table" or data.action~="NET_THROW" then return end
    if not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq
    local now=serverNow()
    local alive,root=healthy(player)
    local team=getTeamName(player)
    if not MusouBind.canNet({
        phase=match.phase,team=team,role=roles[player] or "RAIDER",
        alive=alive,egg=carry[player]~=nil,bound=slowed[player]~=nil,
        now=now,last=lastNet[player] or -math.huge,
    }) or not root then return end
    local nearest=nil
    local best=MusouBind.NET_RANGE+.01
    for _,other in ipairs(Players:GetPlayers()) do
        if other~=player and getTeamName(other)==Rules.opponent(team) then
            local ok,targetRoot=healthy(other)
            if ok and targetRoot then
                local delta=targetRoot.Position-root.Position
                local dist=delta.Magnitude
                local forward=if dist>0.001 then root.CFrame.LookVector:Dot(delta.Unit) else 1
                local visible=false
                if dist<=MusouBind.NET_RANGE then
                    local params=RaycastParams.new()
                    params.FilterType=Enum.RaycastFilterType.Exclude
                    params.FilterDescendantsInstances={player.Character :: Model,horde.folder}
                    local hit=workspace:Raycast(root.Position,delta,params)
                    visible=hit==nil or (other.Character~=nil and hit.Instance:IsDescendantOf(other.Character))
                end
                if dist<best and MusouBind.canTarget({
                    enemy=true,alive=ok,bound=slowed[other]~=nil,
                    immune=now<(netImmuneUntil[other] or 0),
                    invulnerable=now<(invulnUntil[other] or 0),
                    distance=dist,facing=forward,visible=visible,
                }) then nearest=other;best=dist end
            end
        end
    end
    if not nearest then return end
    local targetAlive,_,hum=healthy(nearest)
    if not targetAlive or not hum then return end
    lastNet[player]=now
    stopWind(nearest)
    slowed[nearest]={
        hum=hum,untilAt=now+MusouBind.NET_DURATION,kind="NET",
        startedAt=now,jumpPower=hum.JumpPower,jumpHeight=hum.JumpHeight,
    }
    hum.WalkSpeed=0
    hum.JumpPower=0
    hum.JumpHeight=0
    netImmuneUntil[nearest]=now+MusouBind.NET_DURATION+MusouBind.NET_IMMUNITY
    local glow=Instance.new("Highlight")
    glow.Name="EGG_RUMBLE_VISIBLE_SHORT_NET_BIND"
    glow.FillColor=Color3.fromRGB(123,218,246)
    glow.OutlineColor=Color3.fromRGB(245,246,255)
    glow.FillTransparency=.5
    glow.Parent=nearest.Character
    -- Stored as part of the exact same authoritative movement record.
    -- Debris is only fail-safe for interrupted shutdowns.
    slowed[nearest].highlight=glow
    game:GetService("Debris"):AddItem(glow,MusouBind.NET_DURATION)
    broadcast()
end
local function applyBreakOrRescue(player: Player,data)
    if not RunService:IsStudio() or type(data)~="table" or (data.action~="BREAK_FREE" and data.action~="RESCUE") then return end
    if not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq
    if match.phase~="ACTIVE" then return end
    local now=serverNow()
    if data.action=="BREAK_FREE" then
        if MusouBind.canBreak(slowed[player],now) then
            restoreSlow(player)
            broadcast()
        end
        return
    end
    local alive,root=healthy(player)
    if not alive or not root or slowed[player] then return end
    for _,other in ipairs(Players:GetPlayers()) do
        local rec=slowed[other]
        if other~=player and rec and rec.kind=="NET" then
            local ok,targetRoot=healthy(other)
            if ok and targetRoot then
                local delta=targetRoot.Position-root.Position
                local params=RaycastParams.new()
                params.FilterType=Enum.RaycastFilterType.Exclude
                params.FilterDescendantsInstances={player.Character :: Model,horde.folder}
                local hit=workspace:Raycast(root.Position,delta,params)
                local visible=hit==nil or (other.Character~=nil and hit.Instance:IsDescendantOf(other.Character))
                if MusouBind.canRescue({
                    phase=match.phase,teammate=getTeamName(player)~="NONE"
                        and getTeamName(player)==getTeamName(other),
                    alive=alive,targetBound=true,visible=visible,
                    distance=delta.Magnitude,
                }) then
                    restoreSlow(other)
                    broadcast()
                    return
                end
            end
        end
    end
end

-- Server-only monotonic replication ordinal, never reset on match changes.
local snapshotUpdateId = 0
snapshotFor = function(player: Player)
    snapshotUpdateId += 1
    local now = serverNow()
    local uid=h2Ids[player]
    local inventory=if uid and rewardState.players[uid]
        then RewardRules.export(rewardState,uid) else nil
    local profile=persistentProfiles[player]
    -- Display ONLY acknowledged saved data while persistence says SAVED.
    local owned=if persistenceState[player]=="SAVED" and profile then profile.owned
        else (if inventory then inventory.owned else {})
    local selected=if persistenceState[player]=="SAVED" and profile
        then profile.equipped else (if inventory then inventory.equipped else "starter_scout")
    local stats=if uid then rewardState.players[uid] else nil
    local p=progressionProfile[player]
    local r=progressionRound[player]
    local eliteWarning=if RunService:IsStudio() then horde:eliteWarningSeconds(now) else 0
    local first90=First90Guide.view(match.phase,
        if match.phase=="ACTIVE" then math.max(0,math.floor(now-match.startedAt)) else 0,
        guideProgress[player],{
            mode=if EXPERIMENTAL_FIVE_EGG_MODE then "SCORE_5" else "CLASSIC",
            eliteWarning=eliteWarning,
            bound=slowed[player]~=nil and slowed[player].kind=="NET",
            rescueNearby=hasBoundAllyNearby(player),
            carrying=carry[player]~=nil,
            ownEggSafe=if getTeamName(player)=="RED" or getTeamName(player)=="BLUE"
                then match.eggOwners[getTeamName(player)]==nil else false,
            scoutReady=if stats then stats.activeUntil<=math.floor(now)
                and stats.nextUseAt<=math.floor(now) else false
        })
    local powerState=earnedPower[player]
    local evo=if profile and persistenceState[player]=="SAVED"
        and player.UserId>0 then
        PersistentHatch.toEvolutionProfile(profile,player.UserId) else nil
    local evoForm=if evo and profile
        then Evolution.form(evo,profile.equipped,profile.owned) else nil
    local evoMastery=if profile and profile.progress and profile.progress.mastery
        then profile.progress.mastery[profile.equipped] else nil
    local evoNext=if evo and profile and profile.progress
        then Evolution.nextEvolution(evo,profile.equipped,profile.owned,
            profile.progress.level,if evoMastery then evoMastery.level else 1)
        else nil
    -- The original MapBuilder owns all actual egg/pad parts; the server chooses
    -- ONLY presently eligible eggs or one's real pad. Client cannot choose a
    -- destination or send back a position. 5-egg mode sees only prompt-enabled eggs.
    local first90Target=nil
    if RunService:IsStudio() and first90.visible==true then
        local alive,root=healthy(player)
        local team=getTeamName(player)
        if alive and root and (team=="RED" or team=="BLUE") then
            local origin={x=root.Position.X,y=root.Position.Y,z=root.Position.Z}
            local pad=map.teams[team].scorePad.Position
            local candidates={}
            if first90.step=="PICKUP" then
                if EXPERIMENTAL_FIVE_EGG_MODE then
                    for _,id in ipairs({"N1","R1","B1","R2","B2"}) do
                        local def=h2Eggs[id]
                        if def and def.prompt.Enabled and def.part.Transparency<.9 then
                            local pos=def.part.Position
                            table.insert(candidates,{id=id,owner=def.owner,
                                available=true,x=pos.X,y=pos.Y,z=pos.Z})
                        end
                    end
                else
                    local enemy=Rules.opponent(team)
                    local egg=map.teams[enemy]
                    if egg.eggPrompt.Enabled and egg.egg.Transparency<.9
                        and match.eggOwners[enemy]==nil then
                        local pos=egg.egg.Position
                        table.insert(candidates,{id=if enemy=="RED" then "R1" else "B1",
                            owner=enemy,available=true,x=pos.X,y=pos.Y,z=pos.Z})
                    end
                end
            end
            first90Target=First90Waypoint.select(match.phase,
                math.max(0,math.floor(now-match.startedAt)),
                team,if EXPERIMENTAL_FIVE_EGG_MODE then "SCORE_5" else "CLASSIC",
                first90.step,origin,{x=pad.X,y=pad.Y,z=pad.Z},candidates)
        end
    end
    local masteryItem=if r and type(r.equippedItemId)=="string" then r.equippedItemId
        else selected
    local mastery=if p and p.mastery and p.mastery[masteryItem]
        then p.mastery[masteryItem] else nil
    local seconds = 0
    if match.phase == "ACTIVE" then
        seconds = math.max(0, math.ceil(match.deadline - now))
    elseif match.phase == "COUNTDOWN" or match.phase == "RESULTS" then
        seconds = math.max(0, math.ceil(match.phaseUntil - now))
    end
    return {
        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,
        updateId = snapshotUpdateId, -- view ordering only, not gameplay authority
        time = seconds, scores = {RED = match.scores.RED, BLUE = match.scores.BLUE},
        hp = {RED = match.hp.RED, BLUE = match.hp.BLUE},
        maxHp = Config.CastleMaxHp,
        team = getTeamName(player), role = roles[player] or "RAIDER",
        carrying = if EXPERIMENTAL_FIVE_EGG_MODE and carry[player]~=nil
            then (if carry[player]=="N1" then "NEUTRAL"
                else (if string.sub(carry[player],1,1)=="R" then "RED" else "BLUE"))
            else carry[player] or "",
        eggId = if EXPERIMENTAL_FIVE_EGG_MODE then carry[player] or "" else "",
        scoreMode = if EXPERIMENTAL_FIVE_EGG_MODE then "FIVE_EGG_SCORE" else "ONE_EGG_CAPTURE",
        modeVote = modeVoteSnapshot(), -- first return only: projected choice; read-only
        voteClassic = select(2,modeVoteSnapshot()),
        voteFive = select(3,modeVoteSnapshot()),
        myModeVote = modeVotes[player] or "",
        modeVotingOpen = match.phase=="LOBBY" or match.phase=="COUNTDOWN",
        modeScoreAvailable = RunService:IsStudio(),
        -- View-only bounded collection summary. Clients cannot create grants or change cooldown.
        hatchEnabled = RunService:IsStudio(),
        hatchLast = lastFreeHatch[player] or "",
        hatchOwned = {starter_scout=owned.starter_scout or 0,
            forest_scout=owned.forest_scout or 0,star_scout=owned.star_scout or 0},
        hatchEquipped = selected,
        hatchSaveStatus = persistenceState[player] or "LOCAL_ONLY",
        hatchSaved = persistenceState[player]=="SAVED",
        -- All progression is server authored. Not the #284 simulated preview.
        progressLevel = if p then p.level else 1,
        progressXp = if p then p.xp else 0,
        progressNextXp = if p then Progression.xpToNext(p.level) else 60,
        progressFocus = if r then Progression.focusLevel(r) else 1,
        progressMastery = if mastery then mastery.level else 1,
        progressMasteryXp = if mastery then mastery.xp else 0,
        progressItem = masteryItem or "starter_scout",
        progressLastAward = progressionLastAward[player] or 0,
        progressSaveStatus = progressionStatus[player] or "LOCAL_ONLY",
        -- Read-only earned-power HUD. The client may NOT submit charge,
        -- level, mastery, target choice, timestamp or combat multiplier.
        powerEnabled = RunService:IsStudio() and match.phase=="ACTIVE"
            and powerState~=nil,
        powerLevel = if powerState then powerState.level else 1,
        powerCharge = if powerState then powerState.charge else 0,
        powerReady = if powerState
            then select(1,Power.canAwaken(powerState,powerSecond(),carry[player]~=nil,true))
            else false,
        powerAwakened = if powerState
            then Power.isAwakened(powerState,powerSecond()) else false,
        powerTelegraph = if powerState and powerState.awakeningStartsAt
            then math.max(0,powerState.awakeningStartsAt-powerSecond()) else 0,
        powerSecondsLeft = if powerState and powerState.awakeningEndsAt
            then math.max(0,powerState.awakeningEndsAt-powerSecond()) else 0,
        powerMinionMultiplier = earnedDamageMultiplier(player,"MINION"),
        -- Real canonical DEV DataStore state only. No fake evolution stage.
        evoEnabled = RunService:IsStudio() and evo~=nil,
        evoPending = evolutionPending[player]==true,
        evoStage = if evoForm then evoForm.stage else 0,
        evoBranch = if evoForm then evoForm.branch else "NONE",
        evoFormId = if evoForm then evoForm.formId else "",
        evoFragments = if evo then evo.fragments else 0,
        evoNextStage = if evoNext and not evoNext.complete then evoNext.toStage else 0,
        evoNextCost = if evoNext and not evoNext.complete then evoNext.fragmentCost else 0,
        evoCanUpgrade = evoNext~=nil and evoNext.complete==false
            and evoNext.available==true,
        evoBranchChoice = evoNext~=nil and evoNext.needsChoice==true,
        evoCombatActive = evoForm~=nil and evoForm.stage>=2,
        -- Read-only view; never accepts mob hit or net outcome from the client.
        musouActive = RunService:IsStudio() and match.phase=="ACTIVE",
        musouMobCount = horde:livingCount(),
        musouEliteWarningSeconds = eliteWarning,
        first90 = first90,
        first90Target = first90Target,
        musouCombo = if now<(mobComboUntil[player] or 0) then mobCombo[player] or 0 else 0,
        musouImpactSeq = mobImpactSeq[player] or 0,
        musouLastHits = mobLastHits[player] or 0,
        musouLastKOs = mobLastKOs[player] or 0,
        netBound = slowed[player]~=nil and slowed[player].kind=="NET",
        netRescueNearby = hasBoundAllyNearby(player),
        netCooldown = math.max(0,(lastNet[player] or -math.huge)+MusouBind.NET_COOLDOWN-now),
        scoutCooldown = if stats then math.max(0,math.ceil(stats.nextUseAt-math.floor(now))) else 0,
        scoutActive = if stats then stats.activeUntil>math.floor(now) else false,
        winner = match.winner,
        reason = match.reason, alarm = match.alarm,
        alarmTime = math.max(0, math.ceil(match.alarmUntil - now)),
        redPlayers = teamCount("RED"), bluePlayers = teamCount("BLUE"),
        trapCooldown = math.max(0, math.ceil((lastTrap[player] or -math.huge)
            + TrapRules.COOLDOWN - now)),
        trapRole = (roles[player] or "RAIDER") == "GUARDIAN",
        windCooldown = math.max(0, math.ceil((lastWind[player] or -math.huge)
            + WindRules.COOLDOWN - now)),
        windActive = (windUntil[player] or 0) > now,
    }
end
broadcast = function()
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
        map.teams[name].eggPrompt.Enabled = enabled and
            (if EXPERIMENTAL_FIVE_EGG_MODE then
                h2ScoreState~=nil and h2ScoreState.active and
                h2ScoreState.eggs[if name=="RED" then "R1" else "B1"].state~="CARRIED"
            else match.eggOwners[name] == nil)
        map.teams[name].scorePrompt.Enabled = enabled
    end
    if EXPERIMENTAL_FIVE_EGG_MODE then
        for _,def in pairs(h2Eggs) do
            def.prompt.Enabled=enabled and h2ScoreState~=nil and h2ScoreState.active
                and h2ScoreState.eggs[def.id].state~="CARRIED"
        end
    end
end
-- Free Hatch -> actual BEAST scout thin authoritative server-only adapter.
-- One existing Remote and single original Game owns epoch, eligibility and ability.
local function cleanupScout(player: Player)
    evolutionGuards[player]=nil
    scoutActivitySerial[player]=(scoutActivitySerial[player] or 0)+1
    local old=scoutModels[player]
    scoutModels[player]=nil
    if old then old:Destroy() end
end

local function ownScoutClass(player: Player): string
    -- Current ACTUAL H1 has only RAIDER/GUARDIAN, not all proposed 7 classes.
    return if roles[player]=="GUARDIAN" then "WARRIOR" else "NINJA"
end

local function visibleCarrierTarget(player: Player,root: BasePart): (Vector3?, Model?)
    local own=getTeamName(player)
    for _,other in ipairs(Players:GetPlayers()) do
        if other~=player and carry[other]~=nil and getTeamName(other)~=own then
            local alive,enemyRoot=healthy(other)
            if alive and enemyRoot and
                (enemyRoot.Position-root.Position).Magnitude<=SCOUT_MAX_LOS_DISTANCE then
                local rayParams=RaycastParams.new()
                rayParams.FilterType=Enum.RaycastFilterType.Exclude
                local excluded={player.Character}
                if other.Character then table.insert(excluded,other.Character) end
                rayParams.FilterDescendantsInstances=excluded
                local ray=workspace:Raycast(root.Position,
                    enemyRoot.Position-root.Position,rayParams)
                if ray==nil then return enemyRoot.Position,other.Character end
            end
        end
    end
    return nil,nil
end

local function spawnActualScout(player: Player,token: any)
    -- This private Studio-only ability is REAL 3D replicated Roblox Instances.
    local ok,root=healthy(player)
    local side=getTeamName(player)
    if not RunService:IsStudio() or match.phase~="ACTIVE" or not ok or not root
        or carry[player]~=nil or (side~="RED" and side~="BLUE")
        or token.ability~="SCOUT" or token.duration~=SCOUT_DURATION then return false end
    local teamCountActive=0
    for owner,model in pairs(scoutModels) do
        if owner~=player and model.Parent~=nil and getTeamName(owner)==side then
            teamCountActive+=1
        end
    end
    if teamCountActive>=SCOUT_MAX_TEAM or scoutModels[player]~=nil then return false end
    local model=Instance.new("Model")
    local evolutionForm=savedEvolutionForm(player) -- verified saved and equipped item
    local stage=if evolutionForm then evolutionForm.stage else 0
    local branch=if evolutionForm then evolutionForm.branch else "NONE"
    local scale=if stage>=3 then 1.65 elseif stage>=2 then 1.3
        elseif stage>=1 then 1.12 else 1
    model.Name=if evolutionForm then "EVOLVED_REAL_SCOUT_"..evolutionForm.formId
        else "EGG_RUMBLE_OWNED_REAL_SCOUT"
    local color=if stage>=3 then Color3.fromRGB(255,211,80)
        elseif stage>=2 and branch=="ASSAULT" then Color3.fromRGB(239,91,76)
        elseif stage>=2 and branch=="GUARD" then Color3.fromRGB(89,171,250)
        elseif token.cosmetic=="star" then Color3.fromRGB(255,210,86)
        elseif token.cosmetic=="forest" then Color3.fromRGB(89,230,146)
        else Color3.fromRGB(175,220,250)
    local function piece(name:string,shape:Enum.PartType,size:Vector3,transparency:number): Part
        local part=Instance.new("Part")
        part.Name=name
        part.Shape=shape
        part.Size=size
        part.Anchored=true
        part.CanCollide=false;part.CanTouch=false;part.CanQuery=false
        part.Material=Enum.Material.Neon
        part.Color=color
        part.Transparency=transparency
        part.Parent=model
        return part
    end
    local body=piece("FriendlyScoutBody",Enum.PartType.Ball,Vector3.new(2.7,2.7,2.7)*scale,.1)
    local left=piece("LeftWing",Enum.PartType.Block,Vector3.new(1.8,.35,.95)*scale,.2)
    local right=piece("RightWing",Enum.PartType.Block,Vector3.new(1.8,.35,.95)*scale,.2)
    local eye=piece("ForwardEye",Enum.PartType.Ball,Vector3.new(.7,.7,.7)*scale,0)
    local evolvedAura: Part?=nil
    if stage>=2 then
        evolvedAura=piece(if branch=="GUARD" then "REAL_GUARD_SHIELD"
            else "REAL_ASSAULT_AURA",Enum.PartType.Ball,
            Vector3.new(4.5,4.5,4.5)*scale,.72)
    end
    eye.Color=Color3.fromRGB(255,255,255)
    local beam=piece("LiveEnemyCarrierScanBeam",Enum.PartType.Block,Vector3.new(.16,.16,1),.42)
    model.PrimaryPart=body
    model.Parent=map.model -- server-created and replicated to BOTH clients, never local gallery
    scoutModels[player]=model
    scoutActivitySerial[player]=(scoutActivitySerial[player] or 0)+1
    local generation=scoutActivitySerial[player]
    local epoch=match.serial
    -- The only H1 Game owns both actual abilities; no new Remote or scheduler
    -- beyond the existing timed scout lifecycle.
    if stage>=2 and branch=="GUARD" then
        evolutionGuards[player]={untilAt=serverNow()+SCOUT_DURATION,
            hits=if stage>=3 then 5 else 3}
    end
    task.spawn(function()
        local evolvedStrikeUsed=false -- one meaningful hit per authorized 5sec scout token
        local highlighted: Highlight?=nil
        local t=0
        while t<SCOUT_DURATION and scoutModels[player]==model
            and scoutActivitySerial[player]==generation and match.phase=="ACTIVE"
            and match.serial==epoch and player.Parent==Players do
            local alive,currentRoot=healthy(player)
            if not alive or not currentRoot then break end
            local anchor=currentRoot.Position+Vector3.new(0,4.5,0)
                +currentRoot.CFrame.LookVector*3.5
            body.CFrame=CFrame.new(anchor)
            left.CFrame=body.CFrame*CFrame.new(-1.7*scale,.1,0)
            right.CFrame=body.CFrame*CFrame.new(1.7*scale,.1,0)
            eye.CFrame=body.CFrame*CFrame.new(0,0,-1.25*scale)
            if evolvedAura then evolvedAura.CFrame=body.CFrame end
            if stage>=2 and branch=="ASSAULT" and not evolvedStrikeUsed then
                -- Existing server horde:hit authority, PvE ONLY. Do not stack
                -- permanent evolution with #285 PvP multiplier or award kill XP.
                local hits=horde:hit(currentRoot.Position,currentRoot.CFrame.LookVector,
                    if stage>=3 then 40 else 26,serverNow(),player.Character)
                if hits>0 then
                    evolvedStrikeUsed=true
                    mobImpactSeq[player]=(mobImpactSeq[player] or 0)+1
                    mobLastHits[player]=hits
                    mobLastKOs[player]=0
                end
            end
            local target,character=visibleCarrierTarget(player,currentRoot)
            if target and character then
                if highlighted and highlighted.Adornee~=character then highlighted:Destroy();highlighted=nil end
                if not highlighted then
                    highlighted=Instance.new("Highlight")
                    highlighted.Name="SCOUT_ENEMY_CARRIER_ALERT"
                    highlighted.DepthMode=Enum.HighlightDepthMode.Occluded -- walls/cover counter the scan
                    highlighted.FillTransparency=.72
                    highlighted.OutlineTransparency=.1
                    highlighted.FillColor=color
                    highlighted.OutlineColor=color
                    highlighted.Adornee=character
                    highlighted.Parent=model
                end
                local delta=target-anchor
                local dist=delta.Magnitude
                beam.Transparency=if dist<.2 then 1 else .42
                if dist>=.2 then
                    beam.Size=Vector3.new(.16,.16,dist)
                    beam.CFrame=CFrame.lookAt((anchor+target)*.5,target)
                end
            else
                if highlighted then highlighted:Destroy();highlighted=nil end
                beam.Transparency=1
            end
            task.wait(.2);t+=.2
        end
        if scoutModels[player]==model and scoutActivitySerial[player]==generation then
            cleanupScout(player)
        elseif model.Parent~=nil then model:Destroy() end
    end)
    return true
end

local function giveFreeHatchAtRealEnd()
    if not RunService:IsStudio() then return end
    local eligible={}
    local rare={}
    for _,player in ipairs(Players:GetPlayers()) do
        local uid=h2Ids[player]
        if uid and roundEligible[uid] and getTeamName(player)~="NONE" then
            eligible[uid]=true
            -- Only contested NEUTRAL egg held by THIS server at buzzer qualifies.
            rare[uid]=EXPERIMENTAL_FIVE_EGG_MODE and carry[player]=="N1" or false
        end
    end
    local ok=RewardRules.finishRound(rewardState,match.serial,eligible,rare)
    if not ok then warn("EGG_RUMBLE_HATCH_ISSUER_DENIED_ROUND");return end
    for _,player in ipairs(Players:GetPlayers()) do
        local uid=h2Ids[player]
        if uid and eligible[uid] then
            local granted,item,status=RewardRules.claimFreeHatch(rewardState,
                uid,match.serial,rewardRng:NextInteger(1,10000))
            if granted and status=="GRANTED" then
                local receipt=PersistentHatch.makeReceipt(hatchSessionGUID,match.serial)
                if receipt then
                    if persistenceState[player]=="SAVED" or persistenceState[player]=="LOADING" then
                        commitFreeReward(player,receipt,item)
                    else
                        lastFreeHatch[player]=item -- LOCAL_ONLY explicitly shown
                    end
                else
                    persistenceState[player]="SAVE_FAILED"
                end
            end
        end
    end
end

local function applyEquipScout(player: Player,data:any)
    if type(data)~="table" or data.action~="EQUIP_SCOUT" then return end
    if not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq
    local item=data.itemId
    local uid=h2Ids[player]
    if not RunService:IsStudio() or not uid or type(item)~="string"
        or #item>32 or match.phase~="LOBBY"
        or getTeamName(player)=="NONE" then return end
    local inv=RewardRules.export(rewardState,uid)
    if inv==nil or not inv.owned[item] then return end
    if persistenceState[player]=="LOADING" then return end
    if canWriteProfile(player) then
        outstandingWrites+=1
        task.spawn(function()
            local confirmed,profile=PersistentHatch.equip(studioHatchStore,player.UserId,item)
            if confirmed then
                local prior=persistentProfiles[player]
                if not prior or profile.revision>=prior.revision then
                    persistentProfiles[player]=profile
                end
                restoreSavedProfile(player)
            else
                persistenceState[player]="SAVE_FAILED"
                warn("EGG_RUMBLE_EQUIP_SAVE_UNCONFIRMED",player.UserId)
            end
            outstandingWrites-=1
            if player.Parent==Players then remote:FireClient(player,snapshotFor(player)) end
        end)
    else
        local ok=RewardRules.equip(rewardState,uid,item,ownScoutClass(player))
        if ok then remote:FireClient(player,snapshotFor(player)) end
    end
end

local function applyActualScout(player: Player,data:any)
    if type(data)~="table" or data.action~="ACTIVATE_SCOUT" then return end
    if not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq
    local uid=h2Ids[player]
    local alive=healthy(player)
    if not RunService:IsStudio() or match.phase~="ACTIVE" or not uid
        or not alive or carry[player]~=nil
        or getTeamName(player)=="NONE" or scoutModels[player]~=nil then return end
    local teamScouts=0
    for other,model in pairs(scoutModels) do
        if model.Parent~=nil and getTeamName(other)==getTeamName(player) then teamScouts+=1 end
    end
    if teamScouts>=SCOUT_MAX_TEAM then return end
    local granted,token=RewardRules.requestScout(rewardState,
        uid,match.serial,math.floor(serverNow()))
    if not granted then return end
    if spawnActualScout(player,token) then
        First90Guide.mark(guideProgress[player],match.serial,"SCOUT",true)
        recordServerProgress(player,"EQUIP_USE")
        broadcast()
    end
end

local function stopRound(winner: string, reason: string)
    if match.phase ~= "ACTIVE" then return end
    stopCanonical("ROUND_END")
    settleProgressAtRealEnd(winner)
    giveFreeHatchAtRealEnd() -- before any server egg owner drop/cleanup
    for _,p in ipairs(Players:GetPlayers()) do cleanupScout(p) end
    match.phase = "RESULTS"
    match.phaseUntil = serverNow() + Config.ResultsSeconds
    match.winner = winner
    match.reason = reason
    match.alarm = "IDLE"
    match.alarmUntil = 0
    setObjectiveEnabled(false)
    clearTraps()
    horde:clear()
    for _, p in ipairs(Players:GetPlayers()) do
        stopWind(p)
        dropEgg(p)
        local state=earnedPower[p]
        if state then Power.endRound(state) end
        clearEarnedPowerVisual(p)
    end
    broadcast()
end
local function resetRound()
    stopCanonical("ROUND_RESET")
    clearTraps()
    match.serial += 1
    if RunService:IsStudio() then
        for _,p in ipairs(Players:GetPlayers()) do
            if delayedRestore[p] then restoreSavedProfile(p) end
        end
        local started=RewardRules.startRound(rewardState,match.serial)
        assert(started,"EGG_RUMBLE_REWARD_ROUND_DOUBLE_START")
        table.clear(roundEligible)
        for _,p in ipairs(Players:GetPlayers()) do
            local uid=h2Ids[p]
            if uid and getTeamName(p)~="NONE" then roundEligible[uid]=true end
            cleanupScout(p)
        end
    end
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
        stopWind(p)
        dropEgg(p)
        local state=earnedPower[p]
        if state then Power.endRound(state) end
        earnedPower[p]=nil
        clearEarnedPowerVisual(p)
        lastAttack[p] = -math.huge
        lastTrap[p] = -math.huge
        lastWind[p] = -math.huge
        lastNet[p] = -math.huge
        netImmuneUntil[p] = 0
        mobCombo[p] = 0
        mobComboUntil[p] = 0
        mobLastHits[p] = 0
        mobLastKOs[p] = 0
        guideProgress[p] = First90Guide.newRound(match.serial)
        -- Player seq stays monotonic across round transitions; never rewind replay ceiling.
        p:LoadCharacter()
    end
    -- All previous epoch egg carriers were cleaned above while OLD mode was active.
    -- Freeze only here at match start; never re-evaluate score policy in ACTIVE.
    local chosenMode=ModeVote.tally(modeVotes,Players:GetPlayers())
    EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE
    if RunService:IsStudio() then
        beginProgressRounds(if EXPERIMENTAL_FIVE_EGG_MODE then "SCORE" else "CLASSIC")
    end
    h2ScoreState=if EXPERIMENTAL_FIVE_EGG_MODE then H2Score.new() else nil
    for _, team in ipairs({"RED", "BLUE"}) do resetEgg(team) end
    for _,def in pairs(h2Eggs) do
        def.part.CFrame=CFrame.new(def.home)
        def.part.Transparency=if (def.id=="R1" or def.id=="B1")
            or EXPERIMENTAL_FIVE_EGG_MODE then 0 else 1
        def.prompt.Enabled=false
    end
    if EXPERIMENTAL_FIVE_EGG_MODE then
        match.deadline=match.startedAt+H2Score.LENGTH_SECONDS
    end
    setObjectiveEnabled(true)
    -- This private H1 has 8 cheap server-driven neutral enemies + 1 telegraphed elite.
    if RunService:IsStudio() then horde:reset(match.serial,serverNow()) end
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
        stopWind(player) -- no burst survives respawn or a new Humanoid
        local role = roles[player] or "RAIDER"
        hum.MaxHealth = Config.RoleHealth[role]
        hum.Health = hum.MaxHealth
        hum.WalkSpeed = Config.RoleWalkSpeed[role]
        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability
        hum.Died:Connect(function()
            stopWind(player)
            restoreSlow(player)
            dropEgg(player)
            invulnUntil[player] = 0
        end)
    end
end

-- EGG RAID RUMBLE experiment: replace only the original egg prompt behavior
-- while keeping ORIGINAL S1 combat, Guardian traps, Raider wind, teams and Remote.
local function createFiveEggs()
    -- One map is shared by both modes. Additional three eggs exist only in
    -- local Studio but remain hidden/disabled when Classic is selected.
    if not RunService:IsStudio() then return end
    local extras={
        R2={owner="RED",home=Vector3.new(-98,2.5,20)},
        B2={owner="BLUE",home=Vector3.new(98,2.5,20)},
        N1={owner="NEUTRAL",home=Vector3.new(0,3,0)}
    }
    h2Eggs.R1={id="R1",owner="RED",
        part=map.teams.RED.egg,prompt=map.teams.RED.eggPrompt,
        home=map.teams.RED.egg.Position}
    h2Eggs.B1={id="B1",owner="BLUE",
        part=map.teams.BLUE.egg,prompt=map.teams.BLUE.eggPrompt,
        home=map.teams.BLUE.egg.Position}
    for id,data in pairs(extras) do
        local egg=Instance.new("Part")
        egg.Name="H2_REAL_SCORE_EGG_"..id
        egg.Shape=Enum.PartType.Ball
        egg.Size=Vector3.new(3,3.6,3)
        egg.Material=Enum.Material.Neon
        egg.Color=if data.owner=="RED" then Color3.fromRGB(255,98,114)
            elseif data.owner=="BLUE" then Color3.fromRGB(88,163,255)
            else Color3.fromRGB(255,221,95)
        egg.Anchored=true;egg.CanCollide=false;egg.CanTouch=false
        egg.Transparency=1
        egg.Position=data.home
        egg.Parent=map.model
        local prompt=Instance.new("ProximityPrompt")
        prompt.Name="H2_SERVER_AUTH_EGG_"..id
        prompt.ActionText="卵を拾う"
        prompt.ObjectText="🥚 "..id
        prompt.MaxActivationDistance=Config.InteractDistance
        prompt.HoldDuration=.12
        prompt.RequiresLineOfSight=false
        prompt.Enabled=false;prompt.Parent=egg
        h2Eggs[id]={id=id,owner=data.owner,part=egg,prompt=prompt,home=data.home}
    end
    for id,def in pairs(h2Eggs) do
        def.prompt.ObjectText="🥚 "..id.." "..def.owner
    end
end

local function pickupFiveEgg(player:Player,id:string)
    if not EXPERIMENTAL_FIVE_EGG_MODE or match.phase~="ACTIVE"
        or h2ScoreState==nil or h2ScoreState.active~=true then return end
    local def=h2Eggs[id];local uid=h2Ids[player]
    if not def or not uid or not def.prompt.Enabled or carry[player]~=nil then return end
    local alive=healthy(player)
    local side=getTeamName(player)
    if not alive or (side~="RED" and side~="BLUE")
        or not within(player,def.part.Position,Config.InteractDistance) then return end
    local success=H2Score.pickup(h2ScoreState,id,uid,side)
    if not success then return end
    stopWind(player)
    carry[player]=id
    def.part.Transparency=1;def.prompt.Enabled=false
    giveEggVisual(player)
    recordServerProgress(player,"PICKUP")
    broadcast()
end

local function depositFiveEgg(player:Player,side:string)
    if not EXPERIMENTAL_FIVE_EGG_MODE or match.phase~="ACTIVE"
        or h2ScoreState==nil or h2ScoreState.active~=true then return end
    local uid=h2Ids[player]
    local eggId=carry[player]
    if not uid or not eggId or getTeamName(player)~=side
        or not healthy(player)
        or not within(player,map.teams[side].scorePad.Position,Config.InteractDistance) then return end
    local ok=H2Score.deposit(h2ScoreState,uid,side)
    if not ok then return end
    local def=h2Eggs[eggId]
    carry[player]=nil
    removeCarrierVisual(player)
    local pad=map.teams[side].scorePad
    local index=if eggId=="R1" or eggId=="B1" then -2
        elseif eggId=="R2" or eggId=="B2" then 2 else 0
    def.part.CFrame=CFrame.new(pad.Position+Vector3.new(index,4,0))
    def.part.Transparency=0
    def.prompt.Enabled=true
    match.scores.RED=h2ScoreState.scores.RED
    match.scores.BLUE=h2ScoreState.scores.BLUE
    recordServerProgress(player,"DEPOSIT")
    broadcast()
end

createFiveEggs()
if RunService:IsStudio() then
    for _,id in ipairs({"R2","B2","N1"}) do
        h2Eggs[id].prompt.Triggered:Connect(function(player:Player)
            pickupFiveEgg(player,id)
        end)
    end
end

for _, team in ipairs({"RED", "BLUE"}) do
    map.teams[team].eggPrompt.Triggered:Connect(function(player: Player)
        if EXPERIMENTAL_FIVE_EGG_MODE then
            pickupFiveEgg(player,if team=="RED" then "R1" else "B1")
            return
        end
        local thiefTeam = getTeamName(player)
        local alive = healthy(player)
        local free = match.eggOwners[team] == nil
        if not Rules.canSteal(match.phase, thiefTeam, team,
            if within(player, map.teams[team].egg.Position, Config.InteractDistance)
                then 0 else 1e8, alive, carry[player] ~= nil, free,
            Config.InteractDistance) then return end
        stopWind(player) -- cannot carry an egg at burst speed
        match.eggOwners[team] = player
        carry[player] = team
        map.teams[team].egg.Transparency = 1
        map.teams[team].eggPrompt.Enabled = false
        giveEggVisual(player)
        recordServerProgress(player,"PICKUP")
        broadcast()
    end)
    map.teams[team].scorePrompt.Triggered:Connect(function(player: Player)
        if EXPERIMENTAL_FIVE_EGG_MODE then
            depositFiveEgg(player,team)
            return
        end
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
        recordServerProgress(player,"DEPOSIT")
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
    local mobHits=0
    -- Original ATTACK cooldown/seq/phase also gates PvE. No second Remote or damage event.
    if RunService:IsStudio() then
        local touched,defeated = horde:hit(root.Position,look,
            Config.CombatDamage[roles[player] or "RAIDER"]
                *earnedDamageMultiplier(player,"MINION"),now,player.Character)
        mobHits=touched
        if touched>0 then
            mobCombo[player]=if now<(mobComboUntil[player] or 0)
                then math.min(99,(mobCombo[player] or 0)+touched) else touched
            mobComboUntil[player]=now+2.4
            First90Guide.mark(guideProgress[player],match.serial,"HIT",true)
            mobImpactSeq[player]=(mobImpactSeq[player] or 0)+1
            mobLastHits[player]=touched
            mobLastKOs[player]=defeated
        end
    end
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
        if ok and hum then
            hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"]
                *earnedDamageMultiplier(player,"PLAYER"))
        end
        return
    end
    -- Cannot hit castle with the same swing after hitting neutral soldiers.
    if mobHits>0 then return end
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
    local winner = if EXPERIMENTAL_FIVE_EGG_MODE then nil
        else Rules.winner(match.scores, match.hp, Config.CapturesToWin)
    if winner then stopRound(winner, "CASTLE_DESTROYED") else broadcast() end
end

-- H1 RAIDER wind: server accepts intent only, never client position or speed.
local function applyWind(player: Player, data)
    if type(data) ~= "table" or data.action ~= "WIND_BURST" then return end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq -- consume all replayed and rejected intents
    local team = getTeamName(player)
    local alive, root, hum = healthy(player)
    if not alive or not root or not hum then return end
    local now = serverNow()
    if not WindRules.canActivate({
        phase = match.phase, team = team, role = roles[player] or "RAIDER",
        alive = alive, carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil,
        active = (windUntil[player] or 0) > now, now = now,
        lastAt = lastWind[player] or -math.huge,
        x = root.Position.X, y = root.Position.Y, z = root.Position.Z,
    }) then return end
    stopWind(player)
    lastWind[player] = now
    windUntil[player] = now + WindRules.DURATION
    hum.WalkSpeed = WindRules.SPEED
    -- Obvious warning to opposing Guardians: flank sprint is NOT stealth/invulnerability.
    local glow = Instance.new("Highlight")
    glow.Name = "S1_RAIDER_WIND_SERVER_TELL"
    glow.FillColor = Color3.fromRGB(98, 208, 255)
    glow.OutlineColor = Color3.fromRGB(247, 251, 255)
    glow.FillTransparency = 0.45
    glow.OutlineTransparency = 0.1
    glow.DepthMode = Enum.HighlightDepthMode.Occluded
    glow.Parent = player.Character
    windHighlight[player] = glow
    broadcast()
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
    stopWind(player)
    roles[player] = role
    remote:FireClient(player, snapshotFor(player))
end

-- One original Game and Remote own awakening; Lv10, 80 earned objective charge,
-- once/round, 2-sec visible tell, 8-sec window, no awakening while carrying.
local function applyEarnedAwaken(player: Player,data)
    if type(data)~="table" or data.action~="AWAKEN_POWER" then return end
    if not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq
    local ok,_,hum=healthy(player)
    if not RunService:IsStudio() or match.phase~="ACTIVE" or not ok or not hum
        or getTeamName(player)=="NONE" or slowed[player]~=nil then return end
    local state=earnedPower[player]
    if not state then return end
    local accepted=Power.beginAwaken(state,powerSecond(),carry[player]~=nil,true)
    if not accepted then return end
    clearEarnedPowerVisual(player)
    local character=player.Character
    if character then
        local fx=Instance.new("Highlight")
        fx.Name="P0D_EarnedAwakenTell"
        fx.Adornee=character
        fx.DepthMode=Enum.HighlightDepthMode.Occluded
        fx.FillColor=Color3.fromRGB(255,142,50)
        fx.OutlineColor=Color3.fromRGB(255,232,80)
        fx.FillTransparency=.45
        fx.OutlineTransparency=.10
        fx.Parent=character
        earnedPowerVisual[player]=fx
    end
    broadcast()
end

local function applyEvolveScout(player: Player,data)
    if type(data)~="table" or data.action~="EVOLVE_SCOUT" then return end
    if not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq
    if not RunService:IsStudio() or match.phase~="LOBBY"
        or evolutionPending[player]==true or not canWriteProfile(player)
        or getTeamName(player)=="NONE" then return end
    -- Client chooses only a branch for the equipped item. No item/level/shard,
    -- receipt, target, stat, XP, or damage is accepted from client.
    local choice=data.role
    if choice~="NONE" and choice~="ASSAULT" and choice~="GUARD" then return end
    local raw=persistentProfiles[player]
    local evo=if raw then PersistentHatch.toEvolutionProfile(raw,player.UserId) else nil
    local mastery=if raw and raw.progress and raw.progress.mastery
        then raw.progress.mastery[raw.equipped] else nil
    local nextStage=if evo and raw and raw.progress
        then Evolution.nextEvolution(evo,raw.equipped,raw.owned,
            raw.progress.level,if mastery then mastery.level else 1) else nil
    if not nextStage or nextStage.complete==true
        or nextStage.available~=true
        or (nextStage.needsChoice and choice=="NONE")
        or (not nextStage.needsChoice and choice~="NONE") then return end
    local requestId="E"..HttpService:GenerateGUID(false)
    evolutionPending[player]=true
    outstandingWrites+=1
    task.spawn(function()
        local success=false
        local updated=nil
        for attempt=1,3 do
            local ok,record=PersistentHatch.evolve(studioHatchStore,
                player.UserId,requestId,choice)
            if ok then success=true;updated=record;break end
            if attempt<3 then task.wait(attempt*.5) end
        end
        if player.Parent==Players then
            if success and updated then
                local prior=persistentProfiles[player]
                if not prior or updated.revision>=prior.revision then
                    persistentProfiles[player]=updated
                end
                persistenceState[player]="SAVED"
            else
                persistenceState[player]="SAVE_FAILED"
                warn("P0D_EVOLUTION_SAVE_UNCONFIRMED",player.UserId)
            end
            evolutionPending[player]=nil
            broadcast()
        end
        outstandingWrites-=1
    end)
end

local function applyModeVote(player: Player,data)
    if type(data)~="table" or data.action~="MODE_VOTE" then return end
    if not Rules.validSeq(data.seq,lastSeq[player] or 0) then return end
    lastSeq[player]=data.seq -- consume invalid/replayed vote intents as all other actions
    local now=serverNow()
    if getTeamName(player)=="NONE"
        or not ModeVote.canVote(match.phase,data.mode,RunService:IsStudio(),
            now,lastModeVote[player] or -math.huge) then return end
    lastModeVote[player]=now
    if modeVotes[player]~=data.mode then
        modeVotes[player]=data.mode
        broadcast()
    end
end

remote.OnServerEvent:Connect(function(player: Player, data)
    if type(data) ~= "table" then return end
    if data.action == "ATTACK" then applyAttack(player, data)
    elseif data.action == "ROLE" then applyRole(player, data)
    elseif data.action == "PLACE_TRAP" then placeTrap(player, data)
    elseif data.action == "WIND_BURST" then applyWind(player, data)
    elseif data.action == "MODE_VOTE" then applyModeVote(player,data)
    elseif data.action == "EQUIP_SCOUT" then applyEquipScout(player,data)
    elseif data.action == "ACTIVATE_SCOUT" then applyActualScout(player,data)
    elseif data.action == "NET_THROW" then applyNet(player,data)
    elseif data.action == "AWAKEN_POWER" then applyEarnedAwaken(player,data)
    elseif data.action == "EVOLVE_SCOUT" then applyEvolveScout(player,data)
    elseif data.action == "BREAK_FREE" or data.action == "RESCUE" then
        applyBreakOrRescue(player,data)
    end
end)

local function onJoin(player: Player)
    chooseTeam(player)
    modeVotes[player]=nil
    lastModeVote[player]=-math.huge
    if RunService:IsStudio() then
        h2NextId+=1
        h2Ids[player]=h2NextId -- positive server ID, Studio fake UserIds can be negative
        assert(RewardRules.enroll(rewardState,h2NextId),"EGG_RUMBLE_FREE_STARTER_ENROLL_FAILED")
        progressionProfile[player]=Progression.newProfile(progressUid(player) or h2NextId)
        progressionStatus[player]="LOADING"
        loadHatchProfile(player)
    end
    roles[player] = "RAIDER"
    lastSeq[player] = 0
    lastAttack[player] = -math.huge
    lastRoleChange[player] = -math.huge
    lastTrap[player] = -math.huge
    lastWind[player] = -math.huge
    lastNet[player] = -math.huge
    netImmuneUntil[player] = 0
    mobCombo[player] = 0
    mobComboUntil[player] = 0
    mobImpactSeq[player] = 0
    mobLastHits[player] = 0
    mobLastKOs[player] = 0
    invulnUntil[player] = 0
    player.CharacterAdded:Connect(function(character)
        clearEarnedPowerVisual(player)
        cleanupScout(player)
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
    cleanupScout(player)
    lastFreeHatch[player]=nil
    persistenceState[player]=nil
    persistentProfiles[player]=nil
    delayedRestore[player]=nil
    progressionProfile[player]=nil
    progressionRound[player]=nil
    progressionEvents[player]=nil
    progressionStatus[player]=nil
    progressionLastAward[player]=nil
    evolutionPending[player]=nil
    guideProgress[player]=nil
    local state=earnedPower[player]
    if state then Power.endRound(state) end
    earnedPower[player]=nil
    clearEarnedPowerVisual(player)
    h2Ids[player]=nil
    modeVotes[player]=nil
    lastModeVote[player]=nil
    stopWind(player)
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
    lastWind[player] = nil
    lastNet[player] = nil
    netImmuneUntil[player] = nil
    mobCombo[player] = nil
    mobComboUntil[player] = nil
    mobImpactSeq[player] = nil
    mobLastHits[player] = nil
    mobLastKOs[player] = nil
    windUntil[player] = nil
    windHighlight[player] = nil
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
    -- Reuse the sole 0.5-second Game tick for visible/counterable awakening.
    for player,fx in pairs(earnedPowerVisual) do
        local state=earnedPower[player]
        if not state or match.phase~="ACTIVE" or fx.Parent==nil
            or (state.awakeningEndsAt and powerSecond()>=state.awakeningEndsAt) then
            clearEarnedPowerVisual(player)
        elseif Power.isAwakened(state,powerSecond()) then
            fx.FillColor=Color3.fromRGB(255,232,45)
            fx.OutlineColor=Color3.fromRGB(255,255,214)
        end
    end
    -- Existing server tick is the sole PvE attack authority; no extra game loop.
    if RunService:IsStudio() and match.phase=="ACTIVE" then
        for _,impact in ipairs(horde:tick(now,Players:GetPlayers(),healthy)) do
            local victim=impact.player
            local ok,victimRoot,hum=healthy(victim)
            if ok and hum and victimRoot and now>=(invulnUntil[victim] or 0) then
                local blocked=false
                for owner,shield in pairs(evolutionGuards) do
                    local ownerOk,ownerRoot=healthy(owner)
                    if ownerOk and ownerRoot
                        and shield.hits>0 and now<shield.untilAt
                        and getTeamName(owner)==getTeamName(victim)
                        and (victimRoot.Position-ownerRoot.Position).Magnitude<=13 then
                        shield.hits-=1
                        blocked=true
                        break
                    end
                end
                if not blocked then hum:TakeDamage(impact.damage) end
            end
        end
    end
    -- Clean up boosts through the ONLY existing authoritative 0.5-second tick.
    for player, untilAt in pairs(windUntil) do
        local alive = healthy(player)
        if match.phase ~= "ACTIVE" or not alive or now >= untilAt
            or carry[player] ~= nil or slowed[player] ~= nil then
            stopWind(player)
        end
    end
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
        if EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState and h2ScoreState.active then
            local desired=math.clamp(math.floor(now-match.startedAt),0,H2Score.LENGTH_SECONDS)
            local backlog=math.min(math.max(desired-h2ScoreState.now,0),10)
            for _=1,backlog do H2Score.advance(h2ScoreState,1) end
            assert(H2Score.assertConserved(h2ScoreState),"H2_REAL_H1_FIVE_EGG_INTEGRITY")
            match.scores.RED=h2ScoreState.scores.RED
            match.scores.BLUE=h2ScoreState.scores.BLUE
        end
        if teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")
        elseif teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")
        elseif EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState
            and h2ScoreState.active==false then
            stopRound(h2ScoreState.winner,"FIVE_EGG_SCORE_240S")
        elseif now >= match.deadline then
            local red=if EXPERIMENTAL_FIVE_EGG_MODE then match.scores.RED
                else match.scores.RED*1000+match.hp.RED
            local blue=if EXPERIMENTAL_FIVE_EGG_MODE then match.scores.BLUE
                else match.scores.BLUE*1000+match.hp.BLUE
            stopRound(if red==blue then "DRAW" else (if red>blue then "RED" else "BLUE"),
                if EXPERIMENTAL_FIVE_EGG_MODE then "FIVE_EGG_TIME_LIMIT" else "TIME_LIMIT")
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
            -- New match / new vote; previous result never silently dictates next match.
            table.clear(modeVotes)
            table.clear(lastModeVote)
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
                    stopWind(player)
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

-- Do not pretend UpdateAsync is instant. Hold a bounded shutdown grace for
-- already-started grants; the Studio API can still fail or time out, and the
-- HUD must never assert a durable save without an acknowledged write.
game:BindToClose(function()
    local started=os.clock()
    while outstandingWrites>0 and os.clock()-started<23 do
        task.wait(.25)
    end
    if outstandingWrites>0 then
        warn("EGG_RUMBLE_PENDING_HATCH_SAVE_NOT_CONFIRMED",outstandingWrites)
    end
end)
