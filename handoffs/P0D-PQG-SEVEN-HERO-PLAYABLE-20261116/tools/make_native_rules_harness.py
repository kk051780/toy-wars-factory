#!/usr/bin/env python3
"""Build a *real Luau VM* functional smoke from the unchanged pure Rules module.

Only for local/offline CI; never generate or replace the actual server game file.
The module's last top-level return is replaced in an isolated /tmp script,
so native Luau's CLI can execute all its functions without Roblox Studio.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EGGRUMBLE_CastleMatchRules.luau"
TESTS = ROOT / "tests" / "eggrumble_rules_native_cases.luau"


def build(output: Path) -> None:
    source = SOURCE.read_text(encoding="utf-8").rstrip()
    tests = TESTS.read_text(encoding="utf-8")
    if not source.endswith("\nreturn M"):
        raise RuntimeError("EGGRUMBLE rules source no longer ends in an isolated return M")
    body = source[: -len("\nreturn M")]
    code = body + "\nlocal Rules=M\n" + tests + "\n"
    if "local Rules=M" not in code or "function M.auditEggConservation" not in code:
        raise RuntimeError("unexpected module source contract")
    output.write_text(code, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    build(arguments.out)
    print(f"created isolated native Luau functional harness: {arguments.out}")
