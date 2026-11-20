#!/usr/bin/env python3
"""Source-locked, private-only castle egg deposit HUD refresh overlay.

No original owner, main, protected RC, Roblox publish or remote changes.
"""
import argparse
import hashlib
from pathlib import Path

SOURCE_AUTHOR_HEAD = "6b52eaf1f2725496277998fe0c5532b7a8fcaab5"
EXPECTED_GIT_BLOB = "c1ff23cd2883401d44d6fc47311bebcfd53eb1c6"
ANCHOR = '''  if c.alive and c.heldEggs>0 then pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end) end
'''
REPLACEMENT = '''  if c.alive and c.heldEggs>0 then
   local ok=pcall(function() Rules.depositEggs(session.rules,entry.id,c.heldEggs) end)
   if ok then session.refresh() end
  end
'''


def git_blob_sha(source: bytes) -> str:
    return hashlib.sha1(f"blob {len(source)}\\0".encode().replace(b"\\0", b"\0") + source).hexdigest()


def compose(source: bytes, *, on: bool = True, verify_blob: bool = True) -> bytes:
    found = git_blob_sha(source)
    if verify_blob and found != EXPECTED_GIT_BLOB:
        raise ValueError(f"ORIGINAL_HOST_SOURCE_DRIFT expected={EXPECTED_GIT_BLOB} found={found}")
    if not on:
        return source
    before = source.decode("utf-8")
    if before.count(ANCHOR) != 1 or REPLACEMENT in before:
        raise ValueError("UNIQUE_DEPOSIT_CALLBACK_ANCHOR_NOT_FOUND")
    return before.replace(ANCHOR, REPLACEMENT, 1).encode("utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--off", action="store_true")
    args = p.parse_args()
    changed = compose(args.input.read_bytes(), on=not args.off)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(changed)
    print("V3_SOURCE_PINNED_LOCAL_OVERLAY_ONLY; OFFICIAL_RC_NOT_ADOPTED")


if __name__ == "__main__":
    main()
