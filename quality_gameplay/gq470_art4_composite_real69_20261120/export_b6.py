#!/usr/bin/env python3
"""Fail-closed, source-only ART6 handoff for the one authenticated RC writer.

This exports exact original selected Luau bytes from a rebuilt A candidate;
it does NOT modify the RC, launch Studio, approve ART, or authorize a writer.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import compose_art4 as gate

BUNDLE_NAME = "B220_ART6_SOURCE_ONLY_NOT_FORMAL.json"
SOURCE_FOLDER = "selected_sources"


def rows(before: dict[str, bytes], after: dict[str, bytes],
         classes: dict[str, str]) -> list[dict]:
    expected = {item.target for item in gate.SLICES}
    gate.changed_routes(before, after, expected)
    gate.demand(set(classes) == set(after), "B220_CLASS_ROUTE_SET")
    out = []
    for s in gate.SLICES:
        cls = classes[s.target]
        gate.demand(isinstance(cls, str) and cls in
                    ("Script", "LocalScript", "ModuleScript"),
                    "B220_SELECTED_CLASS_" + str(s.pr))
        out.append({
            "pr": s.pr,
            "selected_route": s.target,
            "source_class": cls,
            "artifact_path": SOURCE_FOLDER + "/" + s.target + ".luau",
            "original_sha256": gate.digest(before[s.target]),
            "candidate_sha256": gate.digest(after[s.target]),
            "source_bytes": len(after[s.target]),
            "pinned_author_head": s.head,
        })
    return out


def expected_manifest(before: dict[str, bytes], after: dict[str, bytes],
                      classes: dict[str, str]) -> dict:
    return {
        "schema": "GQ470_ART6_B220_SOURCE_SELECT_V1",
        "official_parent": gate.BASE,
        "official_branch": "rc/p0d-s1-kids-rc01",
        "requires_fresh_official_head_and_authenticated_B220_CAS": True,
        "candidate_only": True,
        "formal_rc_modified": False,
        "p0_playable_loop_910_priority": True,
        "art_gate": "NO_GO",
        "studio_solo": "NOT_TESTED",
        "studio_two_client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "human_art": "NOT_TESTED",
        "kid_fun": "NOT_TESTED",
        "owner_accepted": False,
        "selected_source_count": 69,
        "changed_selected_routes": 6,
        "unchanged_selected_routes": 63,
        "source_only": rows(before, after, classes),
    }


def build(candidate: Path, output: Path) -> None:
    gate.verify_candidate(candidate)
    formal_receipt, before = gate.verify_formal(candidate / gate.OFF)
    after = gate.data_map(candidate)
    manifest = expected_manifest(before, after, formal_receipt["source_classes"])
    gate.demand(not output.exists(), "B220_OUTPUT_EXISTS")
    output.mkdir(parents=True)
    for item in manifest["source_only"]:
        route = item["selected_route"]
        raw = after[route]
        dest = output / item["artifact_path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        gate.demand(gate.digest(dest.read_bytes()) == item["candidate_sha256"],
                    "B220_WRITTEN_BYTES")
    (output / BUNDLE_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    check(candidate, output)
    print("GQ470_ART6_B220_6_SOURCE_BYTES_ONLY_PACKAGE_PASS")


def check(candidate: Path, output: Path) -> None:
    gate.verify_candidate(candidate)
    formal_receipt, before = gate.verify_formal(candidate / gate.OFF)
    after = gate.data_map(candidate)
    expected = expected_manifest(before, after, formal_receipt["source_classes"])
    supplied = json.loads((output / BUNDLE_NAME).read_text(encoding="utf-8"))
    gate.demand(supplied == expected, "B220_MANIFEST_DRIFT")
    expected_names = {BUNDLE_NAME} | {x["artifact_path"] for x in expected["source_only"]}
    found = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    gate.demand(found == expected_names, "B220_EXTRA_OR_MISSING_FILE")
    gate.demand(not any(p.is_symlink() for p in output.rglob("*")),
                "B220_SYMLINK")
    for item in expected["source_only"]:
        actual = (output / item["artifact_path"]).read_bytes()
        gate.demand(actual == after[item["selected_route"]] and
                    gate.digest(actual) == item["candidate_sha256"],
                    "B220_SELECTED_BYTES_MISMATCH")


def self_test() -> None:
    original = {s.target: b"before-" + str(s.pr).encode() for s in gate.SLICES}
    for n in range(63):
        original["UNCHANGED_" + str(n)] = b"same"
    after = dict(original)
    for s in gate.SLICES:
        after[s.target] = b"after-" + str(s.pr).encode()
    classes = {route: "ModuleScript" for route in original}
    classes[gate.SLICES[1].target] = "LocalScript"
    good = expected_manifest(original, after, classes)
    gate.demand(len(good["source_only"]) == 6 and
                good["changed_selected_routes"] == 6, "B220_POSITIVE")
    for bad_before, bad_after, bad_classes in (
        (original, dict(after, UNCHANGED_0=b"tampered"), classes),
        (original, dict(after, **{gate.SLICES[0].target: original[gate.SLICES[0].target]}), classes),
        (original, after, {**classes, gate.SLICES[1].target: "BadClass"}),
        (original, after, {key: value for key, value in classes.items() if key != "UNCHANGED_0"}),
    ):
        try:
            expected_manifest(bad_before, bad_after, bad_classes)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("RED_B220_BAD_BUNDLE_ACCEPTED")
    print("GQ470_ART6_B220_4_NEGATIVE_ADMISSION_TESTS_PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        gate.demand(args.candidate is not None and args.out is not None,
                    "B220_MISSING_INPUT")
        if args.check:
            check(args.candidate, args.out)
        else:
            build(args.candidate, args.out)
