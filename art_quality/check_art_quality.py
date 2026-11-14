#!/usr/bin/env python3
"""P0D art gate: inspect real Rojo Place + externally supplied Studio evidence.

This deliberately never claims that source patterns or CI prove visual beauty.
Only a real OWNER review can change ART_NO_GO into OWNER_ACCEPTED.
stdlib-only, read-only, suitable for GitHub Actions.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SCENES = ("lobby", "field_wide", "castle", "sea", "forest",
          "neutral", "beast", "combat")
DEVICES = ("pc", "android")
VERSIONS = ("before", "after")
CATEGORIES = {
    "terrain": ("FantasyWorldArt", "Owner361CastleBattlefield"),
    "castle": ("CastleDetailArt", "Owner361CastleBattlefield"),
    "sea": ("H1CoastalSeascape", "H1SeaGroundRepair"),
    "forest": ("FoliagePassageFix", "FoliageCameraFade"),
    "neutral": ("ArtMinionSilhouette", "MusouHorde"),
    "beast": ("GoroganRigDriver", "FB015GoroganVisual"),
    "roles": ("SoloTeamBots", "SevenJobsRules"),
    "combat": ("P0DConfirmedCombatFX", "TrapRaidersHUD"),
    "lobby": ("LobbyDojoIsland", "BattleHUDGovernor"),
    "atmosphere": ("FantasyWorldArt",),
}
FPS_FLOOR = {"pc": 45.0, "android": 25.0}
PNG = b"\x89PNG\r\n\x1a\n"
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def scene_inventory(place: Path) -> dict:
    if not place.is_file() or place.suffix.lower() != ".rbxlx":
        raise ValueError("REAL_RBXLX_REQUIRED")
    data = place.read_bytes()
    scripts = collections.defaultdict(list)
    for item in ET.fromstring(data).iter("Item"):
        kind = item.attrib.get("class")
        if kind not in ("Script", "LocalScript", "ModuleScript"):
            continue
        properties = item.find("Properties")
        if properties is None:
            continue
        src = properties.find("string[@name='Source']")
        name = properties.find("string[@name='Name']")
        if src is None or name is None or name.text is None:
            continue
        value = src.text or ""
        scripts[name.text].append({"type": kind, "sha256": digest(value.encode("utf8")),
                                   "source": value})
    violations = []
    for name, kind in (("Game", "Script"), ("TrapRaidersHUD", "LocalScript"),
                       ("BattleHUDGovernor", "LocalScript")):
        found = scripts.get(name, [])
        if len(found) != 1 or found[0]["type"] != kind:
            violations.append("AUTHORITY_OR_HUD_COUNT:" + name)
    coverage = {}
    for category, required in CATEGORIES.items():
        present = [name for name in required if scripts.get(name)]
        coverage[category] = {"required": list(required), "present": present,
                              "present_count": len(present)}
        if len(present) != len(required):
            violations.append("ART_SOURCE_COVERAGE:" + category + ":" +
                              ",".join(sorted(set(required) - set(present))))
    if len(scripts["TrapRaidersHUD"]) == 1:
        hud = scripts["TrapRaidersHUD"][0]["source"]
        if "attack.Activated:Connect" not in hud:
            violations.append("ATTACK_INPUT_NOT_ACTIVATED")
    risky = {}
    for category, required in CATEGORIES.items():
        source = "\n".join(t["source"] for name in required for t in scripts.get(name, []))
        risky[category] = {
            "neon_mentions": len(re.findall(r"\bNeon\b", source)),
            "gui_mentions": len(re.findall(r"\bBillboardGui\b|\bScreenGui\b", source)),
            "basic_part_mentions": len(re.findall(r'Instance\.new\(["\x27]Part["\x27]\)', source)),
        }
    return {
        "place_bytes": len(data), "place_sha256": digest(data),
        "script_count": sum(len(a) for a in scripts.values()),
        "unique_script_names": len(scripts),
        "source_coverage": coverage,
        "style_risk_indicators_not_beauty_scores": risky,
        "source_gate": "PASS" if not violations else "FAIL",
        "source_violations": violations,
    }

def png_info(path: Path) -> tuple[int, int, str]:
    if not path.is_file() or path.is_symlink() or path.suffix.lower() != ".png":
        raise ValueError("PNG_FILE_REQUIRED")
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != PNG or data[12:16] != b"IHDR":
        raise ValueError("INVALID_PNG_HEADER")
    width, height = struct.unpack(">II", data[16:24])
    if width < 720 or height < 400 or width > 16384 or height > 16384:
        raise ValueError("INVALID_SCREENSHOT_DIMENSIONS")
    if len(data) < 1024:
        raise ValueError("IMAGE_TOO_SMALL_FOR_EVIDENCE")
    return width, height, digest(data)

def evidence_audit(manifest_file: Path | None, root: Path | None, place_sha: str) -> dict:
    if manifest_file is None:
        return {"gate": "MISSING", "violations": ["NO_STUDIO_EVIDENCE_MANIFEST"],
                "shots_received": 0, "shots_required": len(SCENES)*len(DEVICES)*len(VERSIONS)}
    violations = []
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf8"))
    except (OSError, ValueError) as exc:
        return {"gate": "FAIL", "violations": ["INVALID_MANIFEST:" + type(exc).__name__],
                "shots_received": 0}
    if manifest.get("schema") != "P0D_ART_STUDIO_EVIDENCE_V1":
        violations.append("SCHEMA_MISMATCH")
    for key in ("before_head", "after_head"):
        if not HEAD_RE.fullmatch(str(manifest.get(key, ""))):
            violations.append("HEAD_MISSING:" + key)
    if manifest.get("after_place_sha256") != place_sha:
        violations.append("STUDIO_PLACE_SHA_MISMATCH")
    root = root if root is not None else manifest_file.parent
    root = root.resolve()
    shots = manifest.get("shots", [])
    seen = set()
    duplicate_sha = {}
    for shot in shots if isinstance(shots, list) else []:
        if not isinstance(shot, dict):
            violations.append("INVALID_SHOT"); continue
        key = (shot.get("scene"), shot.get("device"), shot.get("version"))
        if key in seen:
            violations.append("DUPLICATE_SHOT_KEY:" + str(key)); continue
        seen.add(key)
        if key[0] not in SCENES or key[1] not in DEVICES or key[2] not in VERSIONS:
            violations.append("UNKNOWN_CAMERA_ID:" + str(key)); continue
        name = shot.get("file")
        if not isinstance(name, str):
            violations.append("MISSING_SHOT_FILE:" + str(key)); continue
        candidate = root / name
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(root):
            violations.append("UNSAFE_SCREENSHOT_PATH:" + str(key)); continue
        try:
            width, height, sha = png_info(candidate)
        except (ValueError, OSError) as exc:
            violations.append("INVALID_SCREENSHOT:" + str(key) + ":" + str(exc)); continue
        if key[1] == "pc" and (width < 1280 or height < 720):
            violations.append("LOW_PC_RESOLUTION:" + str(key))
        if sha in duplicate_sha:
            other = duplicate_sha[sha]
            if (key[0], key[1], key[2]) != (other[0], other[1], other[2]):
                violations.append("REUSED_SCREENSHOT:" + str(key))
        duplicate_sha[sha] = key
    expected = {(scene, dev, version) for scene in SCENES
                for dev in DEVICES for version in VERSIONS}
    for missing in sorted(expected - seen):
        violations.append("MISSING_SCREENSHOT:" + "/".join(missing))
    ratings = manifest.get("ratings", {})
    for category in CATEGORIES:
        values = ratings.get(category, {}) if isinstance(ratings, dict) else {}
        for dev in DEVICES:
            rating = values.get(dev) if isinstance(values, dict) else None
            if type(rating) is not int or rating not in range(1, 6):
                violations.append("MISSING_RATING:" + category + "/" + dev)
            elif rating < 4:
                violations.append("ART_SCORE_BELOW_4:" + category + "/" + dev)
    performance = manifest.get("performance", {})
    for dev in DEVICES:
        item = performance.get(dev, {}) if isinstance(performance, dict) else {}
        if not isinstance(item, dict) or not item.get("device_model") or not item.get("graphics_quality"):
            violations.append("MISSING_HARDWARE_CONFIG:" + dev)
        value = item.get("fps_p10") if isinstance(item, dict) else None
        if type(value) not in (int, float) or not 0 < value <= 300:
            violations.append("MISSING_FPS_P10:" + dev)
        elif value < FPS_FLOOR[dev]:
            violations.append("FPS_P10_BELOW_FLOOR:" + dev)
    if manifest.get("critical_visual_blockers") != []:
        violations.append("CRITICAL_BLOCKERS_NOT_CLEARED")
    if not manifest.get("human_reviewer"):
        violations.append("NO_HUMAN_REVIEWER")
    # Even perfect submitted images/scores are not cryptographic proof of Roblox
    # execution or owner acceptance: an OWNER review of the actual images is required.
    return {
        "gate": "REVIEW_READY" if not violations else "FAIL",
        "violations": violations, "shots_received": len(seen),
        "shots_required": len(expected), "human_reviewer_claim": bool(manifest.get("human_reviewer")),
        "owner_accepted": False,
    }

def audit(place: Path, evidence: Path | None = None, screenshots: Path | None = None) -> dict:
    source = scene_inventory(place)
    visual = evidence_audit(evidence, screenshots, source["place_sha256"])
    source_ok = source["source_gate"] == "PASS"
    visual_ready = visual["gate"] == "REVIEW_READY"
    return {
        "schema": "P0D_ART_QUALITY_GATE_V1",
        "source": source,
        "evidence": visual,
        "gate_level": ("REVIEW_READY_OWNER_PENDING" if source_ok and visual_ready
                       else "SOURCE_READY_EVIDENCE_MISSING" if source_ok and visual["gate"] == "MISSING"
                       else "ART_QA_BLOCKED"),
        "art_decision": "ART_NO_GO",
        "owner_accepted": False,
        "note": "Source patterns, screenshot metadata, and reviewer ratings cannot prove beauty or Studio execution; OWNER must review real PC/Android images.",
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--place", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = audit(args.place, args.evidence, args.screenshots)
    except (ET.ParseError, OSError, ValueError) as exc:
        result = {"schema": "P0D_ART_QUALITY_GATE_V1", "art_decision": "ART_NO_GO",
                  "gate_level": "ART_QA_BLOCKED", "error": str(exc)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("P0D_ART_GATE", result["gate_level"], result["art_decision"])
    return 2 if (result["gate_level"] == "ART_QA_BLOCKED" or
                 (args.strict and result["gate_level"] != "REVIEW_READY_OWNER_PENDING")) else 0

if __name__ == "__main__":
    sys.exit(main())
