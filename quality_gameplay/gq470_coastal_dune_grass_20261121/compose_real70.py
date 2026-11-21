#!/usr/bin/env python3
"""A-only honest REAL69 -> REAL70 source-select candidate, never an RC writer."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL = "rc/p0d-s1-kids-rc01"
REAL69_PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
REAL69_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
REAL69_BYTES = 798390
REAL69_RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
PROJECT = "EGGRUMBLE_REAL69.project.json"
FEATURE = "GQ470_FB015_COASTAL_DUNE_GRASS_20261121"
NEW_NAME = "EGGRUMBLE_CoastalDuneGrass"
NEW_ROUTE = "StarterPlayer/StarterPlayerScripts/" + NEW_NAME
NEW_FILE = "sources/StarterPlayer/StarterPlayerScripts/" + NEW_NAME + ".client.luau"
HERE = Path(__file__).resolve().parent
NEW_SOURCE = HERE / (NEW_NAME + ".client.luau")
OUT_RECEIPT = "GQ470_DUNE_GRASS_A_SOURCE_RECEIPT.json"
B_PACKET = "B220_DUNE_GRASS_ONE_CLIENT_SOURCE_NOT_FORMAL"
B_MANIFEST = "SOURCE_SELECT_MANIFEST.json"
sys.path.insert(0, str(HERE.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

def demand(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_DUNE_GRASS_" + why)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def original_lock(root: Path, allow_new: bool = False) -> tuple[dict, dict]:
    place = root / REAL69_PLACE
    demand(place.is_file() and place.stat().st_size == REAL69_BYTES
           and digest(place.read_bytes()) == REAL69_SHA, "OFFICIAL_PLACE_IDENTITY")
    receipt = json.loads((root / REAL69_RECEIPT).read_text(encoding="utf-8"))
    demand(receipt.get("canonical_build") is True
           and receipt.get("official_branch") == FORMAL
           and receipt.get("build_head") == BASE
           and receipt.get("selected_source_count") == 69,
           "OFFICIAL_SOURCE_RECEIPT_PROVENANCE")
    hashes = receipt.get("source_hashes")
    classes = receipt.get("source_classes")
    demand(isinstance(hashes, dict) and isinstance(classes, dict)
           and len(hashes) == len(classes) == 69, "OFFICIAL_RECEIPT_69")
    scanned = project_scan(root, PROJECT)
    if allow_new:
        # The candidate contains one extra optional LocalScript. Verify all
        # original 69 route/class/digests remain byte-identical; do NOT relax
        # the pristine Place/receipt pin or accept arbitrary extra sources.
        demand(len(scanned) == 70
               and set(scanned) == (set(hashes) | {NEW_ROUTE})
               and set(hashes) == set(classes),
               "CANDIDATE_EXACT_69_PLUS_1_SCRIPT_SET")
    else:
        demand(len(scanned) == 69 and set(scanned) == set(hashes) == set(classes)
               and NEW_ROUTE not in scanned, "OFFICIAL_ORIGINAL_SCRIPT_SET")
    for route in hashes:
        info = scanned[route]
        demand(info["sha256"] == hashes[route] and info["class"] == classes[route],
               "OFFICIAL_ORIGINAL_SHA_CLASS_" + route)
    # Confirm the reference world really exists in original selected source,
    # instead of trusting only a coincidental scene name in proposed art.
    lss = "ServerScriptService/EGGRUMBLE_LandSeaSkyTraversal"
    demand(lss in scanned, "OFFICIAL_LSS_ROUTE_MISSING")
    lss_text = (root / scanned[lss]["path"]).read_text(encoding="utf-8")
    demand('local NAME = "EGGRUMBLE_LAND_SEA_SKY_20261117"' in lss_text
           and 'local landDock=put(scene,"PublicSeaDock"' in lss_text
           and 'local floor=world:FindFirstChild("TacticalBattlefield")' in lss_text
           and 'CFrame.new(x,y+0.9,shoreZ-92)' in lss_text,
           "OFFICIAL_LSS_DOCK_OR_FLOOR_DRIFT")
    art = NEW_SOURCE.read_text(encoding="utf-8")
    demand("scene.Name ~= SCENE_NAME" in art
           and "FilterDescendantsInstances = {floor}" in art
           and 'GetAttribute("EGGRUMBLE_ReducedEffects")' in art,
           "NEW_ART_SCENE_FLOOR_SAFETY")
    return {route: scanned[route] for route in hashes}, receipt

def compose(original: Path, target: Path) -> None:
    original = original.resolve()
    target = target.resolve()
    demand(original.is_dir() and not target.exists() and original != target,
           "BAD_OR_EXISTING_TARGET")
    original_sources, _ = original_lock(original)
    shutil.copytree(original, target)
    project_file = target / PROJECT
    project = json.loads(project_file.read_text(encoding="utf-8"))
    try:
        scripts = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    except (KeyError, TypeError):
        raise ValueError("RED_GQ470_DUNE_GRASS_PROJECT_STARTER_MISSING") from None
    demand(isinstance(scripts, dict) and NEW_NAME not in scripts
           and "$path" not in scripts, "CLIENT_ROUTE_ALREADY_OWNED")
    scripts[NEW_NAME] = {"$path": NEW_FILE}
    source_file = target / NEW_FILE
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_bytes(NEW_SOURCE.read_bytes())
    project_file.write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    chosen = project_scan(target, PROJECT)
    demand(len(chosen) == 70 and set(chosen) == set(original_sources) | {NEW_ROUTE},
           "CANDIDATE_ROUTES_NOT_69_PLUS_1")
    for route, item in original_sources.items():
        demand(chosen[route] == item, "CHANGED_OFFICIAL_SOURCE_" + route)
    demand(chosen[NEW_ROUTE]["class"] == "LocalScript"
           and chosen[NEW_ROUTE]["sha256"] == digest(NEW_SOURCE.read_bytes()),
           "NEW_CLIENT_SOURCE_CLASS_SHA")
    report = {
        "schema": "GQ470_DUNE_GRASS_REAL69_TO_70_A_ONLY_V1",
        "feature_id": FEATURE, "formal_base": BASE,
        "formal_branch": FORMAL, "source_profile": "PRIVATE_COMPANION",
        "original_selected_exact": 69, "candidate_selected_exact": 70,
        "added_route": NEW_ROUTE, "added_source_sha256": chosen[NEW_ROUTE]["sha256"],
        "added_source_class": "LocalScript",
        "official_place_bytes": REAL69_BYTES, "official_place_sha256": REAL69_SHA,
        "touch_parts_max": 12, "desktop_parts_max": 18,
        "decision": "DEFER_P0_FIRST_ART_NO_GO",
        "formal_integrated": False, "owner_accepted": False,
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android15": "NOT_TESTED", "fun": "NOT_TESTED",
        "art_screenshots": "0/32", "art_gate": "ART_NO_GO"
    }
    (target / OUT_RECEIPT).write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                                     encoding="utf-8")
    print("GQ470_DUNE_GRASS_EXACT_69_PLUS_1_SOURCE_COMPOSE_NOT_RC", report)

def place_scripts(place: Path) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    for item in ET.parse(place).getroot().iter("Item"):
        klass = item.attrib.get("class")
        if klass not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        demand(props is not None, "PLACE_MISSING_PROPERTIES")
        name = next((node.text for node in props if node.attrib.get("name") == "Name"), None)
        source = next((node for node in props if node.attrib.get("name") == "Source"), None)
        demand(isinstance(name, str) and name not in found
               and source is not None, "PLACE_DUPLICATE_OR_MISSING_SOURCE")
        found[name] = (klass, digest((source.text or "").encode("utf-8")))
    return found

def verify(candidate: Path, actual_place: Path) -> None:
    # Verify source identity of ORIGINAL Place copied into candidate.
    original_sources, _ = original_lock(candidate, allow_new=True)
    selected = project_scan(candidate, PROJECT)
    demand(len(selected) == 70 and set(selected) == set(original_sources) | {NEW_ROUTE},
           "CANDIDATE_ROUTES_INCORRECT")
    for route, item in original_sources.items():
        demand(selected[route] == item, "CANDIDATE_ORIGINAL_MUTATED_" + route)
    demand(selected[NEW_ROUTE]["class"] == "LocalScript"
           and selected[NEW_ROUTE]["sha256"] == digest(NEW_SOURCE.read_bytes()),
           "NEW_SOURCE_MUTATED")
    actual = place_scripts(actual_place)
    demand(len(actual) == 70, "PLACE_NOT_70_SCRIPTS")
    for route, info in selected.items():
        name = route.rsplit("/", 1)[-1]
        demand(actual.get(name) == (info["class"], info["sha256"]),
               "PLACE_SOURCE_CLASS_MISMATCH_" + name)
    b_path = candidate / B_PACKET
    demand(not b_path.exists(), "B_PACKET_PATH_ALREADY_EXISTS")
    selected_file = b_path / "selected_sources" / NEW_FILE.removeprefix("sources/")
    selected_file.parent.mkdir(parents=True, exist_ok=True)
    selected_file.write_bytes(NEW_SOURCE.read_bytes())
    b_meta = {
        "schema": "GQ470_DUNE_GRASS_B220_SOURCE_SELECT_V1",
        "feature_id": FEATURE, "formal_base": BASE, "formal_branch": FORMAL,
        "source_profile": "PRIVATE_COMPANION_REAL69_TO_70_A_ONLY",
        "new_source_route": NEW_ROUTE, "new_source_path":
            str(selected_file.relative_to(b_path)).replace("\\", "/"),
        "new_source_sha256": digest(NEW_SOURCE.read_bytes()),
        "new_source_bytes": len(NEW_SOURCE.read_bytes()),
        "new_source_class": "LocalScript",
        "official_69_exact": True, "candidate_sources": 70,
        "candidate_place_bytes": actual_place.stat().st_size,
        "candidate_place_sha256": digest(actual_place.read_bytes()),
        "formal_integrated": False, "owner_accepted": False,
        "b_admission": "DEFER_P0_910_FIRST_ART_NOT_TESTED",
        "needs_fresh_head_nonforce_expected_sha": True
    }
    (b_path / B_MANIFEST).write_text(json.dumps(b_meta, indent=2)+"\n",
                                     encoding="utf-8")
    print("GQ470_DUNE_GRASS_A_PRIVATE_PLACE_REAL70_VERIFIED_B_PACKET_NOT_FORMAL", b_meta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--built", type=Path)
    args = parser.parse_args()
    if args.verify is not None:
        demand(args.built is not None and args.verify.is_dir(),
               "VERIFY_REQUIRES_CANDIDATE_AND_BUILT")
        verify(args.verify, args.built)
    else:
        demand(args.original is not None and args.out is not None,
               "COMPOSE_REQUIRES_OFFICIAL_AND_OUT")
        compose(args.original, args.out)
