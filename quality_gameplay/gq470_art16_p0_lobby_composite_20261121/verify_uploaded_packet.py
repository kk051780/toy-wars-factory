#!/usr/bin/env python3
"""Independent replay of the *uploaded* ART16+P0 A artifact from true formal REAL69.

B220 can reject a forged, stale or incomplete artifact even when its original
CI said green. This script runs only on isolated temp worktree; no official RC.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from compose_art16_p0 import (
    FORMAL, ART16_HEAD, P0_HEAD, PROJECT, PLACE, RECEIPT, NOTE, OFF,
    PACKET, HOST, exact_formal, sha, selected, verify, need,
)
from verify_b220_packet import check, negatives

UPLOAD_REPORT = "GQ470_ART16_P0_INDEPENDENT_UPLOAD_REPLAY.json"


def uploaded_candidate(path: Path) -> Path:
    available = [
        p.parent for p in path.rglob(PROJECT)
        if (p.parent / RECEIPT).is_file()
        and (p.parent / PLACE).is_file()
        and (p.parent / PACKET / "SOURCE_SELECT_MANIFEST.json").is_file()
        and OFF not in p.parts
    ]
    need(len(available) == 1, "UPLOADED_ARTIFACT_HAS_AMBIGUOUS_OR_NO_CANDIDATE")
    return available[0]


def prepare(formal: Path, download_root: Path, out: Path) -> None:
    need(not out.exists(), "POST_UPLOAD_NO_OVERWRITE")
    base_receipt, original, classes = exact_formal(formal)
    uploaded = uploaded_candidate(download_root)
    uploaded_project = uploaded / PROJECT
    received_receipt = json.loads((uploaded / RECEIPT).read_text())
    note = received_receipt.get(NOTE, {})
    need(uploaded_project.read_bytes() == (formal / PROJECT).read_bytes() and
         received_receipt.get("canonical_build") is False and
         received_receipt.get("build_head") == "GQ470_ART16_P0_A_CANDIDATE_NOT_FORMAL" and
         note.get("formal_head") == FORMAL and
         note.get("art16_head") == ART16_HEAD and
         note.get("p0_head") == P0_HEAD and
         note.get("formal_adopted") is False and
         note.get("owner_accepted") is False and
         note.get("art_gate") == "ART_NO_GO" and
         note.get("screen_shots") == "0/32" and
         note.get("studio_spawn_fix_proven") is False and
         note.get("changed_selected_sources") == 17 and
         note.get("unchanged_original_sources") == 52 and
         received_receipt.get("source_classes") == classes and
         note.get("native_rojo") == "PASS_SOURCE_ONLY",
         "POST_UPLOAD_RECEIPT_NOT_ACTUAL_A")
    received_place = (uploaded / PLACE).read_bytes()
    need(sha(received_place) == received_receipt.get("private_place_sha256") and
         len(received_place) == received_receipt.get("private_place_bytes") and
         received_receipt["private_place_sha256"] != sha((formal / PLACE).read_bytes()),
         "POST_UPLOAD_PLACE_DIGEST_MISMATCH")
    packet = uploaded / PACKET
    manifest = json.loads((packet / "SOURCE_SELECT_MANIFEST.json").read_text())
    need(manifest.get("schema") == "GQ470_ART16_P0_17_ROUTE_B220_SOURCE_ONLY_V1" and
         manifest.get("selected_count") == 17 and
         manifest.get("original_untouched") == 52 and
         manifest.get("original_selected_count") == 69 and
         manifest.get("formal_head") == FORMAL and
         manifest.get("parent_art16_head") == ART16_HEAD and
         manifest.get("parent_p0_head") == P0_HEAD and
         manifest.get("candidate_private_place_sha256") == sha(received_place) and
         manifest.get("candidate_private_place_bytes") == len(received_place) and
         manifest.get("formal_adopted") is False and
         manifest.get("owner_accepted") is False and
         manifest.get("art_gate") == "ART_NO_GO" and
         manifest.get("art_images") == "0/32" and
         manifest.get("requires_writer_220_fresh_nonforce_cas") is True,
         "POST_UPLOAD_MANIFEST_FALSE_OR_STALE")
    rows = manifest.get("source_only")
    need(isinstance(rows, list) and len(rows) == 17, "POST_UPLOAD_ROWS_NOT17")
    shutil.copytree(formal, out)
    shutil.copytree(formal, out / OFF)
    shutil.copytree(packet, out / PACKET)
    scripts = selected(out)
    got: set[str] = set()
    for row in rows:
        need(isinstance(row, dict) and set(row) ==
             {"route", "class", "path", "old_sha256", "new_sha256", "source"},
             "POST_UPLOAD_ROW_FIELDS")
        route = row["route"]
        need(isinstance(route, str) and route in original and
             route not in got and
             row["class"] == classes[route] and
             row["old_sha256"] == sha(original[route]) and
             row["source"] == (980 if route == HOST else 970),
             "POST_UPLOAD_WRITER_ROUTE_OLD_SOURCE")
        got.add(route)
        correct_rel = Path("selected_sources") / (route + ".luau")
        need(row["path"] == correct_rel.as_posix(), "POST_UPLOAD_UNSAFE_FILE_PATH")
        path = (packet / correct_rel).resolve()
        need(path.is_relative_to(packet.resolve()) and path.is_file() and
             not path.is_symlink(), "POST_UPLOAD_FILE_ESCAPE")
        new = path.read_bytes()
        need(sha(new) == row["new_sha256"] and new != original[route] and
             received_receipt["source_hashes"][route] == sha(new),
             "POST_UPLOAD_BLOB_HASH_OR_NO_DIFF")
        scripts[route][0].write_bytes(new)
    need(got == set(note["authors"]["art16_970"] + note["authors"]["early_lobby_980"]) and
         len(note["authors"]["art16_970"]) == 16 and
         note["authors"]["early_lobby_980"] == [HOST],
         "POST_UPLOAD_BAD_AUTHOR_MAP")
    (out / RECEIPT).write_bytes((uploaded / RECEIPT).read_bytes())
    # Original Place remains temporarily until pinned Rojo builds expected new Place.
    verify(out, sealed=False)
    print("GQ470_POST_UPLOAD_REPLAY_SELECTED17_SOURCE_EXACT_52_PRISTINE")


def seal_and_report(formal: Path, downloaded_root: Path, rebuild: Path,
                    report_path: Path) -> None:
    uploaded = uploaded_candidate(downloaded_root)
    verify(rebuild, sealed=True)
    result = check(rebuild)
    independent_negative = negatives(rebuild)
    actual_place = (rebuild / PLACE).read_bytes()
    need(actual_place == (uploaded / PLACE).read_bytes() and
         sha(actual_place) != sha((formal / PLACE).read_bytes()),
         "POST_UPLOAD_ROJO_PLACE_NOT_BYTE_IDENTICAL")
    expected = json.loads((uploaded / RECEIPT).read_text())
    need(expected["private_place_bytes"] == len(actual_place) and
         expected["private_place_sha256"] == sha(actual_place),
         "POST_UPLOAD_ACTUAL_PLACE_RECEIPT")
    need(independent_negative.get("tamper_cases_rejected") == 28 and
         result.get("validated_routes") == 17 and
         result.get("remaining_original_byte_exact") == 52,
         "POST_UPLOAD_B220_NEGATIVE_OR_NONLOSS_FAILED")
    report = {
        "schema": "GQ470_ART16_P0_POST_UPLOAD_REPLAY_RECEIPT_V1",
        "official_head": FORMAL, "formal_rc_updated": False,
        "upload_artifact_reloaded": True, "artifact_real_luaus": 17,
        "replayed_selected_original": 17, "original_unchanged": 52,
        "all_source_classes_exact": True,
        "on_place_822713_expected_bytes": len(actual_place),
        "reproduced_candidate_place_sha256": sha(actual_place),
        "uploaded_candidate_place_sha256": sha((uploaded / PLACE).read_bytes()),
        "native_on_off_source": "PREVIOUS_A_RUN_PASS_SOURCE_ONLY",
        "rojo_original_off_byte_exact": True,
        "rojo_candidate_on_reproduced_byte_exact": True,
        "tamper_negatives_rechecked_from_uploaded": 28,
        "formal_rc_adopted": False, "studio": "NOT_TESTED",
        "studio_spawn_fix": "NOT_PROVEN", "android_15min": "NOT_TESTED",
        "art_images": "0/32", "art_gate": "ART_NO_GO",
        "fun_gate": "FUN_NO_GO", "owner_accepted": False,
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print("GQ470_POST_UPLOAD_INDEPENDENT_REAL_PLACE_BYTE_EXACT_17_OF69_24_NEGATIVES",
          len(actual_place), sha(actual_place), "ART_NO_GO")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--formal", type=Path, required=True)
    p.add_argument("--downloaded", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seal", action="store_true")
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    if args.seal:
        need(args.report is not None, "POST_UPLOAD_REPORT_REQUIRED")
        seal_and_report(args.formal, args.downloaded, args.out, args.report)
    else:
        prepare(args.formal, args.downloaded, args.out)
