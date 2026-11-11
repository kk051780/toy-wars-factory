#!/usr/bin/env python3
"""Small fail-closed PUBLIC_SOURCE_V1 manifest verifier; no network and no extraction."""
import argparse
import hashlib
import json
import re
from pathlib import Path

FORMAT = "P0D_PUBLIC_SOURCE_V1"
PACKET = "P0D-S1-LOBBY-TEAM-DEADLOCK-RECOVERY-20261111-01"
ROOT_KEYS = {"format", "game_id", "work_id", "packet_id", "public_source_allowed", "files"}
ENTRY_KEYS = {"path", "bytes", "sha256"}


def check(root: Path):
    raw = (root / "BUILD_MANIFEST.json").read_bytes()
    def unique_pairs(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError(f"DUPLICATE_KEY {k}")
            d[k] = v
        return d
    doc = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs,
                     parse_constant=lambda k: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))
    if type(doc) is not dict or set(doc) != ROOT_KEYS:
        raise ValueError("MANIFEST_SCHEMA")
    if (doc["format"] != FORMAT or doc["game_id"] != "TRAP_RAIDERS"
            or doc["work_id"] != "p0d-siege-v19" or doc["packet_id"] != PACKET
            or doc["public_source_allowed"] is not True):
        raise ValueError("IDENTITY_MISMATCH")
    if not isinstance(doc["files"], list) or not doc["files"]:
        raise ValueError("EMPTY_FILES")
    names = set()
    for entry in doc["files"]:
        if type(entry) is not dict or set(entry) != ENTRY_KEYS:
            raise ValueError("INVALID_FILE_ENTRY")
        rel = entry["path"]
        if (not isinstance(rel, str) or not re.fullmatch(r"[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)*", rel)
                or any(p in (".", "..") for p in rel.split("/")) or rel == "BUILD_MANIFEST.json"
                or rel in names):
            raise ValueError("UNSAFE_OR_DUPLICATE_PATH")
        names.add(rel)
        target = root / rel
        if not target.is_file() or target.is_symlink():
            raise ValueError("MISSING_OR_SYMLINK")
        data = target.read_bytes()
        if (type(entry["bytes"]) is not int or entry["bytes"] != len(data)
                or type(entry["sha256"]) is not str
                or hashlib.sha256(data).hexdigest() != entry["sha256"]):
            raise ValueError("HASH_OR_SIZE_MISMATCH")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    if actual != names | {"BUILD_MANIFEST.json"}:
        raise ValueError(f"EXTRA_OR_MISSING {sorted(actual ^ (names | {'BUILD_MANIFEST.json'}))}")
    return {"source_files": len(names), "total_files": len(names) + 1,
            "manifest_sha256": hashlib.sha256(raw).hexdigest()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    print(check(ap.parse_args().root))
