#!/usr/bin/env python3
"""B220 one-route source-select export: no formal RC write, strict source lock."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from patch_trapper_portal69 import (
    BASE, BRANCH, FEATURE, PROJECT, RECEIPT, OFF, PLACE, ROUTE,
    NEW_PAD, OLD_PAD, selected, unpatch,
)

def need(ok, name):
    if not ok:
        raise ValueError("RED_GQ470_TRAPPER_B220_" + name)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def changed_one(before, after):
    need(len(before) == len(after) == 69, "69_ROUTES")
    need(set(before) == set(after), "ROUTE_SET")
    need({k for k in before if before[k] != after[k]} == {ROUTE},
         "ONE_CHANGED_OTHER68_EXACT")

def inspect(root: Path) -> tuple[bytes, dict]:
    root = root.resolve()
    source_on = selected(root)
    source_off = selected(root / OFF)
    off_meta = json.loads((root / OFF / RECEIPT).read_text())
    on_meta = json.loads((root / RECEIPT).read_text())
    before = {k: sha(f.read_bytes()) for k, f in source_off.items()}
    after = {k: sha(f.read_bytes()) for k, f in source_on.items()}
    changed_one(before, after)
    need(off_meta.get("build_head") == BASE and
         off_meta.get("official_branch") == BRANCH and
         off_meta.get("selected_source_count") == 69 and
         off_meta.get("canonical_build") is True and
         off_meta.get("source_hashes") == before,
         "PINNED_OFFICIAL_PARENT")
    need(on_meta.get("build_head") == BASE and
         on_meta.get("official_branch") == BRANCH and
         on_meta.get("source_hashes") == after,
         "CANDIDATE_RECEIPT_HASHES")
    need(on_meta.get("source_classes") == off_meta.get("source_classes") and
         len(on_meta.get("source_classes", {})) == 69,
         "SCRIPT_CLASS_NONLOSS")
    art_meta = on_meta.get("gq470_trapper_portal_art", {})
    need(art_meta.get("feature_id") == FEATURE and
         art_meta.get("changed_source_routes") == 1 and
         art_meta.get("byte_exact_unmodified_routes") == 68 and
         art_meta.get("new_scripts") == 0 and
         art_meta.get("new_remotes") == 0 and
         art_meta.get("modified_travel_authority") is False and
         art_meta.get("owner_accepted") is False,
         "ART_FEATURE_RECEIPT")
    original = source_off[ROUTE].read_bytes()
    replacement = source_on[ROUTE].read_bytes()
    need(OLD_PAD.encode() in original and NEW_PAD.encode() in replacement,
         "ACTUAL_VISUAL_SOURCE")
    need(unpatch(replacement.decode("utf-8")).encode("utf-8") == original,
         "EXACT_INVERSE_LUAU")
    place = root / PLACE
    need(place.is_file() and
         on_meta.get("private_place_bytes") == place.stat().st_size and
         on_meta.get("private_place_sha256") == sha(place.read_bytes()),
         "PRIVATE_PLACE_BYTE_SHA_EXACT")
    art = json.loads((root / "ART_CHECK_REPORT.json").read_text())
    need(art["source_gate"]["status"] == "PASS_SOURCE_ONLY" and
         art["source_gate"]["actual_place_scripts"] == 69 and
         art["visual_evidence_gate"]["screenshots_received"] == 0 and
         art["art_gate"] == "ART_NO_GO" and
         art["owner_accepted"] is False,
         "NOT_FABRICATED_ART")
    manifest = {
        "schema": "GQ470_TRAPPER_ONE_SOURCE_B220_HANDOFF_V1",
        "feature_id": FEATURE,
        "official_branch": BRANCH,
        "expected_parent_head": BASE,
        "source_route": ROUTE,
        "source_class": off_meta["source_classes"][ROUTE],
        "expected_original_source_sha256": before[ROUTE],
        "candidate_source_sha256": after[ROUTE],
        "other_68_byte_exact": True,
        "source_count_before_after": [69, 69],
        "candidate_private_place_bytes": place.stat().st_size,
        "candidate_private_place_sha256": sha(place.read_bytes()),
        "new_runtime_authority": False,
        "same_source_class": True,
        "requires_certified_b220_writer": True,
        "requires_fresh_formal_head_cas": True,
        "formal_rc_integrated": False,
        "studio_solo": "NOT_TESTED",
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "human_art": "NOT_TESTED",
        "owner_accepted": False,
    }
    return replacement, manifest

def validate_b_manifest(meta: dict) -> None:
    import re
    need(meta.get("feature_id") == FEATURE and
         meta.get("official_branch") == BRANCH and
         meta.get("expected_parent_head") == BASE and
         meta.get("source_route") == ROUTE and
         meta.get("source_class") == "Script",
         "MANIFEST_SOURCE_IDENTITY")
    for key in ("expected_original_source_sha256", "candidate_source_sha256",
                "candidate_private_place_sha256"):
        need(isinstance(meta.get(key), str) and
             re.fullmatch(r"[0-9a-f]{64}", meta[key]) is not None,
             "MANIFEST_SHA256_" + key)
    need(meta["expected_original_source_sha256"] !=
         meta["candidate_source_sha256"], "MANIFEST_NO_SOURCE_DELTA")
    need(meta.get("other_68_byte_exact") is True and
         meta.get("source_count_before_after") == [69, 69] and
         meta.get("new_runtime_authority") is False and
         meta.get("same_source_class") is True and
         meta.get("requires_certified_b220_writer") is True and
         meta.get("requires_fresh_formal_head_cas") is True and
         meta.get("formal_rc_integrated") is False and
         meta.get("owner_accepted") is False,
         "MANIFEST_NO_FAKE_ADOPTION")
    for key in ("studio_solo", "studio_2client", "android_15min", "human_art"):
        need(meta.get(key) == "NOT_TESTED", "MANIFEST_NO_FAKE_RUNTIME_" + key)
    need(isinstance(meta.get("candidate_private_place_bytes"), int) and
         meta["candidate_private_place_bytes"] > 0, "MANIFEST_PLACE_BYTES")


def export(root: Path, out: Path, check: bool):
    data, manifest = inspect(root)
    validate_b_manifest(manifest)
    out = out.resolve()
    rel = Path("selected_sources/ServerScriptService/EGGRUMBLE_SevenRoleCombat.luau")
    source_path = out / rel
    manifest_path = out / "SOURCE_SELECT_MANIFEST.json"
    if check:
        need(source_path.read_bytes() == data and
             json.loads(manifest_path.read_text()) == manifest,
             "B_PACKET_DRIFT")
        files = {f.relative_to(out).as_posix() for f in out.rglob("*") if f.is_file()}
        need(files == {rel.as_posix(), "SOURCE_SELECT_MANIFEST.json"},
             "PACKET_HAS_UNEXPECTED_FILES")
        print("GQ470_TRAPPER_B220_EXACT_PACKET_READBACK_PASS")
        return
    need(not out.exists(), "OUTPUT_ALREADY_EXISTS")
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(data)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False,
                                        sort_keys=True, indent=2) + "\n")
    print("GQ470_TRAPPER_B220_ONE_SOURCE_PREP_NOT_FORMAL",
          manifest["candidate_source_sha256"])

def selftest():
    sample = {f"TEST/{i}": f"HASH{i}" for i in range(68)}
    sample[ROUTE] = "OLD"
    changed = dict(sample)
    changed[ROUTE] = "NEW"
    changed_one(sample, changed)
    for bad in (
        sample, {**changed, "TEST/0": "MUTATED"},
        dict(list(changed.items())[:-1]),
        {**changed, "EXTRA": "BAD"},
        {**sample, "TEST/0": "MUTATED"},
    ):
        try:
            changed_one(sample, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_B220_FORGED_INPUT_ACCEPTED")
    import copy
    valid = {
        "feature_id": FEATURE, "official_branch": BRANCH,
        "expected_parent_head": BASE, "source_route": ROUTE,
        "source_class": "Script",
        "expected_original_source_sha256": "a" * 64,
        "candidate_source_sha256": "b" * 64,
        "candidate_private_place_sha256": "c" * 64,
        "candidate_private_place_bytes": 799348,
        "other_68_byte_exact": True,
        "source_count_before_after": [69, 69],
        "new_runtime_authority": False,
        "same_source_class": True,
        "requires_certified_b220_writer": True,
        "requires_fresh_formal_head_cas": True,
        "formal_rc_integrated": False,
        "owner_accepted": False,
        "studio_solo": "NOT_TESTED", "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED", "human_art": "NOT_TESTED",
    }
    validate_b_manifest(valid)
    mutants = [
        ("expected_parent_head", "deadbeef"),
        ("source_class", "LocalScript"),
        ("expected_original_source_sha256", "deadbeef"),
        ("candidate_source_sha256", valid["expected_original_source_sha256"]),
        ("requires_certified_b220_writer", False),
        ("requires_fresh_formal_head_cas", False),
        ("formal_rc_integrated", True),
        ("owner_accepted", True),
        ("studio_2client", "PASS"),
        ("source_count_before_after", [68, 69]),
        ("candidate_private_place_bytes", 0),
    ]
    for key, val in mutants:
        altered = copy.deepcopy(valid)
        altered[key] = val
        try:
            validate_b_manifest(altered)
        except ValueError:
            pass
        else:
            raise AssertionError("RED_B220_FORGED_MANIFEST_ACCEPTED_" + key)
    print("GQ470_TRAPPER_B220_FIVE_ROUTE_AND_11_MANIFEST_MUTANTS_RED_PASS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        selftest()
    else:
        need(args.base is not None and args.out is not None,
             "BASE_AND_OUTPUT_REQUIRED")
        export(args.base, args.out, args.check)
