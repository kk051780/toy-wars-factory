#!/usr/bin/env python3
"""Continue GQ618 with two exact target-selection fixes in selected REAL69 Combat.

This adapter does not change the historical original21/current31 composers.
The caller must verify the other 68 selected sources and the generated Place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat

FEATURE_ID = "GQ_BEAST_ESCORT_REAL_UNIT_20261117"
COMBAT_PATH = "ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau"
BEFORE = {
    "bytes": 73774,
    "sha256": "1b4ec066f4273c7cfc88d075a4a1df4855233e759f81d0241b134383bef42f76",
}
AFTER = {'bytes': 73889, 'sha256': 'ba37d904cc9a5529ffaae7602ae25830a65abb4634fe3e3cdbfa95a767c87f4a'}

# Each anchor is inside the existing inline BeastEscort.pickTarget only.
# Swarm excludes every registered charmed neutral until releaseCharmed clears
# its marker. The existing human helper retains real-egg carrier reveal.
HUNKS = (
    (
        b"    if scanned > MAX_NEUTRAL_SCAN then break end\n    consider(v)\n",
        b"    if scanned > MAX_NEUTRAL_SCAN then break end\n"
        b'    if v:GetAttribute("EGGRUMBLE_NeutralFriendlyOwnerId") == nil then consider(v) end\n',
    ),
    (
        b"  if other ~= player and eligible(session, casterState, tostring(other.UserId))\n"
        b"   and (session.isCurrentHuman == nil or session.isCurrentHuman(other) == true) then\n",
        b"  if other ~= player and eligible(session, casterState, tostring(other.UserId))\n"
        b"   and currentHumanMember(session, other)\n"
        b"   and humanCombatTargetable(session.rules.castles[tostring(other.UserId)], other) then\n",
    ),
)


def require(value, reason):
    if not value:
        raise ValueError("RED_GQ618_CURRENT69_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def transform(raw: bytes, mode: str = "on") -> bytes:
    require(mode in ("on", "off"), "UNKNOWN_MODE")
    expected, target = (BEFORE, AFTER) if mode == "on" else (AFTER, BEFORE)
    require(identity(raw) == expected, "COMBAT_PREIMAGE")
    result = raw
    pairs = HUNKS if mode == "on" else tuple((new, old) for old, new in reversed(HUNKS))
    for old, new in pairs:
        require(result.count(old) == 1, "ANCHOR_CARDINALITY")
        require(result.count(new) == 0, "OVERLAY_ALREADY_PRESENT")
        result = result.replace(old, new, 1)
    require(identity(result) == target, "COMBAT_POSTIMAGE")
    return result


def read_regular(path: Path) -> bytes:
    path = path.absolute()
    require(not any(p.is_symlink() for p in (path, *path.parents)), "SYMLINK_PATH")
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), "REGULAR_FILE_REQUIRED")
    return path.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combat", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--mode", choices=("on", "off"), default="on")
    args = parser.parse_args()
    source, out, receipt = (p.absolute() for p in (args.combat, args.out, args.receipt))
    require(len({source, out, receipt}) == 3, "OUTPUT_ALIASES_INPUT")
    for path in (out, receipt):
        require(not path.exists() and not any(p.is_symlink() for p in (path, *path.parents)),
                "OUTPUT_MUST_BE_NEW_REGULAR_PATH")
        require(path.parent.is_dir(), "OUTPUT_PARENT_REQUIRED")
    before = read_regular(source)
    result = transform(before, args.mode)
    require(transform(result, "off" if args.mode == "on" else "on") == before, "EXACT_INVERSE")
    record = {
        "schema": "GQ618_CURRENT69_TARGET_SELECTION_V1",
        "feature_id": FEATURE_ID,
        "mode": args.mode,
        "before": identity(before),
        "after": identity(result),
        "hunk_count": len(HUNKS),
        "exact_inverse": True,
        "changed_source": COMBAT_PATH,
        "scope": "BEAST_NEUTRAL_CHARM_AND_HUMAN_TARGET_ELIGIBILITY_ONLY",
        "official_rc_adopted": False,
        "studio_tested": False,
    }
    with out.open("xb") as handle:
        handle.write(result)
    with receipt.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, indent=2) + "\n")
    require(read_regular(source) == before, "INPUT_CHANGED")
    print("GQ618_CURRENT69_TWO_HUNKS_EXACT_INVERSE_PASS_SOURCE_ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
