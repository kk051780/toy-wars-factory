#!/usr/bin/env python3
"""Independent B220 replay after GitHub uploaded A artifact re-download.

Runs in a fresh Actions job, not the producer's process. Compares every
uploaded B selected source byte, actual Rojo Place, provenance, manifest,
source classes, official rollback and ART honesty to a new full rebuild.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from compose_real70 import (
    BASE, FEATURE, OFF_BYTES, OFF_SHA, PLACE, PROJECT, RECEIPT,
    REL, ROUTE, SOURCE, digest, need, baseline, built_source_map,
)

B_PACKET = "B220_LOBBY_EDGE_ONE_NEW_CLIENT_SOURCE_NOT_FORMAL"
MANIFEST = "SOURCE_SELECT_MANIFEST.json"
REPORT = "GQ470_LOBBY_EDGE_A_SOURCE_RECEIPT.json"
ON_PLACE = "EGGRUMBLE_REAL70_PRIVATE.rbxlx"


def uploaded_paths(root: Path) -> dict[str, Path]:
    """Reject any invisible extra file; never trust a naked file-name match."""
    paths = {
        p.relative_to(root).as_posix(): p
        for p in root.rglob("*") if p.is_file()
    }
    expected = {
        "OFF69_REBUILT.rbxlx",
        "candidate/" + PROJECT,
        "candidate/" + ON_PLACE,
        "candidate/" + REPORT,
        "candidate/" + B_PACKET + "/" + MANIFEST,
        "candidate/" + B_PACKET + "/selected_sources/" + REL.removeprefix("sources/"),
    }
    need(set(paths) == expected, "UPLOADED_EXACT_SIX_FILES")
    need(all(path.resolve().is_relative_to(root.resolve())
             and not path.is_symlink() for path in paths.values()), "NO_SYMLINK_OR_ESCAPE")
    return paths


def replay(original: Path, rebuilt: Path, uploaded: Path) -> dict:
    receipt, selected = baseline(original)
    files = uploaded_paths(uploaded)
    def get(path: str) -> bytes:
        return files[path].read_bytes()
    suffix = B_PACKET + "/selected_sources/" + REL.removeprefix("sources/")
    manifest = json.loads(get("candidate/" + B_PACKET + "/" + MANIFEST))
    report = json.loads(get("candidate/" + REPORT))
    recreated_manifest = json.loads((rebuilt / B_PACKET / MANIFEST).read_text())
    recreated_report = json.loads((rebuilt / REPORT).read_text())

    # Both hash and complete exact byte match are needed. Hash alone is
    # checked only after the source/route/class was compared to actual Place.
    built = rebuilt / ON_PLACE
    on = get("candidate/" + ON_PLACE)
    need(on == built.read_bytes(), "ON70_PLACE_NOT_BYTE_EXACT")
    need(get("OFF69_REBUILT.rbxlx") == (original / PLACE).read_bytes(),
         "OFF69_PLACE_NOT_BYTE_EXACT")
    need(get("candidate/" + PROJECT) == (rebuilt / PROJECT).read_bytes(),
         "PROJECT_TAMPER")
    need(get("candidate/" + REPORT) == (rebuilt / REPORT).read_bytes()
         and report == recreated_report, "RECEIPT_TAMPER")
    need(manifest == recreated_manifest, "B_MANIFEST_TAMPER")
    need(get("candidate/" + suffix) == SOURCE.read_bytes(),
         "NEW_SELECTED_SOURCE_TAMPER")
    need(manifest.get("source_sha256") == digest(SOURCE.read_bytes())
         and manifest.get("new_script_route") == ROUTE
         and manifest.get("new_script_class") == "LocalScript"
         and manifest.get("formal_base_sha") == BASE
         and manifest.get("source_only") is True
         and manifest.get("official_rc_adopted") is False
         and manifest.get("art_gate") == "ART_NO_GO"
         and manifest.get("owner_accepted") is False
         and report.get("screenshots") == "0/32",
         "B_EVIDENCE_AUTHORITY_OR_FALSE_ART")
    actual = built_source_map(built)
    need(len(actual) == 70 and actual[ROUTE.rsplit("/",1)[-1]]
         == ("LocalScript", digest(SOURCE.read_bytes())), "ACTUAL_PLACE_LOCAL_SOURCE")
    need(len(selected) == 69
         and receipt["selected_source_count"] == 69
         and (original / PLACE).stat().st_size == OFF_BYTES
         and digest((original / PLACE).read_bytes()) == OFF_SHA, "ORIGINAL_69_EVIDENCE")
    return {
        "schema": "GQ470_LOBBY_EDGE_B_POSTUPLOAD_INDEPENDENT_REPLAY_V1",
        "head_role": "A_PREP_ONLY_NO_FORMAL_CHANGE",
        "feature_id": FEATURE,
        "formal_rc_head": BASE,
        "candidate_place_bytes": len(on),
        "candidate_place_sha256": digest(on),
        "new_source_sha256": digest(SOURCE.read_bytes()),
        "source_count_on": len(actual),
        "source_count_off": len(selected),
        "uploaded_files_exact": len(files),
        "original_69_source_class_route": "EXACT",
        "native_source_artifact": "SOURCE_ONLY",
        "studio": "NOT_TESTED",
        "android15": "NOT_TESTED",
        "screenshots": "0/32",
        "human_art": "NOT_TESTED",
        "product_gate": "PRODUCT_NO_GO",
        "art_gate": "ART_NO_GO",
        "owner_accepted": False,
        "official_adopted": False,
    }


def negatives(original: Path, rebuilt: Path, uploaded: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="gq470-verify-mutant-") as temp:
        root = Path(temp)
        fails = 0
        relative = [
            "candidate/" + ON_PLACE,
            "OFF69_REBUILT.rbxlx",
            "candidate/" + REPORT,
            "candidate/" + B_PACKET + "/" + MANIFEST,
            "candidate/" + B_PACKET + "/selected_sources/" + REL.removeprefix("sources/"),
        ]
        for i, path in enumerate(relative):
            broken = root / str(i)
            shutil.copytree(uploaded, broken)
            target = broken / path
            data = target.read_bytes()
            # A tiny but real 1 byte corruption must be rejected.
            target.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))
            try:
                replay(original, rebuilt, broken)
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
                fails += 1
            else:
                raise AssertionError("RED_POSTUPLOAD_MUTANT_ACCEPTED_" + str(i))
        broken = root / "extra"
        shutil.copytree(uploaded, broken)
        (broken / "EXTRA.txt").write_text("malicious extra")
        try:
            replay(original, rebuilt, broken)
        except ValueError:
            fails += 1
        else:
            raise AssertionError("RED_POSTUPLOAD_EXTRA_ACCEPTED")
    need(fails == 6, "NEGATIVE_MUTATION_COUNT")
    return fails


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--rebuilt", type=Path, required=True)
    p.add_argument("--uploaded", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    result = replay(args.original, args.rebuilt, args.uploaded)
    result["tamper_negative_cases_rejected"] = negatives(
        args.original, args.rebuilt, args.uploaded
    )
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print("GQ470_LOBBY_EDGE_INDEPENDENT_POSTUPLOAD_70_SOURCE_REPLAY_PASS", result)
