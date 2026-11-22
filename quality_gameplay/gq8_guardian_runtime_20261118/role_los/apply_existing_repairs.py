#!/usr/bin/env python3
"""Compose the original Guardian role170 and outgoing-LOS30 repairs exactly."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROLE = HERE.parent / "role_session"
VARIANTS = {
    "baseline": (False, False),
    "role_only": (True, False),
    "los_only": (False, True),
    "combined": (True, True),
}
FROZEN_ROLE_FILES = {"apply_role_snapshot.py", "INPUT_LOCK.json", "case.luau",
                     "fixture_boundary.luau", "run.py", "README.md"}

# Exact original ca1ff proposal, PR796 comment7078362242. Incoming is untouched.
LOS_BEFORE = b'''   ray.FilterDescendantsInstances={exclude,entry.model}
   local hit=workspace:Raycast(at,diff,ray)
'''
LOS_AFTER = b'''   ray.FilterDescendantsInstances={exclude,entry.model}
   ray.RespectCanCollide=true
   local hit=workspace:Raycast(at,diff,ray)
'''


def identity(raw: bytes) -> dict:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def load_lock() -> dict:
    lock = json.loads((HERE / "INPUT_LOCK.json").read_text())
    if lock.get("schema") != "GQ815_EXISTING_ROLE170_LOS30_COMBINED_V1":
        raise ValueError("COMBINED_LOCK_SCHEMA")
    if set(lock["guardian"]["variants"]) != set(VARIANTS):
        raise ValueError("COMBINED_VARIANT_SET")
    if set(lock["frozen_role_package"]) != FROZEN_ROLE_FILES:
        raise ValueError("COMBINED_FROZEN_ROLE_FILE_SET")
    return lock


def load_frozen_role(lock: dict):
    for name, expected in lock["frozen_role_package"].items():
        path = ROLE / name
        if path.is_symlink() or identity(path.read_bytes()) != expected:
            raise ValueError("FROZEN_ROLE_PACKAGE_DRIFT:" + name)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("gq815_frozen_role_adapter", ROLE / "apply_role_snapshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_exact(raw: bytes, before: bytes, after: bytes) -> bytes:
    if raw.count(before) != 1:
        raise ValueError("COMBINED_EXPECT_ONE_EXACT_ANCHOR")
    return raw.replace(before, after, 1)


def transform(raw: bytes, source: str, target: str) -> bytes:
    lock = load_lock()
    if source not in VARIANTS or target not in VARIANTS or source == target:
        raise ValueError("COMBINED_EXPLICIT_DISTINCT_VARIANTS_REQUIRED")
    if identity(raw) != lock["guardian"]["variants"][source]:
        raise ValueError("COMBINED_INPUT_IDENTITY_MISMATCH")
    role = load_frozen_role(lock)
    old_role, old_los = VARIANTS[source]
    new_role, new_los = VARIANTS[target]
    result = raw
    if old_los and not new_los:
        result = replace_exact(result, LOS_AFTER, LOS_BEFORE)
    if old_role and not new_role:
        for before, after in reversed(role.HUNKS):
            result = replace_exact(result, after, before)
    if new_role and not old_role:
        for before, after in role.HUNKS:
            result = replace_exact(result, before, after)
    if new_los and not old_los:
        result = replace_exact(result, LOS_BEFORE, LOS_AFTER)
    if identity(result) != lock["guardian"]["variants"][target]:
        raise ValueError("COMBINED_OUTPUT_IDENTITY_MISMATCH")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--from", dest="source", required=True, choices=VARIANTS)
    parser.add_argument("--to", dest="target", required=True, choices=VARIANTS)
    args = parser.parse_args()
    result = transform(args.input.read_bytes(), args.source, args.target)
    with args.output.open("xb") as output:
        output.write(result)
    print(json.dumps({"from": args.source, "to": args.target, **identity(result)}, sort_keys=True))


if __name__ == "__main__":
    main()
