"""Verify a standalone PUBLIC_SOURCE_V1 fixed source package; does not run Studio."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys

EXPECTED={"format","game_id","work_id","packet_id","public_source_allowed","files"}
SUFFIX={".luau",".py",".json",".md",".txt"}
PACKET="P0D-S1-CASTLE-ARCHITECTURE-VISUAL-20261111-01"

def verify(root: Path) -> int:
    manifest = root / "BUILD_MANIFEST.json"
    raw = manifest.read_bytes()
    doc=json.loads(raw)
    assert set(doc)==EXPECTED, "MANIFEST_SCHEMA"
    assert doc["format"]=="P0D_PUBLIC_SOURCE_V1"
    assert doc["game_id"]=="TRAP_RAIDERS"
    assert doc["work_id"]=="p0d-siege-v19"
    assert doc["packet_id"]==PACKET
    assert doc["public_source_allowed"] is True
    listed=doc["files"]
    assert isinstance(listed,list) and 1 <= len(listed) <= 250
    listed_paths=[]
    for item in listed:
        assert set(item)=={"path","size","sha256"}, "ENTRY_SCHEMA"
        path=item["path"]
        p=Path(path)
        assert not p.is_absolute() and len(p.parts)>0 and all(x not in ("..", ".") and not x.startswith(".") for x in p.parts), "INVALID_PATH"
        assert p.suffix in SUFFIX, "SUFFIX"
        assert isinstance(item["size"],int) and not isinstance(item["size"],bool)
        assert re.fullmatch("[a-f0-9]{64}",item["sha256"]), "DIGEST"
        full=root / p
        assert full.is_file() and not full.is_symlink(), "UNTRUSTED_FILE"
        b=full.read_bytes()
        assert len(b)==item["size"], "SIZE"
        assert hashlib.sha256(b).hexdigest()==item["sha256"], "SHA256"
        assert len(b) <= 2*1024*1024
        assert b.decode("utf8").encode("utf8")==b, "UTF8"
        # conservative token/high-confidence secret patterns
        assert not re.search(rb"(?:ghp|gho|ghs|ghr)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",b)
        listed_paths.append(path)
    assert listed_paths == sorted(set(listed_paths)), "UNSORTED_OR_DUPLICATE"
    all_files=sorted(str(p.relative_to(root)).replace(os.sep,"/") for p in root.rglob("*") if p.is_file())
    assert all_files == sorted(listed_paths+["BUILD_MANIFEST.json"]), "MISSING_OR_UNLISTED_FILES"
    print("PUBLIC_SOURCE_V1_VERIFY_PASS",len(listed),"source files; manifest_sha256",hashlib.sha256(raw).hexdigest())
    return len(listed)

if __name__=="__main__":
    verify(Path(__file__).resolve().parents[1])
