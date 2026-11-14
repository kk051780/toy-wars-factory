#!/usr/bin/env python3
"""Backport the source-authored #397 H2/late spectator safety into full #396 PRIVATE78.

This optional A-PREP adds no feature, only repairs existing Game and
SoloTeamBots. Source locks and prior #396 Game are required; official RC66,
other 76 scripts and existing private parent remain untouched.
"""
from __future__ import annotations
import argparse,json,os,shutil,tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,BASE_RC

GAME="server/Game.server.luau"
BOT="server/SoloTeamBots.luau"
FIX="FB005_PRIVATE78_SPECTATOR_H2_ROSTER_QA_V1"
H2_REASON="SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY"
AUTHOR=397

def once(s:str,a:str,b:str)->str:
    assert s.count(a)==1,("SPECTATOR_SOURCE_DRIFT",a[:95],s.count(a))
    return s.replace(a,b,1)

def region(s:str,start:str,end:str,fn)->str:
    assert s.count(start)==1,("MISSING_OR_DUP_START",start,s.count(start))
    a,b=s.split(start,1)
    assert b.count(end)>=1,("MISSING_END",end)
    body,tail=b.split(end,1)
    return a+start+fn(body)+end+tail

ELIGIBLE=r'''-- FB005_PRIVATE78_SPECTATOR_H2_ROSTER_QA_V1 / #397 eligible combat roster.
-- An arriving observer is NOT an extra human opponent for SOLO bot/egg rules.
local function eligibleSoloPlayers(): {Player}
    local roster: {Player} = {}
    for _,candidate in ipairs(Players:GetPlayers()) do
        local team=candidate.Team
        if candidate:GetAttribute("P0D_LateJoinSpectator")~=true
            and team and (team.Name=="RED" or team.Name=="BLUE") then
            table.insert(roster,candidate)
        end
    end
    return roster
end
'''

def patch_game(src:str)->str:
    assert FIX not in src,"SPECTATOR_ALREADY_PATCHED"
    assert H2_REASON not in src,"H2_ALREADY_PATCHED"
    assert 'FB007_LOBBY_REBALANCE_STAYS_IN_DOJO_QA_V1' in src,"REQUIRES_PRIOR_LOBBY_FIX"
    assert "soloFiveEggUnavailable" in src,"REQUIRES_PRIOR_SOLO_HUD_FIX"
    assert src.count("remote.OnServerEvent:Connect(")==1
    assert src.count("local function resetRound()")==1
    # Single participant definition across mode, readiness, bot start and HUD.
    src=once(src,'local roundReady: {[Player]: boolean} = {}',
        'local roundReady: {[Player]: boolean} = {}\n'+ELIGIBLE)
    # Protect countdown (late spectators must NOT cancel existing consent).
    old='''    local online = Players:GetPlayers()
    if #online == 0 then return false end
    for _, player in ipairs(online) do'''
    new='''    local online = eligibleSoloPlayers()
    if #online == 0 then return false end
    for _, player in ipairs(online) do'''
    # Original READY code has one such unique block.
    src=once(src,old,new)

    # Prevent a late spectator affecting Game's single-human StudioSolo.count
    # during LOBBY or COUNTDOWN.
    src=region(src,'local function tickRound()','-- Recovery uses the existing server-only authoritative tick',
       lambda body:once(body,'local count = #Players:GetPlayers()',
            'local count = #eligibleSoloPlayers()'))

    # A player entering during ACTIVE/COUNTDOWN is not assigned a fighting team.
    def join(body):
        return once(body,"    chooseTeam(player)\n",'''    chooseTeam(player)
    if RunService:IsStudio() and
        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then
        player.Team=nil
        player.Neutral=true
        player:SetAttribute("P0D_LateJoinSpectator",true)
    end
''')
    src=region(src,"local function onJoin(player: Player)",
               "Players.PlayerAdded:Connect(onJoin)",join)
    # A neutral observer's CharacterAdded must send them to the lobby,
    # regardless of ACTIVE phase. No egg/team/HP/Store authority.
    def spawn(body):
        return once(body,'''                else map.teams[team].spawn + Vector3.new(0, 2, 0)
        end''','''                else map.teams[team].spawn + Vector3.new(0, 2, 0)
        elseif RunService:IsStudio()
            and player:GetAttribute("P0D_LateJoinSpectator")==true then
            root.CFrame=LobbyIsland.spawn("RED")
        end''')
    src=region(src,"local function assignSpawn(player: Player, character: Model)",
              'map.teams[team].eggPrompt.Triggered:Connect(',spawn) if False else src
    # Only the function body, excluding all egg prompt/event hooks.
    # Indices MUST be relative to the split body, never the original tail:
    # otherwise the objective loop is half-appended and the script corrupts.
    marker="local function assignSpawn(player: Player, character: Model)"
    objective='for _, team in ipairs({"RED", "BLUE"}) do'
    assert src.count(marker)==1, "ASSIGN_SPAWN_SOURCE_UNIQUE"
    beforeSpawn,afterStart=src.split(marker,1)
    assert objective in afterStart, "OBJECTIVE_HOOK_MISSING_AFTER_SPAWN"
    spawnBody,afterObjective=afterStart.split(objective,1)
    src=beforeSpawn+marker+spawn(spawnBody)+objective+afterObjective

    # Promote neutral spectators only on the NEXT LOBBY, never in ACTIVE or
    # COUNTDOWN. A dead observer receives a bounded one-shot engine respawn.
    def lobby(body):
        old='''if match.phase == "LOBBY" then
        rebalanceLobbyTeams()'''
        new='''if match.phase == "LOBBY" then
        if RunService:IsStudio() then
            for _,entrant in ipairs(Players:GetPlayers()) do
                if entrant:GetAttribute("P0D_LateJoinSpectator")==true then
                    entrant:SetAttribute("P0D_LateJoinSpectator",nil)
                    chooseTeam(entrant)
                    roundReady[entrant]=false
                    local ok,root=healthy(entrant)
                    if ok and root then
                        root.AssemblyLinearVelocity=Vector3.zero
                        root.AssemblyAngularVelocity=Vector3.zero
                        root.CFrame=LobbyIsland.spawn(getTeamName(entrant))
                    else
                        task.defer(function()
                            if entrant.Parent==Players and match.phase=="LOBBY"
                                and not healthy(entrant) then
                                local loaded,err=pcall(function() entrant:LoadCharacter() end)
                                if not loaded then warn("FB005_SPECTATOR_PROMOTION_LOAD_FAIL",err) end
                            end
                        end)
                    end
                end
            end
        end
        rebalanceLobbyTeams()'''
        return once(body,old,new)
    src=region(src,"local function tickRound()",
         '    elseif match.phase == "COUNTDOWN" then',lobby)

    # In resetRound, skip counting spectators for deferred bot start, avoid
    # treating the spectator as the lone fighter, and fail to RESULTS on errors.
    def reset(block):
        block=once(block,'if match.phase=="ACTIVE" and #Players:GetPlayers()==1 then',
            'if match.phase=="ACTIVE" and #eligibleSoloPlayers()==1 then')
        block=once(block,'local player=Players:GetPlayers()[1]',
            'local player=eligibleSoloPlayers()[1]')
        block=once(block,'and #Players:GetPlayers()==1 then',
            'and #eligibleSoloPlayers()==1 then')
        return block
    src=region(src,"local function resetRound()","local function chooseTeam(",reset)

    # Onehuman SCORE vote => CLASSIC bots; H2 SCORE if >1 eligible fighters.
    src=once(src,
        '#Players:GetPlayers()>1 and chosenMode==ModeVote.SCORE',
        '#eligibleSoloPlayers()>1 and chosenMode==ModeVote.SCORE')
    src=once(src,'and #Players:GetPlayers()==1,',
                 'and #eligibleSoloPlayers()==1,')

    # H2 two-human roster shrink must not remain ACTIVE without bots or
    # reinterpret a running H2 egg score as a CLASSIC game.
    def removing(body):
        key='    if match.phase == "ACTIVE" and side ~= "NONE" then'
        alt='''    if RunService:IsStudio() and match.phase=="ACTIVE"
        and EXPERIMENTAL_FIVE_EGG_MODE then
        local survivors=0
        for _,remaining in ipairs(eligibleSoloPlayers()) do
            if remaining~=player then survivors+=1 end
        end
        if survivors==1 then
            stopRound("DRAW","SOLO_H2_ROSTER_CHANGED_REQUIRES_NEW_READY")
        end
    end
    if match.phase == "ACTIVE" and side ~= "NONE" then'''
        return once(body,key,alt)
    src=region(src,"Players.PlayerRemoving:Connect(function(player)",
            "local function tickRound()",removing)

    assert src.count("local function eligibleSoloPlayers()")==1
    assert src.count("P0D_LateJoinSpectator")>=4
    assert src.count("remote.OnServerEvent:Connect(")==1
    assert src.count("local function tickRound()")==1
    assert src.count("local function resetRound()")==1
    assert src.count(H2_REASON)==1
    return src

def patch_bot(src:str)->str:
    assert "P0D_LateJoinSpectator" not in src,"BOT_SPECTATOR_ALREADY_PATCHED"
    # Exact original authored #378 Bot.start source.
    src=once(src,
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
    src=once(src,
        'if #Players:GetPlayers()==0 then Bot.stop();return end',
        '''local eligible=0
    for _,p in ipairs(Players:GetPlayers()) do
        local team=p.Team
        if p:GetAttribute("P0D_LateJoinSpectator")~=true
            and team and (team.Name=="RED" or team.Name=="BLUE") then
            eligible+=1
        end
    end
    if eligible~=1 then Bot.stop();return end''')
    src=once(src,
        'if team~=bot.team and root and hum and hum.Health>0 then',
        '''if p:GetAttribute("P0D_LateJoinSpectator")~=true
            and team and (team=="RED" or team=="BLUE")
            and team~=bot.team and root and hum and hum.Health>0 then''')
    assert src.count("P0D_LateJoinSpectator")>=3
    assert src.count("function Bot.start(")==1
    assert src.count("function Bot.tick(")==1
    assert 'FilterDescendantsInstances={attackerCharacter}' in src
    return src

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_SPECTATOR_H2_OFF_ZERO_WRITE");return False
    base=base.absolute();out=out.absolute()
    assert base.is_dir() and not base.is_symlink(),"SPECTATOR_MISSING_78"
    assert out.parent.is_dir() and not out.exists() and not out.is_symlink(),"SPECTATOR_BAD_OUTPUT"
    assert base!=out and not out.is_relative_to(base) and not base.is_relative_to(out),"SPECTATOR_OVERLAP"
    before=read(base)
    assert len(before)==78 and GAME in before and BOT in before,"SPECTATOR_REQUIRES_REAL_78"
    lock=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(b) for p,b in sorted(before.items())}
    assert lock["total_scripts"]==fl["total_sources"]==78
    assert lock["blobs"]==fl["source_gitblobs"]==pins
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert fl["p0_lobby_rebalance78"]["original_77_other_sources_exact"]
    assert fl["p0_solo78"]["new_feature_count"]==0
    assert FIX not in fl.get("feature_flags",{})
    game=patch_game(before[GAME].decode("utf8")).encode("utf8")
    bot=patch_bot(before[BOT].decode("utf8")).encode("utf8")
    after={**before,GAME:game,BOT:bot}
    assert len(after)==78
    assert {k for k in before if before[k]!=after[k]}=={GAME,BOT}
    pins78={p:gitblob(v) for p,v in sorted(after.items())}
    receipt={
       "id":FIX,"author":AUTHOR,"existing_feature":"FB005_SOLO + FB007_LOBBY",
       "new_feature_count":0,"new_source_count":0,"source_count":78,
       "only_original_Game_and_Bot_patched":True,"other76_byte_exact":True,
       "preserves_78_parent":True,"formal_rc_adopted":False,
       "solo":"ONE_ELIGIBLE_HUMAN_PLUS_FIVE_BOTS",
       "h2_leave":"DRAW_TO_LOBBY_NEW_READY",
       "spectator":"NEUTRAL_OBSERVER_LOBBY_ONLY",
       "studio_engine":"NOT_TESTED","android":"NOT_TESTED",
       "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
       "rollback":"omit isolated private78 spectator/h2 overlay"}
    lock["blobs"]=pins78;fl["source_gitblobs"]=pins78
    lock["p0_spectator_h2_78"]=receipt;fl["p0_spectator_h2_78"]=receipt
    stageparent=Path(tempfile.mkdtemp(prefix=".p0d_spectator_h2_",dir=str(out.parent)))
    stage=stageparent/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(game)
        (stage/"src"/BOT).write_bytes(bot)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins78
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins78
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(stageparent,ignore_errors=True)
    assert read(base)==before,"SPECTATOR_PARENT78_MODIFIED"
    print("P0_PRIVATE78_SPECTATOR_H2_GAME_BOT_SOURCE_LOCK_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
