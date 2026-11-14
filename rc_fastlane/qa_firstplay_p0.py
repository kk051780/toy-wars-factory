#!/usr/bin/env python3
"""P0D private73 combined first-play P0/P1 source QA fixes.

This file modifies ONLY private assembled Game & private SoloTeamBots source.
Five original art Luau, LobbyDojoIsland and the 66 original source inputs remain
byte-exact; the authored upstream patch/module originals remain pinned in
features/firstplay73. No official RC/main write or public publish.
"""
from __future__ import annotations
import re

def one(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, ("FIRSTPLAY_P0_REPAIR_ANCHOR_CHANGED", old[:95], text.count(old))
    return text.replace(old,new,1)

def in_region(text: str, start: str, end: str, edit) -> str:
    assert text.count(start)==1,("FIRSTPLAY_START_DRIFT",start)
    i=text.index(start)
    j=text.index(end,i)
    part=edit(text[i:j])
    return text[:i]+part+text[j:]


def patch_game(text: str) -> str:
    assert "P0D_LateJoinSpectator" not in text, "FIRSTPLAY_QA_DUPLICATE"

    # Studio joins during an ACTIVE/COUNTDOWN game are non-combat spectators.
    # Team nil avoids altering teamCount, score, egg, attack and match winner.
    # Initialization still runs (profile, connections, seq), unlike early return.
    text=in_region(text,"local function onJoin(player: Player)",
        "Players.PlayerAdded:Connect(onJoin)",
        lambda block: one(block,"    chooseTeam(player)\n",
            """    chooseTeam(player)
    if RunService:IsStudio() and
        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then
        player.Team=nil
        player.Neutral=true
        player:SetAttribute("P0D_LateJoinSpectator",true)
    end
"""))

    # Spawn a late joiner in the physical lobby, not the active battlefield.
    # Keeping Team nil makes him/her ineligible for fight and egg transactions.
    text=in_region(text,"local function assignSpawn(player: Player, character: Model)",
        "-- EGG RAID RUMBLE",
        lambda block: one(block,
            """                else map.teams[team].spawn + Vector3.new(0, 2, 0)
        end""",
            """                else map.teams[team].spawn + Vector3.new(0, 2, 0)
        elseif RunService:IsStudio()
            and player:GetAttribute("P0D_LateJoinSpectator")==true then
            root.CFrame=LobbyIsland.spawn("RED")
        end"""))

    # Original LobbyTeamRecovery can physically move rebalance candidates to
    # old battlefield spawns while phase still LOBBY. Keep them on lobby pads.
    text=in_region(text,"local function rebalanceLobbyTeams()",
        "local function assignSpawn(",
        lambda block: one(block,
          "root.CFrame = map.teams[move.to].spawn + Vector3.new(0, 2, 0)",
          """root.CFrame = if RunService:IsStudio()
                    then LobbyIsland.spawn(move.to)
                    else map.teams[move.to].spawn + Vector3.new(0, 2, 0)"""))

    # ONE non-authoritative lobby recovery scheduler shared by RESULTS and
    # neutral late-join promotion. Roblox default CharacterAutoLoads gets its
    # full RespawnTime grace before manual fallback. Original Character identity
    # is captured, so an in-progress engine CharacterAdded wins and prevents a
    # second manual load. Failures retry at most twice, with a cap and guards.
    # No new server loop, datastore, combat state, or second Game authority.
    recovery = """-- FB006: shared guarded post-results lobby character recovery.
local lobbyRecoveryPending: {[Player]: boolean} = {}
local function scheduleLobbyRecovery(player: Player)
    if lobbyRecoveryPending[player] or player.Parent~=Players
        or match.phase~="LOBBY" then return end
    lobbyRecoveryPending[player]=true
    local originalCharacter=player.Character
    local grace=if Players.CharacterAutoLoads
        then math.max(3,(Players.RespawnTime or 5)+2) else 0.1
    local attempt
    attempt=function(number: number)
        if player.Parent~=Players or match.phase~="LOBBY"
            or player.Character~=originalCharacter then
            lobbyRecoveryPending[player]=nil
            return
        end
        local alreadyAlive=healthy(player)
        if alreadyAlive then
            lobbyRecoveryPending[player]=nil
            return
        end
        local ok,err=pcall(function() player:LoadCharacter() end)
        if ok then
            lobbyRecoveryPending[player]=nil
        elseif number < 3 then
            -- Bounded recovery from transient LoadCharacter failures.
            warn("P0D_LOBBY_RESPAWN_RETRY",number,err)
            task.delay(2,function() attempt(number+1) end)
        else
            lobbyRecoveryPending[player]=nil
            warn("P0D_LOBBY_RESPAWN_FAILED",err)
        end
    end
    task.delay(grace,function() attempt(1) end)
end

"""
    assert text.count('local function tickRound()')==1
    text=text.replace('local function tickRound()',recovery+'local function tickRound()',1)

    # At NEXT lobby, promote neutral spectators to balanced team and stay in lobby
    # with default readiness FALSE. No spectator can join an active roster.
    text=in_region(text,"local function tickRound()",
        "elseif match.phase == \"COUNTDOWN\" then",
        lambda block: one(block,
            """if match.phase == "LOBBY" then
        rebalanceLobbyTeams()""",
            """if match.phase == "LOBBY" then
        if RunService:IsStudio() then
            for _,entrant in ipairs(Players:GetPlayers()) do
                if entrant:GetAttribute("P0D_LateJoinSpectator")==true then
                    entrant:SetAttribute("P0D_LateJoinSpectator",nil)
                    chooseTeam(entrant)
                    readyForMatch[entrant]=false
                    local ok,root=healthy(entrant)
                    if ok and root then
                        root.CFrame=LobbyIsland.spawn(getTeamName(entrant))
                    else
                        scheduleLobbyRecovery(entrant)
                    end
                end
            end
        end
        rebalanceLobbyTeams()"""))

    # Only react to missing/failed bots when the active match is a Solo bot
    # match. Ensure engine errors and soft stop from player-count gates never
    # strand a human in empty ACTIVE gameplay.
    text=in_region(text,"local function tickRound()",
        "Players.PlayerAdded:Connect(" if False else "elseif match.phase == \"RESULTS\" then",
        lambda block: one(block,
            """            if not ok then
                warn("FB005_SOLO_TICK_FAIL_CLOSED",err)
                SoloTeamBots.stop()
            end""",
            """            if not ok or (studioSoloRoundStarted and match.phase=="ACTIVE"
                and not SoloTeamBots.isActive()) then
                warn("FB005_SOLO_TICK_FAIL_CLOSED",err)
                SoloTeamBots.stop()
                if studioSoloRoundStarted and match.phase=="ACTIVE" then
                    stopRound("DRAW","SOLO_BOTS_RUNTIME_FAILURE")
                end
            end"""))

    # Consent / input integrity: COUNTDOWN must support cancellation, while
    # an ignored READY input during ACTIVE/RESULTS must never consume the
    # same monotonic seq used by ATTACK/TRAP/MAGIC in this sole original Game.
    text=in_region(text,
        "local function toggleMatchReady(player: Player, data)",
        "remote.OnServerEvent:Connect(",
        lambda block: one(block,
            """    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq
    if match.phase ~= "LOBBY" then return end
    local side = getTeamName(player)
    if side ~= "RED" and side ~= "BLUE" then return end
    readyForMatch[player] = not (readyForMatch[player] == true)
    broadcast()""",
            """    if match.phase ~= "LOBBY" and match.phase ~= "COUNTDOWN" then
        return
    end
    local side = getTeamName(player)
    if side ~= "RED" and side ~= "BLUE" then return end
    if match.phase=="COUNTDOWN" and readyForMatch[player]~=true then
        return
    end
    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end
    lastSeq[player] = data.seq
    if match.phase=="COUNTDOWN" then
        -- Explicit last-second revoke, with immediate peer notification.
        readyForMatch[player]=false
        match.phase="LOBBY"
        match.phaseUntil=0
        broadcast()
        return
    end
    readyForMatch[player] = not (readyForMatch[player] == true)
    broadcast()"""))
    assert 'match.phase=="COUNTDOWN" and readyForMatch[player]~=true' in text
    assert 'match.phaseUntil=0' in text

    # Results -> lobby recovers defeated players, too: the original lobby
    # adapter teleports healthy characters but silently skips dead players.
    # Schedule a guarded re-characterization after state is LOBBY, not while
    # the results screen is active. Any Roblox auto-respawn wins the race safely.
    text=in_region(text,
        'elseif match.phase == "RESULTS" then',
        '-- Recovery uses the existing server-only authoritative tick',
        lambda block: one(block,
            """                        root.CFrame=LobbyIsland.spawn(team)
                    end""",
            """                        root.CFrame=LobbyIsland.spawn(team)
                    elseif (team=="RED" or team=="BLUE"
                        or p:GetAttribute("P0D_LateJoinSpectator")==true)
                        and p.Parent==Players then
                        scheduleLobbyRecovery(p)
                    end"""))
    assert text.count('P0D_LOBBY_RESPAWN_FAILED')==1
    assert text.count('scheduleLobbyRecovery(p)')==1
    assert text.count('scheduleLobbyRecovery(entrant)')==1

    # One definition of eligible humans across mode voting, HUD and startup.
    # Late-join spectators do not turn a solo match into a 2-player match.
    text=one(text,
        'local readyForMatch: {[Player]: boolean} = {}',
        '''local readyForMatch: {[Player]: boolean} = {}
local function eligibleSoloPlayers(): {Player}
    local result: {Player} = {}
    for _,candidate in ipairs(Players:GetPlayers()) do
        local team=candidate.Team
        if candidate:GetAttribute("P0D_LateJoinSpectator")~=true
            and team and (team.Name=="RED" or team.Name=="BLUE") then
            table.insert(result,candidate)
        end
    end
    return result
end''')

    # Exact authored deferred bot start expects one participant, not one
    # connection; a neutral spectator should not silently suppress bots.
    def fix_reset(block: str) -> str:
        sentinel='if match.phase=="ACTIVE" and #Players:GetPlayers()==1 then'
        assert block.count(sentinel)==1, ("SOLO_START_ELIGIBLE_DRIFT",block.count(sentinel))
        block=one(block,sentinel,
                  'if match.phase=="ACTIVE" and #eligibleSoloPlayers()==1 then')
        block=one(block,'local player=Players:GetPlayers()[1]',
                  'local player=eligibleSoloPlayers()[1]')
        sentinel='and #Players:GetPlayers()==1 then'
        assert block.count(sentinel)==1, ("SOLO_FAILURE_ELIGIBLE_DRIFT",block.count(sentinel))
        block=one(block,sentinel,'and #eligibleSoloPlayers()==1 then')
        return block
    text=in_region(text,'local function resetRound()',
                   'local function chooseTeam(',fix_reset)

    # H2 mode has different live score/egg ownership. Do NOT reinterpret its
    # progress as Classic mid-round. Draw immediately on one-person leave,
    # require the survivor to opt-in again at the next lobby.
    text=in_region(text,'Players.PlayerRemoving:Connect(function(player)',
                   'local function tickRound()',
        lambda block: one(block,
            '    if match.phase == "ACTIVE" and side ~= "NONE" then',
            '''    if RunService:IsStudio() and match.phase=="ACTIVE"
        and EXPERIMENTAL_FIVE_EGG_MODE then
        local survivors=0
        for _,remaining in ipairs(eligibleSoloPlayers()) do
            if remaining~=player then survivors+=1 end
        end
        if survivors==1 then
            stopRound("DRAW","SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY")
        end
    end
    if match.phase == "ACTIVE" and side ~= "NONE" then'''))
    assert text.count('SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY')==1

    # Studio solo bot AI only knows ORIGINAL CLASSIC two-egg rules.
    # A SCORE/FIVE_EGG mode vote with one actual player would otherwise
    # start a 15min match without any Bot.start() (guarded from SCORE mode).
    # Single Studio players always receive the working Classic solo variant;
    # preserve legitimate SCORE vote and Game scoring for >=2 people.
    text=one(text,
        'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE',
        '''EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio()
        and #eligibleSoloPlayers()>1 and chosenMode==ModeVote.SCORE''')
    assert text.count('#eligibleSoloPlayers()>1 and chosenMode==ModeVote.SCORE')==1
    # Explain this constraint in the existing LOBBY HUD via SNAPSHOT, not
    # by inventing new message authority or multiplying overlay labels.
    text=one(text,
        'ready = readyForMatch[player] == true,',
        '''ready = readyForMatch[player] == true,
        soloFiveEggUnavailable = RunService:IsStudio()
            and #eligibleSoloPlayers()==1,''')
    assert text.count('soloFiveEggUnavailable = RunService:IsStudio()')==1
    assert 'if match.phase=="ACTIVE" and #eligibleSoloPlayers()==1 then' in text
    assert 'and #eligibleSoloPlayers()==1 then' in text
    assert 'local player=eligibleSoloPlayers()[1]' in text

    # Critical lobby-to-battle proof: original resetRound loads every human
    # AFTER phase ACTIVE, CharacterAdded calls assignSpawn(ACTIVE => battle).
    text_start=text.index("local function resetRound()")
    text_end=text.index("local function chooseTeam(",text_start)
    body=text[text_start:text_end]
    assert 'match.phase = "ACTIVE"' in body
    assert "p:LoadCharacter()" in body
    assert body.index('match.phase = "ACTIVE"') < body.index("p:LoadCharacter()")
    spawn=text[text.index("local function assignSpawn("):
               text.index("-- EGG RAID RUMBLE",text.index("local function assignSpawn("))]
    assert 'match.phase~="ACTIVE"' in spawn
    assert "else map.teams[team].spawn + Vector3.new(0, 2, 0)" in spawn
    assert text.count("remote.OnServerEvent:Connect(")==1
    assert text.count("local function tickRound()")==1
    assert text.count('P0D_LateJoinSpectator')>=4
    return text


def patch_bot(text: str) -> str:
    assert "P0D_LateJoinSpectator" not in text, "FIRSTPLAY_BOT_QA_DUPLICATE"
    # Bot.start must use the same legitimate participant predicate as
    # Game's solo mode selection and deferred start; observers can join while
    # the Game's task.defer is pending.
    text=one(text,
        'if not RunService:IsStudio() or #Players:GetPlayers()~=1 then return false end',
        '''if not RunService:IsStudio() then return false end
    local eligible=0
    for _,p in ipairs(Players:GetPlayers()) do
        local team=p.Team
        if p:GetAttribute("P0D_LateJoinSpectator")~=true
            and team and (team.Name=="RED" or team.Name=="BLUE") then
            eligible+=1
        end
    end
    if eligible~=1 then return false end''')
    # A second real Player may join the Studio server as a *noncombat*
    # spectator; it must not disable the five bots in the active solo match.
    text=one(text,
        "if #Players:GetPlayers()~=1 then Bot.stop();return end",
        """local eligible=0
    for _,p in ipairs(Players:GetPlayers()) do
        local team=p.Team
        if p:GetAttribute("P0D_LateJoinSpectator")~=true
            and team and (team.Name=="RED" or team.Name=="BLUE") then
            eligible+=1
        end
    end
    if eligible~=1 then Bot.stop();return end""")
    text=one(text,
        "if team~=bot.team and root and hum and hum.Health>0 then",
        """if p:GetAttribute("P0D_LateJoinSpectator")~=true
            and team~=bot.team and root and hum and hum.Health>0 then""")

    # Hit only when FIRST raycast target is the actual bot; do not exclude all
    # bots from collision line-of-sight. A wall or another bot blocks the hit.
    text=one(text,
        "params.FilterDescendantsInstances={bot.model,folder,attackerCharacter}",
        "params.FilterDescendantsInstances={attackerCharacter}")
    text=one(text,
        "if not hit then\n                    best=bot",
        "if hit and hit.Instance:IsDescendantOf(bot.model) then\n                    best=bot")
    assert 'params.FilterDescendantsInstances={attackerCharacter}' in text

    # ComputeAsync may yield indefinitely; old task is invalidated after 8sec,
    # bounded concurrently to <=10 outstanding tasks to avoid task leaks.
    # Each old returned callback carries epoch+generation to prevent stale
    # routes overriding a new goal/respawn or releasing a fresh planner.
    text=one(text,
        "local TICK_MIN=.35",
        "local TICK_MIN=.35\nlocal PATH_TIMEOUT_SECONDS=8\nlocal MAX_INFLIGHT_PATHS=10\nlocal inflightPaths=0")
    text=one(text,
        "nextRepath=0,path={},pathIndex=1,planning=false,",
        "nextRepath=0,path={},pathIndex=1,planning=false,planningSince=0,")
    text=one(text,
        """    if bot.planning or now<bot.nextRepath then return end
    bot.nextRepath=now+REPATH_SECONDS""",
        """    if bot.planning and now-(bot.planningSince or now)>PATH_TIMEOUT_SECONDS then
        invalidatePath(bot)
        -- Exponential resource cost is avoided via bounded in-flight workers.
        bot.nextRepath=now+REPATH_SECONDS
    end
    if bot.planning or now<bot.nextRepath
        or inflightPaths>=MAX_INFLIGHT_PATHS then return end
    bot.planningSince=now
    inflightPaths+=1
    bot.nextRepath=now+REPATH_SECONDS""")
    text=one(text,
        """        -- Both the global match and this particular bot/goal must still be""",
        """        inflightPaths=math.max(0,inflightPaths-1)
        -- Both the global match and this particular bot/goal must still be""")
    # A direct MoveTo cannot get across a blocked castle/bridge. When the
    # actual bot has made <3.5 studs progress for 5 seconds while trying to
    # move, invalidate the current/stale path, jump and issue one small
    # alternating lateral detour. Never teleport or invent egg/damage state.
    # This stays inside the same bot intent engine and uses existing scheduler.
    text=one(text,
        "lastAttack=0,lastGoal=nil,pathGeneration=0}",
        """lastAttack=0,lastGoal=nil,pathGeneration=0,
        lastProgressPos=nil,lastProgressAt=0,unstuckAttempts=0}""")
    text=one(text,
        """    if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then
        invalidatePath(bot)
    end
    bot.lastGoal=goal
    pathTo(bot,goal,now)""",
        """    if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then
        invalidatePath(bot)
        bot.lastProgressPos=bot.root.Position
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    end
    bot.lastGoal=goal
    local position=bot.root.Position
    if bot.lastProgressPos==nil then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
    elseif (position-bot.lastProgressPos).Magnitude>=3.5 then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    elseif now-bot.lastProgressAt>=5 then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
        bot.unstuckAttempts=((bot.unstuckAttempts or 0)%4)+1
        -- End any stalled ComputeAsync candidate; it may finish too late.
        invalidatePath(bot)
        -- invalidatePath clears lastGoal for stale async callbacks; restore
        -- the same valid target so retry counts and alternating sides persist.
        bot.lastGoal=goal
        local side=if bot.unstuckAttempts%2==0 then -1 else 1
        local toGoal=goal-position
        local lateral=Vector3.new(-toGoal.Z,0,toGoal.X)
        local detour=if lateral.Magnitude>.2 then
            lateral.Unit*(side*7) else Vector3.new(side*7,0,0)
        bot.hum.Jump=true
        bot.hum:MoveTo(position+detour)
        return
    end
    pathTo(bot,goal,now)""")
    # REVIEW #400: 8 source QA issues. Make the detour persistent for
    # 2.6 seconds, detect *toward-egg* progress in XZ only, and never push an
    # arrived bot away. Keep logical path leases separate from real outstanding
    # ComputeAsync workers (which Roblox cannot cancel).
    text=one(text,
        "local inflightPaths=0",
        """local inflightPaths=0
local MAX_PENDING_PATH_TASKS=10
local pendingPathTasks=0""")
    text=one(text,
        """lastProgressPos=nil,lastProgressAt=0,unstuckAttempts=0}""",
        """lastProgressDistance=nil,lastProgressAt=0,unstuckAttempts=0,
        detourGoal=nil,detourUntil=0,pathLease=nil}""")
    text=one(text,
        "local function invalidatePath(bot)",
        """-- Logical slot released at invalidation, never double-released by
-- a late ComputeAsync completion. The raw worker count stays bounded until
-- Roblox actually resumes its blocking computation.
local function releasePathLease(bot)
    local lease=bot.pathLease
    if lease and lease.held then
        lease.held=false
        inflightPaths=math.max(0,inflightPaths-1)
    end
    bot.pathLease=nil
end
local function invalidatePath(bot)""")
    text=one(text,
        """local function invalidatePath(bot)
    -- PathfindingService:ComputeAsync yields; old callbacks must never claim""",
        """local function invalidatePath(bot)
    releasePathLease(bot)
    -- PathfindingService:ComputeAsync yields; old callbacks must never claim""")
    text=one(text,
        """local function respawn(bot)
    local nextGeneration=bot.pathGeneration+1""",
        """local function respawn(bot)
    releasePathLease(bot)
    local nextGeneration=bot.pathGeneration+1""")
    text=one(text,
        """    for _,bot in ipairs(bots) do
        clearCarry(bot)""",
        """    for _,bot in ipairs(bots) do
        releasePathLease(bot)
        clearCarry(bot)""")
    text=one(text,
        """        invalidatePath(bot)
        -- Exponential resource cost is avoided via bounded in-flight workers.
        bot.nextRepath=now+REPATH_SECONDS""",
        """        invalidatePath(bot)
        bot.lastGoal=goal
        -- Exponential resource cost is avoided via bounded in-flight workers.
        bot.nextRepath=now+REPATH_SECONDS""")
    text=one(text,
        """    if bot.planning or now<bot.nextRepath
        or inflightPaths>=MAX_INFLIGHT_PATHS then return end
    bot.planningSince=now
    inflightPaths+=1
    bot.nextRepath=now+REPATH_SECONDS""",
        """    if bot.planning or now<bot.nextRepath
        or inflightPaths>=MAX_INFLIGHT_PATHS
        or pendingPathTasks>=MAX_PENDING_PATH_TASKS then return end
    bot.planningSince=now
    local lease={held=true}
    bot.pathLease=lease
    inflightPaths+=1
    pendingPathTasks+=1
    bot.nextRepath=now+REPATH_SECONDS""")
    text=one(text,
        """        inflightPaths=math.max(0,inflightPaths-1)
        -- Both the global match and this particular bot/goal must still be""",
        """        pendingPathTasks=math.max(0,pendingPathTasks-1)
        if lease.held then
            lease.held=false
            inflightPaths=math.max(0,inflightPaths-1)
        end
        if bot.pathLease==lease then bot.pathLease=nil end
        -- Both the global match and this particular bot/goal must still be""")
    text=one(text,
        """    if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then
        invalidatePath(bot)
        bot.lastProgressPos=bot.root.Position
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    end
    bot.lastGoal=goal
    local position=bot.root.Position
    if bot.lastProgressPos==nil then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
    elseif (position-bot.lastProgressPos).Magnitude>=3.5 then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    elseif now-bot.lastProgressAt>=5 then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
        bot.unstuckAttempts=((bot.unstuckAttempts or 0)%4)+1
        -- End any stalled ComputeAsync candidate; it may finish too late.
        invalidatePath(bot)
        -- invalidatePath clears lastGoal for stale async callbacks; restore
        -- the same valid target so retry counts and alternating sides persist.
        bot.lastGoal=goal
        local side=if bot.unstuckAttempts%2==0 then -1 else 1
        local toGoal=goal-position
        local lateral=Vector3.new(-toGoal.Z,0,toGoal.X)
        local detour=if lateral.Magnitude>.2 then
            lateral.Unit*(side*7) else Vector3.new(side*7,0,0)
        bot.hum.Jump=true
        bot.hum:MoveTo(position+detour)
        return
    end
    pathTo(bot,goal,now)""",
        """    if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then
        invalidatePath(bot)
        bot.detourGoal=nil
        bot.detourUntil=0
        bot.lastProgressDistance=nil
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    end
    bot.lastGoal=goal
    local position=bot.root.Position
    local flatDistance=Vector3.new(position.X-goal.X,0,position.Z-goal.Z).Magnitude
    -- Guard stationary defenders already at their intended position.
    if flatDistance<=4.5 then
        bot.detourGoal=nil
        bot.detourUntil=0
        bot.lastProgressDistance=flatDistance
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
        bot.hum:MoveTo(position)
        return
    end
    -- A sidestep must not be overwritten on the very next 0.5s tick.
    -- Hold it until within 2.5stud or max 2.6s; no teleport is permitted.
    if bot.detourGoal then
        local gap=Vector3.new(position.X-bot.detourGoal.X,0,
            position.Z-bot.detourGoal.Z).Magnitude
        if now<bot.detourUntil and gap>2.5 then
            bot.hum:MoveTo(bot.detourGoal)
            return
        end
        bot.detourGoal=nil
        bot.detourUntil=0
    end
    if bot.lastProgressDistance==nil
        or flatDistance<=bot.lastProgressDistance-2.5 then
        bot.lastProgressDistance=flatDistance
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    elseif now-bot.lastProgressAt>=5 then
        bot.lastProgressDistance=flatDistance
        bot.lastProgressAt=now
        bot.unstuckAttempts=((bot.unstuckAttempts or 0)%4)+1
        -- Revoke stale async output; preserve the destination and attempts.
        invalidatePath(bot)
        bot.lastGoal=goal
        local side=if bot.unstuckAttempts%2==0 then -1 else 1
        local toGoal=goal-position
        local lateral=Vector3.new(-toGoal.Z,0,toGoal.X)
        local detour=if lateral.Magnitude>.2 then
            lateral.Unit*(side*7) else Vector3.new(side*7,0,0)
        bot.detourGoal=position+detour
        bot.detourUntil=now+2.6
        bot.hum.Jump=true
        bot.hum:MoveTo(bot.detourGoal)
        return
    end
    pathTo(bot,goal,now)""")
    assert 'MAX_PENDING_PATH_TASKS=10' in text
    assert 'releasePathLease(bot)' in text
    assert 'now<bot.detourUntil and gap>2.5' in text
    assert 'flatDistance<=4.5 then' in text
    assert 'flatDistance<=bot.lastProgressDistance-2.5' in text
    assert 'bot.hum:MoveTo(bot.detourGoal)' in text
    assert "if eligible~=1 then Bot.stop();return end" in text
    assert "if eligible~=1 then return false end" in text
    assert text.count("local team=p.Team")>=2
    assert text.count("MAX_INFLIGHT_PATHS")>=2
    return text

def patch_hud(text: str) -> str:
    # The start button cannot be hidden during countdown because the user
    # must be able to revoke a READY even after countdown begins.
    text=one(text,
        """    readyButton.Visible = s.phase == "LOBBY"
    readyButton.Text = if s.ready == true then "✓ 準備解除" else "▶ 出撃する" """.rstrip(),
        """    readyButton.Visible = s.phase == "LOBBY"
        or (s.phase == "COUNTDOWN" and s.ready == true)
    readyButton.Text = if s.phase == "COUNTDOWN" then "✕ 出撃中止"
        elseif s.ready == true then "✓ 準備解除" else "▶ 出撃する" """.rstrip())
    text=one(text,
        '    lobbyHelp.Visible = s.phase == "LOBBY"',
        '''    lobbyHelp.Visible = s.phase == "LOBBY"
    if s.soloFiveEggUnavailable == true then
        lobbyHelp.Text = "1人は通常卵モード（味方2/敵3のAI参戦）\\n5個卵モードは2人以上で有効"
    else
        lobbyHelp.Text = "敵城の卵を奪って自城へ！ または敵城を破壊！\\n攻撃：F／タップ　罠：T　ロビーで職業選択"
    end''')
    return text
