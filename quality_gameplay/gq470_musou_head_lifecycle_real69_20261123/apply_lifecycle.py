#!/usr/bin/env python3
"""Exact, reversible one-source Controller replacement; no network or authority.

The immutable base supplies inverse bytes. A source lock pins both endpoints;
neither an already-applied file nor a different current Controller is accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

SCHEMA = "GQ824_AURA_LIFECYCLE_REAL69_V1"
BASE_HEAD = "93a1147561a531610ac1609ebc68cc0ecf546623"
CONTROLLER = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraController.client.luau"
AURA = "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraClient.luau"
BASE_ID = {"bytes": 1881, "sha256": "13495f0c816f88a78f62e8c40ec5a79c7140c2057b33037695d6073e527768c9"}
AURA_ID = {"bytes": 6205, "sha256": "b2c279371a8fd986b929883290aae58ed9acdafb7cd48f878eae3785e4acccab"}


def identity(data: bytes) -> dict:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def check_identity(data: bytes, expected: dict, label: str) -> dict:
    wanted = {key: expected.get(key) for key in ("bytes", "sha256")}
    actual = identity(data)
    if actual != wanted:
        raise ValueError(f"{label}: identity mismatch; actual={actual}, expected={wanted}")
    return actual


def relative_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("Expected a nonempty portable relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError(f"Unsafe relative path: {value}")
    return path


def rooted(root: Path, relative: str) -> Path:
    base = root.resolve()
    parts = relative_path(relative).parts
    path = base.joinpath(*parts)
    current = base
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink is not an exact packet file: {current}")
    if not path.resolve().is_relative_to(base):
        raise ValueError("Path escaped its root")
    return path


def load_lock(path: Path) -> dict:
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("schema") != SCHEMA or lock.get("base_rc_head") != BASE_HEAD:
        raise ValueError("Unexpected schema or immutable H93 source base")
    if lock.get("controller", {}).get("path") != CONTROLLER:
        raise ValueError("Controller route differs from this bounded repair")
    if lock["controller"].get("before") != BASE_ID:
        raise ValueError("Original Controller pin was changed")
    if lock.get("aura", {}).get("path") != AURA:
        raise ValueError("Aura route differs from the unchanged original module")
    if {key: lock["aura"].get(key) for key in AURA_ID} != AURA_ID:
        raise ValueError("Original AuraClient pin was changed")
    candidate = lock["controller"].get("candidate", {})
    if candidate.get("file") != "MusouAuraController.client.luau":
        raise ValueError("Candidate must be the adjacent one-source packet file")
    if (type(candidate.get("bytes")) is not int or candidate["bytes"] <= 0
            or not re.fullmatch(r"[0-9a-f]{64}", candidate.get("sha256", ""))):
        raise ValueError("Invalid candidate identity")
    if {key: candidate[key] for key in BASE_ID} == BASE_ID:
        raise ValueError("Candidate cannot be identical to the unresolved baseline")
    if lock.get("selected_sources") != 69 or lock.get("instance_count") != 75:
        raise ValueError("This packet requires exact current 69 sources and 75 instances")
    if lock.get("class_counts") != {"LocalScript": 10, "ModuleScript": 47, "Script": 12}:
        raise ValueError("Selected source class counts changed")
    return lock


def forward(original: bytes, candidate: bytes, lock: dict) -> bytes:
    check_identity(original, BASE_ID, "forward original")
    check_identity(original, lock["controller"]["before"], "locked original")
    check_identity(candidate, lock["controller"]["candidate"], "forward candidate")
    return candidate


def inverse(current: bytes, immutable_original: bytes, lock: dict) -> bytes:
    check_identity(current, lock["controller"]["candidate"], "inverse current")
    check_identity(immutable_original, BASE_ID, "immutable inverse original")
    check_identity(immutable_original, lock["controller"]["before"], "locked inverse original")
    return immutable_original


def apply_root(root: Path, base_artifact: Path, packet: Path, lock: dict,
               *, revert: bool = False) -> dict:
    mutable_root, immutable_root = root.resolve(), base_artifact.resolve()
    if (mutable_root == immutable_root or mutable_root.is_relative_to(immutable_root)
            or immutable_root.is_relative_to(mutable_root)):
        raise ValueError("Mutable root and immutable artifact must be disjoint")
    if not mutable_root.is_dir() or not immutable_root.is_dir():
        raise ValueError("Both roots must already exist")
    original_path = rooted(immutable_root, CONTROLLER)
    target_path = rooted(mutable_root, CONTROLLER)
    original = original_path.read_bytes()
    check_identity(original, BASE_ID, "immutable original Controller")
    current = target_path.read_bytes()
    check_identity(rooted(immutable_root, AURA).read_bytes(), AURA_ID, "immutable AuraClient")
    check_identity(rooted(mutable_root, AURA).read_bytes(), AURA_ID, "derived AuraClient")
    candidate_path = rooted(packet, lock["controller"]["candidate"]["file"])
    candidate = candidate_path.read_bytes()
    check_identity(candidate, lock["controller"]["candidate"], "packet candidate")
    changed = inverse(current, original, lock) if revert else forward(current, candidate, lock)
    target_path.write_bytes(changed)
    check_identity(target_path.read_bytes(), identity(changed), "written Controller")
    if original_path.read_bytes() != original or candidate_path.read_bytes() != candidate:
        raise ValueError("Read-only transform inputs drifted")
    return {"direction": "INVERSE" if revert else "FORWARD", "relative_path": CONTROLLER,
            "before": identity(current), "after": identity(changed),
            "byte_delta": len(changed) - len(current), "immutable_original": identity(original),
            "only_write_path": str(target_path), "inverse_uses_immutable_base": revert}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--base-artifact", type=Path, required=True)
    parser.add_argument("--inverse", action="store_true")
    parser.add_argument("--lock", type=Path, default=Path(__file__).with_name("source_lock.json"))
    args = parser.parse_args()
    lock = load_lock(args.lock)
    receipt = apply_root(args.root, args.base_artifact, args.lock.resolve().parent, lock, revert=args.inverse)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"FAIL_CLOSED: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
