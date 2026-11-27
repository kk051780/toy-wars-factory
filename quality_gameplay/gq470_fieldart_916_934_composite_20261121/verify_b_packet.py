#!/usr/bin/env python3
"""Source-select provenance + entire Studio XML safety for B220 handoff.

NOT an engine, Android, human beauty or OWNER acceptance. Genuine REAL69 A PREP.
The 69-source source compiler is elsewhere in the workflow. This verifier also
refuses cosmetic/physical XML drift outside precisely one script's Source node.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROUTE = "ServerScriptService/EGGRUMBLE_FlagshipFieldArt"
SCRIPT_NAME = "EGGRUMBLE_FlagshipFieldArt"
ORIGINAL_SOURCE = "d77fdaf390506f87dfea3064611898320288690f4ef14b97f4e8416eaef40395"
COMPOSED_SOURCE = "fe27abeb71ffbba025ec4625532c5d711b874f9cb91848ac64369229e2d337ce"
ORIGINAL_PLACE = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
COMPOSED_PLACE = "541a4e3e3135281b6fff69944b196c5551f0d1bf639d3ddfeff37a82d68ef9d5"
PLACE_BYTES = 804063
ORIGINAL_BYTES = 798390
FEATURE = "GQ470_FB015_FIELDART_916_934_COMPOSITE_20261121"
CLASSES = {"Script", "LocalScript", "ModuleScript"}

def need(ok: bool, reason: str):
    if not ok:
        raise ValueError("RED_FIELDART_B220_PACKET_" + reason)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def source_items(root: ET.Element) -> dict[str, tuple[str, ET.Element]]:
    result = {}
    for item in root.iter("Item"):
        cls = item.attrib.get("class")
        if cls not in CLASSES:
            continue
        props = item.find("Properties")
        need(props is not None, "MISSING_SCRIPT_PROPERTIES")
        label = props.find("string[@name='Name']")
        source = props.find("string[@name='Source']")
        need(label is not None and label.text and source is not None,
             "MISSING_SCRIPT_NAME_OR_SOURCE")
        need(label.text not in result, "DUPLICATE_SCRIPT_NAME")
        result[label.text] = (cls, source)
    need(len(result) == 69, "ACTUAL_PLACE_69_SCRIPT_COUNT")
    return result

def compare_real_xml(original: ET.Element, candidate: ET.Element):
    # Check both original and generated Place, then normalize only ONE explicit
    # script Source in candidate before a full-document comparison.
    old = source_items(original)
    new = source_items(candidate)
    need(set(old) == set(new), "SCRIPT_NAME_NONLOSS")
    need(SCRIPT_NAME in old, "ONE_FIELDART_OWNER")
    for name in old:
        a_class, a_source = old[name]
        b_class, b_source = new[name]
        need(a_class == b_class, "SCRIPT_CLASS_NONLOSS_" + name)
        if name == SCRIPT_NAME:
            need(a_class == "Script", "FLAGSHIP_SERVER_SCRIPT_CLASS")
            need(sha((a_source.text or "").encode()) == ORIGINAL_SOURCE,
                 "ORIGINAL_EMBEDDED_FIELDART_SHA")
            need(sha((b_source.text or "").encode()) == COMPOSED_SOURCE,
                 "COMPOSED_EMBEDDED_FIELDART_SHA")
        else:
            need((a_source.text or "") == (b_source.text or ""),
                 "OTHER_68_EMBEDDED_SOURCE_CHANGED_" + name)
    new[SCRIPT_NAME][1].text = old[SCRIPT_NAME][1].text
    # All non-script classes, properties, parent transforms, graphics and object
    # decorations must be identical; Rojo source overlays may not change them.
    need(ET.tostring(candidate, encoding="utf-8") ==
         ET.tostring(original, encoding="utf-8"),
         "OTHER_PLACE_XML_DRIFT")
    return len(old)

def check_manifest(manifest: dict, note: dict, source: bytes):
    need(manifest["source_route"] == ROUTE, "WRONG_B220_ROUTE")
    need(manifest["source_class"] == "Script", "WRONG_B220_SOURCE_CLASS")
    need(manifest["formal_branch"] == "rc/p0d-s1-kids-rc01",
         "WRONG_FORMAL_BRANCH")
    need(manifest["formal_base_sha"] == "e80973c354f14a0d0088577f3cc1a875454f0f8f",
         "WRONG_FORMAL_HEAD")
    need(manifest["source_profile"] == "REAL69_PRIVATE_COMPANION", "WRONG_PROFILE")
    need(manifest["feature_id"] == FEATURE == note["feature_id"], "WRONG_FEATURE")
    need(manifest["original_sha256"] == ORIGINAL_SOURCE, "WRONG_PARENT_SOURCE")
    need(manifest["composed_sha256"] == sha(source) == COMPOSED_SOURCE,
         "FORGED_SELECTED_SOURCE_SHA")
    need(manifest["original_author_commit_shas"] ==
         ["e121c11728de6784a2cfddf11beea08f677ae1ae",
          "89bd47dbff105bbcfe1005fdbaaca7cf737cc33c"],
         "AUTHOR_HEAD_DRIFT")
    need(manifest["officially_integrated"] is False and
         manifest["source_only"] is True, "FAKE_FORMAL_ADOPTION")
    need(manifest["art_gate"] == "ART_NO_GO" and
         manifest["studio_android_fun"] == "NOT_TESTED",
         "FALSE_ART_OR_FUN_ACCEPTANCE")
    need(note["after_source_sha256"] == COMPOSED_SOURCE and
         note["before_source_sha256"] == ORIGINAL_SOURCE,
         "RECEIPT_SOURCE_LOCK")
    need(note["changed_selected_routes"] == 1 and
         note["preserved_selected_routes"] == 68,
         "RECEIPT_ROUTE_NONLOSS")
    need(note["visual_part_cap"] == 320 and
         note["castle_min_essential"] == 10 and
         note["maximum_mat_ridges"] == 12, "ART_PART_BUDGET")
    need(note["art_32_screenshots"] == "0/32" and
         note["owner_accepted"] is False and
         note["art_gate"] == "ART_NO_GO",
         "FAKE_ART_ACCEPTANCE")

def inspect(folder: Path):
    folder = folder.resolve()
    receipt = json.loads((folder/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_text())
    note = receipt["gq470_fieldart_916_934_composite"]
    manifest = json.loads((folder/"B220_FIELDART_ONE_SOURCE_NOT_FORMAL"/"SOURCE_SELECT_MANIFEST.json").read_text())
    source = (folder/"B220_FIELDART_ONE_SOURCE_NOT_FORMAL"/"EGGRUMBLE_FlagshipFieldArt.server.luau").read_bytes()
    check_manifest(manifest, note, source)
    original_file = folder/"OFF69_ORIGINAL"/"EGGRUMBLE_REAL69_PRIVATE.rbxlx"
    candidate_file = folder/"EGGRUMBLE_REAL69_PRIVATE.rbxlx"
    o_bytes, c_bytes = original_file.read_bytes(), candidate_file.read_bytes()
    need(len(o_bytes) == ORIGINAL_BYTES and sha(o_bytes) == ORIGINAL_PLACE,
         "ORIGINAL_PLACE_NOT_BYTE_EXACT")
    need(len(c_bytes) == PLACE_BYTES and sha(c_bytes) == COMPOSED_PLACE,
         "CANDIDATE_PLACE_NOT_PINNED")
    need(receipt["private_place_bytes"] == PLACE_BYTES and
         receipt["private_place_sha256"] == COMPOSED_PLACE,
         "CANDIDATE_RECEIPT_PLACE_DRIFT")
    origin_tree = ET.fromstring(o_bytes)
    candidate_tree = ET.fromstring(c_bytes)
    # compare_real_xml mutates its candidate parameter's Source node, not the
    # saved candidate Place, so parse fresh again for negative fixtures below.
    count = compare_real_xml(origin_tree, candidate_tree)
    need(count == 69, "SOURCE_COUNT")
    print("GQ470_B220_REAL_XML_ONLY_ONE_EMBEDDED_FIELDART_CHANGED_68_EXACT")
    return receipt, manifest, source, o_bytes, c_bytes

def negatives(folder: Path):
    receipt, manifest, source, orig, candidate = inspect(folder)
    note = receipt["gq470_fieldart_916_934_composite"]
    blocked = 0
    def red(fn):
        nonlocal blocked
        try:
            fn()
        except ValueError:
            blocked += 1
        else:
            raise AssertionError("GQ470_MUTATION_SHOULD_FAIL_" + str(blocked))
    forged = copy.deepcopy(manifest)
    forged["source_route"] = "ServerScriptService/AnotherGame"
    red(lambda: check_manifest(forged, note, source))
    forged = copy.deepcopy(manifest)
    forged["source_class"] = "LocalScript"
    red(lambda: check_manifest(forged, note, source))
    forged = copy.deepcopy(manifest)
    forged["composed_sha256"] = "0"*64
    red(lambda: check_manifest(forged, note, source))
    forged = copy.deepcopy(manifest)
    forged["officially_integrated"] = True
    red(lambda: check_manifest(forged, note, source))
    forged = copy.deepcopy(manifest)
    forged["art_gate"] = "ART_GO"
    red(lambda: check_manifest(forged, note, source))
    forged = copy.deepcopy(manifest)
    forged["original_author_commit_shas"][0] = "0"*40
    red(lambda: check_manifest(forged, note, source))
    forged_note = copy.deepcopy(note)
    forged_note["visual_part_cap"] = 999
    red(lambda: check_manifest(manifest, forged_note, source))
    forged_note = copy.deepcopy(note)
    forged_note["art_32_screenshots"] = "32/32"
    red(lambda: check_manifest(manifest, forged_note, source))
    red(lambda: check_manifest(manifest, note, source + b"\n--tamper"))
    # In the REAL built XML, protect entire scripts and other XML properties,
    # not only the source-class count and source hashes in receipt.
    old = ET.fromstring(orig)
    evil = ET.fromstring(candidate)
    scripts = source_items(evil)
    scripts[SCRIPT_NAME][1].text = (scripts[SCRIPT_NAME][1].text or "") + "--modified"
    red(lambda: compare_real_xml(copy.deepcopy(old), evil))
    evil = ET.fromstring(candidate)
    scripts = source_items(evil)
    victim = next(k for k in scripts if k != SCRIPT_NAME)
    scripts[victim][1].text = (scripts[victim][1].text or "") + "--modified"
    red(lambda: compare_real_xml(copy.deepcopy(old), evil))
    evil = ET.fromstring(candidate)
    # A non-script Value or Image changes must also be rejected.
    evil.attrib["version"] = "10000"
    red(lambda: compare_real_xml(copy.deepcopy(old), evil))
    need(blocked == 12, "ALL_12_NEGATIVE_CASES")
    print("GQ470_B220_FIELDART_12_MUTANT_SOURCE_XML_AUTHORITY_AND_FAKE_ART_REJECTED")

if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--base", type=Path, required=True)
    cli.add_argument("--negative-tests", action="store_true")
    args = cli.parse_args()
    if args.negative_tests:
        negatives(args.base)
    else:
        inspect(args.base)
