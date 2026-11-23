#!/usr/bin/env python3
"""Source-exact A-only REAL69 -> REAL70 lobby edge art handoff, never formal RC.

All 69 existing selected Luau files and original Place/receipt must remain
byte-exact. Candidate selection adds ONLY a client cosmetic LocalScript.
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
OFF_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
OFF_BYTES = 798390
PROJECT = "EGGRUMBLE_REAL69.project.json"
PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LobbyEdgeMasonry"
REL = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LobbyEdgeMasonry.client.luau"
FEATURE = "GQ470_FB015_LOBBY_EDGE_MASONRY_20261121"
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_LobbyEdgeMasonry.client.luau"
sys.path.insert(0, str(ROOT.parent / "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(ok: bool, detail: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_LOBBY_EDGE_" + detail)


def baseline(original: Path) -> tuple[dict, dict]:
    need(original.is_dir(), "ORIGINAL_DIR")
    place = original / PLACE
    need(place.is_file() and place.stat().st_size == OFF_BYTES
         and digest(place.read_bytes()) == OFF_SHA, "FORMAL_PLACE_BYTE_LOCK")
    receipt = json.loads((original / RECEIPT).read_text())
    need(receipt.get("build_head") == BASE
         and receipt.get("canonical_build") is True
         and receipt.get("official_branch") == "rc/p0d-s1-kids-rc01"
         and receipt.get("selected_source_count") == 69, "RECEIPT_AUTHORITY")
    selected = project_scan(original, PROJECT)
    need(len(selected) == 69 and ROUTE not in selected
         and set(selected) == set(receipt.get("source_hashes", {}))
         == set(receipt.get("source_classes", {})), "ORIGINAL_ROUTE_SET")
    need(all(info["sha256"] == receipt["source_hashes"][r]
             and info["class"] == receipt["source_classes"][r]
             for r, info in selected.items()), "ORIGINAL_SOURCE_SHA_CLASS")
    return receipt, selected


def compose(original: Path, candidate: Path) -> dict:
    need(not candidate.exists() and original.resolve() != candidate.resolve(),
         "NO_OVERWRITE_ORIGINAL")
    receipt, orig = baseline(original)
    code = SOURCE.read_bytes()
    need(code.count(FEATURE.encode()) == 1, "FEATURE_MARKER")
    need(b'CanCollide = false' in code and b'CanQuery = false' in code
         and b'EGGRUMBLE_ReducedEffects' in code
         and b'GQ646_LOBBY_SAFE_GROUND' in code, "SAFE_CLIENT_VISUAL_FENCE")
    combat = orig["StarterPlayer/StarterPlayerScripts/EGGRUMBLE_CombatFeel"]
    need(b'EGGRUMBLE_ReducedEffects' in
         (original / combat["path"]).read_bytes(), "EXISTING_EFFECTS_SETTING")
    shutil.copytree(original, candidate)
    project = json.loads((candidate / PROJECT).read_text())
    player = project["tree"].get("StarterPlayer", {})
    scripts = player.get("StarterPlayerScripts", {})
    need(isinstance(scripts, dict) and "$path" not in scripts
         and ROUTE.rsplit("/", 1)[-1] not in scripts, "EXACT_NEW_CLIENT_ROUTE")
    scripts[ROUTE.rsplit("/", 1)[-1]] = {"$path": REL}
    dest = candidate / REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(code)
    (candidate / PROJECT).write_text(json.dumps(
        project, indent=2, ensure_ascii=False) + "\n")
    on = project_scan(candidate, PROJECT)
    need(len(on) == 70 and set(on) == set(orig) | {ROUTE}
         and all(on[r] == original_data for r, original_data in orig.items())
         and on[ROUTE]["class"] == "LocalScript"
         and on[ROUTE]["sha256"] == digest(code), "ORIGINAL69_EXACT_NEW1")
    # Copy only candidate-specific truth; do not alter canonical receipt.
    note = {
        "feature_id": FEATURE, "stage": "A_SOURCE_ONLY_NOT_FORMAL",
        "formal_branch": "rc/p0d-s1-kids-rc01", "formal_base": BASE,
        "profile": "REAL70_PRIVATE_COMPANION_A_ONLY",
        "old_scripts": 69, "new_scripts": 1, "selected_scripts": 70,
        "added_route": ROUTE, "added_class": "LocalScript",
        "new_source_sha256": digest(code), "new_source_bytes": len(code),
        "original_place_bytes": OFF_BYTES, "original_place_sha256": OFF_SHA,
        "max_extra_parts_touch": 8, "max_extra_parts_desktop": 8,
        "gameplay_authorities_modified": 0, "official_rc_adopted": False,
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android15": "NOT_TESTED", "art_pc": "NOT_TESTED",
        "art_android": "NOT_TESTED", "kid_fun": "NOT_TESTED",
        "screenshots": "0/32", "owner_accepted": False,
        "art_gate": "ART_NO_GO", "product_gate": "PRODUCT_NO_GO",
    }
    (candidate / "GQ470_LOBBY_EDGE_A_SOURCE_RECEIPT.json").write_text(
        json.dumps(note, ensure_ascii=False, indent=2) + "\n")
    return note


def built_source_map(place: Path) -> dict[str, tuple[str, str]]:
    scripts: dict[str, tuple[str, str]] = {}
    for item in ET.parse(place).getroot().iter("Item"):
        cls = item.attrib.get("class")
        if cls not in {"Script", "LocalScript", "ModuleScript"}:
            continue
        properties = item.find("Properties")
        need(properties is not None, "BUILT_XML_PROPERTIES")
        name = next((p.text for p in properties
                     if p.attrib.get("name") == "Name"), None)
        source = next((p.text or "" for p in properties
                       if p.attrib.get("name") == "Source"), None)
        need(isinstance(name, str) and source is not None
             and name not in scripts, "BUILT_DUPLICATE_OR_NO_SOURCE")
        scripts[name] = (cls, digest(source.encode("utf-8")))
    return scripts


def verify(original: Path, candidate: Path, built: Path) -> dict:
    receipt, old = baseline(original)
    note = json.loads((candidate / "GQ470_LOBBY_EDGE_A_SOURCE_RECEIPT.json").read_text())
    current = project_scan(candidate, PROJECT)
    code = SOURCE.read_bytes()
    need(note.get("feature_id") == FEATURE
         and note.get("stage") == "A_SOURCE_ONLY_NOT_FORMAL"
         and note.get("formal_base") == BASE
         and note.get("old_scripts") == 69
         and note.get("new_scripts") == 1
         and note.get("selected_scripts") == 70
         and note.get("official_rc_adopted") is False
         and note.get("owner_accepted") is False
         and note.get("screenshots") == "0/32"
         and note.get("art_gate") == "ART_NO_GO"
         and note.get("studio_solo") == "NOT_TESTED",
         "NO_FALSE_FORMAL_OR_ART_CLAIMS")
    need(set(current) == set(old) | {ROUTE} and len(current) == 70
         and all(current[k] == v for k, v in old.items())
         and current[ROUTE]["class"] == "LocalScript"
         and current[ROUTE]["sha256"] == digest(code)
         and (candidate / REL).read_bytes() == code,
         "SOURCE_CLASS_ROUTE_AND_69_NONLOSS")
    need((candidate / RECEIPT).read_bytes() == (original / RECEIPT).read_bytes()
         and (candidate / PLACE).read_bytes() == (original / PLACE).read_bytes(),
         "ORIGINAL_PLACE_RECEIPT_PRESERVED")
    need(built.is_file() and built.stat().st_size > OFF_BYTES
         and digest(built.read_bytes()) != OFF_SHA, "REAL_BUILT_CANDIDATE")
    actual = built_source_map(built)
    need(len(actual) == 70
         and all(actual.get(route.rsplit("/", 1)[-1])
                 == (info["class"], info["sha256"]) for route, info in current.items()),
         "BUILT_PLACE_ALL70_REAL_SOURCE_CLASS")
    packet = candidate / "B220_LOBBY_EDGE_ONE_NEW_CLIENT_SOURCE_NOT_FORMAL"
    need(not packet.exists(), "PACKET_OVERWRITE")
    path = packet / "selected_sources" / REL.removeprefix("sources/")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(code)
    manifest = {
        "feature_id": FEATURE, "source_only": True,
        "formal_base_sha": BASE, "formal_branch": "rc/p0d-s1-kids-rc01",
        "new_script_route": ROUTE, "new_script_class": "LocalScript",
        "source_sha256": digest(code), "source_bytes": len(code),
        "selected_source_path": "selected_sources/" + REL.removeprefix("sources/"),
        "old_script_count": 69, "new_script_count": 1,
        "candidate_place_bytes": built.stat().st_size,
        "candidate_place_sha256": digest(built.read_bytes()),
        "official_rc_adopted": False, "art_gate": "ART_NO_GO",
        "screenshots": "0/32", "owner_accepted": False,
        "b_admission": "DEFER_P0_PLAYER_FIRST_AND_ART16",
        "rollback": "remove only selected new LocalScript; original69 exact",
    }
    (packet / "SOURCE_SELECT_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    need(path.read_bytes() == code and
         manifest["selected_source_path"].startswith("selected_sources/")
         and manifest["source_sha256"] == current[ROUTE]["sha256"],
         "B_SOURCE_PACKET_BYTE_LOCK")
    return manifest


def self_test() -> None:
    # Static negative checks are intentionally not mislabeled engine tests.
    test = {"stage": "A_SOURCE_ONLY_NOT_FORMAL", "official_rc_adopted": False,
            "art_gate": "ART_NO_GO", "screenshots": "0/32"}
    need(test["stage"] == "A_SOURCE_ONLY_NOT_FORMAL", "TEST_STAGE")
    mutants = [
        {**test, "official_rc_adopted": True},
        {**test, "art_gate": "ART_GO"},
        {**test, "screenshots": "32/32"},
        {**test, "stage": "FORMAL_RC"},
    ]
    for bad in mutants:
        need(not (bad["stage"] == test["stage"]
                  and bad["official_rc_adopted"] is False
                  and bad["art_gate"] == "ART_NO_GO"
                  and bad["screenshots"] == "0/32"), "ACCEPTED_FALSE_PASS")
    assert len(mutants) == 4
    print("GQ470_LOBBY_EDGE_SELFTEST_FALSE_PASS_REJECTED_4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--compose", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--original", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--built", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
    elif args.compose:
        need(args.original is not None and args.candidate is not None, "INPUTS")
        print(json.dumps(compose(args.original, args.candidate), indent=2))
    elif args.verify:
        need(args.original is not None and args.candidate is not None
             and args.built is not None, "INPUTS")
        print(json.dumps(verify(args.original, args.candidate, args.built), indent=2))
    else:
        parser.error("choose --self-test, --compose or --verify")
