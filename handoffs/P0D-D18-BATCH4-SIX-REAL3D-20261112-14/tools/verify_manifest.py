#!/usr/bin/env python3
"""Strict UTF8 SHA256/byte-count proof; reject unlisted or modified source files."""
import hashlib
import json
import pathlib
r=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((r/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
seen=set()
for it in m["files"]:
    p=it["path"]
    assert p not in seen and not p.startswith("/") and ".." not in pathlib.PurePosixPath(p).parts,p
    seen.add(p)
    raw=(r/p).read_bytes()
    assert len(raw)==it["size_bytes"],p
    assert hashlib.sha256(raw).hexdigest()==it["sha256"],p
all_paths={str(p.relative_to(r)) for p in r.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts}
assert all_paths==seen|{"BUILD_MANIFEST.json"},("unlisted_files", sorted(all_paths-seen-{"BUILD_MANIFEST.json"}))
print("PUBLIC_SOURCE_V1_MANIFEST_EXACT_PASS",len(seen))
