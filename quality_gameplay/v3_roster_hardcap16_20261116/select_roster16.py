#!/usr/bin/env python3
"""Select exactly two original #482 roster limit guards, no second Game owner.

The original 16-player invariant existed as MAX_HERO_SLOTS=16, but two guards
still allowed 32. This selector makes both guards consult the single constant.
It fails closed on any original source/blob drift.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

AUTHOR_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_BLOB = "27da5ca1e9e6d9a7afe0674030e387f094ee7492"
OLD = (
    'limit>=2 and limit<=32,"invalid preview slot cap"',
    '#roster>=2 and #roster<=32,"invalid roster size"',
)
NEW = (
    'limit>=2 and limit<=M.MAX_HERO_SLOTS,"invalid preview slot cap"',
    '#roster>=2 and #roster<=M.MAX_HERO_SLOTS,"invalid roster size"',
)
NATIVE_CASES = r"""
local Rules=M
local roster=Rules.makeRoster(Rules.MODE_TEAM,{"HUMAN"},16)
assert(#roster==16,"valid 16-slot TEAM must remain supported")
local game=Rules.new(Rules.MODE_TEAM,roster,24)
Rules.start(game)
assert(game.phase=="ACTIVE","existing TEAM gameplay must still start")
local br={}
for i=1,16 do table.insert(br,{id="BR_"..tostring(i)}) end
local gameBR=Rules.new(Rules.MODE_ROYALE,br,24)
Rules.start(gameBR)
assert(gameBR.phase=="ACTIVE","valid 16-slot BR must remain supported")
local canMake17=pcall(function() Rules.makeRoster(Rules.MODE_TEAM,{"HUMAN"},17) end)
local canMake32=pcall(function() Rules.makeRoster(Rules.MODE_TEAM,{"HUMAN"},32) end)
local extra={}
for i=1,17 do table.insert(extra,{id="EXTRA_"..tostring(i)}) end
local canStart17=pcall(function() Rules.new(Rules.MODE_ROYALE,extra,24) end)
assert(canMake17==EXPECT_OVERLIMIT,"17-slot roster differential mismatch")
assert(canMake32==EXPECT_OVERLIMIT,"32-slot roster differential mismatch")
assert(canStart17==EXPECT_OVERLIMIT,"17-player match differential mismatch")
print("ROSTER16_NATIVE_PASS")
"""


def patch_source(original: str) -> str:
    if "M.MAX_HERO_SLOTS=16" not in original:
        raise ValueError("original 16-slot author invariant missing")
    patched = original
    for old, new in zip(OLD, NEW):
        if original.count(old) != 1:
            raise ValueError("not the exact original two-hunk contract")
        patched = patched.replace(old, new, 1)
    if patched == original:
        raise ValueError("no effective gameplay patch")
    if patched.replace(NEW[0], OLD[0], 1).replace(NEW[1], OLD[1], 1) != original:
        raise ValueError("OFF rollback not byte-identical")
    return patched


def native_harness(source: str, expect_overlimit: bool) -> str:
    trimmed = source.rstrip()
    if not trimmed.endswith("return M") or trimmed.count("\nreturn M") != 1:
        raise ValueError("original module return contract drift")
    body = trimmed[:-len("return M")]
    cases = NATIVE_CASES.replace("EXPECT_OVERLIMIT", "true" if expect_overlimit else "false")
    return body + cases + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    actual = subprocess.check_output(["git", "hash-object", str(args.original)], text=True).strip()
    if actual != ORIGINAL_BLOB:
        raise SystemExit(f"original Git blob changed: expected {ORIGINAL_BLOB}, got {actual}")
    original = args.original.read_text(encoding="utf-8")
    changed = patch_source(original)
    folder = args.out_dir
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "EGGRUMBLE_CastleMatchRules_ROSTER16.luau").write_text(changed, encoding="utf-8")
    (folder / "native_original.spec.luau").write_text(native_harness(original, True), encoding="utf-8")
    (folder / "native_patched.spec.luau").write_text(native_harness(changed, False), encoding="utf-8")
    receipt = {
        "feature_id": "GQ_V3_ROSTER16_HARDCAP",
        "author_head": AUTHOR_HEAD,
        "original_blob": ORIGINAL_BLOB,
        "gameplay_luau_source_changed": 1,
        "changed_guards": 2,
        "all_other_30_rc_sources": "NOT_TOUCHED_BY_THIS_SELECTOR",
        "original_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "patched_sha256": hashlib.sha256(changed.encode()).hexdigest(),
        "off_rollback": "BYTE_EXACT_TO_ORIGINAL_AUTHOR",
        "formal_rc_adoption": False,
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
    }
    (folder / "ROSTER16_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
