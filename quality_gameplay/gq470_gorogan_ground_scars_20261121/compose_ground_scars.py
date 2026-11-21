#!/usr/bin/env python3
"""REAL69 exact-source -> private REAL70 Gorogan ground art A-only candidate.

Only #220 authenticated B writer may adopt the one NEW selected LocalScript.
No official RC, main, Roblox publishing, game authority or old69 modifications.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

FORMAL = "rc/p0d-s1-kids-rc01"
BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ORIGINAL_PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
ORIGINAL_PLACE_BYTES = 798390
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
ORIGINAL_PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
BUILT_PLACE = "EGGRUMBLE_GOROGAN_SCARS_A_CANDIDATE.rbxlx"
FEATURE = "GQ470_FB015_GOROGAN_GROUND_SCARS_REAL69_20261121"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_GoroganGroundScars"
SOURCE = THIS / "EGGRUMBLE_GoroganGroundScars.client.luau"
TARGET = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_GoroganGroundScars.client.luau"
PACKET = "B220_GOROGAN_SCARS_ONE_NEW_SCRIPT_A_ONLY"
PACKET_SOURCE = "selected_sources/" + TARGET.removeprefix("sources/")
PACKET_MANIFEST = "SOURCE_SELECT_MANIFEST.json"


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_GOROGAN_ART_" + why)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_original(root: Path) -> tuple[dict, dict]:
    raw = (root / ORIGINAL_PLACE).read_bytes()
    require(len(raw) == ORIGINAL_PLACE_BYTES and sha(raw) == ORIGINAL_PLACE_SHA,
            "ORIGINAL_PLACE_SHA_SIZE")
    receipt = json.loads((root / RECEIPT).read_text(encoding="utf-8"))
    require(receipt.get("official_branch") == FORMAL and
            receipt.get("build_head") == BASE and
            receipt.get("canonical_build") is True and
            receipt.get("selected_source_count") == 69, "ORIGINAL_RECEIPT")
    before = project_scan(root, PROJECT)
    require(len(before) == 69 and ROUTE not in before and
            set(before) == set(receipt.get("source_hashes", {})) ==
            set(receipt.get("source_classes", {})), "ORIGINAL_ROUTES")
    for route, node in before.items():
        require(node["sha256"] == receipt["source_hashes"][route] and
                node["class"] == receipt["source_classes"][route],
                "ORIGINAL_SOURCE_LOCK_" + route)
    return receipt, before


def source_test() -> None:
    sys.path.insert(0, str(THIS))
    from test_ground_scars_source import verify
    verify(SOURCE.read_text(encoding="utf-8"))


def compose(original: Path, output: Path) -> dict:
    original, output = original.resolve(), output.resolve()
    require(original != output and not output.exists() and original.is_dir(),
            "SAFE_NEW_OUTPUT")
    _, before = verify_original(original)
    source_test()
    shutil.copytree(original, output)
    project = json.loads((output / PROJECT).read_text(encoding="utf-8"))
    scripts = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    require(isinstance(scripts, dict) and "$path" not in scripts and
            ROUTE.rsplit("/", 1)[-1] not in scripts, "PROJECT_CLASS_COLLISION")
    scripts[ROUTE.rsplit("/", 1)[-1]] = {"$path": TARGET}
    target = output / TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(SOURCE.read_bytes())
    (output / PROJECT).write_text(
        json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after = project_scan(output, PROJECT)
    require(len(after) == 70 and set(after) == set(before) | {ROUTE},
            "CANDIDATE_70_AND_69_NONLOSS")
    for route, info in before.items():
        require(after[route] == info, "MUTATED_OLD_69_" + route)
    require(after[ROUTE]["class"] == "LocalScript" and
            after[ROUTE]["sha256"] == sha(SOURCE.read_bytes()),
            "NEW_SCRIPT_SOURCE_CLASS")

    report = {
        "schema": "GQ470_GOROGAN_GROUND_SCARS_SOURCE_A_V1",
        "feature_id": FEATURE, "formal_branch": FORMAL,
        "formal_base_sha": BASE, "formal_integrated": False,
        "source_profile": "PRIVATE_COMPANION_REAL69_TO_70_A_ONLY",
        "original_sources_preserved": 69, "candidate_selected_sources": 70,
        "new_client_route": ROUTE, "new_script_class": "LocalScript",
        "new_source_sha256": sha(SOURCE.read_bytes()),
        "max_parts_touch": 4, "max_parts_desktop": 6,
        "max_bosses": 1, "scan_interval_seconds": .40,
        "collision_or_query_authority": False, "gameplay_changed": False,
        "original_place_bytes": ORIGINAL_PLACE_BYTES,
        "original_place_sha256": ORIGINAL_PLACE_SHA,
        "studio_1_client": "NOT_TESTED", "studio_2_client": "NOT_TESTED",
        "pc_android_old_new_screenshots": "0/32",
        "android_15min": "NOT_TESTED", "kid_fun": "NOT_TESTED",
        "owner_accepted": False, "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
        "b_admission": "DEFER_P0_910_AND_SCOPE_REVIEW",
    }
    (output / "GQ470_GOROGAN_SOURCE_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def place_script_map(place: Path) -> dict:
    root = ET.parse(place).getroot()
    result = {}
    for item in root.iter("Item"):
        cls = item.attrib.get("class")
        if cls not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        require(props is not None, "PLACE_SCRIPT_PROPERTIES")
        name = next((p.text for p in props if p.attrib.get("name") == "Name"), None)
        source = next((p for p in props if p.attrib.get("name") == "Source"), None)
        require(bool(name) and source is not None and name not in result,
                "DUPLICATE_OR_BAD_PLACE_SOURCE")
        result[name] = (cls, sha((source.text or "").encode("utf-8")))
    return result


def assert_place_matches(candidate: Path, place: Path, count: int) -> None:
    scanned = project_scan(candidate, PROJECT)
    scripts = place_script_map(place)
    require(len(scanned) == len(scripts) == count, "PLACE_COUNT")
    for route, info in scanned.items():
        name = route.rsplit("/", 1)[-1]
        require(scripts.get(name) == (info["class"], info["sha256"]),
                "PLACE_SELECTED_SOURCE_" + route)


def verify_manifest(m: dict, built_raw: bytes, source_raw: bytes) -> None:
    require(m.get("schema") == "GQ470_GOROGAN_B220_ONE_SOURCE_V1" and
            m.get("feature_id") == FEATURE and m.get("formal_branch") == FORMAL
            and m.get("formal_base_sha") == BASE and
            m.get("formal_integrated") is False and
            m.get("new_script_route") == ROUTE and
            m.get("new_script_class") == "LocalScript" and
            m.get("new_source_path") == PACKET_SOURCE and
            m.get("new_source_sha256") == sha(source_raw) and
            m.get("new_source_bytes") == len(source_raw) and
            m.get("candidate_place_sha256") == sha(built_raw) and
            m.get("candidate_place_bytes") == len(built_raw) and
            m.get("original_place_sha256") == ORIGINAL_PLACE_SHA and
            m.get("original_place_bytes") == ORIGINAL_PLACE_BYTES and
            m.get("original_69_byte_exact") is True and
            m.get("candidate_source_count") == 70 and
            m.get("b_admission") == "DEFER_P0_910_AND_SCOPE_REVIEW" and
            m.get("art_gate") == "ART_NO_GO" and
            m.get("owner_accepted") is False and
            m.get("needs_fresh_b220_nonforce_cas") is True,
            "B_MANIFEST_MUTATED_OR_FALSE_PASS")


def packet(candidate: Path) -> dict:
    candidate = candidate.resolve()
    verify_original(candidate)
    scanned = project_scan(candidate, PROJECT)
    require(len(scanned) == 70 and ROUTE in scanned, "CANDIDATE_ROUTE")
    assert_place_matches(candidate, candidate / BUILT_PLACE, 70)
    built = (candidate / BUILT_PLACE).read_bytes()
    raw = (candidate / TARGET).read_bytes()
    require(raw == SOURCE.read_bytes(), "TARGET_SOURCE_DRIFT")
    require(sha(built) != ORIGINAL_PLACE_SHA and
            len(built) > ORIGINAL_PLACE_BYTES, "BUILT_A_PLACE_NOT_ORIGINAL")
    target = candidate / PACKET
    require(not target.exists(), "B_PACKET_EXISTS")
    target_file = target / PACKET_SOURCE
    target_file.parent.mkdir(parents=True, exist_ok=False)
    target_file.write_bytes(raw)
    m = {
        "schema": "GQ470_GOROGAN_B220_ONE_SOURCE_V1",
        "feature_id": FEATURE, "formal_branch": FORMAL,
        "formal_base_sha": BASE, "formal_integrated": False,
        "new_script_route": ROUTE, "new_script_class": "LocalScript",
        "new_source_path": PACKET_SOURCE,
        "new_source_sha256": sha(raw), "new_source_bytes": len(raw),
        "candidate_place_sha256": sha(built), "candidate_place_bytes": len(built),
        "original_place_sha256": ORIGINAL_PLACE_SHA,
        "original_place_bytes": ORIGINAL_PLACE_BYTES,
        "original_69_byte_exact": True, "candidate_source_count": 70,
        "b_admission": "DEFER_P0_910_AND_SCOPE_REVIEW",
        "art_gate": "ART_NO_GO", "owner_accepted": False,
        "needs_fresh_b220_nonforce_cas": True,
    }
    verify_manifest(m, built, raw)
    (target / PACKET_MANIFEST).write_text(
        json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return m


def verify_packet(candidate: Path) -> int:
    candidate = candidate.resolve()
    target = candidate / PACKET
    m = json.loads((target / PACKET_MANIFEST).read_text(encoding="utf-8"))
    raw = (target / PACKET_SOURCE).read_bytes()
    built = (candidate / BUILT_PLACE).read_bytes()
    verify_manifest(m, built, raw)
    require(raw == SOURCE.read_bytes() == (candidate / TARGET).read_bytes(),
            "B_SOURCE_BYTES")
    present = {p.relative_to(target).as_posix()
               for p in target.rglob("*") if p.is_file()}
    require(present == {PACKET_MANIFEST, PACKET_SOURCE},
            "B_NO_EXTRA_FILES")
    assert_place_matches(candidate, candidate / BUILT_PLACE, 70)
    return 1


def mutation_tests(candidate: Path) -> int:
    verify_packet(candidate)
    m = json.loads((candidate / PACKET / PACKET_MANIFEST).read_text())
    built = (candidate / BUILT_PLACE).read_bytes()
    raw = SOURCE.read_bytes()
    changes = [
        ("new_script_route", "ServerScriptService/EGGRUMBLE_Game"),
        ("new_script_class", "Script"),
        ("formal_base_sha", "0" * 40),
        ("formal_integrated", True),
        ("new_source_sha256", "0" * 64),
        ("new_source_bytes", len(raw) - 1),
        ("candidate_place_sha256", "0" * 64),
        ("candidate_place_bytes", len(built) - 1),
        ("original_place_sha256", "0" * 64),
        ("original_69_byte_exact", False),
        ("b_admission", "ADOPT"),
        ("art_gate", "ART_GO"),
        ("owner_accepted", True),
        ("needs_fresh_b220_nonforce_cas", False),
    ]
    for name, fake in changes:
        mutated = copy.deepcopy(m)
        mutated[name] = fake
        try:
            verify_manifest(mutated, built, raw)
        except ValueError:
            continue
        raise AssertionError("RED_ACCEPTED_B_PACKET_MUTATION_" + name)
    print("GQ470_GOROGAN_B220_PACKET_14_MUTATIONS_PASS_NOT_FORMAL")
    return len(changes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--verify-packet", type=Path)
    parser.add_argument("--mutations", type=Path)
    args = parser.parse_args()
    if args.packet:
        print(json.dumps(packet(args.packet), ensure_ascii=False, indent=2))
    elif args.verify_packet:
        print("GQ470_GOROGAN_B220_PACKET_PASS", verify_packet(args.verify_packet))
    elif args.mutations:
        mutation_tests(args.mutations)
    else:
        require(args.original is not None and args.output is not None,
                "MISSING_CLI_PARAMETERS")
        print(json.dumps(compose(args.original, args.output), ensure_ascii=False, indent=2))
