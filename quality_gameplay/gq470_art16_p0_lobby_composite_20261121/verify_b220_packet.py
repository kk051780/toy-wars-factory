#!/usr/bin/env python3
"""Independent strict validator of the GQ470 ART16 + P0 B220 17-source handoff.

Reject stale parent heads, forged formal adoption, unknown routes, ambiguous
ownership, altered bytes, extra payloads, unsafe paths or unsupported green claims.
A successful audit is not formal RC, Studio, ART, mobile, or owner acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from compose_art16_p0 import (
    ART16_HEAD, P0_HEAD, FORMAL, HOST, PACKET, OFF, RECEIPT,
    PROJECT, PLACE, NOTE, sha, selected, exact_formal, snapshot, verify, need,
)

SCHEMA = "GQ470_ART16_P0_17_ROUTE_B220_SOURCE_ONLY_V1"
REPORT = "GQ470_ART16_P0_B220_TAMPER_GATE.json"


def check(root: Path, packet_dir: Path | None = None) -> dict:
    """Only original 17 source blobs plus exact expected signed metadata are accepted."""
    root = root.resolve()
    verify(root)
    packet = (packet_dir or (root / PACKET)).resolve()
    need(packet.is_dir() and (packet / "SOURCE_SELECT_MANIFEST.json").is_file(),
         "B_PACKET_MISSING")
    data = json.loads((packet / "SOURCE_SELECT_MANIFEST.json").read_text())
    _, original, old_classes = exact_formal(root / OFF)
    newer, new_classes = snapshot(root)
    rec = json.loads((root / RECEIPT).read_text())
    authors = rec[NOTE]["authors"]
    chosen = set(authors["art16_970"]) | set(authors["early_lobby_980"])
    rows = data.get("source_only")
    need(isinstance(rows, list) and len(rows) == 17, "B_ROWS_WRONG_COUNT")
    need(data.get("schema") == SCHEMA and
         data.get("formal_head") == FORMAL and
         data.get("parent_art16_head") == ART16_HEAD and
         data.get("parent_p0_head") == P0_HEAD and
         data.get("selected_count") == 17 and
         data.get("original_untouched") == 52 and
         data.get("original_selected_count") == 69 and
         data.get("candidate_private_place_sha256") == rec.get("private_place_sha256") and
         data.get("candidate_private_place_bytes") == rec.get("private_place_bytes") and
         data.get("formal_adopted") is False and
         data.get("owner_accepted") is False and
         data.get("requires_writer_220_fresh_nonforce_cas") is True and
         data.get("quality_overlay") == rec[NOTE].get("quality_overlay") and
         data.get("studio") == "NOT_TESTED" and
         data.get("android") == "NOT_TESTED" and
         data.get("art_images") == "0/32" and
         data.get("art_gate") == "ART_NO_GO",
         "B_METADATA_OR_FAKE_GO")
    got: set[str] = set()
    expected_files = {Path("SOURCE_SELECT_MANIFEST.json")}
    for row in rows:
        need(isinstance(row, dict) and set(row) ==
             {"route", "class", "path", "old_sha256", "new_sha256", "source"},
             "B_ROW_SCHEMA_OR_EXTRA")
        route = row["route"]
        need(isinstance(route, str) and route in chosen and route not in got,
             "B_UNOWNED_OR_DUPLICATE_SOURCE")
        got.add(route)
        expected_rel = Path("selected_sources") / (route + ".luau")
        # Reject alternate alias/path traversal even when the bytes happen to match.
        need(row["path"] == expected_rel.as_posix() and
             row["class"] == old_classes[route] == new_classes[route] and
             row["source"] == (980 if route == HOST else 970) and
             row["old_sha256"] == sha(original[route]) and
             row["new_sha256"] == sha(newer[route]) and
             original[route] != newer[route],
             "B_SOURCE_LOCK_OR_WRITER_OWNER")
        candidate = (packet / expected_rel).resolve()
        need(candidate.is_relative_to(packet) and candidate.is_file() and
             not candidate.is_symlink() and
             candidate.read_bytes() == newer[route],
             "B_SOURCE_MISSING_OR_BYTES_CHANGED")
        expected_files.add(expected_rel)
    need(got == chosen, "B_UNOWNED_ROUTE_OR_OMISSION")
    actual_files = {p.relative_to(packet) for p in packet.rglob("*") if p.is_file()}
    need(actual_files == expected_files and len(actual_files) == 18,
         "B_UNEXPECTED_EXTRA_OR_MISSING_FILE")
    return {
        "schema": "GQ470_ART16_P0_B220_INDEPENDENT_PACKET_AUDIT_V1",
        "validated_routes": 17, "unique_writer_970_art_routes": 16,
        "unique_writer_980_p0_host_routes": 1,
        "remaining_original_byte_exact": 52,
        "candidate_place_bytes": rec["private_place_bytes"],
        "candidate_place_sha256": rec["private_place_sha256"],
        "source_pack_status": "PASS_SOURCE_ONLY",
        "formal_rc_adopted": False, "studio_solo": "NOT_TESTED",
        "studio_2client": "NOT_TESTED", "android_15min": "NOT_TESTED",
        "art_images": "0/32", "art_gate": "ART_NO_GO",
        "owner_accepted": False,
    }


def negatives(root: Path) -> dict:
    """Mutations are run against actual generated B packet, not synthetic screenshots."""
    check(root)
    mutations: list[tuple[str, str, object]] = [
        ("forged_formal_go", "formal_adopted", True),
        ("forged_owner_go", "owner_accepted", True),
        ("forged_art_go", "art_gate", "ART_GO"),
        ("forged_art_images", "art_images", "32/32"),
        ("forged_studio", "studio", "PASS"),
        ("forged_parent_art16", "parent_art16_head", "f" * 40),
        ("forged_parent_p0", "parent_p0_head", "f" * 40),
        ("forged_formal_head", "formal_head", "f" * 40),
        ("false_place_sha", "candidate_private_place_sha256", "0" * 64),
        ("false_original_count", "original_untouched", 51),
        ("false_selected_count", "selected_count", 16),
        ("no_writer_cas_required", "requires_writer_220_fresh_nonforce_cas", False),
        ("forged_neutral_parent_sha", "quality_overlay.original_art16_swarm_sha256", "0" * 64),
        ("forged_neutral_source_sha", "quality_overlay.patched_swarm_sha256", "0" * 64),
        ("forged_neutral_studio_pass", "quality_overlay.studio", "PASS"),
        ("forged_neutral_formal_adoption", "quality_overlay.formal_adopted", True),
        ("false_source_owner", "source_only[0].source", 999),
        ("false_source_class", "source_only[0].class", "Folder"),
        ("forged_new_sha", "source_only[0].new_sha256", "0" * 64),
        ("forged_old_sha", "source_only[0].old_sha256", "0" * 64),
        ("unsafe_path", "source_only[0].path", "../../escape.luau"),
        ("duplicate_route", "source_only[1].route", "COPY_ROW0_ROUTE"),
        ("missing_row", "source_only", "REMOVE_LAST"),
        ("unknown_row", "source_only[0].route", "OtherService/Nonexistent"),
        ("extra_row_field", "source_only[0].author_ok", True),
    ]
    accepted: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gq470-art16-p0-b220-") as tmp:
        temp = Path(tmp)
        source = root / PACKET
        for index, (tag, field, value) in enumerate(mutations):
            candidate = temp / f"mutation_{index}"
            shutil.copytree(source, candidate)
            manifest = candidate / "SOURCE_SELECT_MANIFEST.json"
            data = json.loads(manifest.read_text())
            if field.startswith("source_only["):
                offset = int(field.split("[")[1].split("]")[0])
                member = field.split("].")[1]
                if field == "source_only[1].route" and value == "COPY_ROW0_ROUTE":
                    value = data["source_only"][0]["route"]
                data["source_only"][offset][member] = value
            elif field == "source_only" and value == "REMOVE_LAST":
                data["source_only"].pop()
            elif field.startswith("quality_overlay."):
                data["quality_overlay"][field.split(".", 1)[1]] = value
            else:
                data[field] = value
            manifest.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
            try:
                check(root, candidate)
            except ValueError:
                accepted.append(tag)
            else:
                raise AssertionError("B220_TAMPER_ACCEPTED_" + tag)
        for tag in ("alter_content", "missing_blob", "extra_payload"):
            candidate = temp / tag
            shutil.copytree(source, candidate)
            manifest = json.loads((candidate / "SOURCE_SELECT_MANIFEST.json").read_text())
            path = candidate / manifest["source_only"][0]["path"]
            if tag == "alter_content":
                path.write_bytes(path.read_bytes() + b"BAD_AUTHORITY")
            elif tag == "missing_blob":
                path.unlink()
            else:
                (candidate / "UNAUTHORIZED_EXTRA.luau").write_text("return true")
            try:
                check(root, candidate)
            except ValueError:
                accepted.append(tag)
            else:
                raise AssertionError("B220_TAMPER_ACCEPTED_" + tag)
    need(len(accepted) == len(mutations) + 3 == 28, "TAMPER_CASE_COUNT")
    result = check(root)
    result["tamper_cases_tested"] = len(accepted)
    result["tamper_cases_rejected"] = len(accepted)
    result["tamper_names"] = accepted
    result["evidence_scope"] = "SOURCE_ONLY_NO_STUDIO_ART_OR_MOBILE_CLAIM"
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--negatives", action="store_true")
    ap.add_argument("--report", type=Path)
    a = ap.parse_args()
    result = negatives(a.root) if a.negatives else check(a.root)
    if a.report:
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("GQ470_ART16_P0_B220_PACKET_SOURCE_CHECK_PASS",
          result["validated_routes"], result.get("tamper_cases_rejected", 0),
          "ART_NO_GO")
