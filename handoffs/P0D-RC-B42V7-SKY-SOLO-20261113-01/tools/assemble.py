#!/usr/bin/env python3
"""Integrator-only unpublished B42+V7+physical SkyCastle Studio solo A/B.
Exact frozen upstream 42 source via its own assembler, changing ONLY one Game
and adding the already-native-QA-passed StudioSoloPreviewRules ModuleScript.
Never edit upstream author sources, official RC or main.
"""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json, shutil, subprocess, sys

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1]
REPO=HERE.parents[3]
UPSTREAM=REPO/"handoffs/P0D-B42-V7-SKYCASTLE-20261113-01"
UPSTREAM_DIST=UPSTREAM/"dist/EGG_RAID_RUMBLE_FIRST90_V7_SKYCASTLE_PRIVATE"
DIST=ROOT/"dist/EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_SOLO_UNPUBLISHED"
FROZEN_UPSTREAM="a3dfc9b98f22b8edf0a7d0d978d65b1072aed933"
B42_GAME="21b866e801a53ba7ebd66132ae55fe28608750d6"
ORIGINAL_WORLD="0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
ORIGINAL_HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
SOLO_RULE="22e7e22e8837dbf44c57fdfb30efd480457022fb"

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def collect(where:Path)->dict[str,bytes]:
    return {p.relative_to(where/"src").as_posix():p.read_bytes()
        for p in sorted((where/"src").rglob("*.luau"))}

def only_once(text:str, old:str, new:str, label:str)->str:
    if text.count(old)!=1:
        raise RuntimeError(f"FAIL_CLOSED_{label}: anchor count {text.count(old)}")
    return text.replace(old,new,1)

def hunk_game(game:str)->str:
    # B42's original already imports RunService; no additional game services.
    assert game.count('local RunService = game:GetService("RunService")') == 1
    game=only_once(game,
        'local First90Waypoint = require(script.Parent:WaitForChild("First90WaypointRules"))',
        'local First90Waypoint = require(script.Parent:WaitForChild("First90WaypointRules"))\n'
        'local StudioSolo = require(script.Parent:WaitForChild("StudioSoloPreviewRules"))',
        "IMPORT")
    game=only_once(game,
        'if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then',
        'if StudioSolo.canStart(RunService:IsStudio(), count,\n'
        '                teamCount("RED"), teamCount("BLUE"), Config.MinPlayers) then',
        "LOBBY")
    game=only_once(game,
        'if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then',
        'if not StudioSolo.canStart(RunService:IsStudio(), count,\n'
        '                teamCount("RED"), teamCount("BLUE"), Config.MinPlayers) then',
        "COUNTDOWN")
    game=only_once(game,
        'if teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")\n'
        '        elseif teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")\n'
        '        elseif EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState',
        'local emptyWinner = StudioSolo.emptyWinner(RunService:IsStudio(), count,\n'
        '            teamCount("RED"), teamCount("BLUE"))\n'
        '        if emptyWinner then stopRound(emptyWinner, "TEAM_EMPTY")\n'
        '        elseif EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState',
        "TEAM_EMPTY")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('local function tickRound()')==1
    assert game.count('local function resetRound()')==1
    assert game.count('snapshotFor = function(player: Player)')==1
    return game

def main():
    assert not UPSTREAM_DIST.exists() and not DIST.exists(),"FAIL_CLOSED_NO_DIST_OVERWRITE"
    src=ROOT/"src/StudioSoloPreviewRules.luau"
    assert blob(src.read_bytes())==SOLO_RULE,"SOLO_SOURCE_DRIFT"
    assert blob((UPSTREAM/"src/H1FunWorld_SKY_CASTLE_TEST.server.luau").read_bytes())==ORIGINAL_WORLD
    subprocess.run([sys.executable,"-B",str(UPSTREAM/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True)
    original=collect(UPSTREAM_DIST)
    assert len(original)==42 and blob(original["server/Game.server.luau"])==B42_GAME
    assert blob(original["server/H1FunWorld.server.luau"])==ORIGINAL_WORLD
    assert blob(original["server/MusouHorde.luau"])==ORIGINAL_HORDE
    shutil.copytree(UPSTREAM_DIST,DIST)
    game=DIST/"src/server/Game.server.luau"
    game.write_text(hunk_game(game.read_text(encoding="utf8")),encoding="utf8")
    shutil.copyfile(src,DIST/"src/server/StudioSoloPreviewRules.luau")
    project=DIST/"default.project.json"
    config=json.loads(project.read_text(encoding="utf8"))
    assert config["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    config["name"]="EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_STUDIO_SOLO_UNPUBLISHED"
    project.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    all_scripts=collect(DIST)
    assert len(all_scripts)==43 and len(original)==42
    assert sorted(set(original)-set(all_scripts))==[]
    assert sorted(set(all_scripts)-set(original))==["server/StudioSoloPreviewRules.luau"]
    changed=[p for p in original if original[p]!=all_scripts[p]]
    assert changed==["server/Game.server.luau"],changed
    assert all(all_scripts[p]==original[p] for p in original if p!="server/Game.server.luau")
    assert sum(p.endswith("/Game.server.luau") for p in all_scripts)==1
    assert len([p for p in all_scripts if p.endswith(".server.luau")])==2
    assert len([p for p in all_scripts if p.endswith(".client.luau")])==5
    assert Counter(p.split("/")[0] for p in all_scripts)["server"] >= 25
    # No Gameplay authority duplication. No mutating existing 5-egg / XP / evolution.
    c=all_scripts["server/Game.server.luau"].decode("utf8")
    for marker in ('First90GuideRules','First90WaypointRules','Evolution.nextEvolution(',
                   'Power.beginAwaken(','ModeVote.tally(','H2Score.new(',
                   'horde:reset(','horde:tick(','StudioSolo.canStart(',
                   'StudioSolo.emptyWinner('):
        assert marker in c,marker
    assert c.count('remote.OnServerEvent:Connect(')==1
    assert c.count('local RunService = game:GetService("RunService")')==1
    assert all_scripts["server/StudioSoloPreviewRules.luau"]==src.read_bytes()
    lock={
       "status":"RICH_B42_V7_SKYCASTLE_SOLO_UNPUBLISHED_STUDIO_PREVIEW",
       "original_h1_fixed_source_commit":FROZEN_UPSTREAM,
       "original_h1_scripts":42,"unchanged_original_h1_scripts":41,
       "new_module":"server/StudioSoloPreviewRules.luau",
       "new_module_original_blob":SOLO_RULE,
       "modified_original":["server/Game.server.luau"],
       "script_total":43,"game_count":1,"one_remote":True,
       "solo_isStudio_gate":True,"published_min_players_unchanged":True,
       "original_first90_waypoint":True,"original_v7_musou":True,
       "original_physical_skycastle":True,
       "original_h2_5egg_and_XP_evolution":True,
       "official_rc_adopted":False,"roblox_studio_2client":"NOT_TESTED",
       "android":"NOT_TESTED","owner_fun":"NOT_TESTED","published":False,
       "blobs":{p:blob(content) for p,content in sorted(all_scripts.items())}
    }
    (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("P0D_B42_V7_SKYCASTLE_STUDIO_SOLO_43_SOURCE_41_UNCHANGED_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true",required=True)
    p.parse_args()
    main()
