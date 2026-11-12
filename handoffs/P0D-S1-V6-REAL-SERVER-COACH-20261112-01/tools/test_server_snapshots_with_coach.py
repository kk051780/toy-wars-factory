#!/usr/bin/env python3
"""Real seven-Luau-source Game SNAPSHOT -> child Guardian Coach integration QA.

Actual six frozen V6 Game/Map/Rules/Lobby/Config/TrapRules modules and original
vetted Guardian FirstMinuteModel execute together under native Luau. Only the
Roblox external-engine services are test doubles. No production source mutation.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

OFFICIAL = "1263a03701211a652b99b91d2339575dc8104eff"
NATIVE_BASE = "84d061d81ffd28418f6e28e9e85bb684dd0daaf7"
NATIVE_BASE_SHA = "586aaa9b3498f9b28d283211d6f1b5fcd3af1fbe"
NATIVE_BASE_PATH = (
    "handoffs/P0D-S1-V6-REAL-MAP-TRAP-COMPOSED-20261112-01/"
    "tools/run_v6_game_map_trap.py"
)
COACH_SOURCE = "e29d37737890671d458072bebe729127878700f6"
COACH_BLOB = "967ea52df79884e6c73e3e0952d5a97de0d1796e"
COACH_PATH = (
    "handoffs/P0D-S1-GUARDIAN-TRAP-FTUE-COPY-20261112-01/"
    "candidate/src/shared/FirstMinuteModel.luau"
)
GAME_ANCHOR = "local __real_game_controller=(function()\n"
SNAPSHOT_POINTS = {
    'eq(last(pBlue).phase,"LOBBY","blue_lobby")': r'''
local redCoach=__real_Coach.new()
local blueCoach=__real_Coach.new()
eq(__real_Coach.consume(redCoach,last(pRed),0),true,"real_red_lobby_coach_consumes")
eq(__real_Coach.consume(blueCoach,last(pBlue),0),true,"real_blue_lobby_coach_consumes")
eq(__real_Coach.view(redCoach,0).title,"まず役職をえらぼう","real_lobby_coach_title")
eq(redCoach.serial,0,"real_lobby_coach_serial")
''',
    'eq(last(pBlue).role,"GUARDIAN","role_lobby_allowed")': r'''
eq(__real_Coach.consume(blueCoach,last(pBlue),.1),true,"real_guardian_role_snapshot_consumes")
eq(blueCoach.latest.role,"GUARDIAN","real_guardian_role_reflected")
''',
    'eq(last(pRed).phase,"COUNTDOWN","two_player_countdown")': r'''
eq(__real_Coach.consume(redCoach,last(pRed),1),true,"real_countdown_snapshot_consumes")
eq(__real_Coach.view(redCoach,1).title,"もうすぐ対戦！","real_countdown_view")
''',
    'eq(last(pRed).serial,1,"first_round")': r'''
eq(__real_Coach.consume(redCoach,last(pRed),7),true,"real_red_first_active_consumes")
eq(__real_Coach.consume(blueCoach,last(pBlue),7),true,"real_blue_first_active_consumes")
eq(__real_Coach.view(redCoach,7).title,"敵のお城の卵をねらおう！","real_red_raider_active_title")
eq(__real_Coach.view(blueCoach,7).title,"守護：卵を守ろう！","real_blue_guardian_active_title")
eq(string.find(__real_Coach.view(blueCoach,7).detail,"罠ボタン")~=nil,
   true,"real_blue_guardian_trap_button_help")
eq(last(pBlue).trapCooldown,0,"real_guardian_initial_trap_cooldown")
''',
    'eq(last(pRed).carrying,"BLUE","stolen_enemy_egg")': r'''
eq(__real_Coach.consume(redCoach,last(pRed),10),true,"real_red_egg_carrier_consumes")
eq(__real_Coach.view(redCoach,10).title,"卵をゲット！","real_red_egg_carrier_title")
eq(redCoach.carried,true,"real_coach_notes_egg_carry")
''',
    'eq(last(pRed).scores.RED,1,"first_score")': r'''
eq(__real_Coach.consume(redCoach,last(pRed),12),true,"real_red_scoring_consumes")
eq(redCoach.scored,true,"real_red_scored_state")
eq(__real_Coach.view(redCoach,12).title,"得点できたね！","real_red_scoring_title")
''',
    'eq(last(pRed).phase,"RESULTS","winning_result_phase")': r'''
local oldResultsSnapshot=last(pRed)
eq(__real_Coach.consume(redCoach,oldResultsSnapshot,14),true,"real_result_consumes")
local resultView=__real_Coach.view(redCoach,14)
eq(resultView and resultView.title or "", "つぎの対戦も挑戦しよう！",
   "real_results_view")
''',
    'eq(last(pRed).serial,2,"new_serial_for_rematch")': r'''
eq(__real_Coach.consume(redCoach,last(pRed),23.1),true,"real_round2_red_snapshot_consumes")
eq(__real_Coach.consume(blueCoach,last(pBlue),23.1),true,"real_round2_blue_snapshot_consumes")
eq(redCoach.serial,2,"real_round2_coach_serial")
eq(redCoach.scored,false,"real_round2_forgets_old_score")
eq(redCoach.carried,false,"real_round2_forgets_old_carrier")
eq(blueCoach.activeAt,23.1,"real_guardian_round2_reset_time")
eq(__real_Coach.view(redCoach,23.1).title,"敵のお城の卵をねらおう！",
   "real_round2_red_help_resets")
eq(__real_Coach.view(blueCoach,23.1).title,"守護：卵を守ろう！",
   "real_round2_blue_help_resets")
eq(__real_Coach.consume(redCoach,oldResultsSnapshot,24),false,
   "real_old_result_snapshot_rejected_after_rematch")
eq(redCoach.serial,2,"real_old_serial_cannot_roll_back")
eq(__real_Coach.consume(redCoach,
   {kind="SNAPSHOT",serial=2,phase="ACTIVE",scores={},team="RED",
    role="RAIDER",carrying="",time=300},24),false,
   "real_malformed_server_snapshot_rejected")
eq(redCoach.latest.serial,2,"real_malformed_does_not_replace_latest")
eq(__real_Coach.view(redCoach,86).visible,false,
   "real_coach_autohides_after_one_minute")
__real_Coach.setHidden(redCoach,true)
eq(__real_Coach.view(redCoach,24).visible,false,"real_coach_manual_dismiss")
__real_Coach.setHidden(redCoach,false)
eq(__real_Coach.view(redCoach,86).visible,true,"real_coach_manual_help_after_minute")
''',
}
MUTANTS = [
    (
        "guardian_role_ignored_for_first_hint",
        'if elapsed < 12 then\n        if s.role == "GUARDIAN" then',
        'if elapsed < 12 then\n        if false then',
        "GAME_S1_ASSERT_real_blue_guardian_active_title",
    ),
    (
        "egg_carrier_tutorial_ignored",
        'if s.carrying ~= "" then\n        return {title = "卵をゲット！"',
        'if false then\n        return {title = "卵をゲット！"',
        "GAME_S1_ASSERT_real_red_egg_carrier_title",
    ),
    (
        "own_first_score_not_recorded",
        'if own > state.initialScore then state.scored = true end',
        'if false then state.scored = true end',
        "GAME_S1_ASSERT_real_red_scored_state",
    ),
    (
        "results_help_suppressed",
        'if s.phase == "RESULTS" then\n        return {title = "つぎの対戦も挑戦しよう！"',
        'if false then\n        return {title = "つぎの対戦も挑戦しよう！"',
        "GAME_S1_ASSERT_real_results_view",
    ),
    (
        "old_serial_packet_not_rejected",
        'packet.serial < state.serial',
        'packet.serial < -999',
        "GAME_S1_ASSERT_real_old_result_snapshot_rejected_after_rematch",
    ),
    (
        "first_minute_overlay_never_autohides",
        'if elapsed > 60 and not state.manualHelp then',
        'if false then',
        "GAME_S1_ASSERT_real_coach_autohides_after_one_minute",
    ),
]


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    ).hexdigest()


def exact(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)
    if found != 1:
        raise RuntimeError(f"NON_UNIQUE_SOURCE_ANCHOR_{label}_{found}")
    return text.replace(old, new, 1)


def git_read(repo: Path, ref: str, file: str, sha: str) -> str:
    p = subprocess.run(
        ["git", "-C", str(repo), "show", ref + ":" + file],
        capture_output=True, check=False, timeout=25
    )
    if p.returncode or blob_sha(p.stdout) != sha:
        raise RuntimeError("IMMUTABLE_ORIGINAL_LUAU_BLOB_NOT_FOUND_" + file)
    return p.stdout.decode("utf8")


def prepare(repo: Path):
    upstream = git_read(repo, NATIVE_BASE, NATIVE_BASE_PATH, NATIVE_BASE_SHA)
    env = {"__name__": "_p0d_seven_actual_sources_qa"}
    exec(compile(upstream, NATIVE_BASE_PATH, "exec"), env)
    if env["OFFICIAL"] != OFFICIAL or len(env["BLOBS"]) != 6:
        raise RuntimeError("UPSTREAM_SIX_REAL_GAME_MODULE_SELECTION_CHANGED")
    original = git_read(repo, COACH_SOURCE, COACH_PATH, COACH_BLOB)
    base, sources = env["prepare"](repo)
    for needle, extra in SNAPSHOT_POINTS.items():
        base["LUAU_TEST"] = exact(
            base["LUAU_TEST"], needle, needle + "\n" + extra,
            "insert_real_server_client_snapshot"
        )
    return env, base, sources, original


def compose(env, base, sources, coach_source):
    body = env["build"](base, sources)
    body = exact(
        body, GAME_ANCHOR,
        base["wrap"]("__real_Coach", coach_source) + GAME_ANCHOR,
        "load_original_child_guardian_coach_with_real_server"
    )
    return body


def run(luau: str, path: Path, env, base, sources, coach_source):
    path.write_text(compose(env, base, sources, coach_source), encoding="utf8")
    try:
        p = subprocess.run(
            [luau, str(path)], capture_output=True, text=True,
            check=False, timeout=45
        )
    except (OSError, subprocess.TimeoutExpired) as ex:
        raise RuntimeError("GENUINE_LUAU_RUNNER_UNAVAILABLE " + str(ex)) from ex
    return p.returncode, p.stdout + p.stderr


def execute(repo: Path, luau: str):
    env, base, original_sources, original_coach = prepare(repo)
    with TemporaryDirectory(prefix="p0d_s1_snapshot_coach_") as temp:
        file = Path(temp) / "exact_real_server_snapshot_and_coach.luau"
        rc, log = run(luau, file, env, base, original_sources, original_coach)
        match = re.search(
            r"P0D_NATIVE_ORIGINAL_GAME_MAP_COMPOSED_PASS assertions=(\d+)", log
        )
        if rc or not match or int(match.group(1)) < 130:
            raise RuntimeError("SEVEN_REAL_ORIGINAL_LUAU_SNAPSHOT_CONTRACT_FAILED "
                               + log[-2100:])
        print("P0D_S1_REAL_SERVER_TO_CHILD_COACH_NATIVE_PASS assertions=" + match.group(1))
        for name, old, unsafe, expected in MUTANTS:
            modified_coach = exact(original_coach, old, unsafe, name)
            returncode, log = run(
                luau, file, env, base, original_sources, modified_coach
            )
            if returncode == 0 or expected not in log:
                raise RuntimeError(
                    "CHILD_COACH_UNSAFE_SOURCE_MUTANT_NOT_REJECTED_" + name
                    + " " + log[-1300:]
                )
            print("P0D_S1_REAL_CHILD_COACH_UNSAFE_MUTANT_REJECTED " + name)
        print("P0D_S1_SEVEN_ORIGINAL_MODULES_SNAPSHOT_COACH_SUCCESS mutants="
              + str(len(MUTANTS)))


def selftest():
    assert len(OFFICIAL) == len(COACH_SOURCE) == len(NATIVE_BASE) == 40
    assert len(COACH_BLOB) == len(NATIVE_BASE_SHA) == 40
    assert blob_sha(b"abc") == "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f"
    assert exact("a@b", "@", "-", "positive") == "a-b"
    for text, key in [("once", "missing"), ("twice twice", "twice")]:
        try:
            exact(text, key, "bad", "negative")
        except RuntimeError:
            pass
        else:
            raise AssertionError("NON_UNIQUE_ANCHOR_NOT_REJECTED")
    assert len(SNAPSHOT_POINTS) == 8 and len(MUTANTS) == 6
    assert len({m[0] for m in MUTANTS}) == 6
    for s in ("real_blue_guardian_active_title", "real_red_scored_state",
              "real_old_result_snapshot_rejected_after_rematch"):
        assert any(s in snippet for snippet in SNAPSHOT_POINTS.values())
    print("P0D_S1_SEVEN_MODULE_SOURCE_CONTRACT_SELFTEST_PASS checks=9")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path)
    p.add_argument("--luau")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.repo or not args.luau:
        p.error("provide --repo and --luau for native original-source game run")
    execute(args.repo.resolve(), args.luau)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, UnicodeError, OSError) as e:
        print("P0D_S1_REAL_CHILD_COACH_NATIVE_BLOCKED " + str(e), file=sys.stderr)
        sys.exit(2)
