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
import zlib
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


def png_row_widths(width: int, height: int, pixel_bits: int, interlace: int):
    passes = ((0, 0, 1, 1),) if interlace == 0 else (
        (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
        (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2),
    )
    for x, y, dx, dy in passes:
        if width > x and height > y:
            pixels = (width - x + dx - 1) // dx
            stride = 1 + (pixels * pixel_bits + 7) // 8
            for _ in range((height - y + dy - 1) // dy):
                yield stride


def decode_png_blocks(data: bytes, spans: list[tuple[int, int]]):
    decoder = zlib.decompressobj()
    view = memoryview(data)
    try:
        for start, stop in spans:
            for at in range(start, stop, 65536):
                pending = view[at:min(at + 65536, stop)]
                while pending:
                    block = decoder.decompress(pending, 65536)
                    if decoder.unused_data:
                        raise ValueError("INVALID_PNG_IDAT_DEFLATE")
                    yield block
                    pending = decoder.unconsumed_tail
        while not decoder.eof:
            block = decoder.decompress(b"", 65536)
            if not block:
                raise ValueError("INVALID_PNG_IDAT_DEFLATE")
            yield block
    except zlib.error as exc:
        raise ValueError("INVALID_PNG_IDAT_DEFLATE") from exc


def check_png_raster(data: bytes, spans: list[tuple[int, int]], rows) -> None:
    decoded = 0
    filter_at = 0
    for block in decode_png_blocks(data, spans):
        end = decoded + len(block)
        while filter_at < end:
            stride = next(rows, None)
            if stride is None or block[filter_at - decoded] > 4:
                raise ValueError("INVALID_PNG_RASTER")
            filter_at += stride
        decoded = end
    if decoded != filter_at or next(rows, None) is not None:
        raise ValueError("INVALID_PNG_RASTER")


def png_info(path: Path) -> tuple[int, int, str]:
    if not path.is_file() or path.is_symlink() or path.suffix.lower() != ".png":
        raise ValueError("PNG_FILE_REQUIRED")
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != PNG or data[12:16] != b"IHDR":
        raise ValueError("INVALID_PNG_HEADER")
    if struct.unpack_from(">I", data, 8)[0] != 13:
        raise ValueError("INVALID_PNG_IHDR")
    width, height, depth, color, compression, filter_method, interlace = struct.unpack_from(">IIBBBBB", data, 16)
    layouts = {0: (1, {1, 2, 4, 8, 16}), 2: (3, {8, 16}), 3: (1, {1, 2, 4, 8}),
               4: (2, {8, 16}), 6: (4, {8, 16})}
    layout = layouts.get(color)
    if layout is None or depth not in layout[1] or compression != 0 or filter_method != 0 or interlace not in (0, 1):
        raise ValueError("INVALID_PNG_IHDR")
    if width < 720 or height < 400 or width > 16384 or height > 16384:
        raise ValueError("INVALID_SCREENSHOT_DIMENSIONS")
    if len(data) < 1024:
        raise ValueError("IMAGE_TOO_SMALL_FOR_EVIDENCE")
    offset = len(PNG)
    spans = []
    idat_ended = False
    palette = False
    finished = False
    while offset + 12 <= len(data):
        size, kind = struct.unpack_from(">I4s", data, offset)
        checksum_at = offset + 8 + size
        next_offset = checksum_at + 4
        if next_offset > len(data):
            raise ValueError("TRUNCATED_PNG_CHUNK")
        crc, = struct.unpack_from(">I", data, checksum_at)
        if zlib.crc32(data[offset + 4:checksum_at]) != crc:
            raise ValueError("INVALID_PNG_CHUNK_CRC")
        if kind == b"IHDR" and (offset != len(PNG) or size != 13):
            raise ValueError("INVALID_PNG_IHDR")
        if kind == b"PLTE":
            if palette or spans or size == 0 or size > 768 or size % 3 != 0:
                raise ValueError("INVALID_PNG_PALETTE")
            palette = True
        if kind == b"IDAT":
            if idat_ended:
                raise ValueError("NONCONTIGUOUS_PNG_IDAT")
            spans.append((offset + 8, checksum_at))
        elif spans:
            idat_ended = True
        if kind == b"IEND":
            finished = (size == 0 and next_offset == len(data))
            break
        offset = next_offset
    if not spans or not finished or (color == 3 and not palette):
        raise ValueError("INCOMPLETE_PNG_IMAGE")
    check_png_raster(data, spans, png_row_widths(width, height, layout[0] * depth, interlace))
    return width, height, digest(data)

def evidence_audit(manifest_file: Path | None, root: Path | None, place_sha: str) -> dict:
    expected = {(scene, dev, version) for scene in SCENES for dev in DEVICES for version in VERSIONS}
    counts = {"shots_received": 0, "shots_submitted": 0, "shots_required": len(expected)}
    if manifest_file is None:
        return {"gate": "MISSING", "violations": ["NO_STUDIO_EVIDENCE_MANIFEST"], **counts}
    violations = []
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf8"))
        if not isinstance(manifest, dict):
            raise ValueError("MANIFEST_NOT_OBJECT")
    except (OSError, ValueError) as exc:
        return {"gate": "FAIL", "violations": ["INVALID_MANIFEST:" + type(exc).__name__], **counts}
    if manifest.get("schema") != "P0D_ART_STUDIO_EVIDENCE_V1":
        violations.append("SCHEMA_MISMATCH")
    for key in ("before_head", "after_head"):
        if not HEAD_RE.fullmatch(str(manifest.get(key, ""))):
            violations.append("HEAD_MISSING:" + key)
    if manifest.get("after_place_sha256") != place_sha:
        violations.append("STUDIO_PLACE_SHA_MISMATCH")
    usable_identity = not violations
    root = root if root is not None else manifest_file.parent
    root = root.resolve()
    shots = manifest.get("shots", [])
    seen = set()
    eligible = set()
    first_by_sha = {}
    for shot in shots if isinstance(shots, list) else []:
        if not isinstance(shot, dict):
            violations.append("INVALID_SHOT"); continue
        key = (shot.get("scene"), shot.get("device"), shot.get("version"))
        if any(not isinstance(value, str) for value in key) or key not in expected:
            violations.append("UNKNOWN_CAMERA_ID:" + str(key)); continue
        if key in seen:
            violations.append("DUPLICATE_SHOT_KEY:" + str(key))
            eligible.discard(key)
            continue
        seen.add(key)
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
        full_pc_resolution = key[1] != "pc" or (width >= 1280 and height >= 720)
        if not full_pc_resolution:
            violations.append("LOW_PC_RESOLUTION:" + str(key))
        if sha in first_by_sha:
            violations.append("REUSED_SCREENSHOT:" + str(key))
            eligible.discard(first_by_sha[sha])
        else:
            first_by_sha[sha] = key
            if full_pc_resolution:
                eligible.add(key)
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
        # A source- or desktop-only visual grade cannot override real mobile playability.
        median = item.get("fps_median") if isinstance(item, dict) else None
        if type(median) not in (int, float) or not (0 < median <= 300):
            violations.append("MISSING_FPS_MEDIAN:" + dev)
        elif dev == "android" and median < 30:
            violations.append("MOBILE_MEDIAN_FPS_BELOW_30")
        minutes = item.get("session_minutes") if isinstance(item, dict) else None
        if type(minutes) not in (int, float) or minutes < 15:
            violations.append("MISSING_15_MIN_THERMAL_PLAYTEST:" + dev)
        if item.get("oom_crash_free") is not True:
            violations.append("CRASH_OR_OOM_NOT_CLEARED:" + dev)
        if dev == "android":
            drop = item.get("warm_fps_drop_fraction")
            if type(drop) not in (int, float) or not (0 <= drop <= 1):
                violations.append("MISSING_MOBILE_THERMAL_DROP")
            elif drop > 0.20:
                violations.append("MOBILE_WARM_FPS_DROP_OVER_20PCT")
            if not item.get("memory_mb_peak"):
                violations.append("MISSING_MOBILE_PEAK_MEMORY")
    if manifest.get("critical_visual_blockers") != []:
        violations.append("CRITICAL_BLOCKERS_NOT_CLEARED")
    if not manifest.get("human_reviewer"):
        violations.append("NO_HUMAN_REVIEWER")
    # Even perfect submitted images/scores are not cryptographic proof of Roblox
    # execution or owner acceptance: an OWNER review of the actual images is required.
    return {
        "gate": "REVIEW_READY" if not violations else "FAIL",
        "violations": violations, "shots_received": len(eligible) if usable_identity else 0,
        "shots_submitted": len(seen), "shots_required": len(expected),
        "human_reviewer_claim": bool(manifest.get("human_reviewer")),
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
