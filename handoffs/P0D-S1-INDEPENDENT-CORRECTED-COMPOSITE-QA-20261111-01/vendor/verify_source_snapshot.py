#!/usr/bin/env python3
"""Pre-RC immutable source snapshot audit for TRAP_RAIDERS S1.

Read only: verifies actual source bytes against PUBLIC_SOURCE_V1 package manifest,
Rojo source placements and status honesty. Never a completed game/Studio PASS.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

from verify_rc_wiring import QAError, all_files, path_ok, read_json, sha, test_project, HASH

ALLOWED_ROOTS = ("src/", "tests/", "docs/")
CONTROL_FILES = {"BUILD_MANIFEST.json", "README.md", "default.project.json"}
# Exact public-source V1 handoff constraints, independent of author's manifest.
MANIFEST_KEYS = frozenset({"format", "game_id", "work_id", "packet_id", "public_source_allowed", "files"})
ENTRY_KEYS = frozenset({"path", "sha256", "size"})
PACKET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{4,100}$")
MAX_MANIFEST_FILES = 250
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".luau", ".lua", ".py", ".md", ".json", ".txt", ".csv", ".toml", ".yml", ".yaml"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(rb"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b"),
    re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
)


def validate_public_manifest_header(raw: bytes, manifest: dict) -> None:
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        raise QAError("PUBLIC_SOURCE_MANIFEST_SCHEMA_MISMATCH")
    if not isinstance(manifest["packet_id"], str) or not PACKET.fullmatch(manifest["packet_id"]):
        raise QAError("INVALID_PUBLIC_SOURCE_PACKET_ID")
    canonical = (json.dumps(manifest, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if canonical != raw:
        raise QAError("NONCANONICAL_PUBLIC_SOURCE_MANIFEST")


def validate_file_name(rel: str) -> None:
    if any(segment.startswith(".") for segment in rel.split("/")):
        raise QAError("HIDDEN_PUBLIC_SOURCE_PATH:" + rel)
    if Path(rel).suffix.lower() not in ALLOWED_SUFFIXES:
        raise QAError("NON_SOURCE_PUBLIC_EXTENSION:" + rel)
    if rel.rsplit("/", 1)[-1].lower() in {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}:
        raise QAError("CREDENTIAL_LIKE_FILE_NAME:" + rel)



def audit_source(root: Path) -> dict:
    files = all_files(root)
    manifest_path = "BUILD_MANIFEST.json"
    if manifest_path not in files:
        raise QAError("BUILD_MANIFEST_NOT_FOUND")
    manifest = read_json(files[manifest_path])
    validate_public_manifest_header(files[manifest_path].read_bytes(), manifest)
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
    total_size = 0
    previous_rel = ""
    for row in entries:
        if not isinstance(row, dict) or set(row) != ENTRY_KEYS:
            raise QAError("INVALID_MANIFEST_ENTRY_SCHEMA")
        rel = path_ok(row.get("path"))
        validate_file_name(rel)
        if previous_rel and rel < previous_rel:
            raise QAError("UNSORTED_PUBLIC_SOURCE_MANIFEST")
        previous_rel = rel
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
        if size > MAX_FILE_BYTES:
            raise QAError("PUBLIC_FILE_TOO_LARGE:" + rel)
        total_size += size
        if total_size > MAX_TOTAL_BYTES:
            raise QAError("PUBLIC_SOURCE_TOO_LARGE")
        data = files[rel].read_bytes()
        if len(data) != size or sha(data) != h:
            raise QAError("FILE_CONTENT_DIGEST_MISMATCH:" + rel)
        try:
            data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as err:
            raise QAError("PUBLIC_FILE_NOT_UTF8:" + rel) from err
        if any(pattern.search(data) for pattern in SECRET_PATTERNS):
            raise QAError("PUBLIC_SOURCE_SECRET_PATTERN:" + rel)
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
