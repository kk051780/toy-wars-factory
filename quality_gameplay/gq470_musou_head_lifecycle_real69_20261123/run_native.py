#!/usr/bin/env python3
"""Execute byte-exact MUSOU visual bodies against one shared lifecycle fixture.

This source-only runner performs one baseline start and, when supplied, one
candidate start. It saves raw evidence and fails closed on missing assertions,
wrong baseline identities, unexpected baseline failures, candidate failures, or
input drift. It never modifies a source file or substitutes modeled render code.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

AURA_PIN = "b2c279371a8fd986b929883290aae58ed9acdafb7cd48f878eae3785e4acccab"
CONTROLLER_PIN = "13495f0c816f88a78f62e8c40ec5a79c7140c2057b33037695d6073e527768c9"
CLIENT_MARKER = b"--[[MUSOU_EXACT_AURA_CLIENT_BODY]]\n"
CONTROLLER_MARKER = b"--[[MUSOU_EXACT_AURA_CONTROLLER_BODY]]\n"
EXPECTED_CASES = frozenset({
    "control_head_present_initializes",
    "existing_character_head_arrival_renders_without_new_snapshot",
    "new_character_head_arrival_renders_without_new_snapshot",
    "control_later_snapshot_recovers_missing_aura",
    "control_off_before_head_remains_off",
    "control_old_avatar_defer_does_not_resurrect",
    "removed_player_deferred_render_does_not_resurrect",
    "removed_character_deferred_render_does_not_resurrect",
    "same_model_replaced_head_retargets_and_cleans",
    "control_foreign_child_does_not_activate_aura",
    "control_phase_role_updates_reuse_original_visual_contract",
    "control_unrelated_child_unchanged_head_no_reburst",
    "control_lifecycle_connections_bounded_and_disconnected",
})
EXPECTED_BASELINE_FAILURES = frozenset({
    "existing_character_head_arrival_renders_without_new_snapshot",
    "new_character_head_arrival_renders_without_new_snapshot",
    "removed_player_deferred_render_does_not_resurrect",
    "removed_character_deferred_render_does_not_resurrect",
    "same_model_replaced_head_retargets_and_cleans",
})


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": sha(data)}


def build_program(template: bytes, aura: bytes, controller: bytes,
                  aura_path: Path, controller_path: Path) -> tuple[bytes, list[dict]]:
    if template.count(CLIENT_MARKER) != 1 or template.count(CONTROLLER_MARKER) != 1:
        raise ValueError("Fixture must have exactly one marker for each full body")
    before, remainder = template.split(CLIENT_MARKER)
    middle, after = remainder.split(CONTROLLER_MARKER)
    program = before + aura + middle + controller + after
    aura_start = len(before)
    controller_start = len(before) + len(aura) + len(middle)
    spans = []
    for name, path, start, source in [
        ("AuraClient", aura_path, aura_start, aura),
        ("AuraController", controller_path, controller_start, controller),
    ]:
        end = start + len(source)
        if program[start:end] != source:
            raise AssertionError("Source body was changed during embedding")
        spans.append({"kind": name, "source_path": str(path.resolve()),
                      "start_byte": start, "end_byte_exclusive": end,
                      "bytes": len(source), "sha256": sha(source)})
    return program, spans


def execute(name: str, vm: Path, output: Path, template: bytes, aura: bytes,
            controller: bytes, aura_path: Path, controller_path: Path,
            expected_failures: frozenset[str]) -> dict:
    program, spans = build_program(template, aura, controller, aura_path, controller_path)
    program_path = output / f"{name}.exact.luau"
    stdout_path = output / f"{name}.stdout.txt"
    stderr_path = output / f"{name}.stderr.txt"
    program_path.write_bytes(program)
    command = [str(vm), str(program_path)]
    started_at = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, capture_output=True,
                            text=True, timeout=15, check=False)
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    checks = []
    for line in result.stdout.splitlines():
        pieces = line.split("\t", 2)
        if pieces[0] in ("PASS", "FAIL") and len(pieces) == 3:
            checks.append({"name": pieces[1], "passed": pieces[0] == "PASS", "detail": pieces[2]})
    names = [check["name"] for check in checks]
    failed = frozenset(check["name"] for check in checks if not check["passed"])
    passed_count = sum(check["passed"] for check in checks)
    expected_exit = 1 if expected_failures else 0
    expected_summary = f"SUMMARY\t{passed_count} PASS / {len(failed)} FAIL / {len(checks)} expectations"
    violations = []
    if len(names) != len(set(names)):
        violations.append("Duplicate expectation labels")
    if set(names) != EXPECTED_CASES:
        violations.append("Missing or unrecognized expectation labels")
    if failed != expected_failures:
        violations.append("Failed expectation set differs from the explicitly required set")
    if result.returncode != expected_exit:
        violations.append(f"Native exit {result.returncode} differs from expected {expected_exit}")
    if result.stdout.splitlines().count(expected_summary) != 1:
        violations.append("Missing, repeated, or inconsistent summary")
    if expected_failures and "Lifecycle regression expectations failed for the selected exact source bodies" not in result.stderr:
        violations.append("Expected baseline assertion was not the reported Native error")
    if not expected_failures and result.stderr:
        violations.append("Candidate emitted unexpected stderr")
    return {
        "name": name,
        "command": command,
        "cwd": str(Path.cwd()),
        "started_at_utc": started_at,
        "program": identity(program_path),
        "source_spans": spans,
        "stdout": identity(stdout_path),
        "stderr": identity(stderr_path),
        "native_exit": result.returncode,
        "expected_native_exit": expected_exit,
        "expectations": checks,
        "expected_failures": sorted(expected_failures),
        "actual_failures": sorted(failed),
        "pass_count": passed_count,
        "fail_count": len(failed),
        "evidence_matches_expectation": not violations,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aura-client", type=Path, required=True)
    parser.add_argument("--baseline-controller", type=Path, required=True)
    parser.add_argument("--luau", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("native_fixture.luau"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--baseline-only", action="store_true")
    mode.add_argument("--candidate-controller", type=Path)
    parser.add_argument("--candidate-sha256")
    args = parser.parse_args()
    args.luau = args.luau.resolve()
    args.output = args.output.resolve()
    if args.candidate_controller and not re.fullmatch(r"[0-9a-f]{64}", args.candidate_sha256 or ""):
        parser.error("Candidate execution requires its exact --candidate-sha256")
    if args.baseline_only and args.candidate_sha256:
        parser.error("--candidate-sha256 is invalid for baseline-only execution")
    inputs = [args.aura_client, args.baseline_controller, args.fixture, args.luau]
    if args.candidate_controller:
        inputs.append(args.candidate_controller)
    before = [identity(path) for path in inputs]
    aura = args.aura_client.read_bytes()
    original = args.baseline_controller.read_bytes()
    template = args.fixture.read_bytes()
    if sha(aura) != AURA_PIN:
        raise ValueError("AuraClient is not the exact unmodified H93 source")
    if sha(original) != CONTROLLER_PIN:
        raise ValueError("Baseline Controller is not the exact H93 source")
    candidate = args.candidate_controller.read_bytes() if args.candidate_controller else None
    if candidate is not None and sha(candidate) != args.candidate_sha256:
        raise ValueError("Candidate Controller does not match the specified exact digest")
    args.output.mkdir(parents=True, exist_ok=True)
    baseline = execute("baseline", args.luau, args.output, template, aura, original,
                       args.aura_client, args.baseline_controller, EXPECTED_BASELINE_FAILURES)
    runs = [baseline]
    if candidate is not None:
        runs.append(execute("candidate", args.luau, args.output, template, aura, candidate,
                            args.aura_client, args.candidate_controller, frozenset()))
    after = [identity(path) for path in inputs]
    unchanged = before == after
    success = unchanged and all(run["evidence_matches_expectation"] for run in runs)
    receipt = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_mode": "BASELINE_REPRO_ONLY" if args.baseline_only else "BASELINE_AND_CANDIDATE",
        "formal_source_base": "93a1147561a531610ac1609ebc68cc0ecf546623",
        "runner": identity(Path(__file__)),
        "inputs_before": before,
        "inputs_after": after,
        "inputs_unchanged": unchanged,
        "native_starts": len(runs),
        "baseline_expected_red_reproduced": baseline["evidence_matches_expectation"],
        "candidate_all_expectations_passed": len(runs) == 2 and runs[1]["evidence_matches_expectation"],
        "run_valid": success,
        "runs": runs,
        "limits": [
            "Full real source bodies with Roblox API/signal/defer doubles; no actual engine replication or rendering",
            "Native executable identity is recorded; its build provenance is the caller's responsibility",
            "No Studio, multiplayer, Android, ART, FUN, owner acceptance, registered review, or RC adoption claim",
            "Head replacement and removal timing are source boundary checks, not observed live defects",
        ],
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for run in runs:
        print(f"{run['name']}: {run['pass_count']} PASS / {run['fail_count']} FAIL; "
              f"Native exit {run['native_exit']}; expected set matched={run['evidence_matches_expectation']}")
        for violation in run["violations"]:
            print("  " + violation)
    print(f"inputs_unchanged={unchanged}; native_starts={len(runs)}; run_valid={success}")
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"FAIL_CLOSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
