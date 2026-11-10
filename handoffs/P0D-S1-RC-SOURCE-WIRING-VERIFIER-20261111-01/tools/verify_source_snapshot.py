#!/usr/bin/env python3
"""Pre-RC immutable source snapshot audit for TRAP_RAIDERS S1.

Read only: verifies actual source bytes against PUBLIC_SOURCE_V1 package manifest,
Rojo source placements and status honesty. Never a completed game/Studio PASS.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from verify_rc_wiring import QAError, all_files, path_ok, read_json, sha, test_project, HASH

ALLOWED_ROOTS = ("src/", "tests/", "docs/")
CONTROL_FILES = {"BUILD_MANIFEST.json", "README.md", "default.project.json"}
MAX_MANIFEST_FILES = 5000


def audit_source(root: Path) -> dict:
    files = all_files(root)
    manifest_path = "BUILD_MANIFEST.json"
    if manifest_path not in files:
        raise QAError("BUILD_MANIFEST_NOT_FOUND")
    manifest = read_json(files[manifest_path])
    if manifest.get("format") != "P0D_PUBLIC_SOURCE_V1":
        raise QAError("UNSUPPORTED_MANIFEST_FORMAT")
    if manifest.get("game_id") != "TRAP_RAIDERS" or manifest.get("work_id") != "p0d-siege-v19":
        raise QAError("WRONG_GAME_ID")
    if manifest.get("public_source_allowed") is not True:
        raise QAError("SOURCE_PERMISSION_NOT_CONFIRMED")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries or len(entries) > MAX_MANIFEST_FILES:
        raise QAError("INVALID_MANIFEST_ENTRY_LIST")
    recorded = set()
    for row in entries:
        if not isinstance(row, dict):
            raise QAError("INVALID_MANIFEST_ENTRY")
        rel = path_ok(row.get("path"))
        if rel in recorded:
            raise QAError("DUPLICATE_MANIFEST_ENTRY:" + rel)
        recorded.add(rel)
        if not (rel in CONTROL_FILES - {manifest_path} or rel.startswith(ALLOWED_ROOTS)):
            raise QAError("UNEXPECTED_MANIFEST_PATH:" + rel)
        if rel == manifest_path:
            raise QAError("SELF_HASHING_MANIFEST_FORBIDDEN")
        if rel not in files:
            raise QAError("MISSING_MANIFESTED_FILE:" + rel)
        h, size = row.get("sha256"), row.get("size")
        if not isinstance(h, str) or not HASH.fullmatch(h) or type(size) is not int or size < 0:
            raise QAError("INVALID_SIZE_OR_DIGEST:" + rel)
        data = files[rel].read_bytes()
        if len(data) != size or sha(data) != h:
            raise QAError("FILE_CONTENT_DIGEST_MISMATCH:" + rel)
    unexpected = set(files) - recorded - {manifest_path}
    if unexpected:
        raise QAError("UNTRACKED_SOURCE_OR_FILE:" + ",".join(sorted(unexpected)[:3]))
    if "default.project.json" not in recorded:
        raise QAError("MISSING_ROJO_PROJECT_MAPPING")
    paths = test_project(root, files, recorded)
    if "docs/RELEASE_STATUS.json" not in recorded:
        raise QAError("MISSING_SOURCE_STATUS")
    status = read_json(files["docs/RELEASE_STATUS.json"])
    if status.get("game_id") != "TRAP_RAIDERS" or status.get("work_id") != "p0d-siege-v19":
        raise QAError("STATUS_WRONG_GAME")
    if status.get("studio_status") != "NOT_TESTED" or status.get("game_ready") is not False:
        raise QAError("FALSE_STUDIO_OR_GAME_READY_CLAIM")
    if status.get("release_approved") is not False:
        raise QAError("FALSE_RELEASE_APPROVAL")
    if "CHAT_RC_RECEIPT.json" in files:
        raise QAError("SNAPSHOT_WITH_UNVERIFIED_RC_RECEIPT_USE_FINAL_RC_VERIFIER")
    if not any(p.endswith(".server.luau") for p in recorded):
        raise QAError("NO_SERVER_BOOTSTRAP")
    if not any(p.endswith(".client.luau") for p in recorded):
        raise QAError("NO_CLIENT_BOOTSTRAP")
    # This is structural only. No source-based proof of safe event authority.
    return {
        "format": "P0D_S1_INDEPENDENT_SOURCE_SNAPSHOT_QA_V1",
        "game_id": "TRAP_RAIDERS",
        "work_id": "p0d-siege-v19",
        "release_id": status.get("release_id", "UNKNOWN"),
        "status": "PASS_SOURCE_SNAPSHOT_ONLY__NOT_FINAL_RC",
        "source_files_sha256_verified": len(recorded),
        "rojo_project_mappings_verified": paths,
        "actual_gameplay_correctness": "NOT_TESTED",
        "actual_rc_receipt": "NOT_AVAILABLE",
        "engine_luau_parser": "NOT_TESTED",
        "studio_2client_mobile": "NOT_TESTED",
        "publish_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read-only pre-release S1 source snapshot verifier")
    p.add_argument("--source-root", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        report = audit_source(args.source_root)
        code = 0
    except (QAError, OSError, TypeError, ValueError, UnicodeError) as exc:
        report = {
            "format": "P0D_S1_INDEPENDENT_SOURCE_SNAPSHOT_QA_V1",
            "status": "FAIL_SOURCE_SNAPSHOT",
            "defect": str(exc),
            "actual_gameplay_correctness": "NOT_TESTED",
            "studio_2client_mobile": "NOT_TESTED",
            "publish_approved": False,
        }
        code = 2
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
