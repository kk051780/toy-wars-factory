#!/usr/bin/env python3
"""P0 player absent / invisible: static source trace, NOT a root cause verdict.

Reads the exact official 69 selected runtime source packet after source lock.
Does not edit Game/Host/Spawn/Camera or claim a Studio reproduction.
This complements (never replaces) the owner Studio test at #364.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

PATTERNS = {
    "character_auto_loads": r"\bCharacterAutoLoads\s*=",
    "explicit_load_character": r":LoadCharacter(?:Async)?\s*\(",
    "player_added": r"\bPlayerAdded:Connect\s*\(",
    "character_added": r"\bCharacterAdded:Connect\s*\(",
    "character_removing": r"\bCharacterRemoving:Connect\s*\(",
    "camera_subject": r"\bCameraSubject\s*=",
    "camera_type": r"\bCameraType\s*=",
    "transparency_modifier": r"\bLocalTransparencyModifier\s*=",
    "whole_character_transparency": r"\bTransparency\s*=\s*1(?:\b|$)",
    "spawn_location": r"\bSpawnLocation\b",
    "manual_spawn_teleport": r"\b(?:PivotTo|MoveTo)\s*\(",
    "parent_nil": r"\.Parent\s*=\s*nil\b",
    "character_destroy": r"\b(?:character|Character):Destroy\s*\(",
}
EXPECTED_BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"


def strip_comment(line: str) -> str:
    return line.split("--", 1)[0]


def audit_script(script: str) -> list[dict]:
    hits = []
    for number, line in enumerate(script.splitlines(), 1):
        executable = strip_comment(line)
        for category, pattern in PATTERNS.items():
            if re.search(pattern, executable):
                # Do not copy source text or secrets to published logs, emit line/category only.
                hits.append({"line": number, "category": category})
    return hits


def collect(official: Path) -> dict:
    receipt = json.loads((official / "REAL69_LEGACY_INTAKE_RECEIPT.json")
                         .read_text(encoding="utf-8"))
    if (receipt.get("build_head") != EXPECTED_BASE or
            receipt.get("canonical_build") is not True or
            receipt.get("selected_source_count") != 69):
        raise ValueError("RED_P0_SPAWN_TRACE_NOT_EXACT_FORMAL_HEAD")
    selected = project_scan(official, "EGGRUMBLE_REAL69.project.json")
    if len(selected) != 69 or set(selected) != set(receipt["source_hashes"]):
        raise ValueError("RED_P0_SPAWN_TRACE_SOURCE_SET")
    rows = []
    counts = collections.Counter()
    for route, item in sorted(selected.items()):
        path = official / item["path"]
        source = path.read_bytes()
        if hashlib.sha256(source).hexdigest() != item["sha256"]:
            raise ValueError("RED_P0_SPAWN_TRACE_SOURCE_BYTES:" + route)
        found = audit_script(source.decode("utf-8"))
        if found:
            counts.update(entry["category"] for entry in found)
            rows.append({
                "selected_route": route,
                "class": item["class"],
                "categories": dict(sorted(collections.Counter(e["category"] for e in found).items())),
                "sites": found,
            })
    signal = ["character_auto_loads", "explicit_load_character",
              "camera_subject", "camera_type", "transparency_modifier",
              "character_destroy"]
    conclusion = "RUNTIME_UNKNOWN_STATIC_ONLY"
    return {
        "schema": "GQ470_P0_PLAYER_ABSENT_REAL69_STATIC_TRACE_V1",
        "official_head": EXPECTED_BASE,
        "profile": "PRIVATE_COMPANION_REAL69_NOT_ACTIVE_RICH51",
        "selected_sources_verified": 69,
        "static_category_counts": {k: counts[k] for k in sorted(PATTERNS)},
        "high_risk_syntax_categories_present": [x for x in signal if counts[x] > 0],
        "source_routes_with_matches": len(rows),
        "source_route_matches": rows,
        "conclusion": conclusion,
        "studio_solo": "NOT_TESTED",
        "android": "NOT_TESTED",
        "user_repro_player_absent": "OPEN",
        "root_cause_confirmed": False,
        "note": "Presence or absence of tokens cannot prove spawned / hidden player. Need current game profile, runtime Output, player CharacterAdded, camera and viewport observations.",
    }


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--official", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    args = a.parse_args()
    report = collect(args.official)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print("GQ470_SPAWN_STATIC_SELECTED69_HEAD_EXACT_PASS")
    print("GQ470_SPAWN_STATIC_CATEGORIES", json.dumps(report["static_category_counts"]))
    print("GQ470_SPAWN_RELEVANT_ROUTES", report["source_routes_with_matches"])
    for row in report["source_route_matches"]:
        if any(key in row["categories"] for key in
               ("character_auto_loads","explicit_load_character","camera_subject",
                "camera_type","transparency_modifier","character_destroy")):
            print("GQ470_SPAWN_INSPECT", row["selected_route"], json.dumps(row["categories"]))
    print("GQ470_SPAWN_CONCLUSION=RUNTIME_UNKNOWN_STATIC_ONLY_NO_ENGINE_PASS")
