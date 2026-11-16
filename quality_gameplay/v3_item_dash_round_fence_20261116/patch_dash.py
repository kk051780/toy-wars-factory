#!/usr/bin/env python3
"""Strict, one-hunk overlay on the #482 author's existing ITEM source.

No duplicate Game/Remote/Store/Item authority. This file only generates an
isolated source candidate for the #220 authenticated RC writer to select.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ORIGINAL_COMMIT = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_BLOB = "24a35a2e6004c635456cc6f2288cf13f8365ba27"
ORIGINAL_PATH = (
    "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/"
    "EGGRUMBLE_FieldItemPickups.luau"
)
OLD = """    local previous=hum.WalkSpeed
    hum.WalkSpeed=math.max(previous,27)
    task.delay(5,function()
     if hum.Parent and hum.Health>0 and hum.WalkSpeed==math.max(previous,27) then
      hum.WalkSpeed=previous
     end
    end)"""
NEW = """    local previous=hum.WalkSpeed
    local boosted=math.max(previous,27)
    hum.WalkSpeed=boosted
    task.delay(5,function()
     -- Stale item timers may never change the next match's movement speed.
     -- The existing session owns matchActive(): phase ACTIVE + live world.
     if not matchActive() then return end
     if hum.Parent and hum.Health>0 and hum.WalkSpeed==boosted then
      hum.WalkSpeed=previous
     end
    end)"""


def git_blob_sha(content: str) -> str:
    encoded = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(encoded)).encode() + b"\x00" + encoded).hexdigest()


def patch_source(content: str, *, require_pin: bool = True) -> str:
    if require_pin and git_blob_sha(content) != ORIGINAL_BLOB:
        raise ValueError("Source-lock failed: original author blob differs")
    if content.count(OLD) != 1:
        raise ValueError("Refuse source: expected exactly one original DASH expiry callback")
    if content.count("local function matchActive():boolean") != 1:
        raise ValueError("Refuse source: matchActive() safety predicate unavailable")
    fixed = content.replace(OLD, NEW, 1)
    if fixed.replace(NEW, OLD, 1) != content:
        raise AssertionError("Overlay unexpectedly changed unrelated source")
    return fixed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.out.resolve():
        parser.error("Refuse to overwrite the original author's file")
    original = args.source.read_text(encoding="utf-8")
    fixed = patch_source(original)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(fixed, encoding="utf-8")
    print(f"ORIGINAL_BLOB={ORIGINAL_BLOB} PATCHED_BLOB={git_blob_sha(fixed)}")
    print("ONE_HUNK_DASH_OLD_SESSION_FENCE=PASS; OFF=use original author blob")
    print("FORMAL_RC_ADOPTED=0; STUDIO_ANDROID_OWNER=NOT_TESTED")


if __name__ == "__main__":
    main()
