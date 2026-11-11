#!/usr/bin/env python3
"""Read-only official native Luau syntax gate for an immutable S1 source snapshot.

This only confirms parsing/bytecode compilation by luau-lang/luau's official CLI.
It cannot run Roblox DataModel APIs, 2-client gameplay, or Studio physics.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPO / "handoffs/P0D-S1-D07D08-CORRECTED-SPATIAL-COMPOSITE-20261111-01/candidate/src"
EXPECTED_LUAU = 17
UPSTREAM_COMMIT = "f46d879e28302a430029304f7f6a162aed66f103"
GAME_COMMIT = "ff291d7a5e6dc53e841552d1abc3cbdf9a805f48"


def compile_file(compiler: Path, source: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(compiler), "-O0", str(source)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )


def main(args: list[str]) -> int:
    if len(args) != 1:
        print("usage: native_luau_syntax_gate.py <native luau-compile executable>", file=sys.stderr)
        return 2
    compiler = Path(args[0]).resolve()
    if not compiler.is_file() or not SOURCE_ROOT.is_dir():
        print("FAIL_MISSING_OFFICIAL_COMPILER_OR_SOURCE", file=sys.stderr)
        return 2
    inputs = sorted(SOURCE_ROOT.rglob("*.luau"))
    if len(inputs) != EXPECTED_LUAU or len({p.resolve() for p in inputs}) != EXPECTED_LUAU:
        print(f"FAIL_SOURCE_COUNT expected={EXPECTED_LUAU} got={len(inputs)}", file=sys.stderr)
        return 2
    if any(not x.is_file() or x.is_symlink() for x in inputs):
        print("FAIL_SYMLINK_OR_NONREGULAR_SOURCE", file=sys.stderr)
        return 2

    # Verify native compiler can recognize both known-good and known-bad input;
    # a fake command that exits 0 for every file must never produce PASS.
    with tempfile.TemporaryDirectory(prefix="p0d_native_luau_") as name:
        good = Path(name) / "valid.luau"
        bad = Path(name) / "broken.luau"
        good.write_text("local function f(x: number): number\n    return x + 1\nend\nreturn f(1)\n")
        bad.write_text("local =\n")
        result_good = compile_file(compiler, good)
        result_bad = compile_file(compiler, bad)
        if result_good.returncode != 0 or result_bad.returncode == 0:
            print("FAIL_NATIVE_COMPILER_POSITIVE_NEGATIVE_CONTROL", file=sys.stderr)
            print("good:", result_good.stderr[-500:], "bad:", result_bad.stderr[-500:],
                  file=sys.stderr)
            return 2
        print("NATIVE_LUAU_COMPILER_CONTROLS_PASS", flush=True)

    for i, path in enumerate(inputs, 1):
        p = compile_file(compiler, path)
        if p.returncode != 0:
            print(f"FAIL_NATIVE_LUAU_PARSE:{path.relative_to(REPO)}:{p.stderr[-1600:]}",
                  file=sys.stderr)
            return 2
        print(f"NATIVE_LUAU_PARSE_PASS:{i}/{EXPECTED_LUAU}:{path.relative_to(SOURCE_ROOT)}",
              flush=True)
    print(json.dumps({
        "format": "P0D_S1_NATIVE_LUAU_SYNTAX_QA_V1",
        "result": "PASS_OFFICIAL_NATIVE_LUAU_PARSE_ONLY",
        "source_game_commit": GAME_COMMIT,
        "compiler_source_commit": UPSTREAM_COMMIT,
        "luau_files_compiled": EXPECTED_LUAU,
        "native_compile_errors": 0,
        "positive_control": "PASS",
        "invalid_syntax_rejected": True,
        "roblox_runtime": "NOT_TESTED",
        "two_client_studio": "NOT_TESTED",
        "public_release_approved": False
    }, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
