#!/usr/bin/env python3
"""GQ470 sea gulls matte art: source-exact A candidate REAL69 -> REAL70.

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
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
PLACE_BYTES = 798390
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_SeaGullsMatte"
TARGET = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_SeaGullsMatte.client.luau"
FEATURE = "GQ470_FB015_SEA_GULLS_MATTE_20261121"
THIS = Path(__file__).resolve().parent
SOURCE = THIS / "EGGRUMBLE_SeaGullsMatte.client.luau"
sys.path.insert(0, str(THIS.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_SEA_GULLS_" + why)


def hash256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()



def place_sources(place: Path) -> dict[str, tuple[str, str]]:
    """Read all real Rojo Place script bytes; a random .rbxlx is not proof."""
    scripts: dict[str, tuple[str, str]] = {}
    root = ET.parse(place).getroot()
    for item in root.iter("Item"):
        cls = item.attrib.get("class")
        if cls not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        require(props is not None, "PLACE_SCRIPT_PROPERTIES")
        name = next((p.text for p in props if p.attrib.get("name") == "Name"), None)
        source = next((p for p in props if p.attrib.get("name") == "Source"), None)
        require(isinstance(name, str) and len(name) > 0 and
                source is not None and name not in scripts,
                "PLACE_DUPLICATE_NAME_OR_MISSING_SOURCE")
        scripts[name] = (cls, hash256((source.text or "").encode("utf-8")))
    return scripts


def assert_place_selected(place: Path, scanned: dict, expected_count: int) -> None:
    require(place.is_file(), "BUILT_PLACE_NOT_FOUND")
    scripts = place_sources(place)
    require(len(scripts) == expected_count and len(scanned) == expected_count,
            "PLACE_SCRIPT_COUNT_NOT_SELECTED")
    for route, info in scanned.items():
        name = route.rsplit("/", 1)[-1]
        require(scripts.get(name) == (info["class"], info["sha256"]),
                "PLACE_SOURCE_CLASS_NOT_MATCHED_" + name)


def assert_candidate_nonloss(candidate: Path) -> dict:
    """Recheck the authentic original Place and every original route at B time."""
    require((candidate / PLACE).is_file() and
            hash256((candidate / PLACE).read_bytes()) == PLACE_SHA and
            (candidate / PLACE).stat().st_size == PLACE_BYTES,
            "B_ORIGINAL_PLACE_IDENTITY")
    receipt = json.loads((candidate / RECEIPT).read_text(encoding="utf-8"))
    require(receipt.get("official_branch") == "rc/p0d-s1-kids-rc01" and
            receipt.get("build_head") == BASE and
            receipt.get("canonical_build") is True and
            receipt.get("selected_source_count") == 69,
            "B_ORIGINAL_RECEIPT_AUTHORITY")
    hashes = receipt.get("source_hashes")
    classes = receipt.get("source_classes")
    require(isinstance(hashes, dict) and isinstance(classes, dict) and
            len(hashes) == len(classes) == 69,
            "B_ORIGINAL_69_RECEIPT_SET")
    scanned = project_scan(candidate, PROJECT)
    require(len(scanned) == 70 and set(scanned) == set(hashes) | {ROUTE} and
            set(classes) == set(hashes),
            "B_SELECTED_ROUTE_SET_NOT_69_PLUS_1")
    require(all(scanned[route]["sha256"] == digest and
                scanned[route]["class"] == classes[route]
                for route, digest in hashes.items()),
            "B_ORIGINAL_69_SOURCE_CLASS_DRIFT")
    original = {route: scanned[route] for route in hashes}
    assert_place_selected(candidate / PLACE, original, 69)
    require(scanned[ROUTE]["sha256"] == hash256(SOURCE.read_bytes()) and
            scanned[ROUTE]["class"] == "LocalScript",
            "B_NEW_SOURCE_CLASS_DRIFT")
    return scanned


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

    # Do not invent a second accessibility preference: the original REAL69
    # CombatFeel owns EGGRUMBLE_ReducedEffects. Check its actual selected source.
    combat_route = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel"
    reduced_flag = 'GetAttribute("EGGRUMBLE_ReducedEffects")'
    require(combat_route in original_map and
            reduced_flag in (original / original_map[combat_route]["path"]).read_text(encoding="utf-8") and
            reduced_flag in SOURCE.read_text(encoding="utf-8"),
            "MUST_REUSE_ORIGINAL_REAL69_REDUCED_EFFECTS_FLAG")

    # Bind this cosmetic to the actual immutable selected LSS world generator,
    # not merely a misleading name from another visual candidate.
    lss_route = "ServerScriptService/EGGRUMBLE_LandSeaSkyTraversal"
    require(lss_route in original_map, "AUTHENTIC_SEA_DOCK_OWNER_ROUTE")
    lss_source = (original / original_map[lss_route]["path"]).read_text(encoding="utf-8")
    require(all(marker in lss_source for marker in (
        'local NAME = "EGGRUMBLE_LAND_SEA_SKY_20261117"',
        'local scene=Instance.new("Folder")',
        "scene.Name=NAME",
        'local landDock=put(scene,"PublicSeaDock"',
        'CFrame.new(x,y+0.9,shoreZ-92)',
        'CFrame.new(x,y+0.08,shoreZ)',
    )), "AUTHENTIC_LSS_DOCK_AND_SCENE_SOURCE")
    art_source = SOURCE.read_text(encoding="utf-8")
    require('parent.Name == "EGGRUMBLE_LAND_SEA_SKY_20261117"' in art_source and
            'local seaward = 28 + 9 * slot' in art_source,
            "NEW_ART_MUST_MATCH_AUTHENTIC_LSS_SCENE_AND_SEAWARD")

    shutil.copytree(original, destination)
    project = json.loads((destination / PROJECT).read_text(encoding="utf-8"))
    starter = project["tree"].get("StarterPlayer")
    scripts = starter.get("StarterPlayerScripts") if isinstance(starter, dict) else None
    require(isinstance(scripts, dict) and "$path" not in scripts and
            "EGGRUMBLE_SeaGullsMatte" not in scripts,
            "PROJECT_STARTER_CONFLICT")
    scripts["EGGRUMBLE_SeaGullsMatte"] = {"$path": TARGET}
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
        "schema": "GQ470_SEA_GULLS_MOTION_FX_SOURCE_CANDIDATE_V1",
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
        "max_extra_render_parts_desktop": 9,
        "max_extra_render_parts_touch": 6,
        "max_birds_touch": 2,
        "max_birds_desktop": 3,
        "max_parts_per_bird": 3,
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
    (destination / "GQ470_SEA_GULLS_SOURCE_RECEIPT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return report


B_PACKET = "B220_SEA_GULLS_ONE_NEW_CLIENT_SOURCE_NOT_FORMAL"
B_MANIFEST = "SOURCE_SELECT_MANIFEST.json"


def export_b(candidate: Path, built_place: Path) -> dict:
    """Export exactly the single locally-rendered source; never change formal RC."""
    candidate, built_place = candidate.resolve(), built_place.resolve()
    report = json.loads((candidate / "GQ470_SEA_GULLS_SOURCE_RECEIPT.json")
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
    scanned = assert_candidate_nonloss(candidate)
    raw = (candidate / TARGET).read_bytes()
    assert_place_selected(built_place, scanned, 70)
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
        "schema": "GQ470_SEA_GULLS_B220_SOURCE_SELECT_V1",
        "feature_id": FEATURE,
        "formal_branch": "rc/p0d-s1-kids-rc01",
        "formal_base_sha": BASE,
        "source_profile": "PRIVATE_COMPANION_REAL69_TO_70_A_ONLY",
        "new_script_route": ROUTE,
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
    scanned = assert_candidate_nonloss(candidate)
    assert_place_selected(built_place, scanned, 70)
    raw = (candidate / TARGET).read_bytes()
    expected_path = "selected_sources/" + TARGET.removeprefix("sources/")
    require(manifest.get("new_source_path") == expected_path,
            "B_MANIFEST_SOURCE_ROUTE_PATH")
    actual = root / expected_path
    require(actual.resolve().is_relative_to(root.resolve()) and
            actual.read_bytes() == raw and
            manifest["schema"] == "GQ470_SEA_GULLS_B220_SOURCE_SELECT_V1" and
            manifest["formal_base_sha"] == BASE and
            manifest["formal_branch"] == "rc/p0d-s1-kids-rc01" and
            manifest["source_profile"] == "PRIVATE_COMPANION_REAL69_TO_70_A_ONLY" and
            manifest["feature_id"] == FEATURE and
            manifest["source_only"] is True and
            manifest["b_admission"] == "DEFER_P0_910_FIRST_PENDING_CLAIM_AND_250" and
            manifest["studio_android_fun"] == "NOT_TESTED" and
            manifest["original_place_sha256"] == PLACE_SHA and
            manifest["original_place_bytes"] == PLACE_BYTES and
            manifest["new_script_route"] == ROUTE and
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
        print("GQ470_SEA_GULLS_B220_EXACT_ONE_LOCAL_SOURCE_PACKET_PASS")
    else:
        require(opt.official is not None and opt.out is not None,
                "MISSING_OFFICIAL_AND_OUT")
        print(json.dumps(compose(opt.official, opt.out),
                         ensure_ascii=False, indent=2))
