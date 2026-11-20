#!/usr/bin/env python3
"""Fail-closed, one-line P0 combat hotfix from the pinned REAL69 Studio ZIP.

Do not edit the canonical RC branch, author Combat source, rbxlx or receipts here.
This produces a replacement Luau SOURCE candidate for #220 sole RC writer.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
from pathlib import Path
from zipfile import ZipFile

SOURCE = "sources/ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau"
PINNED_SHA256 = "c112b86984d7efe2daf24a9c11ad58c427c9916dab02e6565ac782beb5c81c75"
BUG = 'h:TakeDamage(InvulRuntime.filterDamage(h,damage*duel*mark,"PLAYER",p.UserId))'
FIX = 'h:TakeDamage(InvulRuntime.filterDamage(h,damage*duel*mark,"PLAYER",player.UserId))'


def patch_source(raw: bytes) -> bytes:
    assert hashlib.sha256(raw).hexdigest() == PINNED_SHA256, "SOURCE_HEAD_DRIFT_FAIL_CLOSED"
    original = raw.decode("utf-8")
    start = original.index("local function hitBotHeroes(session:any,player:Player,")
    end = original.index("-- NINJA stealth stops human targeting", start)
    block = original[start:end]
    assert block.count(BUG) == 1, "EXPECTED_ONE_REAL_BOT_DAMAGE_BUG"
    assert "local state=session.rules.castles[tostring(player.UserId)]" in block
    corrected = original[:start] + block.replace(BUG, FIX, 1) + original[end:]
    before_lines = original.splitlines(keepends=True)
    after_lines = corrected.splitlines(keepends=True)
    assert len(before_lines) == len(after_lines) == 1513
    diff = [(a, b) for a, b in zip(before_lines, after_lines) if a != b]
    assert len(diff) == 1 and BUG in diff[0][0] and FIX in diff[0][1], "NOT_EXACTLY_ONE_LINE"
    assert 'h:TakeDamage(InvulRuntime.filterDamage(h,damage*duel*mark,"PLAYER",p.UserId))' not in corrected
    assert corrected.count(FIX) == 1
    return corrected.encode("utf-8")


def from_real69_zip(archive: Path) -> bytes:
    with ZipFile(archive) as z:
        members = z.namelist()
        assert len([m for m in members if m.startswith("sources/") and m.endswith(".luau")]) == 69
        assert members.count(SOURCE) == 1
        return z.read(SOURCE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real69-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = from_real69_zip(args.real69_zip)
    patched = patch_source(raw)
    assert not args.out.exists(), "DO_NOT_OVERWRITE_PREVIOUS_CANDIDATE"
    args.out.write_bytes(patched)
    print("REAL69_P0_USERID_ONE_LINE_PATCH_READY source_only=1 studio_tested=0")
    print("before_sha256=" + hashlib.sha256(raw).hexdigest())
    print("after_sha256=" + hashlib.sha256(patched).hexdigest())


if __name__ == "__main__":
    main()
