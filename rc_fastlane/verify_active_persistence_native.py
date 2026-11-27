"""Run authenticated #1016 Native suites and the two actual retry regressions."""

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess

from apply_active_persistence_lifecycle import PACKAGE
from integrate import gitblob, sources


GAME = "server/Game.server.luau"
H2_FIXTURE = b"local roundReady,lobbyRecoveryRound={},{}\nlocal EXPERIMENTAL_FIVE_EGG_MODE=false\n"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def swap(body, old, new):
    assert body.count(old) == 1
    return body.replace(old, new, 1)


def source_patch(before, after, relative):
    return "".join(unified_diff(before.decode().splitlines(keepends=True),
                                after.decode().splitlines(keepends=True),
                                f"a/{relative}", f"b/{relative}")).encode()


def bind_current_fixture(program, suite, sources, runner):
    if suite != "ui10":
        return H2_FIXTURE + program
    game = sources[GAME].decode()
    helpers = runner.piece(game, "local function eligibleSoloPlayers()", "local function everybodyReady()")
    helpers += runner.piece(game, "local function scoreModeAllowed(", "local function modeVoteSnapshot()")
    mode_vote = b"local function applyModeVote(player: Player,data)\n"
    program = swap(program, mode_vote, helpers.encode() + mode_vote)
    initialize = b"  function player:SetAttribute(name,value)self.attributes[name]=value end\n"
    program = swap(program, initialize, initialize + b"  player.Team={Name=player.team}\n"
                   b"  function player:GetAttribute(name)return self.attributes[name] end\n")
    vote = b' e.vote(p,"SCORE_5",99);eq(e.voted(p),"SCORE_5");eq(e.notice(p),token)\n'
    program = swap(program, vote, b" e.newPlayer(142858) -- Two eligible humans are required by current Game.\n" + vote)
    hud = b"local function makeHud()\n"
    mocks = b" local gui,status={},{}\n local function button(...) return {} end\n"
    mocks += b" local UDim2={fromOffset=function(...)end,new=function(...)end}\n local Vector2={new=function(...)end}\n"
    return H2_FIXTURE + swap(program, hud, hud + mocks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dist", "author", "luau", "out", "reference-dist"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((PACKAGE / "source_lock.json").read_bytes())
    author = subprocess.check_output(["git", "-C", str(args.author), "rev-parse", "HEAD"]).decode().strip()
    assert author == config["source_origins"]["author_head"], "AUTHOR_HEAD"
    authored = args.author / "rc_fastlane"
    selector = load(authored / "apply_active_runtime_repairs.py", "author_selector")
    runner = load(authored / "features/active_runtime_repairs/regression/run_selected.py", "author_runner")
    lock, fixtures = runner.read_fixtures()
    continuation = runner.read_continuation_fixtures(selector)
    flags = json.loads((authored / "ACTIVE_RUNTIME_REPAIRS.json").read_bytes())
    mounted = sources(args.dist)
    for route, identity in config["routes"].items():
        assert gitblob(mounted[route]) == identity["after"], ("WRONG_LIFECYCLE_SOURCE", route)
    args.out.mkdir()
    results = {}

    def run(name, program, expected_exit=0):
        output = args.out / (name+".luau")
        output.write_bytes(program)
        completed = subprocess.run([str(args.luau), str(output)], capture_output=True, timeout=60)
        assert completed.returncode == expected_exit, (name, completed.stderr.decode())
        return completed.stdout.decode()

    for suite in runner.CONTINUATION_SUITES:
        program, _ = runner.render_selected_contract(suite, mounted, flags, lock, fixtures, continuation)
        program = bind_current_fixture(program, suite, mounted, runner)
        expected, exit_code, _ = runner.contract_expectation(suite, lock, continuation)
        logs = run(suite, program, exit_code)
        seen, _ = runner.parse(logs)
        identity = lambda rows: [(row["name"], row["status"]) for row in rows]
        assert identity(seen) == identity(expected), (suite, seen, expected)
        results[suite] = len(seen)
    assert sum(results.values()) == 112, results
    old_v3 = args.out / "reference_v3"
    selector.apply(args.reference_dist, old_v3, "rich51", True, True, True, persistence_continuation_v1=False)
    _, _, old_sources, old_flags, _ = runner.selected_input(old_v3)
    previous = 0
    for suite in runner.SUITES:
        program, _ = runner.render_selected_contract(suite, old_sources, old_flags, lock, fixtures)
        expected, exit_code, _ = runner.contract_expectation(suite, lock)
        logs = run("reference_v3_"+suite, program, exit_code)
        seen, _ = runner.parse(logs)
        actual = [(row["name"], row["status"]) for row in seen]
        assert actual == [(row["name"], row["status"]) for row in expected], (suite, actual, expected)
        previous += len(seen)
    assert previous == 54, previous
    print("ACTIVE_RICH51_PERSISTENCE_AUTHOR_V3_CONTROL_54_PASS")

    diagnostic_passes = diagnostic_failures = 0
    for suite in runner.COMPATIBILITY_SUITES:
        program, _ = runner.render_selected_contract(suite, mounted, flags, lock, fixtures, continuation)
        program = bind_current_fixture(program, suite, mounted, runner)
        expected, exit_code, _ = runner.contract_expectation(suite, lock, continuation, compatibility=True)
        logs = run(suite, program, exit_code)
        seen, _ = runner.parse(logs)
        compare = [(row["name"], row["status"]) for row in seen]
        assert compare == [(row["name"], row["status"]) for row in expected], (suite, compare, expected)
        diagnostic_passes += sum(row["status"] == "PASS" for row in seen)
        diagnostic_failures += sum(row["status"] == "FAIL" for row in seen)
    assert (diagnostic_passes, diagnostic_failures) == (51, 14), (diagnostic_passes, diagnostic_failures)
    print("ACTIVE_RICH51_PERSISTENCE_ORIGINAL_65_DIAGNOSTIC_51_PASS_14_EXPECTED_FAIL")
    probe = (PACKAGE / "regression.luau").read_bytes()
    assert sha256(probe).hexdigest() == config["native_regression_sha256"], "REGRESSION_SOURCE"
    program, _ = runner.render_equipment_contract("ui10", mounted, continuation[2])
    program = bind_current_fixture(program, "ui10", mounted, runner)
    invoke = bytes([10]).join((b"", b"pendingRecovery(true)", b"settledRound(true)", b"supersededFailure()", b""))
    logs = run("late_ack_and_round_settlement", program + probe + invoke)
    measured = [line for line in logs.splitlines() if line.startswith(("RECOVERY_", "SETTLEMENT"))]
    assert len(measured) == 11, measured
    print("ACTIVE_RICH51_PERSISTENCE_NATIVE_AUTHOR_112_PASS", json.dumps(results, sort_keys=True))
    for line in measured:
        print(line)
    print("ACTIVE_RICH51_LIFECYCLE_LATEST_ACK_AND_MATCH_START_EQUIP_PASS")


if __name__ == "__main__":
    main()
