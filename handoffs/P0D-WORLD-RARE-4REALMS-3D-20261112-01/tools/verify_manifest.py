"""Strict full-file original PUBLIC_SOURCE_V1 manifest; no keys or hidden files."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
KEYS={"format","game_id","work_id","packet_id","public_source_allowed","files"}
def verify(root=ROOT):
    m=json.loads((root/"BUILD_MANIFEST.json").read_text("utf-8"))
    if set(m)!=KEYS or m["format"]!="P0D_PUBLIC_SOURCE_V1":
        raise ValueError("bad manifest header")
    if m["game_id"]!="TRAP_RAIDERS" or m["work_id"]!="p0d-siege-v19":
        raise ValueError("game or work id")
    if m["packet_id"]!="P0D-WORLD-RARE-4REALMS-3D-20261112-01" or m["public_source_allowed"] is not True:
        raise ValueError("wrong scope/authority")
    files=m["files"]
    if not isinstance(files,list) or len(files)<10:raise ValueError("too few files")
    names=set()
    for rec in files:
        if set(rec)!={"path","size","sha256"}:raise ValueError("record keys")
        p=rec["path"]
        if not isinstance(p,str) or not p or p.startswith("/") or "\\" in p or any(x in ("",".","..") for x in p.split("/")):
            raise ValueError("path traversal")
        if p in names or p=="BUILD_MANIFEST.json":raise ValueError("duplicate or self")
        names.add(p)
        filepath=root/p
        if filepath.is_symlink() or not filepath.is_file() or not filepath.resolve().is_relative_to(root.resolve()):
            raise ValueError("missing or unsafe")
        raw=filepath.read_bytes()
        if len(raw)!=rec["size"] or hashlib.sha256(raw).hexdigest()!=rec["sha256"]:
            raise ValueError("size or sha256 changed: "+p)
    actual={p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and p.name!="BUILD_MANIFEST.json"}
    if actual!=names:raise ValueError("extra/unlisted file")
    return len(names)
if __name__=="__main__":
    try:print("RARE4_PUBLIC_SOURCE_SHA256_PASS files=",verify())
    except Exception as e:
        print("RARE4_PUBLIC_SOURCE_SHA256_FAIL",e,file=sys.stderr)
        raise
