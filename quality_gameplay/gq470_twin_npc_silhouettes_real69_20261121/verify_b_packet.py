#!/usr/bin/env python3
"""Fail-closed source-select packet gate for B220 sole RC writer.

This tests a candidate packet, NOT a license to write to formal RC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

BASE_SHA = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
OLD_SHA = "c8a78277b74669caebfb7ac6e1dc18f065c537f2da00cf22d8fd7fbca0bf5a00"
NEW_SHA = "2e4b398927873a51203115feda60027c0720b847f3f5f2dd1f5189c1a161a8d6"
PLACE_SHA = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
FEATURE = "GQ470_FB015_TWIN_CREATURE_SILHOUETTES_REAL69_20261121"
ROUTE = "ServerScriptService/EGGRUMBLE_LegacyTwinBiomes"
SELECTED = "selected_sources/ServerScriptService/EGGRUMBLE_LegacyTwinBiomes.server.luau"
BASE_PACKET_FILES = {
    "QA_SOURCE_EXACT.json", "SOURCE_SELECT_MANIFEST.json",
    "REAL69_48FLAG_TRUTH.json", SELECTED,
}

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def require(condition: bool, key: str) -> None:
    if not condition:
        raise ValueError("RED_B220_TWIN_NPC_PACKET_" + key)

def verify(manifest: dict, qa: dict, flags: dict, changed: bytes,
           old: bytes, on: bytes, off: bytes, expected_head: str) -> dict:
    require(len(expected_head)==40 and all(c in "0123456789abcdef" for c in expected_head),
            "EXPECTED_HEAD")
    require(manifest.get("candidate_head") == expected_head, "A_HEAD")
    require(manifest.get("parent_rc_head") == BASE_SHA, "PARENT_HEAD")
    require(manifest.get("feature_id") == FEATURE, "FEATURE")
    require(manifest.get("selected_route") == ROUTE, "ROUTE")
    require(manifest.get("source_class") == "Script", "SCRIPT_CLASS")
    require(manifest.get("selected_source_count") == 69, "SOURCE_COUNT")
    require(manifest.get("unchanged_selected_source_count") == 68, "ONLY_ONE_CHANGED")
    require(manifest.get("old_source_sha256") == OLD_SHA, "OLD_SOURCE_LOCK")
    require(manifest.get("new_source_sha256") == NEW_SHA, "NEW_SOURCE_LOCK")
    require(digest(old) == OLD_SHA and digest(changed) == NEW_SHA, "ACTUAL_SOURCE_BYTES")
    require(manifest.get("rollback") == "ORIGINAL_SOURCE_AND_OFFICIAL_PLACE",
            "ROLLBACK_FLAG")
    require(manifest.get("never_whole_pr_merge") is True, "FULL_PR_MERGE_PROHIBITED")
    require(manifest.get("admission") == "B220_AUTHENTICATED_CAS_REQUIRED",
            "AUTHORIZED_WRITER_ONLY")
    require(manifest.get("off69_original_place_byte_exact") is True and
            off == old_place_from_runtime(), "INVERSE_PLACE_BYTE_EXACT")
    require(digest(off) == PLACE_SHA and len(off) == 798390, "ORIGINAL_PLACE_HASH")
    require(manifest.get("candidate_place_bytes") == len(on) and
            manifest.get("candidate_place_sha256") == digest(on), "CANDIDATE_PLACE_BYTES")
    require(manifest.get("native_69") == "PASS_SOURCE_ONLY" and
            manifest.get("rojo_on_off_69") == "PASS_SOURCE_ONLY" and
            manifest.get("legacy17") == "PASS_SOURCE_ONLY", "SOURCE_CI_TRUTH")
    require(manifest.get("legacy48_inventory_file") == "PRESENT_NOT_SEMANTIC_ENGINE_PROOF",
            "LEGACY48_TRUTH")
    require(all(manifest.get(key) == "NOT_TESTED"
                for key in ("studio", "android", "human_art")), "UNTESTED_TRUTH")
    require(manifest.get("owner_accepted") is False, "OWNER_NOT_ACCEPTED")
    require(qa.get("formal_source_gate") == "EXACT_FORMAL_SOURCE" and
            qa.get("source_sha256") == OLD_SHA and
            qa.get("candidate_sha256") == NEW_SHA and
            qa.get("mutations_rejected") == 9, "QA_REPORT")
    require(qa.get("studio_android_human_art_owner") == "NOT_TESTED",
            "QA_RUNTIME_UNTESTED")
    require(flags.get("source_count") == 69 and
            flags.get("original_legacy_flags") == 48 and
            flags.get("flag_inventory_verified") is True and
            flags.get("all_48_semantic_parity") == "NOT_PROVEN",
            "LEGACY48_ACCOUNTING")
    require(sum(flags["summary"].values()) == 48, "LEGACY48_SUM")
    return {"source_one_of_69": True, "negative_manifest_mutants_rejected": 14,
            "candidate_head": expected_head, "candidate_place_bytes": len(on),
            "original_place_bytes": len(off),
            "formal_rc_write": False, "studio_android_owner": "NOT_TESTED"}

# This sentinel is filled only after reading the immutable exact original
# artifact during the current tool invocation; never hard-code a forged inverse.
_ORIGINAL_PLACE: bytes | None = None
def old_place_from_runtime() -> bytes:
    require(_ORIGINAL_PLACE is not None, "ORIGINAL_PLACE_UNAVAILABLE")
    return _ORIGINAL_PLACE

def adversarial_tests(manifest: dict, qa: dict, flags: dict, changed: bytes,
                      old: bytes, on: bytes, off: bytes, expected_head: str) -> None:
    mutants = [
        ("head", {"candidate_head": BASE_SHA}),
        ("parent", {"parent_rc_head": expected_head}),
        ("path", {"selected_route": "ServerScriptService/OtherOwner"}),
        ("class", {"source_class": "LocalScript"}),
        ("count", {"selected_source_count": 70}),
        ("others", {"unchanged_selected_source_count": 67}),
        ("hash", {"new_source_sha256": OLD_SHA}),
        ("rollback", {"off69_original_place_byte_exact": False}),
        ("merge", {"never_whole_pr_merge": False}),
        ("auth", {"admission": "AUTOMERGE_OK"}),
        ("studio", {"studio": "PASS"}),
        ("mobile", {"android": "PASS"}),
        ("human", {"owner_accepted": True}),
        ("source_only", {"native_69": "ENGINE_PASS"}),
    ]
    for key, delta in mutants:
        poisoned=dict(manifest);poisoned.update(delta)
        try:
            verify(poisoned,qa,flags,changed,old,on,off,expected_head)
        except ValueError:
            continue
        raise AssertionError("MUTANT_NOT_REJECTED_" + key)

def verify_optional_art_report(report: dict, manifest: dict, on: bytes) -> None:
    require(report.get("schema")=="P0D_GQ470_REAL69_TWIN_NPC_ART_SOURCE_REPORT_V1",
            "ART_SCHEMA")
    require(report.get("candidate_head")==manifest["candidate_head"],"ART_HEAD")
    require(report.get("actual_candidate_place_bytes")==len(on) and
            report.get("actual_candidate_place_sha256")==digest(on),
            "ART_ACTUAL_PLACE_IDENTITY")
    require(report.get("source_gate",{}).get("status")=="PASS_SOURCE_ONLY" and
            report.get("source_gate",{}).get("source_count_changed")==1 and
            report.get("source_gate",{}).get("unchanged_other_sources")==68,
            "ART_SOURCE_ONLY")
    verify_optional_art_report_core(report,manifest,on)
    for bad in ("screenshots_received","owner_accepted","art_gate"):
        poisoned=json.loads(json.dumps(report))
        if bad=="screenshots_received":
            poisoned["visual_evidence_gate"]["screenshots_received"]=32
        elif bad=="owner_accepted":
            poisoned["owner_accepted"]=True
        else:
            poisoned["art_gate"]="ART_GO"
        try:
            verify_optional_art_report_core(poisoned,manifest,on)
        except ValueError:
            continue
        raise AssertionError("ART_REPORT_POISON_ACCEPTED_"+bad)

def verify_optional_art_report_core(report: dict, manifest: dict, on: bytes) -> None:
    require(report.get("candidate_head")==manifest["candidate_head"],"ART_HEAD")
    require(report.get("actual_candidate_place_sha256")==digest(on),"ART_PLACE")
    require(report.get("visual_evidence_gate",{}).get("screenshots_required")==32 and
            report.get("visual_evidence_gate",{}).get("screenshots_received")==0,
            "ART_MISSING_PHOTOS")
    require(report.get("owner_accepted") is False,"ART_NOT_OWNER")
    require(report.get("human_art",{}).get("status")=="NOT_TESTED" and
            report.get("mobile_runtime",{}).get("status")=="NOT_TESTED" and
            report.get("kid_first3min_fun",{}).get("status")=="NOT_TESTED",
            "ART_HUMAN_MOBILE")
    require(all(report.get(k)==v for k,v in (
                ("art_gate","ART_NO_GO"),("mobile_gate","MOBILE_NO_GO"),
                ("fun_gate","FUN_NO_GO"),("product_gate","PRODUCT_NO_GO"))),
            "ART_NOT_GO")

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--packet",type=Path,required=True)
    p.add_argument("--on-place",type=Path,required=True)
    p.add_argument("--off-place",type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    args=p.parse_args()
    allfiles={path.relative_to(args.packet).as_posix()
              for path in args.packet.rglob("*") if path.is_file()}
    require(allfiles==BASE_PACKET_FILES or allfiles==BASE_PACKET_FILES|{"ART_CHECK_REPORT.json"},
            "UNEXPECTED_PACKET_FILES")
    def load(name):
        return json.loads((args.packet/name).read_text(encoding="utf-8"))
    manifest=load("SOURCE_SELECT_MANIFEST.json")
    qa=load("QA_SOURCE_EXACT.json")
    flags=load("REAL69_48FLAG_TRUTH.json")
    changed=(args.packet/SELECTED).read_bytes()
    old=(args.root/"TWIN_NPC_OFF69_ORIGINAL_SOURCE.luau").read_bytes()
    on=args.on_place.read_bytes();off=args.off_place.read_bytes()
    global _ORIGINAL_PLACE
    _ORIGINAL_PLACE=(args.root/"EGGRUMBLE_REAL69_PRIVATE.rbxlx").read_bytes()
    r=verify(manifest,qa,flags,changed,old,on,off,args.expected_head)
    adversarial_tests(manifest,qa,flags,changed,old,on,off,args.expected_head)
    if "ART_CHECK_REPORT.json" in allfiles:
        verify_optional_art_report(load("ART_CHECK_REPORT.json"), manifest, on)
        r["art_report_three_negative_mutations_rejected"]=3
    print(json.dumps(r,sort_keys=True))

if __name__=="__main__":
    main()
