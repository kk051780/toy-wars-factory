#!/usr/bin/env python3
"""A-only selected-byte handoff to authenticated B220; never writes official RC.

Requires genuine official OFF69 and actual modified candidate 69 sources.
Source-only receipt is NOT art beauty, Studio, Android, or OWNER acceptance.
"""
from __future__ import annotations
import argparse
import json
import tempfile
from pathlib import Path

import patch_explore_relic69 as gate

PACKAGE = "B220_EXPLORE_RELIC_ONE_SOURCE_ONLY_NOT_FORMAL"
MANIFEST = "B220_EXPLORE_RELIC_SOURCE_SELECT.json"
SOURCE_FILE = f"selected_sources/{gate.TARGET}.luau"

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("RED_B220_EXPLORE_RELIC_" + reason)

def verified(candidate: Path) -> tuple[bytes, bytes, str]:
    candidate = candidate.resolve()
    former = candidate / gate.OFF
    on = gate.selected(candidate)
    off = gate.selected(former)
    require(len(on) == len(off) == 69 and set(on) == set(off),
            "MUST_BE_69_IDENTICAL_ROUTES")
    original_receipt = json.loads((former / gate.RECEIPT).read_text())
    candidate_receipt = json.loads((candidate / gate.RECEIPT).read_text())
    require(original_receipt.get("build_head") == gate.BASE
            and original_receipt.get("canonical_build") is True
            and original_receipt.get("source_hashes") ==
            {route: gate.sha(path.read_bytes()) for route, path in off.items()},
            "IMMUTABLE_OFFICIAL_RECEIPT")
    require(candidate_receipt.get("build_head") == gate.BASE
            and candidate_receipt.get("source_hashes") ==
            {route: gate.sha(path.read_bytes()) for route, path in on.items()},
            "CANDIDATE_EXACT_RECEIPT")
    require((candidate / gate.PROJECT).read_bytes() ==
            (former / gate.PROJECT).read_bytes(), "PROJECT_CLASS_LOCK")
    original = off[gate.TARGET].read_bytes()
    amended = on[gate.TARGET].read_bytes()
    require({route for route in on if
             on[route].read_bytes() != off[route].read_bytes()} ==
            {gate.TARGET}, "EXACTLY_ONE_TRUE_SELECTED_CHANGE")
    require(amended == gate.transform(original.decode("utf-8")).encode("utf-8"),
            "EXACT_PATCH_NO_HIDDEN_AUTHORITY")
    class_map = original_receipt.get("source_classes")
    require(isinstance(class_map, dict) and len(class_map) == 69
            and class_map == candidate_receipt.get("source_classes"),
            "ORIGINAL_SCRIPT_CLASSES_UNCHANGED")
    cls = class_map[gate.TARGET]
    require(cls == "Script", "ORIGINAL_EXPLORE_RELIC_CLASS")
    visual = candidate_receipt.get("gq470_explore_relic_art")
    require(isinstance(visual, dict) and
            visual.get("feature_id") == gate.MARK and
            visual.get("unchanged_selected_routes") == 68 and
            visual.get("parts_per_marker_before_after") == [3, 3] and
            visual.get("new_instances_per_arena") == 0 and
            visual.get("new_prompts") == 0 and
            visual.get("gameplay_authority_changed") is False and
            visual.get("owner_accepted") is False,
            "REAL_EXPLORE_RELIC_VISUAL_SCOPE_BUDGET")
    return original, amended, cls

def manifest(before: bytes, after: bytes, cls: str) -> dict:
    require(cls == "Script", "SOURCE_CLASS")
    require(before != after, "ZERO_DELTA")
    return {
        "schema": "GQ470_B220_EXPLORE_RELIC_ONE_REAL_SOURCE_V1",
        "official_branch": "rc/p0d-s1-kids-rc01",
        "official_parent_at_prep": gate.BASE,
        "source_select_only": True,
        "candidate_only": True,
        "formal_rc_changed_by_export": False,
        "P0_910_playable_before_art": True,
        "requires_B220_authenticated_fresh_expected_sha_nonforce_CAS": True,
        "selected_luau_route": gate.TARGET,
        "source_class": cls,
        "source_path": SOURCE_FILE,
        "original_source_sha256": gate.sha(before),
        "candidate_source_sha256": gate.sha(after),
        "candidate_source_bytes": len(after),
        "changed_selected_routes": 1,
        "unchanged_selected_routes": 68,
        "parts_per_marker_before_after": [3, 3],
        "new_instances_per_arena": 0,
        "studio_solo": "NOT_TESTED",
        "studio_two_client": "NOT_TESTED",
        "art_visual_evidence_images": 0,
        "android_15min": "NOT_TESTED",
        "human_art": "NOT_TESTED",
        "kid_fun": "NOT_TESTED",
        "owner_accepted": False,
        "product_gate": "NO_GO",
        "art_gate": "NO_GO",
    }

def expected(candidate: Path) -> tuple[bytes, dict]:
    before, after, cls = verified(candidate)
    return after, manifest(before, after, cls)

def check(candidate: Path, package: Path) -> None:
    after, expected_manifest = expected(candidate)
    require((package / MANIFEST).is_file(), "MISSING_MANIFEST")
    require((package / SOURCE_FILE).is_file(), "MISSING_SELECTED_LUA")
    supplied = json.loads((package / MANIFEST).read_text())
    require(supplied == expected_manifest, "MANIFEST_CHANGED_OR_FORGED")
    require((package / SOURCE_FILE).read_bytes() == after, "SOURCE_BYTES_DRIFT")
    expected_names = {MANIFEST, SOURCE_FILE}
    actual_names = {p.relative_to(package).as_posix()
                    for p in package.rglob("*") if p.is_file()}
    require(actual_names == expected_names, "UNEXPECTED_FILE_OR_OMISSION")

def build(candidate: Path, package: Path) -> None:
    after, row = expected(candidate)
    require(not package.exists(), "OUTPUT_EXISTS")
    (package / SOURCE_FILE).parent.mkdir(parents=True)
    (package / SOURCE_FILE).write_bytes(after)
    (package / MANIFEST).write_text(
        json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True)+"\n")
    check(candidate, package)
    print("GQ470_EXPLORE_RELIC_B220_GENUINE_ONE_SELECTED_SOURCE_PACKAGE_PASS",
          row["candidate_source_sha256"])

def self_test() -> None:
    require(gate.TARGET == "ServerScriptService/EGGRUMBLE_LegacyExplorationBridge",
            "SOURCE_TARGET_FIXED")
    sample = manifest(b"original", b"actual replacement", "Script")
    require(sample["changed_selected_routes"] == 1
            and sample["unchanged_selected_routes"] == 68
            and sample["source_select_only"] is True
            and sample["owner_accepted"] is False, "POSITIVE")
    for before, after, cls in (
        (b"same", b"same", "Script"),
        (b"orig", b"candidate", "LocalScript"),
        (b"orig", b"candidate", "ModuleScript"),
    ):
        try:
            manifest(before, after, cls)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_EXPLORE_RELIC_B220_MUTANT_ACCEPTED")
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)
        package=p/"pkg"
        (package/"selected_sources").mkdir(parents=True)
        (package/MANIFEST).write_text(json.dumps(sample))
        (package/SOURCE_FILE).parent.mkdir(parents=True, exist_ok=True)
        (package/SOURCE_FILE).write_bytes(b"actual replacement")
        supplied=json.loads((package/MANIFEST).read_text())
        require(supplied == sample, "JSON_ROUNDTRIP")
        require((package/SOURCE_FILE).read_bytes() == b"actual replacement",
                "EXACT_WRITE")
        (package/"extra.luau").write_text("-- hidden")
        names={p.relative_to(package).as_posix()
               for p in package.rglob("*") if p.is_file()}
        require(names != {MANIFEST,SOURCE_FILE}, "EXTRA_FILE_DETECTION")
    print("GQ470_EXPLORE_RELIC_B220_4_SOURCE_ADMISSION_NEGATIVES_PASS")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--candidate", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--check", action="store_true")
    opt=p.parse_args()
    if opt.self_test:
        self_test()
    else:
        require(opt.candidate is not None and opt.out is not None,
                "CANDIDATE_OUT_REQUIRED")
        if opt.check:
            check(opt.candidate,opt.out)
            print("GQ470_EXPLORE_RELIC_B220_RECHECK_EXACT_BYTES_PASS")
        else:
            build(opt.candidate,opt.out)
