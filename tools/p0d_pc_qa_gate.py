#!/usr/bin/env python3
"""Fail-closed, read-only checker for OWNER PC Studio QA evidence.

This validates LOCAL FILE HASHES and reported scenario statuses, not gameplay,
Studio execution, PC identity, or whether a human actually performed a test.
Never starts Windows Codex/Roblox Studio, never decrypts, never writes source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

SCHEMA = "P0D_PC_LOCAL_QA_EVIDENCE_V1"
WORK_ID = "p0d-siege-v19"
GAME_ID = "TRAP_RAIDERS"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CHECKS = (
    "v39_saved_place_2client",
    "v39_reward_no_double",
    "v39_spoof_remote_rejected",
    "v39_result_ui_mobile_layout",
    "v39_same_account_reconnect",
    "v37_bell_real_listening",
    "physical_mobile_play",
    "studio_exit_owned_pids",
)
CRITICAL = (
    "v39_saved_place_2client",
    "v39_reward_no_double",
    "v39_spoof_remote_rejected",
)
RELEASE_CHECKS = CHECKS
STATUSES = {"PASS", "FAIL", "NOT_TESTED", "BLOCKED"}
MAX_JSON_BYTES = 120_000
MAX_EVIDENCE_BYTES = 3_000_000
MAX_BINARY_BYTES = 200_000_000


class QAError(ValueError):
    """A blockable validation problem."""


def strict_json(raw: bytes):
    def no_duplicate(pairs):
        output = {}
        for key, value in pairs:
            if key in output:
                raise QAError("DUPLICATE_JSON_KEY")
            output[key] = value
        return output
    try:
        return json.loads(raw, object_pairs_hook=no_duplicate)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise QAError("INVALID_JSON") from exc


def hash_valid(value):
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def safe_relative(value: str):
    if not isinstance(value, str) or not value or len(value) > 180:
        raise QAError("UNSAFE_RELATIVE_PATH")
    if "\\" in value or "%" in value or ":" in value or "//" in value:
        raise QAError("UNSAFE_RELATIVE_PATH")
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", seg) and seg not in (".", "..") for seg in value.split("/")):
        raise QAError("UNSAFE_RELATIVE_PATH")
    return value


def resolve_beneath(workspace: Path, relative: str):
    safe_relative(relative)
    if workspace.is_symlink() or not workspace.is_dir():
        raise QAError("UNSAFE_WORKSPACE")
    current = workspace
    for segment in relative.split("/"):
        current = current / segment
        if current.is_symlink():
            raise QAError("SYMLINK_REJECTED")
    # Resolve and check root containment even if the filesystem has unusual aliases.
    root_real = workspace.resolve(strict=True)
    candidate_real = current.resolve(strict=True)
    if not candidate_real.is_relative_to(root_real) or not candidate_real.is_file():
        raise QAError("PATH_OUTSIDE_WORKSPACE")
    return candidate_real


def hash_file(path: Path, max_bytes: int):
    if path.stat().st_size > max_bytes:
        raise QAError("FILE_TOO_LARGE")
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(131072):
            h.update(chunk)
    return h.hexdigest()


def require_mapping(value, label):
    if not isinstance(value, dict):
        raise QAError(label)
    return value


def validate(workspace: Path, report: dict):
    """Returns conservative inspection result. No file or process changes."""
    require_mapping(report, "EVIDENCE_NOT_OBJECT")
    if report.get("schema") != SCHEMA or report.get("game_id") != GAME_ID or report.get("work_id") != WORK_ID:
        raise QAError("WRONG_SCHEMA_OR_GAME")
    if not isinstance(report.get("snapshot_id"), str) or not re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", report["snapshot_id"]):
        raise QAError("BAD_SNAPSHOT_ID")
    saved = require_mapping(report.get("files"), "FILES_REQUIRED")
    if set(saved) != {"saved_place", "cumulative_zip"}:
        raise QAError("MISSING_SNAPSHOT_FILE")
    file_hashes = {}
    for kind in ("saved_place", "cumulative_zip"):
        spec = require_mapping(saved[kind], "INVALID_FILE_RECORD")
        if set(spec) != {"path", "sha256"} or not hash_valid(spec["sha256"]):
            raise QAError("BAD_SNAPSHOT_SHA")
        path = resolve_beneath(workspace, spec["path"])
        real = hash_file(path, MAX_BINARY_BYTES)
        if real != spec["sha256"]:
            raise QAError("SNAPSHOT_SHA_MISMATCH:" + kind)
        file_hashes[kind] = real

    checks = require_mapping(report.get("checks"), "CHECKS_REQUIRED")
    if set(checks) != set(CHECKS):
        raise QAError("WRONG_CHECK_SET")
    result_checks = {}
    for label in CHECKS:
        val = require_mapping(checks[label], "INVALID_CHECK:" + label)
        status = val.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            raise QAError("BAD_CHECK_STATUS:" + label)
        binding = val.get("tested_place_sha256")
        if not hash_valid(binding) or binding != file_hashes["saved_place"]:
            raise QAError("STALE_QA_PLACE_BINDING:" + label)
        evidence_keys = {"evidence_path", "evidence_sha256"}
        if status in ("PASS", "FAIL"):
            if not evidence_keys.issubset(val) or not hash_valid(val["evidence_sha256"]):
                raise QAError("MISSING_TEST_LOG:" + label)
            p = resolve_beneath(workspace, val["evidence_path"])
            if p.suffix.lower() not in (".txt", ".json", ".log"):
                raise QAError("UNSUPPORTED_LOG_FILE:" + label)
            if hash_file(p, MAX_EVIDENCE_BYTES) != val["evidence_sha256"]:
                raise QAError("TEST_LOG_SHA_MISMATCH:" + label)
        elif evidence_keys.intersection(val):
            raise QAError("UNVERIFIED_LOG_ATTACHED_TO_UNTESTED:" + label)
        result_checks[label] = status

    reasons = [label + ":FAIL" for label, status in result_checks.items() if status == "FAIL"]
    missing = [label for label in CRITICAL if result_checks[label] != "PASS"]
    unverified = [label for label in RELEASE_CHECKS if result_checks[label] != "PASS"]
    if reasons:
        gate = "STOP_FIX_CRITICAL_OR_OTHER_FAILURE"
    elif missing:
        gate = "WAIT_FOR_CRITICAL_QA"
    else:
        gate = "OWNER_REVIEW_ONLY_NO_AUTO_STUDIO"
    return {
        "schema": "P0D_PC_QA_GATE_RESULT_V1",
        "snapshot_id": report["snapshot_id"],
        "local_file_hashes_verified": 2,
        "local_log_hashes_verified": sum(status in ("PASS", "FAIL") for status in result_checks.values()),
        "qa_statuses_are_PC_REPORTED_not_independently_observed": True,
        "observed_checks": result_checks,
        "v43a_review_gate": gate,
        "release_gate": "REVIEW_ONLY_UNTIL_ALL_CHECKS_AND_OWNER_APPROVAL" if not unverified else "HOLD_NOT_FULLY_TESTED",
        "remaining_release_checks": unverified,
        "failure_reasons": reasons,
        "next_owner_action": "Manual review of original QA logs + current PC SHA; no automatic restore, merge, or publish",
        "disclaimer": "Hash match proves file consistency only. This tool cannot prove Studio tests were run.",
    }


def load_and_check(workspace: Path, relative_evidence: str):
    path = resolve_beneath(workspace, relative_evidence)
    if path.stat().st_size > MAX_JSON_BYTES:
        raise QAError("EVIDENCE_JSON_TOO_LARGE")
    return validate(workspace, strict_json(path.read_bytes()))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, required=True, help="private trusted PC snapshot directory")
    p.add_argument("--evidence", required=True, help="evidence JSON relative to --workspace")
    p.add_argument("--output", type=Path, help="optional new JSON output; refuses overwrite")
    args = p.parse_args(argv)
    try:
        out = load_and_check(args.workspace, args.evidence)
        encoded = (json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if args.output:
            if args.output.is_symlink():
                raise QAError("OUTPUT_SYMLINK_REJECTED")
            with args.output.open("xb") as f:
                f.write(encoded)
        else:
            sys.stdout.buffer.write(encoded)
        return 0 if out["v43a_review_gate"] == "OWNER_REVIEW_ONLY_NO_AUTO_STUDIO" else 2
    except (QAError, OSError, ValueError, TypeError) as exc:
        print("PC_QA_GATE_BLOCKED:" + str(exc).split("\n")[0][:140], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
