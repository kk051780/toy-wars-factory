"""An A-only REAL69 -> REAL70 selected-source candidate; no official branch writes.

Requires genuine pinned full source+project+receipt from the #220 official run.
Source identity, project route/class, and expected official Place bytes fail closed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
FORMAL = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
FORMAL_PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
FORMAL_PLACE_BYTES = 798390
NEW_ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_FarSkyFacets"
NEW_PATH = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_FarSkyFacets.client.luau"
THIS = Path(__file__).resolve().parent
SOURCE = THIS / "EGGRUMBLE_FarSkyFacets.client.luau"
LIB = THIS.parent / "gq8_rc85_rc86_real68_nonloss_20261120"
sys.path.insert(0, str(LIB))
from verify_nonloss import project_scan

def require(test: bool, message: str) -> None:
    if not test:
        raise ValueError("RED_GQ470_FARSKY70_" + message)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def compose(original: Path, destination: Path) -> dict:
    original = original.resolve()
    destination = destination.resolve()
    require(original.is_dir() and original != destination, "ORIGINAL_ROOT_OR_DESTINATION")
    official_project = original / PROJECT
    official_receipt = original / RECEIPT
    place = original / "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
    require(official_project.is_file() and official_receipt.is_file() and place.is_file(),
            "AUTHENTIC_OFFICIAL_ORIGINAL_FILES_REQUIRED")
    require(place.stat().st_size == FORMAL_PLACE_BYTES and digest(place.read_bytes()) == FORMAL_PLACE_SHA,
            "OFFICIAL_PLACE_BYTES_OR_SHA")
    receipt = json.loads(official_receipt.read_text(encoding="utf-8"))
    require(receipt.get("build_head") == FORMAL and receipt.get("selected_source_count") == 69,
            "FORMAL_HEAD_OR_COUNT")
    before = project_scan(original, PROJECT)
    require(len(before) == 69 and set(before) == set(receipt["source_hashes"]),
            "OFFICIAL_69_SOURCE_ROUTE_SET")
    require(all(receipt["source_hashes"][k] == v["sha256"] and
                receipt["source_classes"][k] == v["class"] for k,v in before.items()),
            "OFFICIAL_69_SOURCE_LOCK")
    require(NEW_ROUTE not in before and SOURCE.is_file(), "SKY_ROUTE_COLLISION_OR_SOURCE_MISSING")

    require(not destination.exists(), "DESTINATION_EXISTS")
    shutil.copytree(original, destination)
    candidate_project = json.loads((destination / PROJECT).read_text(encoding="utf-8"))
    tree = candidate_project["tree"]
    starter = tree.get("StarterPlayer")
    scripts = starter.get("StarterPlayerScripts") if isinstance(starter,dict) else None
    require(isinstance(scripts,dict) and "$path" not in scripts, "UNSUPPORTED_STARTERPLAYER_TREE")
    require("EGGRUMBLE_FarSkyFacets" not in scripts, "DUPLICATE_SKY_LOCAL_SCRIPT")
    scripts["EGGRUMBLE_FarSkyFacets"] = {"$path": NEW_PATH}
    source_dst = destination / NEW_PATH
    source_dst.parent.mkdir(parents=True, exist_ok=True)
    source_dst.write_bytes(SOURCE.read_bytes())
    (destination / PROJECT).write_text(
        json.dumps(candidate_project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    after = project_scan(destination, PROJECT)
    require(len(after) == 70 and set(after) == set(before) | {NEW_ROUTE},
            "70_SOURCE_ROUTE_EXACT")
    require(all(after[k]["sha256"] == v["sha256"] and
                after[k]["class"] == v["class"] and
                after[k]["path"] == v["path"] for k,v in before.items()),
            "ALL_ORIGINAL_69_SCRIPTS_UNCHANGED")
    require(after[NEW_ROUTE]["class"] == "LocalScript" and
            after[NEW_ROUTE]["sha256"] == digest(SOURCE.read_bytes()),
            "NEW_LOCAL_SKY_CLASS_OR_SOURCE")
    require(not any(k.startswith("ServerScriptService/TrapRaidersS1/") for k in after),
            "OLD_S1_DUPLICATE_AUTHORITY")

    report = {
        "stage": "A_REAL70_SOURCE_CANDIDATE_NOT_FORMAL",
        "feature_id": "GQ470_FB015_FAR_SKY_MATTE_CLOUD_BANKS_20261121",
        "formal_rc_head": FORMAL,
        "original_source_count": len(before),
        "candidate_source_count": len(after),
        "original_69_routes_sha_and_class_identical": True,
        "new_route": NEW_ROUTE,
        "new_source_sha256": after[NEW_ROUTE]["sha256"],
        "original_place_bytes": FORMAL_PLACE_BYTES,
        "original_place_sha256": FORMAL_PLACE_SHA,
        "original_selected_source_count": receipt["selected_source_count"],
        "added_runtime_authorities": 0,
        "formal_rc_integrated": False,
        "studio": "NOT_TESTED",
        "android15": "NOT_TESTED",
        "kid_fun": "NOT_TESTED",
        "owner_accepted": False,
        "art_status": "ART_NO_GO",
    }
    (destination / "REAL70_ART_CANDIDATE_RECEIPT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--official",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(compose(args.official,args.out),indent=2,ensure_ascii=False))
