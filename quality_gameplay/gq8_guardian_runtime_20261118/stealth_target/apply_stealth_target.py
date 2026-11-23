#!/usr/bin/env python3
"""Apply or invert the existing +294-byte Guardian cloak proposal exactly.

This transports the parent's three frozen replacements. It is not a new runtime
producer, grant, or current-RC composition. Inputs and outputs are pinned bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat

IDENTITIES = {
    "h93": {
        "input": {"bytes": 13707, "sha256": "9455e263a450002a4c578993e508f37d0b6ea8233eae36c8de06210889410096"},
        "candidate": {"bytes": 14001, "sha256": "2c6f53526cb54b1a929db295ca189e7642b0c98c89c20df470642895a118f698"},
    },
    "pr796": {
        "input": {"bytes": 13907, "sha256": "1afd38a70a27ada58ad7418768ce5c6f3b6576635aa467e14a45056af0505825"},
        "candidate": {"bytes": 14201, "sha256": "a6a4433966ba52212d42e12dc69e8bca7a63424fe31c25ade89724928d417ef2"},
    },
}

# Byte-for-byte parent proposal, previously reviewed on both source bases.
REPLACEMENTS = (
    (
        b'local function targetOf(session:any,owner:string,at:Vector3,range:number,exclude:Model):any\n',
        b'local function targetOf(session:any,owner:string,at:Vector3,range:number,exclude:Model,role:string):any\n',
    ),
    (
        b'   and enemy(session,owner,id) then\n',
        b'   and enemy(session,owner,id)\n'
        b'   -- OWNER #804: only the NINJA guardian detects cloaked heroes.\n'
        b'   -- An egg in the existing Rules state reveals a carrier to every role.\n'
        b'   and (role=="NINJA" or session.rules.castles[id].heldEggs>0\n'
        b'    or os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)) then\n',
    ),
    (
        b'  local foe,dist=targetOf(session,d.owner,at,c.range,model)\n',
        b'  local foe,dist=targetOf(session,d.owner,at,c.range,model,d.role)\n',
    ),
)


def identity(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def apply(raw: bytes, base: str, inverse: bool = False) -> bytes:
    if base not in IDENTITIES or type(inverse) is not bool:
        raise ValueError("STEALTH_EXPLICIT_BASE_AND_DIRECTION_REQUIRED")
    before, after = ("candidate", "input") if inverse else ("input", "candidate")
    if identity(raw) != IDENTITIES[base][before]:
        raise ValueError("STEALTH_INPUT_IDENTITY_MISMATCH:" + base)
    result = raw
    operations = tuple((b, a) for a, b in reversed(REPLACEMENTS)) if inverse else REPLACEMENTS
    for old, new in operations:
        if result.count(old) != 1:
            raise ValueError("STEALTH_EXPECT_ONE_FROZEN_ANCHOR")
        result = result.replace(old, new, 1)
    if identity(result) != IDENTITIES[base][after]:
        raise ValueError("STEALTH_OUTPUT_IDENTITY_MISMATCH:" + base)
    if len(result) - len(raw) != (-294 if inverse else 294):
        raise ValueError("STEALTH_EXACT_294_BYTE_DELTA")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--base", required=True, choices=IDENTITIES)
    parser.add_argument("--inverse", action="store_true")
    args = parser.parse_args()
    if args.input.is_symlink() or not args.input.is_file() or not stat.S_ISREG(args.input.stat().st_mode):
        raise ValueError("STEALTH_REGULAR_INPUT_REQUIRED")
    raw = args.input.read_bytes()
    result = apply(raw, args.base, inverse=args.inverse)
    with args.output.open("xb") as output:
        output.write(result)
    print(json.dumps({"base": args.base, "inverse": args.inverse, "input": identity(raw),
                      "output": identity(result), "official_rc_adopted": False}, sort_keys=True))


if __name__ == "__main__":
    main()
