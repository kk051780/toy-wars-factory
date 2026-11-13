#!/usr/bin/env python3
"""Fail-closed preflight for P0D candidate admission; never edits a Roblox place.

Source/CI evidence is necessary but cannot replace official product selection,
OWNER Studio test, independent QA, or sole #220 RC admission.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = (
    "adoption_id", "official_rc_sha", "candidate_source_sha", "feature_source_qa",
    "product_official_rc_selected", "independent_rc_qa", "studio_2client",
    "android", "owner_fun", "source_lock_verified", "single_authority_review",
    "rollback_sha",
)


def scan_place(path: Path) -> dict:
    """Extract *static* embedded Script counts from an unpacked XML .rbxlx."""
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise ValueError("DTD or entity declaration not permitted")
    root = ET.fromstring(raw)
    if root.tag != "roblox":
        raise ValueError("not a .rbxlx Roblox XML root")
    counts = {"Script": 0, "LocalScript": 0, "ModuleScript": 0}
    game_count = 0
    names = []
    for item in root.iter("Item"):
        kind = item.get("class")
        if kind not in counts:
            continue
        counts[kind] += 1
        props = item.find("Properties")
        name = None
        if props is not None:
            for node in props:
                if node.attrib.get("name") == "Name":
                    name = node.text or ""
                    break
        names.append(name)
        if kind == "Script" and name == "Game":
            game_count += 1
    return {"counts": counts, "game_scripts": game_count,
            "source_count": sum(counts.values()), "sha256": hashlib.sha256(raw).hexdigest()}


def evaluate(receipt: dict, place: Path | None = None) -> dict:
    blockers = []
    for key in REQUIRED:
        if key not in receipt:
            blockers.append("MISSING_FIELD:" + key)
    if not SHA40.fullmatch(str(receipt.get("official_rc_sha", ""))):
        blockers.append("INVALID_OFFICIAL_SHA")
    if not SHA40.fullmatch(str(receipt.get("candidate_source_sha", ""))):
        blockers.append("INVALID_CANDIDATE_SHA")
    if not SHA40.fullmatch(str(receipt.get("rollback_sha", ""))):
        blockers.append("INVALID_ROLLBACK_SHA")
    if receipt.get("feature_source_qa") != "PASS":
        blockers.append("FEATURE_SOURCE_QA_NOT_PASS")
    if receipt.get("product_official_rc_selected") is not True:
        blockers.append("PRODUCT_NOT_OFFICIALLY_SELECTED")
    for key in ("independent_rc_qa", "studio_2client", "android", "owner_fun",
                "source_lock_verified", "single_authority_review"):
        if receipt.get(key) is not True:
            blockers.append(key.upper() + "_NOT_VERIFIED")
    scan = None
    if place is not None:
        try:
            scan = scan_place(place)
            expected = receipt.get("expected_place_sha256")
            if not SHA256.fullmatch(str(expected)) or scan["sha256"] != expected:
                blockers.append("PLACE_SHA256_MISMATCH")
            expected_counts = receipt.get("expected_script_counts")
            if scan["counts"] != expected_counts:
                blockers.append("SCRIPT_COUNTS_MISMATCH")
            if scan["game_scripts"] != 1:
                blockers.append("SINGLE_GAME_SCRIPT_NOT_VERIFIED")
        except (ET.ParseError, ValueError, OSError) as exc:
            blockers.append("INVALID_PLACE:" + str(exc)[:120])
    else:
        blockers.append("PLACE_NOT_INDEPENDENTLY_SCANNED")
    blockers = sorted(set(blockers))
    return {"adoption_id": receipt.get("adoption_id", "UNKNOWN"),
            "decision": "ELIGIBLE_FOR_SOLE_INTEGRATOR_REVIEW" if not blockers else "BLOCKED",
            "blockers": blockers, "static_place_scan": scan,
            "warning": "ELIGIBLE != integrated. Only #220 may write official RC; no Studio pass inferred."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--place", type=Path, help="optional real unpublished XML .rbxlx for independent static scan")
    args = parser.parse_args()
    result = evaluate(json.loads(args.receipt.read_text(encoding="utf-8")), args.place)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["decision"].startswith("ELIGIBLE") else 2


if __name__ == "__main__":
    sys.exit(main())
