#!/usr/bin/env python3
"""Untrusted A-only B220 one-source packet: fail-closed validation + mutations.

This verifier does not write the formal RC or certify Studio, ART or gameplay.
"""
from __future__ import annotations
import argparse
import json
import shutil
import tempfile
from pathlib import Path
import compose_real70 as c

def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_DUNE_B_PACKET_" + why)

def verify_payload(packet: Path, built: Path) -> dict:
    require(packet.is_dir() and built.is_file(), "PACKET_OR_PLACE_MISSING")
    mpath = packet / c.B_MANIFEST
    require(mpath.is_file(), "MANIFEST_MISSING")
    meta = json.loads(mpath.read_text(encoding="utf-8"))
    expected_source_path = "selected_sources/" + c.NEW_FILE.removeprefix("sources/")
    expected = {
        "schema": "GQ470_DUNE_GRASS_B220_SOURCE_SELECT_V1",
        "feature_id": c.FEATURE,
        "formal_base": c.BASE,
        "formal_branch": c.FORMAL,
        "source_profile": "PRIVATE_COMPANION_REAL69_TO_70_A_ONLY",
        "new_source_route": c.NEW_ROUTE,
        "new_source_path": expected_source_path,
        "new_source_sha256": c.digest(c.NEW_SOURCE.read_bytes()),
        "new_source_bytes": len(c.NEW_SOURCE.read_bytes()),
        "new_source_class": "LocalScript",
        "official_69_exact": True,
        "candidate_sources": 70,
        "candidate_place_bytes": built.stat().st_size,
        "candidate_place_sha256": c.digest(built.read_bytes()),
        "formal_integrated": False,
        "owner_accepted": False,
        "b_admission": "DEFER_P0_910_FIRST_ART_NOT_TESTED",
        "needs_fresh_head_nonforce_expected_sha": True,
    }
    require(set(meta) == set(expected), "UNKNOWN_OR_MISSING_MANIFEST_KEYS")
    for key, value in expected.items():
        require(type(meta[key]) is type(value) and meta[key] == value, "MANIFEST_" + key.upper())
    actual_files = {
        p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()
    }
    require(actual_files == {c.B_MANIFEST, expected_source_path},
            "PACKET_EXTRA_OR_MISSING_FILE")
    source = packet / expected_source_path
    require(source.is_file() and source.read_bytes() == c.NEW_SOURCE.read_bytes(),
            "EXPORTED_SOURCE_IDENTITY")
    require(meta["new_source_route"].startswith("StarterPlayer/StarterPlayerScripts/"),
            "CLIENT_SELECTION_ONLY")
    return meta

def mutate_negatives(packet: Path, built: Path) -> int:
    # Each case is a NEW untrusted copy, never altering the official artifact.
    bad_values = [
        ("formal_integrated", True),
        ("owner_accepted", True),
        ("b_admission", "ADOPT"),
        ("new_source_route", "ServerScriptService/Forged"),
        ("new_source_sha256", "0" * 64),
        ("new_source_bytes", 0),
        ("new_source_class", "Script"),
        ("candidate_place_sha256", "0" * 64),
        ("candidate_place_bytes", 1),
        ("formal_base", "0" * 40),
        ("source_profile", "ACTIVE_RUNTIME_rich51"),
        ("official_69_exact", False),
        ("candidate_sources", 69),
        ("needs_fresh_head_nonforce_expected_sha", False),
    ]
    tested = 0
    with tempfile.TemporaryDirectory(prefix="gq470_dune_tamper_") as tmp:
        root = Path(tmp)
        for index, (field, bad) in enumerate(bad_values):
            suspect = root / f"mutant{index}"
            shutil.copytree(packet, suspect)
            manifest = suspect / c.B_MANIFEST
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data[field] = bad
            manifest.write_text(json.dumps(data), encoding="utf-8")
            try:
                verify_payload(suspect, built)
            except (ValueError, KeyError):
                tested += 1
            else:
                raise AssertionError("RED_ACCEPTED_B_PACKET_TAMPER_" + field)
        for label in ("mutated_source", "injected_file", "missing_manifest"):
            suspect = root / label
            shutil.copytree(packet, suspect)
            selected = suspect / "selected_sources" / c.NEW_FILE.removeprefix("sources/")
            if label == "mutated_source":
                selected.write_bytes(selected.read_bytes() + b"\n-- forged\n")
            elif label == "injected_file":
                (suspect / "forged.lua").write_text("return true")
            else:
                (suspect / c.B_MANIFEST).unlink()
            try:
                verify_payload(suspect, built)
            except (ValueError, KeyError):
                tested += 1
            else:
                raise AssertionError("RED_ACCEPTED_B_PACKET_TAMPER_" + label)
    require(tested == len(bad_values) + 3, "TAMPER_TEST_COUNT")
    return tested

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--built", type=Path, required=True)
    opts = parser.parse_args()
    packet = opts.candidate / c.B_PACKET
    verify_payload(packet, opts.built)
    failures = mutate_negatives(packet, opts.built)
    verify_payload(packet, opts.built)
    print("GQ470_DUNE_B220_ONE_SOURCE_PACKET_VALID_TAMPER_REJECTED",
          failures, "SOURCE_ONLY_NOT_FORMAL")
