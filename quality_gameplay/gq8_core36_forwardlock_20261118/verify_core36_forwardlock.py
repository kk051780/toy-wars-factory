#!/usr/bin/env python3
"""Fail-closed source-input lock for the formal Core36 RC companion build.

Allows unrelated future official RC changes without silently changing any input
that the Core36 source composer actually consumes. Does not write RC or source.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

# Exact blobs observed on formal RC f77b4d4393d9e9b19b65566413432a7a9f13962b.
# A B-writer must deliberately re-pin and re-test if a real input ever changes.
INPUT_BLOBS = {
    "rc_fastlane/EGGRUMBLE_V3_CORE36.json": "42d8dd205a520264f945cee943e6921e5e44c87b",
    "rc_fastlane/ACTIVE.json": "34ce2f8fdb67815d62cbba635e1bb1637e6cf496",
    "handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/EGGRUMBLE_LandSeaSkyTraversal.server.luau": "c4ca82218d985914ad98dead565f9f79f5374dcb",
    "quality_gameplay/gq8_lss_real31_20261117/rehydrate_real31.py": "7f9453a101e371f21423b4f0af8bfed0437cf225",
}
ORIGINAL_ADOPTION = {
    "rc_fastlane/EGGRUMBLE_V3_CORE36.json",
    "rc_fastlane/ACTIVE.json",
    ".github/workflows/p0d-rc-eggrumble-v3-core36.yml",
}


class SourceLockViolation(RuntimeError):
    pass


def verify_changed_paths(changed: set[str], observed: dict[str, str]) -> dict:
    """Check adoption provenance and immutable live input hashes.

    Extra changed paths are allowed because parallel B can integrate unrelated
    RC features. Unlike the legacy changed==ORIGINAL_ADOPTION test, this does
    not become permanently RED after the first unrelated legitimate RC commit.
    """
    missing = ORIGINAL_ADOPTION.difference(changed)
    if missing:
        raise SourceLockViolation("RED_ADOPTION_PROVENANCE_MISSING:" + ",".join(sorted(missing)))
    for path, expected in INPUT_BLOBS.items():
        actual = observed.get(path)
        if actual != expected:
            raise SourceLockViolation(
                f"RED_CORE36_REAL_INPUT_DRIFT:{path}:expected={expected}:actual={actual}"
            )
    return {
        "locked_source_inputs": len(INPUT_BLOBS),
        "original_adoption_paths": len(ORIGINAL_ADOPTION),
        "noninput_paths_since_adoption": len(changed - ORIGINAL_ADOPTION),
    }


def hash_checked_out_inputs() -> dict[str, str]:
    observed = {}
    for path in INPUT_BLOBS:
        if not Path(path).is_file():
            raise SourceLockViolation("RED_CORE36_INPUT_MISSING:" + path)
        observed[path] = subprocess.check_output(
            ["git", "hash-object", "--", path], text=True
        ).strip()
    return observed


def verify_compare_response(data: dict) -> dict:
    if data.get("status") not in {"ahead", "identical"}:
        raise SourceLockViolation("RED_CORE36_BASE_ANCESTRY:" + str(data.get("status")))
    files = data.get("files")
    if not isinstance(files, list):
        raise SourceLockViolation("RED_CORE36_COMPARE_FILES_MISSING")
    changed = {x["filename"] for x in files if isinstance(x, dict) and "filename" in x}
    return verify_changed_paths(changed, hash_checked_out_inputs())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compare-json", required=True, type=Path)
    options = parser.parse_args()
    data = json.loads(options.compare_json.read_text(encoding="utf-8"))
    result = verify_compare_response(data)
    print("GQ8_CORE36_FORWARD_INPUT_LOCK_GREEN", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
