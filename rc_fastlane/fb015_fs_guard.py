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


def reject_symlink_ancestors(path: Path) -> None:
    """Inspect the spelling supplied by caller BEFORE pathlib.resolve()."""
    path=Path(os.path.abspath(path))
    for node in (path, *path.parents):
        if node.is_symlink():
            raise RuntimeError("FB015_SYMLINK_PARENT_COMPONENT_REFUSED:" + str(node))


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
    """Create a new sibling receipt/journal, never replace ANY caller data.

    The file is staged and fsynced before publication. Hard links, symlinks
    and dangling links at the requested destination are all treated as
    collisions. This is safe for our single-writer protocol but not a
    substitute for protecting the parent directory from hostile writers.
    """
    path=Path(path)
    reject_symlink_ancestors(path.parent)
    if os.path.lexists(path):
        raise RuntimeError("FB015_ATOMIC_JSON_DESTINATION_ALREADY_EXISTS")
    fd,name=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf8") as f:
            json.dump(payload,f,sort_keys=True,ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        # Atomic hardlink creation (fails if target exists, including a
        # dangling symlink) instead of os.replace() which overwrites data.
        os.link(name,path,follow_symlinks=False)
        parent_fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(parent_fd)
        finally: os.close(parent_fd)
    finally:
        if os.path.lexists(name):
            os.unlink(name)
