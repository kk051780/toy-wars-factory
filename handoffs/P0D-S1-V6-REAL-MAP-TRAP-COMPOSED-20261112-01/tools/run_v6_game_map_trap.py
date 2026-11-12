#!/usr/bin/env python3
"""Exact S1 V6 actual MapBuilder + Guardian trap + game controller native integration.

Immutable old map-integrated harness is used ONLY as a vetted test baseline.
This program loads actual new official RC Luau (Game, Map, Rules, Lobby, Config,
TrapRules) by pinned Git blob, composes them in native Luau and extends actual
real-world-map/Guardian trap assertions; only *external* Roblox APIs are faked.
No official RC file is edited. This is not Roblox Studio.
"""
import argparse
import hashlib
import re
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

OFFICIAL = "1263a03701211a652b99b91d2339575dc8104eff"
UPSTREAM_QA = "b2ae7828b641ab5acccc279117d36c6c413b543b"
UPSTREAM_SHA = "b80fe46bff2ffdc59a25ce6db9a2a7e4bddcf5a0"
UPSTREAM_PATH = "handoffs/P0D-S1-REAL-GAME-MAP-NATIVE-20261112-05/tools/run_original_game_and_map.py"
ROOT = "releases/P0D_S1_KIDS_RC01/"
BLOBS = {
    "src/server/Game.server.luau": ("Game", "7c5229f600f17537bc1bbbb0b96b6a2435875374"),
    "src/server/S1Rules.luau": ("Rules", "5652b5b43d753c2fcbd27b6c040a34a3642f71ee"),
    "src/server/LobbyTeamRecovery.luau": ("Lobby", "db1a369133550bc8356a4ee3ac22b97fcb1b46c4"),
    "src/shared/Config.luau": ("Config", "62023303118454fa395f6bfce4c3a50552f840da"),
    "src/server/MapBuilder.luau": ("MapBuilder", "d2127b8c20c8abd880a21f84aeeb706feeb14ce8"),
    "src/server/S1TrapRules.luau": ("TrapRules", "feabd705e4cfa5483d440e506277080f226343ef"),
}
TRAP_REQUIRE = 'local TrapRules = require(script.Parent:WaitForChild("S1TrapRules"))'
GAME_ANCHOR = "local __real_game_controller=(function()\n"
OLD_DISCONNECT = "-- On player disconnect, existing match ends by SERVER authority."
EXTRA = r'''
-- V6 real map+trap cross product: physical map from authentic MapBuilder,
-- no made-up egg/spawn/core locations or isolated fake map objects.
local trapFolder=arena.model:FindFirstChild("S1_GUARDIAN_TRAPS")
eq(trapFolder~=nil,true,"v6_real_map_trap_folder")
eq(trapFolder.ClassName,"Folder","v6_folder_class")
eq(trapFolder.Parent,arena.model,"v6_trap_under_actual_map")
eq(countCreated("Folder"),4,"v6_exact_four_folders_in_real_world")
eq(countCreated("Part"),27,"v6_real_map_27_parts_before_trap")
-- Trap must be rejected even for a Guardian standing on his own
-- real geometry egg (pBlue's team is BLUE, egg x=98,z=-20).
local actualBlueEgg=arena.teams.BLUE.egg.Position
setNear(pBlue,V.new(actualBlueEgg.X,5,actualBlueEgg.Z))
send(pBlue,"PLACE_TRAP",4,{position={x=40,y=5,z=0},damage=999})
eq(countCreated("Part"),27,"v6_egg_clearance_uses_real_map")
-- Client tries to tell server a fake far position. Actual BLUE player root
-- at x=40 should win over fake client coordinates.
setNear(pBlue,V.new(40,5,0))
send(pBlue,"PLACE_TRAP",5,{position={x=-999,y=99,z=-999}})
eq(countCreated("Part"),28,"v6_genuine_blue_trap_created")
local disc=trapFolder:FindFirstChild("S1_VISIBLE_TRAP_BLUE_1")
eq(disc~=nil,true,"v6_actual_trap_mounted_under_real_map")
eq(disc.ClassName,"Part","v6_actual_trap_part")
eq(disc.Position.X,40,"v6_uses_real_server_position")
eq(disc.Position.Z,0,"v6_clamped_to_actual_server_z")
eq(disc.CanCollide,false,"v6_trap_no_collide")
eq(disc.CanQuery,false,"v6_trap_does_not_block_real_map_raycast")
send(pBlue,"PLACE_TRAP",6,{})
eq(countCreated("Part"),28,"v6_cooldown_no_second_trap")
setNear(pRed,V.new(40,5,0))
tick(29.5)
eq(pRed.Character.hum.WalkSpeed,10,"v6_real_map_enemy_slow")
eq(pBlue.Character.hum.WalkSpeed,15,"v6_real_map_friend_not_slow")
eq(disc.Destroyed,true,"v6_first_triggered_trap_destroyed")
tick(32.6)
eq(pRed.Character.hum.WalkSpeed,19,"v6_real_map_slow_restored")
eq(arena.model:FindFirstChild("S1_GUARDIAN_TRAPS"),trapFolder,"v6_real_map_survives_trap")
eq(workspace:FindFirstChild("TRAP_RAIDERS_S1"),arena.model,"v6_real_map_still_mounted")
'''
MUTATIONS = [
    # Actual unsafe map mutation must break real Game -> Map crossing, not
    # merely a stand-alone map constructor fixture.
    ("map_blue_egg_collapses_to_mid", "MapBuilder",
     "Vector3.new(sign * 98, 2.5, -20)", "Vector3.new(sign * 14, 2.5, -20)",
     "GAME_S1_ASSERT_actual_RED_egg_location"),
    ("map_prompt_enabled_in_lobby", "MapBuilder",
     "p.Enabled = false", "p.Enabled = true",
     "GAME_S1_ASSERT_actual_RED_egg_disabled_in_lobby"),
    ("trap_egg_clearance_disabled", "TrapRules",
     "TrapRules.OBJECTIVE_CLEARANCE = 15",
     "TrapRules.OBJECTIVE_CLEARANCE = 0",
     "GAME_S1_ASSERT_v6_egg_clearance_uses_real_map"),
    ("trap_uses_forged_location", "Game",
     "x = root.Position.X, y = root.Position.Y, z = root.Position.Z,\n        count = countTraps(team), avoid = avoid,",
     "x = data.position.x, y = data.position.y, z = data.position.z,\n        count = countTraps(team), avoid = avoid,",
     "GAME_S1_ASSERT_v6_egg_clearance_uses_real_map"),
    ("trap_melee_ray_query_blocked", "Game",
     "disc.CanQuery = false -- traps never obstruct melee raycast or castle aim",
     "disc.CanQuery = true -- deliberate broken variant",
     "GAME_S1_ASSERT_v6_trap_does_not_block_real_map_raycast"),
]


def blob_sha(payload):
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\x00" + payload).hexdigest()


def unique(text, anchor, replacement, name):
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(f"ANCHOR_NOT_EXACTLY_ONCE {name} count={count}")
    return text.replace(anchor, replacement, 1)


def read(repo, commit, path, expected):
    proc = subprocess.run(["git", "-C", str(repo), "show", commit + ":" + path],
                          capture_output=True, timeout=20, check=False)
    if proc.returncode:
        raise RuntimeError("PINNED_SOURCE_MISSING " + path)
    got = blob_sha(proc.stdout)
    if got != expected:
        raise RuntimeError(f"PINNED_SOURCE_CHANGED {path} got={got} wanted={expected}")
    return proc.stdout.decode("utf-8")


def prepare(repo):
    qa_source = read(repo, UPSTREAM_QA, UPSTREAM_PATH, UPSTREAM_SHA)
    base = {"__name__": "_p0d_read_only_map_qa"}
    exec(compile(qa_source, UPSTREAM_QA + ":" + UPSTREAM_PATH, "exec"), base)
    if base.get("RC") != "5dc6c958ea5549b1e859d6d250e6179e731181fb":
        raise RuntimeError("UPSTREAM_QA_BASE_CHANGED")
    sources = {key: read(repo, OFFICIAL, ROOT + path, sha)
               for path, (key, sha) in BLOBS.items()}
    base["RC"] = OFFICIAL
    base["FAKES"] = unique(base["FAKES"],
         "local ch={root=root,head=head,hum=hum,__type=\"Instance\"}",
         "local ch={root=root,head=head,hum=hum,__type=\"Instance\"}\n  hum.Parent=ch",
         "external_fake_humanoid_parent")
    base["LUAU_TEST"] = unique(base["LUAU_TEST"],
         'eq(countCreated("Folder"),3,"actual_map_folder_count")',
         'eq(countCreated("Folder"),4,"actual_map_folder_count")',
         "real_map_plus_guardian_trap_folder")
    base["LUAU_TEST"] = unique(base["LUAU_TEST"], OLD_DISCONNECT,
         EXTRA + "\n" + OLD_DISCONNECT, "actual_cross_source_trap_test_insert")
    return base, sources


def build(base, sources):
    # The official Game source is held byte-exact in "sources". Harness ONLY
    # substitutes its require boundary with a separately-pinned genuine module.
    incoming = dict(sources)
    incoming["Game"] = unique(incoming["Game"], TRAP_REQUIRE,
                              "local TrapRules = __real_TrapRules",
                              "inject_actual_trap_rules")
    script = base["build"](incoming)
    script = unique(script, GAME_ANCHOR,
             base["wrap"]("__real_TrapRules", sources["TrapRules"]) + GAME_ANCHOR,
             "compose_actual_trap_module_before_game")
    return script


def run(luau, path, base, sources):
    path.write_text(build(base, sources), encoding="utf-8")
    try:
        p = subprocess.run([luau, str(path)], capture_output=True,
                           text=True, timeout=35, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"NATIVE_EXEC_UNAVAILABLE {exc}")
    return p.returncode, p.stdout + p.stderr


def execute(repo, luau):
    base, sources = prepare(repo)
    with TemporaryDirectory(prefix="p0d_v6_real_map_trap_") as tmp:
        out = Path(tmp) / "actual_v6_map_trap.luau"
        status, log = run(luau, out, base, sources)
        match = re.search(r"P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS assertions=(\d+)", log)
        if status or not match or int(match.group(1)) < 95:
            raise RuntimeError("POSITIVE_ORIGINAL_SIX_SOURCE_COMPOSITION_BLOCKED " + log[-1500:])
        print("S1_V6_ACTUAL_REAL_MAP_PLUS_GUARDIAN_TRAP_NATIVE_PASS assertions=" + match.group(1))
        for name, module, original, unsafe, expected in MUTATIONS:
            bad = dict(sources)
            bad[module] = unique(bad[module], original, unsafe, name)
            status, result = run(luau, out, base, bad)
            if status == 0 or expected not in result:
                raise RuntimeError("UNDETECTED_UNSAFE_MUTATION " + name + " " + result[-750:])
            print("S1_V6_REAL_MAP_UNSAFE_MUTATION_DETECTED " + name)
        print("S1_V6_REAL_GAME_MAP_TRAP_FINAL_SUCCESS mutants=" + str(len(MUTATIONS)))


def selftest():
    assert len(OFFICIAL) == len(UPSTREAM_QA) == 40
    assert len(UPSTREAM_SHA) == 40 and len(BLOBS) == 6
    assert blob_sha(b"abc") == "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert unique("a|b", "|", "-", "test") == "a-b"
    for text, anchor in [("a b", "c"), ("x x", "x")]:
        try:
            unique(text, anchor, "z", "negative")
        except RuntimeError:
            pass
        else:
            raise AssertionError("FAILING_CLOSED_ANCHOR_NOT_REJECTED")
    assert len({x[0] for x in MUTATIONS}) == len(MUTATIONS) == 5
    for path, (name, sha) in BLOBS.items():
        assert len(sha) == 40 and path.endswith(".luau") and name
    for k in ("v6_real_map_enemy_slow","v6_genuine_blue_trap_created",
              "v6_egg_clearance_uses_real_map"):
        assert k in EXTRA
    print("P0D_S1_V6_COMPOSITE_PYTHON_SELFTEST_PASS count=9")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path)
    p.add_argument("--luau")
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.repo or not a.luau:
        p.error("Provide both --repo and --luau, or --selftest")
    execute(a.repo.resolve(), a.luau)
    return 0


if __name__=="__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, UnicodeError) as e:
        print("P0D_V6_REAL_MAP_TRAP_NATIVE_BLOCKED " + str(e), file=sys.stderr)
        sys.exit(2)
