#!/usr/bin/env python3
"""GQ470 local nearby-teammate visual art: source-exact A candidate REAL69 -> REAL70.

Operates ONLY in a temporary directory using the immutable official PRIVATE
companion Place/receipt. Never pushes to the official RC, publishes or changes
the independent active S1 rich51 runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
PLACE_BYTES = 798390
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AllySilhouette"
COMPETING_CREST_ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_PlayerTeamCrest"
TARGET = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AllySilhouette.client.luau"
FEATURE = "GQ470_FB015_ALLY_SILHOUETTE_REAL69_20261121"
THIS = Path(__file__).resolve().parent
SOURCE = THIS / "EGGRUMBLE_AllySilhouette.client.luau"
sys.path.insert(0, str(THIS.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_ALLY_SILHOUETTE_" + why)


def hash256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def compose(original: Path, destination: Path) -> dict:
    original, destination = original.resolve(), destination.resolve()
    require(original.is_dir() and not destination.exists() and
            original != destination, "INPUT_OR_EXISTING_OUTPUT")
    raw_place = (original / PLACE).read_bytes()
    require(len(raw_place) == PLACE_BYTES and hash256(raw_place) == PLACE_SHA,
            "OFF69_SOURCE_PLACE_IDENTITY")
    receipt = json.loads((original / RECEIPT).read_text(encoding="utf-8"))
    require(receipt.get("canonical_build") is True and
            receipt.get("official_branch") == "rc/p0d-s1-kids-rc01" and
            receipt.get("build_head") == BASE and
            receipt.get("selected_source_count") == 69,
            "AUTHENTIC_OFFICIAL_RECEIPT")
    original_map = project_scan(original, PROJECT)
    require(COMPETING_CREST_ROUTE not in original_map, "COMPETING_PR976_AVATAR_CREST_ROUTE")
    require(len(original_map) == 69 and
            set(original_map) == set(receipt["source_hashes"]) ==
            set(receipt["source_classes"]) and ROUTE not in original_map,
            "ORIGINAL_69_SOURCE_SET_OR_COLLISION")
    require(all(original_map[k]["sha256"] == receipt["source_hashes"][k] and
                original_map[k]["class"] == receipt["source_classes"][k]
                for k in original_map),
            "ORIGINAL_69_SOURCE_LOCK")

    shutil.copytree(original, destination)
    project = json.loads((destination / PROJECT).read_text(encoding="utf-8"))
    starter = project["tree"].get("StarterPlayer")
    scripts = starter.get("StarterPlayerScripts") if isinstance(starter, dict) else None
    require(isinstance(scripts, dict) and "$path" not in scripts and
            "EGGRUMBLE_AllySilhouette" not in scripts,
            "PROJECT_STARTER_CONFLICT")
    scripts["EGGRUMBLE_AllySilhouette"] = {"$path": TARGET}
    new_file = destination / TARGET
    new_file.parent.mkdir(parents=True, exist_ok=True)
    new_file.write_bytes(SOURCE.read_bytes())
    (destination / PROJECT).write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    candidate = project_scan(destination, PROJECT)
    require(len(candidate) == 70 and
            set(candidate) == set(original_map) | {ROUTE} and
            all(candidate[k] == info for k, info in original_map.items()),
            "NONLOSS_69_EXACT")
    require(candidate[ROUTE]["class"] == "LocalScript" and
            candidate[ROUTE]["sha256"] == hash256(SOURCE.read_bytes()),
            "NEW_LOCAL_SOURCE_IDENTITY")
    report = {
        "schema": "GQ470_ALLY_SILHOUETTE_SOURCE_CANDIDATE_V1",
        "feature_id": FEATURE,
        "stage": "A_SOURCE_CANDIDATE_NOT_FORMAL",
        "canonical_branch": "rc/p0d-s1-kids-rc01",
        "base_head": BASE,
        "source_profile": "REAL70_PRIVATE_COMPANION_A_ONLY",
        "original_sources_preserved": 69,
        "candidate_source_count": 70,
        "added_selected_script": ROUTE,
        "added_script_class": "LocalScript",
        "added_script_sha256": candidate[ROUTE]["sha256"],
        "new_gameplay_authorities": 0,
        "new_gameplay_parts": 0,
        "max_client_highlights": 3,
        "scan_interval_seconds": 0.75,
        "no_per_frame_hook": True,
        "original_place_bytes": PLACE_BYTES,
        "original_place_sha256": PLACE_SHA,
        "formal_integrated": False,
        "studio_solo": "NOT_TESTED",
        "studio_2client": "NOT_TESTED",
        "android15": "NOT_TESTED",
        "human_art": "NOT_TESTED",
        "screenshots": "0/32",
        "owner_accepted": False,
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
    }
    (destination / "GQ470_ALLY_SILHOUETTE_SOURCE_RECEIPT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return report


B_PACKET = "B220_ALLY_SILHOUETTE_ONE_NEW_CLIENT_SOURCE_NOT_FORMAL"
B_MANIFEST = "SOURCE_SELECT_MANIFEST.json"


def export_b(candidate: Path, built_place: Path) -> dict:
    """Export exactly the single locally-rendered source; never change formal RC."""
    candidate, built_place = candidate.resolve(), built_place.resolve()
    report = json.loads((candidate / "GQ470_ALLY_SILHOUETTE_SOURCE_RECEIPT.json")
                        .read_text(encoding="utf-8"))
    require(report.get("stage") == "A_SOURCE_CANDIDATE_NOT_FORMAL" and
            report.get("formal_integrated") is False and
            report.get("base_head") == BASE and
            report.get("candidate_source_count") == 70 and
            report.get("original_sources_preserved") == 69 and
            report.get("added_selected_script") == ROUTE and
            report.get("added_script_class") == "LocalScript" and
            report.get("owner_accepted") is False and
            report.get("art_gate") == "ART_NO_GO",
            "B_RECEIPT_MUST_NOT_CLAIM_FORMAL_OR_ART_GO")
    scanned = project_scan(candidate, PROJECT)
    raw = (candidate / TARGET).read_bytes()
    require(len(scanned) == 70 and
            scanned[ROUTE]["sha256"] == hash256(raw) ==
            report["added_script_sha256"] and
            scanned[ROUTE]["class"] == "LocalScript" and
            raw == SOURCE.read_bytes(),
            "B_NEW_CLIENT_SOURCE_LOCK")
    require(built_place.is_file() and
            len(built_place.read_bytes()) > PLACE_BYTES and
            hash256(built_place.read_bytes()) != PLACE_SHA,
            "B_GENUINE_BUILT_CANDIDATE_REQUIRED")
    folder = candidate / B_PACKET
    require(not folder.exists(), "B_NO_OVERWRITE")
    dest = folder / "selected_sources" / TARGET.removeprefix("sources/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    manifest = {
        "schema": "GQ470_ALLY_SILHOUETTE_B220_SOURCE_SELECT_V1",
        "feature_id": FEATURE,
        "formal_branch": "rc/p0d-s1-kids-rc01",
        "formal_base_sha": BASE,
        "source_profile": "PRIVATE_COMPANION_REAL69_TO_70_A_ONLY",
        "new_script_route": ROUTE,
        "exclusive_alternative_route": COMPETING_CREST_ROUTE,
        "exclusive_alternative_pr": 976,
        "new_script_class": "LocalScript",
        "new_source_path": "selected_sources/" + TARGET.removeprefix("sources/"),
        "new_source_sha256": hash256(raw),
        "new_source_bytes": len(raw),
        "original_selected_sources_preserved": 69,
        "candidate_selected_sources": 70,
        "source_only": True,
        "candidate_place_bytes": built_place.stat().st_size,
        "candidate_place_sha256": hash256(built_place.read_bytes()),
        "original_place_bytes": PLACE_BYTES,
        "original_place_sha256": PLACE_SHA,
        "formal_integrated": False,
        "b_admission": "DEFER_P0_910_FIRST_PENDING_CLAIM_AND_250",
        "needs_b220_authenticated_fresh_head_nonforce_cas": True,
        "art_status": "ART_NO_GO",
        "studio_android_fun": "NOT_TESTED",
        "owner_accepted": False,
    }
    (folder / B_MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    verify_b(candidate, built_place)
    return manifest


def verify_b(candidate: Path, built_place: Path) -> None:
    root = candidate.resolve() / B_PACKET
    manifest = json.loads((root / B_MANIFEST).read_text(encoding="utf-8"))
    raw = (candidate / TARGET).read_bytes()
    actual = root / manifest["new_source_path"]
    require(actual.resolve().is_relative_to(root.resolve()) and
            actual.read_bytes() == raw and
            manifest["schema"] == "GQ470_ALLY_SILHOUETTE_B220_SOURCE_SELECT_V1" and
            manifest["formal_base_sha"] == BASE and
            manifest["new_script_route"] == ROUTE and
            manifest["exclusive_alternative_route"] == COMPETING_CREST_ROUTE and
            manifest["exclusive_alternative_pr"] == 976 and
            manifest["new_script_class"] == "LocalScript" and
            manifest["new_source_sha256"] == hash256(raw) and
            manifest["new_source_bytes"] == len(raw) and
            manifest["original_selected_sources_preserved"] == 69 and
            manifest["candidate_selected_sources"] == 70 and
            manifest["formal_integrated"] is False and
            manifest["owner_accepted"] is False and
            manifest["art_status"] == "ART_NO_GO" and
            manifest["needs_b220_authenticated_fresh_head_nonforce_cas"] is True and
            manifest["candidate_place_bytes"] == built_place.stat().st_size and
            manifest["candidate_place_sha256"] == hash256(built_place.read_bytes()),
            "B_SOURCE_SELECT_BAD_LOCK_OR_FAKE_ADMISSION")
    present = {p.relative_to(root).as_posix()
               for p in root.rglob("*") if p.is_file()}
    require(present == {B_MANIFEST, manifest["new_source_path"]},
            "B_PACKET_UNEXPECTED_FILES")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--official", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--export-b", type=Path)
    parser.add_argument("--verify-b", type=Path)
    parser.add_argument("--built-place", type=Path)
    opt = parser.parse_args()
    if opt.export_b is not None:
        require(opt.built_place is not None, "B_MISSING_BUILT_PLACE")
        print(json.dumps(export_b(opt.export_b, opt.built_place),
                         ensure_ascii=False, indent=2))
    elif opt.verify_b is not None:
        require(opt.built_place is not None, "B_MISSING_BUILT_PLACE")
        verify_b(opt.verify_b, opt.built_place)
        print("GQ470_ALLY_B220_EXACT_ONE_LOCAL_SOURCE_PACKET_PASS")
    else:
        require(opt.official is not None and opt.out is not None,
                "MISSING_OFFICIAL_AND_OUT")
        print(json.dumps(compose(opt.official, opt.out),
                         ensure_ascii=False, indent=2))
