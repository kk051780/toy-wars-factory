#!/usr/bin/env python3
"""Independent B220/ART420 receipt replay of GitHub-uploaded A PRIVATE Place.
Reads ZIP-extracted files, not text claims. SOURCE only; never Studio PASS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

ORIGINAL_PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
ORIGINAL_PLACE_BYTES = 798390
FEATURE = "GQ470_FB015_PLAYER_CONTACT_SHADOW_REAL69_20261121"
NEW_NAME = "EGGRUMBLE_PlayerContactShadow"
ORIGINAL_PLACE = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
NEW_PLACE = "GQ470_PLAYER_CONTACT_SHADOW_ON70_NOT_FORMAL.rbxlx"
NEW_SOURCE = "quality_gameplay/gq470_player_contact_shadow_20261121/EGGRUMBLE_PlayerContactShadow.client.luau"
B_DIR = "on70/B220_PLAYER_CONTACT_SHADOW_ONE_NEW_CLIENT_SOURCE_NOT_FORMAL"
B_SOURCE = B_DIR + "/selected_sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_PlayerContactShadow.client.luau"
B_MANIFEST = B_DIR + "/SOURCE_SELECT_MANIFEST.json"
ART = "ART_CHECK_REPORT.json"

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def check(condition: bool, why: str):
    if not condition:
        raise ValueError("RED_GQ470_AVATAR_POSTUPLOAD_" + why)

def scan(place: Path) -> dict[str, tuple[str, str]]:
    root = ET.parse(place).getroot()
    output: dict[str, tuple[str, str]] = {}
    def visit(item, parent):
        p = item.find("Properties")
        if p is None:
            return
        n = p.find('string[@name="Name"]')
        check(n is not None and n.text is not None, "ITEM_NAME_MISSING")
        full = parent + "/" + n.text if parent else n.text
        source = p.find('ProtectedString[@name="Source"]')
        if source is None:
            source = p.find('string[@name="Source"]')
        if source is not None:
            check(full not in output, "DUPLICATE_LUAU_ROUTE")
            output[full] = (item.attrib.get("class",""), source.text or "")
        for child in item.findall("Item"):
            visit(child, full)
    for item in root.findall("Item"):
        visit(item,"")
    return output

def verify(artifact: Path, original: Path, current: Path) -> dict:
    artifact, original, current = artifact.resolve(), original.resolve(), current.resolve()
    check(artifact.is_dir() and original.is_dir(), "ARTIFACT_DIRS")
    off = original / ORIGINAL_PLACE
    on = artifact / NEW_PLACE
    check(off.is_file() and on.is_file(), "ACTUAL_PLACE_MISSING")
    check(off.stat().st_size == ORIGINAL_PLACE_BYTES
          and digest(off.read_bytes()) == ORIGINAL_PLACE_SHA, "IMMUTABLE_ORIGINAL")
    original_scripts = scan(off)
    candidate_scripts = scan(on)
    check(len(original_scripts) == 69 and len(candidate_scripts) == 70, "REAL_SCRIPT_COUNT")
    check(set(original_scripts).issubset(candidate_scripts), "ORIGINAL_ROUTE_LOST")
    for route, body in original_scripts.items():
        check(candidate_scripts[route] == body, "ORIGINAL_CLASS_OR_SOURCE_CHANGED_"+route)
    only_new = set(candidate_scripts) - set(original_scripts)
    check(len(only_new) == 1 and next(iter(only_new)).endswith(
        "/StarterPlayerScripts/" + NEW_NAME), "UNEXPECTED_OR_MISSING_NEW_ROUTE")
    new_route = next(iter(only_new))
    actual_class, actual_src = candidate_scripts[new_route]
    check(actual_class == "LocalScript", "WRONG_NEW_SCRIPT_CLASS")
    source_raw = current.read_bytes()
    selected = artifact / B_SOURCE
    check(selected.read_bytes() == source_raw, "ARTIFACT_NOT_SOURCE_HEAD")
    check(actual_src.strip() == source_raw.decode("utf-8").strip(), "BUILT_PLACE_NEW_SOURCE_DRIFT")
    manifest = json.loads((artifact / B_MANIFEST).read_text(encoding="utf-8"))
    receipt = json.loads((artifact / "on70/GQ470_PLAYER_CONTACT_SHADOW_SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
    report = json.loads((artifact / ART).read_text(encoding="utf-8"))
    check(manifest["feature_id"] == FEATURE and
          manifest["new_script_class"] == "LocalScript" and
          manifest["new_script_route"] == "StarterPlayer/StarterPlayerScripts/" + NEW_NAME and
          manifest["new_source_sha256"] == digest(source_raw) and
          manifest["new_source_bytes"] == len(source_raw) and
          manifest["original_selected_sources_preserved"] == 69 and
          manifest["candidate_selected_sources"] == 70 and
          manifest["candidate_place_sha256"] == digest(on.read_bytes()) and
          manifest["candidate_place_bytes"] == on.stat().st_size and
          manifest["original_place_sha256"] == ORIGINAL_PLACE_SHA and
          manifest["formal_integrated"] is False and
          manifest["owner_accepted"] is False and
          manifest["art_status"] == "ART_NO_GO" and
          manifest["needs_b220_authenticated_fresh_head_nonforce_cas"] is True,
          "B_MANIFEST_MISMATCH_OR_FAKE_RC_APPROVAL")
    check(receipt["candidate_source_count"] == 70 and
          receipt["original_sources_preserved"] == 69 and
          receipt["formal_integrated"] is False and
          receipt["owner_accepted"] is False and
          receipt["added_script_sha256"] == digest(source_raw), "SOURCE_RECEIPT_MISMATCH")
    check(report["comparison_image_count"] == 0 and
          len(report["comparison_images"]) == 32 and
          report["studio_solo"] == "NOT_TESTED" and
          report["studio_2client"] == "NOT_TESTED" and
          report["art_gate"] == "ART_NO_GO" and
          report["product_gate"] == "PRODUCT_NO_GO" and
          report["owner_accepted"] is False, "ART_SCORE_FORGED")
    allowed = {
        NEW_PLACE, B_MANIFEST, B_SOURCE, ART,
        "on70/GQ470_PLAYER_CONTACT_SHADOW_SOURCE_RECEIPT.json",
        "on70/sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_PlayerContactShadow.client.luau"
    }
    actual = {p.relative_to(artifact).as_posix() for p in artifact.rglob("*") if p.is_file()}
    check(actual == allowed, "UNEXPECTED_UPLOAD_FILE_OR_MISSING_EVIDENCE")
    return {
        "stage":"POSTUPLOAD_SOURCE_EXACT_NOT_STUDIO",
        "new_route":new_route,
        "preserved":len(original_scripts),
        "candidate":len(candidate_scripts),
        "private_place_bytes":on.stat().st_size,
        "private_place_sha256":digest(on.read_bytes()),
        "new_source_sha256":digest(source_raw),
        "art_gate":"ART_NO_GO", "official_rc_integrated":False,
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--artifact",type=Path,required=True)
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--current",type=Path,required=True)
    args = p.parse_args()
    result = verify(args.artifact,args.original,args.current)
    print("GQ470_PLAYER_CONTACT_SHADOW_POSTUPLOAD_INDEPENDENT_SOURCE_EXACT_PASS")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
