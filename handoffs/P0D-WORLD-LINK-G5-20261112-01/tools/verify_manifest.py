"""Strict keyless original PUBLIC_SOURCE_V1 manifest verifier."""
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
KEYS={"files","format","game_id","packet_id","public_source_allowed","work_id"}

def verify(root=ROOT,manifest=None):
    if manifest is None:
        manifest=json.loads((root/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
    if set(manifest)!=KEYS: raise ValueError("root keys")
    if manifest["format"]!="P0D_PUBLIC_SOURCE_V1" or manifest["game_id"]!="TRAP_RAIDERS":
        raise ValueError("format or game")
    if manifest["work_id"]!="p0d-siege-v19" or manifest["public_source_allowed"] is not True:
        raise ValueError("unsafe authority")
    if manifest["packet_id"]!="P0D-WORLD-LINK-G5-20261112-01":raise ValueError("wrong packet")
    rows=manifest["files"]
    if not isinstance(rows,list) or len(rows)<10:raise ValueError("too few source files")
    declared=set()
    for row in rows:
        if set(row)!={"path","size","sha256"}:raise ValueError("file entry keys")
        name=row["path"]
        if not isinstance(name,str) or not name or name.startswith("/") or "\\" in name:
            raise ValueError("unsafe path")
        if any(c in ("",".","..") for c in name.split("/")):
            raise ValueError("path traversal")
        if name in declared or name=="BUILD_MANIFEST.json":raise ValueError("duplicate")
        declared.add(name)
        file=root/name
        if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError("missing or escaped")
        raw=file.read_bytes()
        if len(raw)!=row["size"] or hashlib.sha256(raw).hexdigest()!=row["sha256"]:
            raise ValueError("checksum mismatch "+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and p.name!="BUILD_MANIFEST.json"}
    if actual!=declared:raise ValueError("unlisted or extra source")
    return len(declared)
if __name__=="__main__":
    try: print("WORLD_G5_MANIFEST_SOURCE_PASS files=",verify())
    except Exception as e:
        print("WORLD_G5_MANIFEST_SOURCE_FAIL",e,file=sys.stderr)
        raise
