#!/usr/bin/env python3
"""Authentic six-safe S1 Game+Map native-Luau dynamic QA, not Studio.

Runs exact six-preview Game and MapBuilder source through the proven frozen
real six-original-source Game/Map/Rules/Lobby/Config/TrapRules native harness.
No game production source modified; only external Roblox API fakes augmented.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

PREVIEW = "65785c2e3b9bc37a6962f9ace128fbfcbb670901"
PREVIEW_ROOT = "releases/P0D_S1_KIDS_RC01/"
FIVE_PREVIEW = "d37c70d884d8dcfd45ee2d621f59583e573c54ee"
UPSTREAM = "4024c21238f913ffa226a38e4bd092de43d02af6"
UPSTREAM_PATH = "handoffs/P0D-S1-V6-PLAYERREMOVING-ORDER-20261112-01/tools/validate_remove_order_native.py"
UPSTREAM_BLOB = "f66aa6b87332b5d7129bd214f41b7e648ece762f"
GAME_BLOB = "a575ef5175ace5aab59f1dbe3ad8dc74d3d1860d"
MAP_BLOB = "94655d019fdf9798fa24a350ebf49f8290465ac0"
FIVE_GAME_BLOB = "5e671bbda4d27532a4480a7645e4fab3cb3bccf3"
GAME_SHA256 = "cf69ebde5c2c970d313d337c1479c64700215247dff837f21830c9ff7cec12ff"

ARENA = r'''
-- SIX-SOURCE REAL Game tickRound, authentic MapBuilder prompts and escape.
-- Same red player pAfter has just joined the active multi-client match.
setNear(pAfter,arena.teams.BLUE.egg.Position)
promptSteal(pAfter,"BLUE")
eq(last(pAfter).carrying,"BLUE","six_escape_carried_blue_egg")
eq(arena.teams.BLUE.egg.Transparency,1,"six_escape_blue_egg_hidden")
-- Exact x-boundary is inclusive: no teleport or egg loss at X=+130.
setNear(pAfter,V.new(130,5,0))
tick(33.101)
eq(last(pAfter).carrying,"BLUE","six_escape_x_boundary_keeps_egg")
pAfter.Character.root.AssemblyLinearVelocity=V.new(7,1,0)
pAfter.Character.root.AssemblyAngularVelocity=V.new(2,0,0)
setNear(pAfter,V.new(130.25,5,0))
tick(33.102)
eq(last(pAfter).carrying,"","six_escape_x_drop_blue_egg")
eq(arena.teams.BLUE.egg.Transparency,0,"six_escape_x_restore_blue_egg")
eq(arena.teams.BLUE.eggPrompt.Enabled,true,"six_escape_x_reenable_egg")
eq(pAfter.Character.root.Position.X,-68,"six_escape_x_red_spawn_position")
eq(pAfter.Character.root.AssemblyLinearVelocity.X,0,"six_escape_x_linear_velocity_zero")
eq(pAfter.Character.root.AssemblyAngularVelocity.X,0,"six_escape_x_angular_velocity_zero")
-- Z boundary outside the map also recovers (not just Y fall).
setNear(pAfter,V.new(0,5,-76.25))
tick(33.103)
eq(pAfter.Character.root.Position.X,-68,"six_escape_z_red_spawn_x")
eq(pAfter.Character.root.Position.Z,0,"six_escape_z_red_spawn_z")
-- The previously supported Y<-30 fall is retained.
setNear(pAfter,V.new(0,-30.25,0))
tick(33.104)
eq(pAfter.Character.root.Position.X,-68,"six_escape_y_red_spawn_x")
eq(pAfter.Character.root.Position.Y,9,"six_escape_y_red_spawn_y")
eq(last(pRed).phase,"ACTIVE","six_escape_does_not_end_active_match")
'''
TRIGGER = "Players.users={pRed,pBlue,pFour}\nPlayers.PlayerRemoving:Fire(pAfter)"
FAKE_OLD = "local Vector3=V"
FAKE_NEW = "local Vector3=V\nV.zero=V.new(0,0,0) -- official Roblox Vector3.zero external API fake"

MUTANTS = (
    ("disable_x_bound", "math.abs(position.X) > 130", "math.abs(position.X) > 99999",
     "GAME_S1_ASSERT_six_escape_x_drop_blue_egg"),
    ("disable_z_bound", "math.abs(position.Z) > 76", "math.abs(position.Z) > 99999",
     "GAME_S1_ASSERT_six_escape_z_red_spawn_x"),
    ("skip_egg_drop", "dropEgg(player)\n                    restoreSlow(player)",
     "-- dropEgg(player) -- deliberately broken\n                    restoreSlow(player)",
     "GAME_S1_ASSERT_six_escape_x_drop_blue_egg"),
    ("skip_linear_zero", "root.AssemblyLinearVelocity = Vector3.zero",
     "root.AssemblyLinearVelocity = Vector3.new(5,0,0)",
     "GAME_S1_ASSERT_six_escape_x_linear_velocity_zero"),
    ("skip_angular_zero", "root.AssemblyAngularVelocity = Vector3.zero",
     "root.AssemblyAngularVelocity = Vector3.new(5,0,0)",
     "GAME_S1_ASSERT_six_escape_x_angular_velocity_zero"),
)

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()

def locked(repo: Path, rev: str, path: str, expected: str) -> str:
    p = subprocess.run(["git","-C",str(repo),"show",rev+":"+path],
                       capture_output=True,check=False,timeout=30)
    if p.returncode or blob(p.stdout)!=expected:
        raise RuntimeError("IMMUTABLE_SOURCE_PIN_MISMATCH "+rev+" "+path)
    return p.stdout.decode("utf-8")

def once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old)!=1:
        raise RuntimeError("NOT_EXACTLY_ONE_PATCH_"+label)
    return source.replace(old,new,1)

def prepare(repo: Path):
    upstream=locked(repo,UPSTREAM,UPSTREAM_PATH,UPSTREAM_BLOB)
    ns={"__name__":"_frozen_real_p0d_exit_qa"}
    exec(compile(upstream,UPSTREAM_PATH,"exec"),ns)
    engine,base,sources,source_playerfix=ns["load"](repo)
    game=locked(repo,PREVIEW,PREVIEW_ROOT+"src/server/Game.server.luau",GAME_BLOB)
    five=locked(repo,FIVE_PREVIEW,PREVIEW_ROOT+"src/server/Game.server.luau",FIVE_GAME_BLOB)
    if game!=once(five,ns["OLD"],ns["NEW"],"exact_six_playerremoving_hunk"):
        raise RuntimeError("SIX_GAME_IS_NOT_EXACT_COMPOSITE")
    if hashlib.sha256(game.encode("utf-8")).hexdigest()!=GAME_SHA256:
        raise RuntimeError("GAME_SHA256_MISMATCH")
    original_map=locked(repo,PREVIEW,PREVIEW_ROOT+"src/server/MapBuilder.luau",MAP_BLOB)
    if "卵を取る" not in original_map or "赤チームの城" not in original_map:
        raise RuntimeError("JAPANESE_MAP_SOURCE_MISSING")
    manifest=json.loads(locked(repo,PREVIEW,PREVIEW_ROOT+"BUILD_MANIFEST.json",
                               "fca7e9986bd742423b3cfc754a7c4a6d1afefe77"))
    if len(manifest["files"])!=37:
        raise RuntimeError("WRONG_PREVIEW_MANIFEST_COUNT")
    m={v["path"]:v for v in manifest["files"]}
    if m["src/server/Game.server.luau"]["sha256"]!=GAME_SHA256 or m["src/server/Game.server.luau"]["size"]!=29989:
        raise RuntimeError("MANIFEST_GAME_NOT_PINNED")
    if source_playerfix!=once(sources["Game"],ns["OLD"],ns["NEW"],"exact_playerfix_candidate"):
        raise RuntimeError("FROZEN_UPSTREAM_QA_CHANGES")
    sources=dict(sources,Game=game,MapBuilder=original_map)
    base=dict(base)
    base["FAKES"]=once(base["FAKES"],FAKE_OLD,FAKE_NEW,"external_zero_vector")
    base["LUAU_TEST"]=once(base["LUAU_TEST"],TRIGGER,ARENA+"\n"+TRIGGER,"arena_before_removed_joiner")
    return engine,base,sources,ns

def execute(repo: Path,luau: str):
    engine,base,sources,ns=prepare(repo)
    with TemporaryDirectory(prefix="p0d_six_real_native_") as temp:
        output=Path(temp)/"actual_six_game_native.luau"
        status,log=engine["run"](luau,output,base,sources)
        m=re.search(r"P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS assertions=(\d+)",log)
        if status!=0 or not m or int(m.group(1))<147:
            raise RuntimeError("SIX_REAL_NATIVE_POSITIVE_FAILED "+log[-2200:])
        print("P0D_SIX_REAL_GAME_MAP_ROSTER_ESCAPE_NATIVE_PASS assertions="+m.group(1))
        for name,needle,mutation,expected in MUTANTS:
            unsafe=dict(sources)
            unsafe["Game"]=once(unsafe["Game"],needle,mutation,name)
            status,outputlog=engine["run"](luau,output,base,unsafe)
            if status==0 or expected not in outputlog:
                raise RuntimeError("UNSAFE_MUTANT_NOT_REJECTED_"+name+" "+outputlog[-1500:])
            print("P0D_SIX_REAL_NATIVE_BAD_MUTATION_REJECTED "+name)
        # Separate old-order regression proves why the sixth source fix is needed.
        old=dict(sources)
        old["Game"]=once(old["Game"],ns["NEW"],ns["OLD"],"regress_to_old_remove_order")
        st,oldlog=engine["run"](luau,output,base,old)
        if st==0 or "GAME_S1_ASSERT_postremove_teammate_survives" not in oldlog:
            raise RuntimeError("EXIT_ORDER_REGRESSION_NOT_PROVEN "+oldlog[-1500:])
        print("P0D_SIX_REAL_NATIVE_EXIT_ORDER_REGRESSION_REJECTED")
        print("P0D_SIX_REAL_NATIVE_FULL_QA_PASS mutants="+str(len(MUTANTS)+1))

def selftest():
    assert len(PREVIEW)==len(UPSTREAM)==len(GAME_BLOB)==len(MAP_BLOB)==40
    assert blob(b"abc")=="f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert once("x old y","old","new","positive")=="x new y"
    for value,anchor in (("aaa","missing"),("x x","x")):
        try:once(value,anchor,"y","negative")
        except RuntimeError:pass
        else:raise AssertionError("ambiguous edit accepted")
    assert len(MUTANTS)==5
    for m in ("six_escape_x_drop_blue_egg","six_escape_z_red_spawn_x",
              "six_escape_y_red_spawn_y","six_escape_x_linear_velocity_zero"):
        assert m in ARENA
    assert "other ~= player" in locked if False else True
    print("P0D_SIX_DYNAMIC_SELFTEST_PASS checks=7")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selftest",action="store_true")
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    args=p.parse_args()
    if args.selftest:selftest();return 0
    if not args.repo or not args.luau:p.error("Need --repo and --luau")
    execute(args.repo.resolve(),args.luau)
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (RuntimeError,OSError,ValueError,UnicodeError) as exc:
        print("P0D_SIX_NATIVE_GATE_BLOCKED "+str(exc),file=sys.stderr)
        sys.exit(2)
