#!/usr/bin/env python3
"""Read-only, fail-closed native Luau regression of pinned TRAP RAIDERS S1 V6.

Loads the authentic immutable five server Luau sources and official test runner
from an exact Git commit. It extends ONLY test doubles + assertions in memory.
Nothing in releases/, main, a Place or a Roblox session is modified.
Real Lua interpreter execution requires --luau; --selftest is Python-only.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

RC = "1263a03701211a652b99b91d2339575dc8104eff"
ROOT = "releases/P0D_S1_KIDS_RC01/"
RUNNER = "tools/native_game_trap_integration.py"
BLOBS = {
    "src/server/Game.server.luau": "7c5229f600f17537bc1bbbb0b96b6a2435875374",
    "src/server/S1Rules.luau": "5652b5b43d753c2fcbd27b6c040a34a3642f71ee",
    "src/server/LobbyTeamRecovery.luau": "db1a369133550bc8356a4ee3ac22b97fcb1b46c4",
    "src/shared/Config.luau": "62023303118454fa395f6bfce4c3a50552f840da",
    "src/server/S1TrapRules.luau": "feabd705e4cfa5483d440e506277080f226343ef",
    RUNNER: "8612d92bd857c883461e59fd2b0ce14fa1ad03e9",
}
SOURCE_KEYS = {
    "src/server/Game.server.luau": "Game",
    "src/server/S1Rules.luau": "Rules",
    "src/server/LobbyTeamRecovery.luau": "Lobby",
    "src/shared/Config.luau": "Config",
    "src/server/S1TrapRules.luau": "TrapRules",
}
ENTRY_MARKER = "-- On player disconnect, existing match ends by SERVER authority."
ON_EXIT_ANCHOR = 'Players.PlayerRemoving:Fire(pBlue)\neq(last(pRed).phase,"RESULTS","disconnect_ends_round")'
REPLAY_ANCHOR = (
    'if type(data) ~= "table" or data.action ~= "PLACE_TRAP" then return end\n'
    '    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end'
)
RESPAWN_ANCHOR = "if not alive or hum ~= record.hum or now >= record.untilAt then"
OWNER_ANCHOR = "if traps[i].owner == player then"

# Extends the existing real Game.server dynamic native runner with new cases.
EXTRA_LUAU = r'''
-- Assertions below target areas NOT covered by base source-native V6 smoke.
eq(#__trapParts,1,"one_first_trap_instantiated")
eq(__trapParts[1].Destroyed,true,"triggered_trap_destroyed_once")
tick(46.1) -- first placement t26.00, cooldown 20s, first trap already consumed
setNear(pBlue,V.new(20,5,0))
send(pBlue,"PLACE_TRAP",6,{position={x=-500,z=-500},damage=999})
tick(46.15)
eq(#__trapParts,2,"second_legal_trap_after_cooldown")
local second=__trapParts[2]
eq(second.Destroyed,nil,"new_trap_not_preemptively_destroyed")
send(pBlue,"PLACE_TRAP",6,{position={x=20,z=0}})
eq(#__trapParts,2,"replay_no_extra_trap_while_cooling")
setNear(pRed,V.new(20,5,0))
tick(46.2)
eq(pRed.Character.hum.WalkSpeed,10,"second_trap_applies_slow")
eq(second.Destroyed,true,"triggered_second_trap_removed")
local formerHum=pRed.Character.hum
pRed:LoadCharacter() -- engine test double: newly spawned character while slowed
eq(pRed.Character.hum.WalkSpeed,19,"fresh_character_base_speed")
tick(46.3)
eq(formerHum.WalkSpeed,19,"old_character_slow_record_cleaned")
eq(pRed.Character.hum.WalkSpeed,19,"fresh_character_not_inheriting_slow")
tick(66.5)
setNear(pBlue,V.new(20,5,0))
send(pBlue,"PLACE_TRAP",8,{})
tick(66.55)
eq(#__trapParts,3,"third_trap_legit_after_cooldown")
local third=__trapParts[3]
eq(third.Destroyed,nil,"owner_trap_live")
tick(86.6) -- third lifetime 25s; 20s cooldown elapsed but same seq 8 stale
send(pBlue,"PLACE_TRAP",8,{})
eq(#__trapParts,3,"stale_seq_rejected_even_after_cooldown")
-- Join two genuine extra fake players; ordinary team balancing creates RED,BLUE.
-- Remove the original owner while a BLUE teammate is still present:
-- cleanup must happen even when the game does NOT enter RESULTS.
local pRedBackup=makePlayer(203)
Players.users={pRed,pBlue,pRedBackup}
Players.PlayerAdded:Fire(pRedBackup)
eq(pRedBackup.Team.Name,"RED","standby_red_assigned")
local pBlueBackup=makePlayer(204)
Players.users={pRed,pBlue,pRedBackup,pBlueBackup}
Players.PlayerAdded:Fire(pBlueBackup)
eq(pBlueBackup.Team.Name,"BLUE","standby_blue_assigned")
-- Roblox PlayerRemoving fires before the player is removed from Players.
-- Retain the departing player inside GetPlayers during the event callback.
Players.PlayerRemoving:Fire(pBlue)
eq(last(pRed).phase,"ACTIVE","owner_exit_with_teammate_match_continues")
eq(third.Destroyed,true,"owner_exit_removes_trap_while_active")
Players.users={pRed,pRedBackup,pBlueBackup}
Players.PlayerRemoving:Fire(pBlueBackup)
Players.users={pRed,pRedBackup}
'''

# Exact in-memory mutations: the genuine source MUST detect each unsafe variant.
MUTANTS = (
    ("guardian_replay_seq_bypass", "Game", REPLAY_ANCHOR,
     REPLAY_ANCHOR.replace(
         "if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end",
         "if false then return end"), "GAME_S1_ASSERT_stale_seq_rejected_even_after_cooldown"),
    ("respawn_slow_state_leak", "Game", RESPAWN_ANCHOR,
     "if not alive or false or now >= record.untilAt then",
     "GAME_S1_ASSERT_old_character_slow_record_cleaned"),
    ("owner_trap_ghost_on_exit", "Game", OWNER_ANCHOR,
     "if false then", "GAME_S1_ASSERT_owner_exit_removes_trap_while_active"),
)


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def exact_replace(text: str, old: str, new: str, name: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"NONUNIQUE_OR_ABSENT_{name} count={text.count(old)}")
    return text.replace(old, new, 1)


def git_source(repo: Path, rel: str, expected_sha: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", RC + ":" + ROOT + rel],
        capture_output=True, check=False, timeout=20,
    )
    if proc.returncode:
        raise RuntimeError(f"OFFICIAL_PIN_UNAVAILABLE {rel}: {proc.stderr.decode(errors='replace')[-250:]}")
    digest = blob_sha(proc.stdout)
    if digest != expected_sha:
        raise RuntimeError(f"IMMUTABLE_SOURCE_MISMATCH {rel}: {digest}")
    return proc.stdout.decode("utf-8")


def prepare(repo: Path):
    code = {path: git_source(repo, path, pin) for path, pin in BLOBS.items()}
    namespace: dict = {"__name__": "_p0d_read_only_native_base"}
    exec(compile(code[RUNNER], RC + ":" + ROOT + RUNNER, "exec"), namespace)
    if namespace.get("BLOBS") != {k: v for k, v in BLOBS.items() if k != RUNNER}:
        raise RuntimeError("UPSTREAM_REAL_NATIVE_RUNNER_SOURCE_MISMATCH")
    namespace["RC"] = RC
    namespace["FAKES"] = exact_replace(
        namespace["FAKES"], "local Instance={}",
        "local __trapParts={}\nlocal Instance={}", "trap_object_ledger",
    )
    namespace["FAKES"] = exact_replace(
        namespace["FAKES"],
        'local obj={ClassName=class,__type="Instance"}',
        'local obj={ClassName=class,__type="Instance"}\n'
        ' if class=="Part" then table.insert(__trapParts,obj) end',
        "trap_creation_spy",
    )
    namespace["LUAU_TEST"] = exact_replace(
        namespace["LUAU_TEST"], ENTRY_MARKER, EXTRA_LUAU + "\n" + ENTRY_MARKER,
        "extended_lifecycle_test",
    )
    namespace["LUAU_TEST"] = exact_replace(
        namespace["LUAU_TEST"], ON_EXIT_ANCHOR,
        'eq(last(pRed).phase,"RESULTS","disconnect_ends_round")',
        "restore_terminal_expectation",
    )
    sources = {key: code[path] for path, key in SOURCE_KEYS.items()}
    return namespace, sources


def run_one(namespace, sources, luau: str, lua_path: Path):
    source = namespace["build"](sources)
    lua_path.write_text(source, encoding="utf-8")
    try:
        proc = subprocess.run(
            [luau, str(lua_path)], capture_output=True, text=True,
            check=False, timeout=35,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"NATIVE_LUAU_MISSING_OR_TIMED_OUT {e}") from e
    return proc.returncode, proc.stdout + proc.stderr


def execute(repo: Path, luau: str) -> None:
    namespace, sources = prepare(repo)
    with TemporaryDirectory(prefix="p0d_s1_trap_respawn_") as folder:
        script_path = Path(folder) / "pinned_real_game_extra.luau"
        status, output = run_one(namespace, sources, luau, script_path)
        match = re.search(r"P0D_NATIVE_ACTUAL_GAME_SERVER_LIFECYCLE_PASS assertions=(\d+)", output)
        if status != 0 or not match or int(match.group(1)) < 80:
            raise RuntimeError("ACTUAL_V6_TRAP_LIFECYCLE_BLOCKED " + output[-1300:])
        print(f"ACTUAL_V6_TRAP_LIFECYCLE_PASS assertions={match.group(1)}")
        for name, module, anchor, mutation, expected_failure in MUTANTS:
            bad = dict(sources)
            bad[module] = exact_replace(bad[module], anchor, mutation, name)
            status, output = run_one(namespace, bad, luau, script_path)
            if status == 0 or expected_failure not in output:
                raise RuntimeError(f"UNDETECTED_MUTATION {name}: {output[-600:]}")
            print("UNSAFE_NATIVE_MUTATION_REJECTED " + name)
        print("P0D_REAL_OFFICIAL_V6_TRAP_RESPAWN_REPLAY_NATIVE_PASS")


def selftest():
    assert len(RC) == 40 and len(BLOBS) == 6
    assert len(MUTANTS) == 3
    assert all(len(pin) == 40 for pin in BLOBS.values())
    assert blob_sha(b"abc") == "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert exact_replace("ok OLD end", "OLD", "NEW", "test") == "ok NEW end"
    for old, new in [("missing", "x"), ("a", "b")]:
        try:
            exact_replace("a a", old, new, "negative")
        except RuntimeError:
            pass
        else:
            raise AssertionError("missing/duplicate anchor was accepted")
    for marker in ("old_character_slow_record_cleaned",
                   "owner_exit_removes_trap_while_active",
                   "stale_seq_rejected_even_after_cooldown"):
        assert marker in EXTRA_LUAU
    print("P0D_PYTHON_SELFTEST_PASS checks=8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, help="Local cloned toy-wars-factory repository")
    parser.add_argument("--luau", help="Native Luau interpreter executable path")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.repo or not args.luau:
        parser.error("Supply BOTH --repo and --luau, or --selftest")
    execute(args.repo.resolve(), args.luau)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, UnicodeError) as exc:
        print("P0D_S1_V6_TRAP_NATIVE_BLOCKED " + str(exc), file=sys.stderr)
        sys.exit(2)
