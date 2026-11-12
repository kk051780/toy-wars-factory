#!/usr/bin/env python3
"""Strict keyless PUBLIC_SOURCE_V1 SHA256 / byte size / git blob source verifier."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
assert manifest["schema"]=="P0D_D18_SOURCE_ONLY_SHA256_V1"
assert manifest["game_id"]=="TRAP_RAIDERS"
rows=manifest["files"]
names=[row["path"] for row in rows]
assert len(names)==len(set(names)) and len(rows)>10
assert names==sorted(names), "manifest rows must be sorted"
for row in rows:
    name=row["path"]
    assert Path(name).is_absolute() is False and ".." not in Path(name).parts and "\\" not in name
    file=ROOT/name
    assert file.is_file() and not file.is_symlink(), "source absent or symlink: "+name
    content=file.read_bytes()
    assert len(content)==row["utf8_bytes"], "size mismatch: "+name
    assert hashlib.sha256(content).hexdigest()==row["sha256"], "sha256 mismatch: "+name
    git_blob=b"blob "+str(len(content)).encode()+b"\\0"+content
    assert hashlib.sha1(git_blob).hexdigest()==row["git_blob_sha1"], "git blob mismatch: "+name
actual={str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and
    p.name!="BUILD_MANIFEST.json" and "__pycache__" not in p.parts and not p.name.endswith(".pyc")}
assert set(names)==actual, "unlisted source files: "+str(sorted(actual-set(names)))+" missing: "+str(sorted(set(names)-actual))
print("D18_BATCH6_SHA256_SOURCE_MANIFEST_EXACT_PASS files="+str(len(rows)))
