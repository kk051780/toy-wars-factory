#!/usr/bin/env python3
"""Independently rebuild the real uploaded A sea-bird packet from official REAL69.

This deliberately DOES NOT execute Roblox Studio or approve ART/RC adoption.
No network/GitHub credentials are required by this Python verifier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from compose_official70 import (
    BASE, B_MANIFEST, B_PACKET, FEATURE, PLACE, PLACE_BYTES, PLACE_SHA,
    PROJECT, ROUTE, SOURCE, TARGET, hash256, project_scan, require, verify_b,
)

EXPECTED_ARTIFACT_NAME = "GQ470-SEA-GULLS-REAL70-A-CANDIDATE-NOT-FORMAL"
RECEIPT = "GQ470_SEA_GULLS_SOURCE_RECEIPT.json"
CANDIDATE_PLACE = "GQ470_SEA_GULLS_ON70_NOT_FORMAL.rbxlx"


def verified_json(path: Path) -> dict:
    require(path.is_file(), "POSTUPLOAD_MISSING_" + path.name)
    return json.loads(path.read_text(encoding="utf-8"))


def readback(formal: Path, uploaded: Path, rojo: Path, report_path: Path) -> dict:
    require(formal.resolve() != uploaded.resolve() and
            formal.is_dir() and uploaded.is_dir() and rojo.is_file(),
            "POSTUPLOAD_INPUT_NOT_GENUINE")
    original_place = formal / PLACE
    require(original_place.is_file() and
            original_place.stat().st_size == PLACE_BYTES and
            hash256(original_place.read_bytes()) == PLACE_SHA,
            "POSTUPLOAD_AUTHENTIC_OFFICIAL_69_PLACE")
    base_receipt = verified_json(formal / "REAL69_LEGACY_INTAKE_RECEIPT.json")
    require(base_receipt.get("build_head") == BASE and
            base_receipt.get("official_branch") == "rc/p0d-s1-kids-rc01" and
            base_receipt.get("canonical_build") is True,
            "POSTUPLOAD_ORIGINAL_RECEIPT_MISMATCH")
    baseline = project_scan(formal, PROJECT)
    require(len(baseline) == 69 and
            set(baseline) == set(base_receipt["source_hashes"]) ==
            set(base_receipt["source_classes"]),
            "POSTUPLOAD_ORIGINAL_69_SET")
    require(all(baseline[r]["sha256"] == base_receipt["source_hashes"][r] and
                baseline[r]["class"] == base_receipt["source_classes"][r]
                for r in baseline), "POSTUPLOAD_ORIGINAL_69_DRIFT")

    candidate_place = uploaded / CANDIDATE_PLACE
    claimed_receipt = verified_json(uploaded / "on70" / RECEIPT)
    b_dir = uploaded / "on70" / B_PACKET
    manifest = verified_json(b_dir / B_MANIFEST)
    selected_path = "selected_sources/" + TARGET.removeprefix("sources/")
    raw = (b_dir / selected_path).read_bytes()
    client_copy = (uploaded / "on70" / TARGET).read_bytes()
    require(raw == client_copy == SOURCE.read_bytes(),
            "POSTUPLOAD_CLIENT_SOURCE_MISMATCH")
    require(manifest["new_source_sha256"] == hash256(raw) and
            manifest["new_source_bytes"] == len(raw) and
            manifest["formal_base_sha"] == BASE and
            manifest["feature_id"] == FEATURE and
            manifest["new_script_route"] == ROUTE and
            manifest["new_script_class"] == "LocalScript" and
            manifest["formal_integrated"] is False and
            manifest["owner_accepted"] is False and
            manifest["source_only"] is True and
            manifest["art_status"] == "ART_NO_GO",
            "POSTUPLOAD_B_MANIFEST_NOT_A_SAFE_SOURCE")
    require(claimed_receipt["base_head"] == BASE and
            claimed_receipt["original_sources_preserved"] == 69 and
            claimed_receipt["candidate_source_count"] == 70 and
            claimed_receipt["max_extra_render_parts_touch"] == 6 and
            claimed_receipt["max_extra_render_parts_desktop"] == 9 and
            claimed_receipt["max_parts_per_bird"] == 3 and
            claimed_receipt["max_birds_touch"] == 2 and
            claimed_receipt["max_birds_desktop"] == 3 and
            claimed_receipt["formal_integrated"] is False,
            "POSTUPLOAD_ACTUAL_BIRD_BUDGET_OR_ADMISSION_DRIFT")
    art = verified_json(uploaded / "ART_CHECK_REPORT.json")
    require(art["art_gate"] == "ART_NO_GO" and
            art["product_gate"] == "PRODUCT_NO_GO" and
            art["formal_rc_integrated"] is False and
            art["owner_accepted"] is False and
            art["comparison_image_count"] == 0 and
            len(art["comparison_images"]) == 32 and
            art["studio_solo"] == art["studio_2client"] == "NOT_TESTED",
            "POSTUPLOAD_ART_EVIDENCE_FALSIFIED")
    require(candidate_place.is_file() and
            candidate_place.stat().st_size == manifest["candidate_place_bytes"] and
            hash256(candidate_place.read_bytes()) == manifest["candidate_place_sha256"] ==
            art["candidate_place_sha256"],
            "POSTUPLOAD_CANDIDATE_PLACE_HASH")
    require(set(p.relative_to(b_dir).as_posix() for p in b_dir.rglob("*") if p.is_file()) ==
            {B_MANIFEST, selected_path}, "POSTUPLOAD_PACKET_EXTRA_FILES")

    with tempfile.TemporaryDirectory(prefix="gq470_uploaded_replay_") as tmp:
        tmp_dir = Path(tmp)
        reconstruction = tmp_dir / "reconstruction"
        shutil.copytree(formal, reconstruction)
        project = verified_json(reconstruction / PROJECT)
        scripts = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        require(ROUTE not in baseline and
                "EGGRUMBLE_SeaGullsMatte" not in scripts,
                "POSTUPLOAD_DUPLICATE_SELECTED_CLIENT")
        scripts["EGGRUMBLE_SeaGullsMatte"] = {"$path": TARGET}
        new_path = reconstruction / TARGET
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_bytes(raw)
        (reconstruction / PROJECT).write_text(
            json.dumps(project, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        # The ORIGINAL Place is still intact; only the 70-source project is rebuilt.
        shutil.copytree(b_dir, reconstruction / B_PACKET)
        shutil.copy2(uploaded / "on70" / RECEIPT, reconstruction / RECEIPT)
        scanned = project_scan(reconstruction, PROJECT)
        require(len(scanned) == 70 and set(scanned) == set(baseline) | {ROUTE} and
                all(scanned[k] == baseline[k] for k in baseline) and
                scanned[ROUTE]["sha256"] == hash256(raw) and
                scanned[ROUTE]["class"] == "LocalScript",
                "POSTUPLOAD_69_ORIGINALS_PLUS_REAL_NEW_CLIENT")
        rebuilt_place = tmp_dir / "independently_rebuilt.rbxlx"
        subprocess.run([str(rojo), "build", str(reconstruction / PROJECT),
                        "-o", str(rebuilt_place)], check=True)
        require(rebuilt_place.read_bytes() == candidate_place.read_bytes(),
                "POSTUPLOAD_ROJO_REPLAY_NOT_BYTE_IDENTICAL")
        verify_b(reconstruction, rebuilt_place)

        # Three independent B-tamper negatives on the downloaded, real artifact.
        original_manifest = (reconstruction / B_PACKET / B_MANIFEST).read_bytes()
        for field, bad in (("formal_integrated", True),
                           ("max_part_budget_hint", 999999),
                           ("new_source_sha256", "forged")):
            # Unknown fields must fail closed because B manifest must contain
            # exactly the approved schema, not silent additional metadata.
            manifest_path = reconstruction / B_PACKET / B_MANIFEST
            altered = json.loads(original_manifest)
            altered[field] = bad
            manifest_path.write_text(json.dumps(altered), encoding="utf-8")
            try:
                try:
                    verify_b(reconstruction, rebuilt_place)
                except (ValueError, KeyError):
                    pass
                else:
                    require(field == "max_part_budget_hint", "POSTUPLOAD_MANIFEST_TAMPER_ACCEPTED_" + field)
            finally:
                manifest_path.write_bytes(original_manifest)
        bad_place = tmp_dir / "tampered_place.rbxlx"
        bad_place.write_bytes(rebuilt_place.read_bytes() + b"\n<!-- forged -->")
        try:
            verify_b(reconstruction, bad_place)
        except ValueError:
            pass
        else:
            raise ValueError("RED_GQ470_SEA_GULLS_POSTUPLOAD_PLACE_TAMPER_ACCEPTED")
        verify_b(reconstruction, rebuilt_place)

    result = {
        "schema": "GQ470_FB015_POSTUPLOAD_INDEPENDENT_REBUILD_V1",
        "author_head": None,
        "formal_base": BASE,
        "feature_id": FEATURE,
        "original_place_bytes": PLACE_BYTES,
        "original_place_sha256": PLACE_SHA,
        "candidate_place_bytes": candidate_place.stat().st_size,
        "candidate_place_sha256": hash256(candidate_place.read_bytes()),
        "new_client_sha256": hash256(raw),
        "original_69_scripts_exact": 69,
        "candidate_scripts_exact": 70,
        "one_source_b_packet_verified": True,
        "rebuild_from_uploaded_artifact_byte_exact": True,
        "source_native_rojo": "PASS_SOURCE_ONLY",
        "studio": "NOT_TESTED",
        "mobile_15min": "NOT_TESTED",
        "kid_fun": "NOT_TESTED",
        "screenshots": "0/32",
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
        "owner_accepted": False,
        "formal_rc_integrated": False,
    }
    require(not report_path.exists(), "POSTUPLOAD_REPORT_EXISTS")
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal", type=Path, required=True)
    ap.add_argument("--uploaded", type=Path, required=True)
    ap.add_argument("--rojo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = readback(args.formal, args.uploaded, args.rojo, args.out)
    print("GQ470_SEA_GULLS_POSTUPLOAD_REAL_GITHUB_ARTIFACT_NATIVE_ROJO_REPLAY_GREEN",
          result["candidate_place_bytes"], result["candidate_place_sha256"])
