#!/usr/bin/env python3
"""GQ470 ground motion art: source-exact A candidate REAL69 -> REAL70.

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
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_GroundMotionFX"
TARGET = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_GroundMotionFX.client.luau"
FEATURE = "GQ470_FB015_GROUND_MOTION_MATTE_20261121"
THIS = Path(__file__).resolve().parent
SOURCE = THIS / "EGGRUMBLE_GroundMotionFX.client.luau"
sys.path.insert(0, str(THIS.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_GROUND_FX_" + why)


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
            "EGGRUMBLE_GroundMotionFX" not in scripts,
            "PROJECT_STARTER_CONFLICT")
    scripts["EGGRUMBLE_GroundMotionFX"] = {"$path": TARGET}
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
        "schema": "GQ470_GROUND_MOTION_FX_SOURCE_CANDIDATE_V1",
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
        "max_transient_fx_parts_local": 6,
        "max_parts_step_android": 1,
        "max_parts_step_pc": 2,
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
    (destination / "GQ470_GROUND_FX_SOURCE_RECEIPT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--official", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    opt = parser.parse_args()
    print(json.dumps(compose(opt.official, opt.out), ensure_ascii=False, indent=2))
