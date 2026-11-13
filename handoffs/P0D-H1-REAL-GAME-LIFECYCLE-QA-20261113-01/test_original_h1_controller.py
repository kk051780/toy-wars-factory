#!/usr/bin/env python3
"""Run the ACTUAL H1 whole Game.server.lua controller under native Luau.

This deliberately reuses the source-verified prior Game lifecycle 2-player
Roblox fake harness. Only test doubles (external services) are fake, not S1
round/eggs/attack/trap/wind source. No Roblox Studio / phone claims.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "handoffs/P0D-H1-COMPOSITE-20261113-01/src"
OLD_HARNESS = REPO / "releases/P0D_S1_KIDS_RC01/tools/native_game_trap_integration.py"
SOURCE_SHA = "1498c2d344ede2d9da6c2bfdd025ebc1a15ec48b"
LOCK = {
    "Game": ("server/Game.server.luau", "adecfee41a594bdd54393050b4890a5733a536ce"),
    "WindRules": ("server/S1RaiderWindRules.luau", "7d5706774b874759e7ab994dc0654c3ae9a46502"),
    "Rules": ("server/S1Rules.luau", "5652b5b43d753c2fcbd27b6c040a34a3642f71ee"),
    "TrapRules": ("server/S1TrapRules.luau", "feabd705e4cfa5483d440e506277080f226343ef"),
    "LobbyTeamRecovery": ("server/LobbyTeamRecovery.luau", "db1a369133550bc8356a4ee3ac22b97fcb1b46c4"),
    "Config": ("shared/Config.luau", "62023303118454fa395f6bfce4c3a50552f840da"),
}
ORIGINAL_HARNESS_BLOB="8612d92bd857c883461e59fd2b0ce14fa1ad03e9"
GAMEMUTATIONS=[
    ("wind_role_guard", "WindRules", 's.role ~= "RAIDER"', 's.role ~= "GUARDIAN"',
     "GAME_S1_ASSERT_RAIDER_wind_speed"),
    ("wind_carry_block", "WindRules", 's.carrying == true', 'false',
     "GAME_S1_ASSERT_wind_after_egg_pickup_denied"),
    ("wind_cooldown", "WindRules", "s.now - s.lastAt < Wind.COOLDOWN",
     "s.now - s.lastAt > Wind.COOLDOWN",
     "GAME_S1_ASSERT_RAIDER_wind_speed"),
    ("wind_duration", "WindRules", "Wind.DURATION = 2.5", "Wind.DURATION = 100",
     "GAME_S1_ASSERT_wind_expires_after_2_5_seconds"),
    ("wind_boost_on_egg_pickup", "Game",
     'stopWind(player) -- cannot carry an egg at burst speed',
     'if false then stopWind(player) end -- intentionally broken egg speed guard',
     "GAME_S1_ASSERT_egg_pickup_cancels_wind"),
    ("replay_seq_guard", "Game",
     'local function applyWind(player: Player, data)\n    if type(data) ~= "table" or data.action ~= "WIND_BURST" then return end\n    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end',
     'local function applyWind(player: Player, data)\n    if type(data) ~= "table" or data.action ~= "WIND_BURST" then return end\n    if false then return end',
     "GAME_S1_ASSERT_wind_replay_not_refresh")
]

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def load_old():
    if blob(OLD_HARNESS.read_bytes())!=ORIGINAL_HARNESS_BLOB:
        raise RuntimeError("ORIGINAL_VETTED_TWO_PLAYER_REAL_GAME_HARNESS_CHANGED")
    spec=importlib.util.spec_from_file_location("old_real_game_test", OLD_HARNESS)
    if not spec or not spec.loader: raise RuntimeError("ORIGINAL_HARNESS_IMPORT_FAILED")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def source_locked():
    source={}
    for module,(path,expected) in LOCK.items():
        p=SRC/path
        raw=p.read_bytes()
        if blob(raw)!=expected:raise RuntimeError("H1_GENUINE_SOURCE_BLOB_CHANGED_"+module)
        source[module]=raw.decode("utf-8")
    assert 'remote.Name = "TrapRaidersS1Remote"' in source["Game"]
    assert source["Game"].count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "WIND_BURST" in source["Game"] and "S1RaiderWindRules" in source["Game"]
    return source

def insert_new_true_H1_e2e_tests(older):
    marker='-- On player disconnect, existing match ends by SERVER authority.'
    if older.count(marker)!=1:
        raise RuntimeError("PREVIOUS_HARNESS_GAME_TEST_ANCHOR_CHANGED")
    new_cases=r'''
-- New H1: execute the ACTUAL Game's actual WIND_BURST handler, not just pure rules.
setNear(pRed,V.new(5,5,0))
send(pRed,"WIND_BURST",6)
eq(pRed.Character.hum.WalkSpeed,27,"RAIDER_wind_speed")
eq(last(pRed).windActive,true,"wind_server_snapshot_active")
eq(last(pRed).windCooldown,18,"wind_server_cooldown_18")
local firstWindVisual=pRed.Character
local firstBurstSent=#remotes[1].sent
send(pRed,"WIND_BURST",6)
eq(#remotes[1].sent,firstBurstSent,"wind_replay_not_refresh")
send(pBlue,"WIND_BURST",6)
eq(pBlue.Character.hum.WalkSpeed,15,"GUARDIAN_cannot_wind")
-- Fully authentic original server task updates duration and restores speed.
tick(32.0)
eq(pRed.Character.hum.WalkSpeed,19,"wind_expires_after_2_5_seconds")
eq(last(pRed).windActive,false,"wind_expiry_server_snapshot")
send(pRed,"WIND_BURST",7)
eq(pRed.Character.hum.WalkSpeed,19,"wind_cooldown_rejects_early")
tick(47.5)
setNear(pRed,V.new(5,5,0))
-- Replayed old packet must not become a new burst AFTER cooldown has passed.
send(pRed,"WIND_BURST",6)
eq(pRed.Character.hum.WalkSpeed,19,"wind_replay_not_refresh")
send(pRed,"WIND_BURST",8)
eq(pRed.Character.hum.WalkSpeed,27,"wind_second_valid_after_cooldown")
eq(last(pRed).windActive,true,"second_wind_server_active")
-- An authentic ProximityPrompt steal while boosted MUST clear server Wind.
setNear(pRed,arena.teams.BLUE.egg.Position)
promptSteal(pRed,"BLUE")
eq(last(pRed).carrying,"BLUE","egg_pickup_while_wind")
eq(last(pRed).windActive,false,"egg_pickup_cancels_wind")
eq(pRed.Character.hum.WalkSpeed,19,"egg_pickup_restores_normal_speed")
-- Wait out the full 18s cooldown while still CARRYING; rule must deny it
-- even if time/position/role are otherwise eligible.
tick(66.0)
setNear(pRed,V.new(40,5,4))
send(pRed,"WIND_BURST",9)
eq(last(pRed).windActive,false,"wind_after_egg_pickup_denied")
eq(pRed.Character.hum.WalkSpeed,19,"egg_carrier_has_no_wind_boost")
-- Real server-only carrying and death rules still govern; fake client cannot
-- gain a Wind faster speed while carrying the opponent egg.
'''
    return older.replace(marker,new_cases+marker)

def updated_fakes(raw):
    old='local Enum={RaycastFilterType={Exclude="Exclude"}, Material={Neon="Neon"}}'
    assert raw.count(old)==1,"ORIGINAL_ROBLOX_FAKE_ENUM_CHANGED"
    newer='local Enum={RaycastFilterType={Exclude="Exclude"}, Material={Neon="Neon"}, HighlightDepthMode={Occluded="Occluded"}}'
    return raw.replace(old,newer)

def build(mod,src):
    previous=mod.SOURCES
    substitutions={}
    for key,anchor in previous.items():
        if key in ("Config","Rules","LobbyTeamRecovery","TrapRules"):
            substitutions[key]='local '+key+' = __real_'+key
        else:
            substitutions[key]='local '+key+' = '+key
    substitutions["WindRules"]="local WindRules = __real_WindRules"
    anchors=dict(previous)
    anchors["WindRules"]='local WindRules = require(script.Parent:WaitForChild("S1RaiderWindRules"))'
    game=src["Game"]
    for key,anchor in anchors.items():
        if game.count(anchor)!=1: raise RuntimeError("REAL_GAME_REQUIRE_ANCHOR_NOT_UNIQUE_"+key)
        game=game.replace(anchor,substitutions[key],1)
    cases=insert_new_true_H1_e2e_tests(mod.LUAU_TEST)
    return (updated_fakes(mod.FAKES)
        +mod.wrap("__real_Config",src["Config"])
        +mod.wrap("__real_Rules",src["Rules"])
        +mod.wrap("__real_LobbyTeamRecovery",src["LobbyTeamRecovery"])
        +mod.wrap("__real_TrapRules",src["TrapRules"])
        +mod.wrap("__real_WindRules",src["WindRules"])
        +mod.wrap("__real_game_controller",game)
        +cases)

def execute(luau:Path, mod, src, path:Path):
    path.write_text(build(mod,src),encoding="utf-8")
    r=subprocess.run([str(luau),str(path)],capture_output=True,text=True,timeout=40)
    return r.returncode,r.stdout+r.stderr

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--luau",type=Path,required=True)
    parser.add_argument("--build-only",type=Path)
    args=parser.parse_args()
    mod=load_old()
    src=source_locked()
    if args.build_only:
        args.build_only.parent.mkdir(parents=True,exist_ok=True)
        args.build_only.write_text(build(mod,src),encoding="utf-8")
        print("H1_REAL_GAME_NATIVE_SOURCE_READY")
        return
    with TemporaryDirectory(prefix="h1_actual_game_native_") as tmp:
        path=Path(tmp)/"real_h1_game_lifecycle.luau"
        ret,out=execute(args.luau,mod,src,path)
        if ret or "P0D_NATIVE_ACTUAL_GAME_SERVER_LIFECYCLE_PASS" not in out:
            raise RuntimeError("H1_ORIGINAL_GAME_CONTROLLER_ACTUAL_NATIVE_EXECUTION_FAILED "+out[-3000:])
        print(out.strip().split("\n")[-1])
        print("H1_GENUINE_GAME_CONTROLLER_WIND_EGG_LIFECYCLE_PASS")
        rejected=0
        for key,modname,old,new,expected in GAMEMUTATIONS:
            s=src[modname]
            if s.count(old)!=1:
                print("H1_MUTANT_ANCHOR_UNIQUE_FAIL",key,s.count(old))
                raise RuntimeError("H1_MUTANT_ANCHOR_CHANGED_"+key)
            bad=dict(src);bad[modname]=s.replace(old,new,1)
            code,logs=execute(args.luau,mod,bad,path)
            if code==0 or expected not in logs:
                raise RuntimeError("H1_MUTATION_NOT_CAUGHT_"+key+" "+logs[-1200:])
            rejected+=1
            print("H1_ACTUAL_GAME_SERVER_MUTATION_REJECTED",key)
        if rejected!=len(GAMEMUTATIONS):raise RuntimeError("MUTATIONS_INCOMPLETE")
        print("H1_GENUINE_GAME_NATIVE_NEGATIVE_CONTROLS_PASS",rejected)
    print("H1_OWNER_STUDIO_2CLIENT_PHONE_FUN_NOT_TESTED")
if __name__=="__main__":
    try:
        main()
    except (OSError,RuntimeError,AssertionError,subprocess.TimeoutExpired) as exc:
        print("H1_NATIVE_REAL_GAME_QA_BLOCKED",str(exc),file=sys.stderr)
        sys.exit(1)
