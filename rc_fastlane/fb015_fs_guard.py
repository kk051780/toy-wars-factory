#!/usr/bin/env python3
"""Fail-closed exact-tree inventory for temporary FB-015 private game builds.

These manifests are NOT authentication against an editor who also controls
the manifests; they detect unexpected files, file modes, empty directories and
symlinks. A separate immutable/external trust root is still needed before
a distributable general-purpose destructive cleanup can be approved.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import json
import os
import tempfile


def strict_inventory(root: Path, exclude: str = "") -> dict[str, str]:
    root = Path(root)
    if root.is_symlink():
        raise RuntimeError("FB015_SYMLINK_DISTRIBUTION_REFUSED")
    rootstat = root.lstat()
    if not stat.S_ISDIR(rootstat.st_mode):
        raise RuntimeError("FB015_EXPECTED_REAL_DIRECTORY")
    entries = {".": f"D:{stat.S_IMODE(rootstat.st_mode):04o}"}
    for path in sorted(root.rglob("*")):
        st = path.lstat()
        rel = path.relative_to(root).as_posix()
        # An excluded self-manifest is not a license for special file types.
        if stat.S_ISLNK(st.st_mode):
            raise RuntimeError("FB015_SYMLINK_ENTRY_REFUSED:" + rel)
        mode = f"{stat.S_IMODE(st.st_mode):04o}"
        if stat.S_ISDIR(st.st_mode):
            entries[rel] = "D:" + mode
        elif stat.S_ISREG(st.st_mode):
            if rel != exclude:
                entries[rel] = "F:" + mode + ":" + hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            raise RuntimeError("FB015_SPECIAL_ENTRY_REFUSED:" + rel)
    return entries

def verify_partial_tree(root: Path, expected: dict[str,str]) -> None:
    """Only known, byte-and-type-identical leftovers can be resumed."""
    remaining=strict_inventory(root)
    if not all(name in expected and identity==expected[name]
               for name, identity in remaining.items()):
        raise RuntimeError("FB015_PARTIAL_DELETE_UNTRUSTED_LEFTOVERS")

def atomic_json(path: Path, payload: dict) -> None:
    """Write external manifest / recovery journal atomically on same fs."""
    fd,name=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf8") as f:
            json.dump(payload,f,sort_keys=True,ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
