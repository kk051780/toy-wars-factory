#!/usr/bin/env python3
"""Fail-closed audit for #431: art that exists in Studio but not non-Studio play.

Never claim actual release parity from source; human authorized private
PC/Android play must supply the separate runtime evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_PLACE_BYTES = 10_000_000
ART_INSTANCES = {
    "CastleDetailArt": ("Script", "castle"),
    "FantasyWorldArt": ("Script", "forest_world"),
    "H1CoastalSeascape": ("Script", "sea"),
    "H1SeaGroundRepair": ("Script", "sea_ground"),
    "ArtMinionSilhouette": ("Script", "neutral_minion"),
    "FB015GoroganVisual": ("LocalScript", "gorogan_beast"),
    "P0DConfirmedCombatFX": ("LocalScript", "combat_fx"),
}
_TOP_GUARD = re.compile(
    r"^if\s+not\s+RunService:IsStudio\(\)\s+then\s+return\s+end(?:\s*--.*)?\s*$"
)

def classify(source: str) -> str:
    """Classify an actual executable early-return, not a comment or string search."""
    raw_lines = source.splitlines()
    for line in raw_lines[:40]:
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if _TOP_GUARD.fullmatch(line):
            return "TOP_STUDIO_ONLY"
    if "IsStudio()" in source:
        return "CONDITIONAL_OR_UNKNOWN"
    return "NO_TOP_GUARD_SOURCE_ONLY"

def inspect(place: Path, expected_scripts: int = 80) -> dict:
    if not 80 <= expected_scripts <= 96:
        raise ValueError('EXPECTED_SCRIPT_COUNT_OUT_OF_RANGE')
    raw = place.read_bytes()
    if not raw or len(raw) > MAX_PLACE_BYTES:
        raise ValueError("PLACE_SIZE_INVALID")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("UNSAFE_XML_ENTITY")
    root = ET.fromstring(raw)
    scripts = {}
    counts = {}
    for item in root.iter("Item"):
        kind = item.get("class")
        if kind not in {"Script", "LocalScript", "ModuleScript"}:
            continue
        properties = item.find("Properties")
        if properties is None:
            continue
        name = properties.find("string[@name='Name']")
        src = properties.find("string[@name='Source']")
        if name is None or src is None:
            continue
        name_text = name.text or ""
        src_text = src.text or ""
        key = (kind, name_text)
        counts[key] = counts.get(key, 0) + 1
        scripts.setdefault(key, []).append(src_text)
    report = []
    problems = []
    for name, (kind, group) in ART_INSTANCES.items():
        vals = scripts.get((kind, name), [])
        if len(vals) != 1:
            problems.append(f"ART_INSTANCE_CARDINALITY:{name}:{len(vals)}")
            label = "MISSING_OR_DUPLICATE"
        else:
            label = classify(vals[0])
        report.append({"name": name, "category": group, "class": kind,
                       "source_guard": label, "source_match_count": len(vals)})
    for kind, name in (("Script", "Game"), ("LocalScript", "TrapRaidersHUD")):
        if counts.get((kind, name), 0) != 1:
            problems.append(f"GAMEPLAY_AUTHORITY_CARDINALITY:{name}")
    script_count = sum(counts.values())
    if script_count != expected_scripts:
        problems.append(f"EXPECTED_{expected_scripts}_ACTUAL_{script_count}_LUA_SOURCE_MISMATCH")
    top_only = sum(item["source_guard"] == "TOP_STUDIO_ONLY" for item in report)
    return {
        "schema": "P0D_LIVE_ART_SOURCE_PARITY_GATE_V1",
        "place_bytes": len(raw), "place_sha256": hashlib.sha256(raw).hexdigest(),
        "script_count": script_count,
        "expected_script_count": expected_scripts,
        "source_gate": "PASS" if not problems else "FAIL",
        "source_errors": problems,
        "expected_visual_groups": len(ART_INSTANCES),
        "top_studio_only_count": top_only,
        "visual_sources": report,
        "nonstudio_visual_status": "NOT_RUNTIME_VERIFIED",
        "android_real_15min": "NOT_TESTED",
        "owner_accepted": False,
        "live_art_decision": "LIVE_ART_NO_GO",
        "art_decision": "ART_NO_GO",
        "reason": "Source-only audit cannot establish private live/PC/Android rendering parity; top-level Studio guards suppress art outside Studio.",
    }

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--place", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--expected-scripts", type=int, default=80)
    a = p.parse_args(argv)
    try:
        result = inspect(a.place, expected_scripts=a.expected_scripts)
    except (OSError, ValueError, ET.ParseError) as exc:
        result = {"schema": "P0D_LIVE_ART_SOURCE_PARITY_GATE_V1",
                  "source_gate": "FAIL", "live_art_decision": "LIVE_ART_NO_GO",
                  "owner_accepted": False, "error": str(exc)}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("P0D_LIVE_ART_SOURCE_GATE", result["source_gate"], result["live_art_decision"],
          result.get("top_studio_only_count", "UNKNOWN"))
    return 0 if result["source_gate"] == "PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
