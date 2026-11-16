#!/usr/bin/env python3
"""Concatenate byte-exact policy source and native Luau assertions; no text rewriting."""
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument("--out",required=True)
args=p.parse_args()
src=(ROOT/"EGGRUMBLE_NeutralEncounterFairness.luau").read_text(encoding="utf-8")
suffix="\nreturn Fair\n"
assert src.endswith(suffix), "source return trailer changed: stop, do not run stale harness"
cases=(ROOT/"tests/native_cases.luau").read_text(encoding="utf-8")
Path(args.out).write_text(src[:-len(suffix)]+"\n"+cases,encoding="utf-8")
print("EXACT_SOURCE_NATIVE_HARNESS_PREPARED")
