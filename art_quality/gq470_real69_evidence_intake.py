#!/usr/bin/env python3
"""#470/#420 REAL69 art evidence intake: 32 real PNG checks, NEVER art approval.

The canonical REAL69 SOURCE gate audits the actual 69 Luau scripts but correctly
ships with zero Studio captures. This independent companion consumes a matching
official Place + source report and optional real Studio evidence. Reuse the
existing #420 evidence validator; do not fork its rules or touch game scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

from check_art_quality import SCENES, DEVICES, VERSIONS, CATEGORIES, evidence_audit, png_info

FORMAL = "rc/p0d-s1-kids-rc01"
PROFILE = "REAL69_PRIVATE_COMPANION"
SOURCE_SCHEMA = "P0D_REAL69_GQ470_ART_CHECK_REPORT_V1"
HEAD = re.compile(r"^[0-9a-f]{40}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = len(SCENES) * len(DEVICES) * len(VERSIONS)


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("RED_REAL69_ART_EVIDENCE_" + reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()



def verified_png_integrity(path: Path) -> tuple[int, int, str, str]:
    """Require a complete CRC-valid PNG, not just its magic bytes and IHDR.

    The common art checker supplies the resolution/size gates; this stricter
    evidence counter blocks truncated, corrupted, or trailing-junk files from
    inflating the REAL69 capture progress metric. It is NOT Studio provenance.
    """
    width, height, sha = png_info(path)
    data = path.read_bytes()
    offset = 8
    seen_header = seen_pixels = seen_end = False
    encoded_scanlines: list[bytes] = []
    while offset < len(data):
        if len(data) - offset < 12:
            raise ValueError("TRUNCATED_PNG_CHUNK")
        length = struct.unpack_from(">I", data, offset)[0]
        label = data[offset + 4:offset + 8]
        payload_end = offset + 8 + length
        next_offset = payload_end + 4
        if next_offset > len(data):
            raise ValueError("TRUNCATED_PNG_PAYLOAD")
        if len(label) != 4 or not all(
            65 <= letter <= 90 or 97 <= letter <= 122 for letter in label
        ):
            raise ValueError("INVALID_PNG_CHUNK_NAME")
        stored_crc = struct.unpack_from(">I", data, payload_end)[0]
        actual_crc = zlib.crc32(data[offset + 4:payload_end]) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ValueError("PNG_CHUNK_CRC_MISMATCH")
        if label == b"IHDR":
            if seen_header or offset != 8 or length != 13:
                raise ValueError("PNG_IHDR_ORDER")
            seen_header = True
        elif not seen_header:
            raise ValueError("PNG_IHDR_MISSING")
        if label == b"IDAT":
            seen_pixels = True
            encoded_scanlines.append(data[offset + 8:payload_end])
        if label == b"IEND":
            if seen_end or length != 0 or next_offset != len(data):
                raise ValueError("PNG_IEND_OR_TRAILING_DATA")
            seen_end = True
        offset = next_offset
    if not (seen_header and seen_pixels and seen_end):
        raise ValueError("PNG_REQUIRED_CHUNKS_MISSING")

    # CRC alone does not prove valid image pixels: an attacker can recompute a
    # chunk CRC around a corrupt or truncated zlib stream. Bound inflation by
    # the IHDR's exact scanline budget (also handles Adam7 interlace), require
    # the zlib checksum/end marker, and hash *decoded scanlines* so merely
    # recompressing the same screenshot cannot count as a second camera view.
    depth, color, compression, filtering, interlace = data[24:29]
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if (channels is None or depth not in (1, 2, 4, 8, 16)
            or compression != 0 or filtering != 0 or interlace not in (0, 1)
            or (color in (2, 4, 6) and depth not in (8, 16))
            or (color == 3 and depth == 16)):
        raise ValueError("PNG_UNSUPPORTED_IHDR")
    passes = ((0, 0, 1, 1),) if interlace == 0 else (
        (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8),
        (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))
    scanlines: list[tuple[int, int]] = []
    expected = 0
    for x0, y0, dx, dy in passes:
        cols = max(0, (width - x0 + dx - 1) // dx)
        rows = max(0, (height - y0 + dy - 1) // dy)
        if not cols or not rows:
            continue
        row_length = 1 + (cols * channels * depth + 7) // 8
        scanlines.append((rows, row_length))
        expected += rows * row_length
    if not 0 < expected <= 128 * 1024 * 1024:
        raise ValueError("PNG_DECODE_BUDGET_EXCEEDED")
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(b"".join(encoded_scanlines), expected + 1)
    except zlib.error as exc:
        raise ValueError("PNG_INVALID_IDAT_ZLIB") from exc
    if (len(raw) != expected or not decoder.eof or
            decoder.unused_data or decoder.unconsumed_tail):
        raise ValueError("PNG_INVALID_IDAT_SCANLINES")
    cursor = 0
    for rows, row_length in scanlines:
        for _ in range(rows):
            if raw[cursor] > 4:
                raise ValueError("PNG_INVALID_SCANLINE_FILTER")
            cursor += row_length
    return width, height, sha, hashlib.sha256(raw).hexdigest()


def actual_png_count(manifest_path: Path | None, screenshots: Path | None,
                     expected_head: str | None = None,
                     expected_place_sha: str | None = None) -> int:
    """Count actual valid, distinct PNG files, never just manifest rows.

    The legacy generic evidence gate counts unique declared keys even when
    image files are missing; this metric intentionally excludes those rows.
    """
    if manifest_path is None or not manifest_path.is_file():
        return 0
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return 0
    if not isinstance(manifest, dict):
        return 0
    # A real PNG from a stale Studio build is not valid progress for this RC.
    # The standalone counter remains backwards compatible for synthetic QA;
    # production audit always pins both the official HEAD and exact Place.
    if expected_head is not None and manifest.get("after_head") != expected_head:
        return 0
    if (expected_place_sha is not None and
            manifest.get("after_place_sha256") != expected_place_sha):
        return 0
    shots = manifest.get("shots")
    if not isinstance(shots, list):
        return 0
    root = (screenshots or manifest_path.parent).resolve()
    seen_keys: set[tuple[str, str, str]] = set()
    seen_hashes: set[str] = set()
    seen_pixel_streams: set[str] = set()
    count = 0
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        scene, device, version = (shot.get("scene"), shot.get("device"), shot.get("version"))
        if not all(isinstance(v, str) for v in (scene, device, version)):
            continue
        key = (scene, device, version)
        if (key in seen_keys or key[0] not in SCENES or
                key[1] not in DEVICES or key[2] not in VERSIONS):
            continue
        # Only validated, distinct PNGs consume a camera slot. The shared
        # #420 gate still independently rejects duplicate manifest rows.
        name = shot.get("file")
        if not isinstance(name, str):
            continue
        file = root / name
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            continue
        try:
            width, height, sha, pixel_sha = verified_png_integrity(file)
        except (OSError, ValueError):
            continue
        if key[1] == "pc" and (width < 1280 or height < 720):
            continue
        # Ancillary PNG metadata can change the file SHA without changing a
        # single pixel. Count the same image at most once across 32 slots.
        if sha in seen_hashes or pixel_sha in seen_pixel_streams:
            continue
        seen_keys.add(key)
        seen_hashes.add(sha)
        seen_pixel_streams.add(pixel_sha)
        count += 1
    return count


def audit(source_report_path: Path, place: Path, expected_head: str,
          evidence_path: Path | None, screenshots: Path | None) -> dict:
    need(HEAD.fullmatch(expected_head) is not None, "EXPECTED_HEAD_REQUIRED")
    source = json.loads(source_report_path.read_text(encoding="utf-8"))
    need(source.get("schema") == SOURCE_SCHEMA and
         source.get("only_formal_branch") == FORMAL and
         source.get("selected_profile") == PROFILE and
         source.get("official_build_head") == expected_head,
         "STALE_OR_WRONG_SOURCE_REPORT")
    gate = source.get("source_gate")
    need(isinstance(gate, dict) and
         gate.get("status") == "PASS_SOURCE_ONLY" and
         gate.get("actual_place_scripts") == 69 and
         gate.get("selected_routes_source_class_hash_exact") == 69 and
         gate.get("verified_visual_feature_sources", 0) >= 3,
         "SOURCE_69_NOT_VERIFIED")
    expected_sha = source.get("private_place_sha256")
    need(isinstance(expected_sha, str) and SHA.fullmatch(expected_sha) is not None,
         "INVALID_SOURCE_PLACE_SHA")
    data = place.read_bytes()
    need(len(data) == source.get("private_place_bytes") and
         digest(data) == expected_sha, "PLACE_BYTES_OR_SHA_MISMATCH")
    need(source.get("owner_accepted") is False and
         source.get("art_gate") == "ART_NO_GO", "UNAUTHORIZED_ART_APPROVAL")

    # The shared #420 validator assumes mapping-shaped JSON. Fail closed with
    # a report (not an uncaught traceback) for structurally invalid manifests.
    try:
        visual = evidence_audit(evidence_path, screenshots, expected_sha)
    except (AttributeError, TypeError):
        visual = {"gate": "FAIL", "violations": ["INVALID_MANIFEST_STRUCTURE"],
                  "shots_received": 0}
    violations = list(visual.get("violations", []))
    valid = actual_png_count(evidence_path, screenshots,
                             expected_head, expected_sha)
    manifest = None
    if evidence_path is not None and evidence_path.is_file():
        try:
            parsed = json.loads(evidence_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                manifest = parsed
                if (("shots" in manifest and not isinstance(manifest["shots"], list)) or
                    ("ratings" in manifest and not isinstance(manifest["ratings"], dict)) or
                    ("performance" in manifest and not isinstance(manifest["performance"], dict))):
                    violations.append("INVALID_MANIFEST_STRUCTURE")
            else:
                violations.append("INVALID_MANIFEST_ROOT")
        except (ValueError, OSError):
            pass
    if manifest is not None:
        if manifest.get("after_head") != expected_head:
            violations.append("AFTER_HEAD_NOT_CURRENT_REAL69")
        if manifest.get("before_head") == expected_head:
            violations.append("BEFORE_EQUALS_AFTER_HEAD")
        if valid != REQUIRED:
            violations.append("REAL_FILES_VERIFIED_" + str(valid) + "_OF_" + str(REQUIRED))
        ratings = manifest.get("ratings", {})
        for category in CATEGORIES:
            pc = (ratings.get(category, {}).get("pc")
                  if isinstance(ratings, dict) and
                  isinstance(ratings.get(category), dict) else None)
            # #420 PC target 4.5/5 means 5/5 with integer 1-to-5 ratings.
            if type(pc) is int and pc < 5:
                violations.append("PC_ART_TARGET_4_5_NOT_MET:" + category)
    ready = (visual.get("gate") == "REVIEW_READY" and
             valid == REQUIRED and not violations)
    return {
        "schema": "GQ470_REAL69_ART_EVIDENCE_INTAKE_V1",
        "official_branch": FORMAL,
        "official_head": expected_head,
        "private_place_sha256": expected_sha,
        "selected_game_scripts": 69,
        "source_gate": "PASS_SOURCE_ONLY",
        "expected_fixed_scenes": list(SCENES),
        "image_evidence": {
            "required": REQUIRED, "actual_distinct_valid_png_files": valid,
            "declared_shot_keys": visual.get("shots_received", 0),
            "generic_gate": visual.get("gate"),
            "status": "REVIEW_READY_OWNER_PENDING" if ready else "BLOCKED",
            "violations": sorted(set(violations)),
        },
        "pc_art_target_out_of_5": 4.5,
        "android_art_target_out_of_5": 4.0,
        "android_15min_and_first3min_fun": "NOT_PROVEN_BY_IMAGE_INTAKE",
        "image_authenticity_and_same_camera": "HUMAN_REVIEW_REQUIRED",
        "studio_gameplay_loop": "NOT_PROVEN_BY_IMAGE_INTAKE",
        "owner_accepted": False,
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--place", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.source_report, args.place, args.expected_head,
                   args.manifest, args.screenshots)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True,
                                    indent=2) + "\n", encoding="utf-8")
    print("REAL69_ART_EVIDENCE_INTAKE_SOURCE_PASS_ART_NO_GO",
          report["image_evidence"]["actual_distinct_valid_png_files"], "/", REQUIRED)


if __name__ == "__main__":
    main()
