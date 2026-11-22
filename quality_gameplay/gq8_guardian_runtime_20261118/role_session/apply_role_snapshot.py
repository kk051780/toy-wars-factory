#!/usr/bin/env python3
"""One locked Guardian lifecycle repair; no project composition or RC writes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

ATTACH_BEFORE = b''' local actors={}
 local closed=false
 local seq=0
'''
ATTACH_AFTER = b''' -- Freeze this match's castle roles before the shared lobby selections change.
 local castleRoles={}
 for owner in pairs(session.rules.castles) do
  local humanId=tonumber(owner)
  local selection=humanId and type(chosenRole)=="table" and chosenRole[humanId]
  castleRoles[owner]=CONFIG[selection] and selection or "WARRIOR"
 end
 local actors={}
 local closed=false
 local seq=0
'''
REFRESH_BEFORE = b'''    local role="WARRIOR"
    local humanId=tonumber(owner)
    if humanId and type(chosenRole)=="table" then
     local selection=chosenRole[humanId]
     if CONFIG[selection] then role=selection end
    end
'''
REFRESH_AFTER = b'''    local role=castleRoles[owner] or "WARRIOR"
'''
HUNKS = ((ATTACH_BEFORE, ATTACH_AFTER), (REFRESH_BEFORE, REFRESH_AFTER))


def identity(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def apply(raw: bytes, *, reverse: bool = False) -> bytes:
    lock = json.loads((HERE / "INPUT_LOCK.json").read_text())
    before, after = ("candidate", "original") if reverse else ("original", "candidate")
    if identity(raw) != lock["guardian"][before]:
        raise ValueError("GUARDIAN_INPUT_IDENTITY_MISMATCH")
    result = raw
    for old, new in reversed(HUNKS) if reverse else HUNKS:
        if reverse:
            old, new = new, old
        if result.count(old) != 1:
            raise ValueError("GUARDIAN_EXPECT_ONE_EXACT_ANCHOR")
        result = result.replace(old, new, 1)
    if identity(result) != lock["guardian"][after]:
        raise ValueError("GUARDIAN_OUTPUT_IDENTITY_MISMATCH")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()
    result = apply(args.input.read_bytes(), reverse=args.reverse)
    # Exclusive creation also rejects input==output and existing output files.
    with args.output.open("xb") as output:
        output.write(result)
    print(json.dumps(identity(result), sort_keys=True))


if __name__ == "__main__":
    main()
