#!/usr/bin/env python3
"""Deterministic exact-anchor source patch of ONE real H1 Game controller.

H0 default OFF preserves original 1-egg event/round controls; private H2 ON
uses original Game and its SINGLE existing S1 Remote. Never patch official RC.
"""
from __future__ import annotations
import hashlib,re
SOURCE_SHA="adecfee41a594bdd54393050b4890a5733a536ce"

def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def once(s,old,new,what):
    matches=s.count(old)
    if matches!=1:
        raise RuntimeError("H2_GAME_PATCH_NON_UNIQUE_"+what+" count="+str(matches))
    return s.replace(old,new,1)

def inject(original:bytes,enable:bool):
    if blob(original)!=SOURCE_SHA:
        raise RuntimeError("NOT_ORIGINAL_SINGLE_GAME_SOURCE_"+blob(original))
    s=original.decode("utf-8")
    assert s.count('remote.Name = "TrapRaidersS1Remote"')==1
    mode="true" if enable else "false"
    s=once(s,
      'local Players = game:GetService("Players")\n',
      'local Players = game:GetService("Players")\n'
      'local H2_SCORE_MODE = game:GetService("RunService"):IsStudio() and '+mode+
      ' -- PRIVATE experiment; never LIVE\n'
      'local H2ScoreIntegration = if H2_SCORE_MODE then '
      'require(script.Parent:WaitForChild("H2ScoreIntegration")) else nil\n',
      "single_server_head")
    s=once(s,
      'local carryVisuals: {[Player]: Instance} = {}\n',
      'local carryVisuals: {[Player]: Instance} = {}\n'
      'local h2Mode: any = nil -- initialized AFTER original Game closure helpers\n',
      "h2_mode_local")
    s=once(s,
      '    carry[player] = nil\n'
      '    removeCarrierVisual(player)\n'
      '    if match.eggOwners[egg] == player then resetEgg(egg) end\n',
      '    carry[player] = nil\n'
      '    removeCarrierVisual(player)\n'
      '    if h2Mode then h2Mode.onDrop(player) end -- after old carry cleared\n'
      '    if match.eggOwners[egg] == player then resetEgg(egg) end\n',
      "single_original_drop_safe_sync")
    s=once(s,
      '    return {\n'
      '        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,',
      '    local snapshot = {\n'
      '        kind = "SNAPSHOT", serial = match.serial, phase = match.phase,',
      "snapshot_existing_packet")
    s=once(s,
      '        windActive = (windUntil[player] or 0) > now,\n'
      '    }\n'
      'end\n'
      'local function broadcast()',
      '        windActive = (windUntil[player] or 0) > now,\n'
      '    }\n'
      '    if h2Mode then\n'
      '        local scoreInfo = h2Mode.snapshot(player)\n'
      '        for k,v in pairs(scoreInfo) do snapshot[k] = v end\n'
      '        if type(scoreInfo.scoreTime) == "number" then\n'
      '            snapshot.time = scoreInfo.scoreTime\n'
      '        end\n'
      '    end\n'
      '    return snapshot\n'
      'end\n'
      'local function broadcast()',
      "snapshot_H2_only_addition")
    s=once(s,
      'local function setObjectiveEnabled(enabled: boolean)\n',
      'local function setObjectiveEnabled(enabled: boolean)\n'
      '    if h2Mode then h2Mode.enable(enabled); return end\n',
      "old_one_egg_objectives_gate")
    s=once(s,
      '    match.deadline = match.startedAt + Config.MatchSeconds\n',
      '    match.deadline = match.startedAt + '
      '(if h2Mode then 270 else Config.MatchSeconds)\n',
      "score_mode_timewindow_240_plus30")
    s=once(s,
      '    for _, team in ipairs({"RED", "BLUE"}) do resetEgg(team) end\n'
      '    setObjectiveEnabled(true)\n',
      '    for _, team in ipairs({"RED", "BLUE"}) do resetEgg(team) end\n'
      '    if h2Mode then h2Mode.reset(match.serial,Players:GetPlayers()) end\n'
      '    setObjectiveEnabled(true)\n',
      "single_H2_reset")
    # Existing Game initialization and handlers are the ONLY match authority.
    s=once(s,
      'for _, team in ipairs({"RED", "BLUE"}) do\n'
      '    map.teams[team].eggPrompt.Triggered:Connect',
      'if H2_SCORE_MODE and H2ScoreIntegration then\n'
      '    h2Mode = H2ScoreIntegration.new({\n'
      '        map = map,\n'
      '        distance = Config.InteractDistance,\n'
      '        onPick = function(player: Player,eggId: string)\n'
      '            stopWind(player)\n'
      '            carry[player] = eggId\n'
      '            giveEggVisual(player)\n'
      '        end,\n'
      '        onDeposit = function(player: Player,_eggId: string)\n'
      '            carry[player] = nil\n'
      '            removeCarrierVisual(player)\n'
      '        end,\n'
      '        onForcedDrop = function(player: Player)\n'
      '            carry[player] = nil\n'
      '            removeCarrierVisual(player)\n'
      '        end,\n'
      '        onScores = function(scores)\n'
      '            match.scores.RED = scores.RED\n'
      '            match.scores.BLUE = scores.BLUE\n'
      '        end,\n'
      '        broadcast = broadcast,\n'
      '    })\n'
      'end\n'
      'for _, team in ipairs({"RED", "BLUE"}) do\n'
      '    map.teams[team].eggPrompt.Triggered:Connect',
      "H2_adaptor_init_single_S1_owner")
    s=once(s,
      '    map.teams[team].eggPrompt.Triggered:Connect(function(player: Player)\n'
      '        local thiefTeam = getTeamName(player)\n',
      '    map.teams[team].eggPrompt.Triggered:Connect(function(player: Player)\n'
      '        if h2Mode then return end -- H2 prompt exclusively owned by score adapter\n'
      '        local thiefTeam = getTeamName(player)\n',
      "disable_old_pickup_in_H2")
    s=once(s,
      '    map.teams[team].scorePrompt.Triggered:Connect(function(player: Player)\n'
      '        local alive = healthy(player)\n',
      '    map.teams[team].scorePrompt.Triggered:Connect(function(player: Player)\n'
      '        if h2Mode then return end -- H2 score delivery exclusively authoritative\n'
      '        local alive = healthy(player)\n',
      "disable_old_1egg_scoring_in_H2")
    # Exact two winner call sites: original 1egg old handler (skips H2),
    # original combat HP winner (H2 regulation point mode supersedes).
    winner='local winner = Rules.winner(match.scores, match.hp, Config.CapturesToWin)'
    if s.count(winner)!=2:
        raise RuntimeError("GAME_WINNER_SOURCE_CALL_COUNT_CHANGED_"+str(s.count(winner)))
    s=s.replace(winner,
       'local winner = if h2Mode then nil else '
       'Rules.winner(match.scores, match.hp, Config.CapturesToWin)')
    s=once(s,
      '        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability\n',
      '        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability\n'
      '        if h2Mode then h2Mode.onRespawn(player) end\n',
      "restore_respawn_score_player")
    s=once(s,
      '    invulnUntil[player] = 0\n'
      '    player.CharacterAdded:Connect',
      '    invulnUntil[player] = 0\n'
      '    if h2Mode then h2Mode.onJoin(player) end\n'
      '    player.CharacterAdded:Connect',
      "dynamic_join_during_active")
    s=once(s,
      '        elseif now >= match.deadline then\n'
      '            local red = match.scores.RED * 1000 + match.hp.RED\n',
      '        elseif h2Mode then\n'
      '            local result = h2Mode.tick(math.floor(now-match.startedAt))\n'
      '            if result then stopRound(result.winner,"H2_SCORE_"..result.reason) end\n'
      '        elseif now >= match.deadline then\n'
      '            local red = match.scores.RED * 1000 + match.hp.RED\n',
      "one_Game_time_drives_H2")
    assert s.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert s.count("H2ScoreIntegration.new(")==1
    assert s.count("h2Mode.tick(")==1
    assert s.count("if h2Mode then return end")==2
    assert s.count("Rules.winner(match.scores, match.hp, Config.CapturesToWin)")==2
    assert 'H2_SCORE_MODE = game:GetService("RunService"):IsStudio() and '+mode in s
    assert "CANONICAL_S1_ENABLED = false" in s and "D07_D08_RELEASE_REVIEW_APPROVED = false" in s
    return s.encode("utf-8")
