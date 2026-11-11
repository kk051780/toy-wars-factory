#!/usr/bin/env python3
"""Execute exact pinned S1 LobbyTeamRecovery in official native Luau interpreter.

Pure Luau assertions only. This does NOT model Roblox Player, Team, server loop,
DataModel or Roblox Studio gameplay. The official CLI is built separately in CI.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile

EXPECTED_ORIGINAL_SHA256 = "35c546f33e0454ceaf7fa26cf5ee44763673c6764906cc249ef282bb096ea404"
EXPECTED_NATIVE_MARKER = "P0D_LOBBY_NATIVE_SEMANTIC_PASS"
HERE = Path(__file__).resolve().parents[1]


def run(binary: Path, lua: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(binary), str(lua)], capture_output=True,
                          text=True, encoding="utf-8", timeout=90, check=False)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--luau", type=Path, required=True)
    p.add_argument("--planner", type=Path, required=True)
    args = p.parse_args()
    luau = args.luau.resolve(strict=True)
    planner = args.planner.resolve(strict=True)
    source_bytes = planner.read_bytes()
    if hashlib.sha256(source_bytes).hexdigest() != EXPECTED_ORIGINAL_SHA256:
        raise SystemExit("FAIL_ORIGINAL_LUAU_SOURCE_HASH")
    source = source_bytes.decode("utf-8")
    if source.count("return LobbyTeamRecovery") != 1 or not source.startswith("--!strict\n"):
        raise SystemExit("FAIL_ORIGINAL_LUAU_SOURCE_LAYOUT")
    body = (HERE / "tests/lobby_native_cases.luau").read_text(encoding="utf-8")
    if not body.startswith("--!strict\n"):
        raise SystemExit("FAIL_NATIVE_TEST_BODY_INVALID")
    # Native Luau CLI can execute the original module without Roblox's require.
    # Preserve source EXACTLY; wrapper only provides local function scope for return.
    full_test = "local LobbyTeamRecovery = (function()\n" + source + "\nend)()\n" + body
    with tempfile.TemporaryDirectory(prefix="p0d_luau_replay_") as tmp:
        tmpdir = Path(tmp)
        good = tmpdir / "good.luau"
        bad = tmpdir / "expected_failure.luau"
        test = tmpdir / "actual_planner_execution.luau"
        good.write_text('local function plus(x: number): number return x + 1 end\nassert(plus(2)==3)\nprint("NATIVE_POSITIVE_CONTROL_PASS")\n', encoding="utf-8")
        bad.write_text('error("INTENTIONAL_NATIVE_RUNTIME_FAILURE")\n', encoding="utf-8")
        test.write_text(full_test, encoding="utf-8")
        positive, negative, result = run(luau, good), run(luau, bad), run(luau, test)
    if positive.returncode != 0 or "NATIVE_POSITIVE_CONTROL_PASS" not in positive.stdout:
        print("FAIL_NATIVE_INTERPRETER_POSITIVE_CONTROL", positive.stderr[-1000:], file=sys.stderr)
        return 1
    if negative.returncode == 0 or "INTENTIONAL_NATIVE_RUNTIME_FAILURE" not in negative.stderr+negative.stdout:
        print("FAIL_NATIVE_INTERPRETER_NEGATIVE_CONTROL", negative.stderr[-1000:], file=sys.stderr)
        return 1
    print("NATIVE_LUAU_POSITIVE_NEGATIVE_CONTROLS_PASS", flush=True)
    if result.returncode != 0 or EXPECTED_NATIVE_MARKER not in result.stdout:
        print("FAIL_NATIVE_LUAU_LOBBY_SEMANTICS", result.stderr[-3500:],result.stdout[-1500:], file=sys.stderr)
        return 1
    m = re.search(r"assertions=(\d+)", result.stdout)
    if not m or int(m.group(1)) < 5000 or "exhaustive=511" not in result.stdout or "seeded_fuzz=512" not in result.stdout:
        print("FAIL_NATIVE_LUAU_OUTPUT_COUNT", result.stdout[-1200:], file=sys.stderr)
        return 1
    print(result.stdout.strip(), flush=True)
    print("LUAU_NATIVE_RUNTIME_SEMANTIC_PASS original_module_sha256="+EXPECTED_ORIGINAL_SHA256, flush=True)
    print("Roblox_Studio=NOT_TESTED Game_Server=NOT_TESTED True_PvP=NOT_TESTED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
