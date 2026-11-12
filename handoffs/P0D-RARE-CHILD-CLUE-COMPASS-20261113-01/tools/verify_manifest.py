"""Strict plaintext P0D_PUBLIC_SOURCE_V1 file-size/SHA256 verification.
Disallow hidden unmanifested scripts, duplicates, external symlinks or traversals.
"""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
HEAD={"format","game_id","work_id","packet_id","public_source_allowed","files"}
def verify(root=ROOT):
    m=json.loads((root/"BUILD_MANIFEST.json").read_text("utf-8"))
    if set(m)!=HEAD or m["format"]!="P0D_PUBLIC_SOURCE_V1":
        raise ValueError("invalid strict manifest")
    if m["game_id"]!="TRAP_RAIDERS" or m["work_id"]!="p0d-siege-v19" or m["packet_id"]!="P0D-RARE-CHILD-CLUE-COMPASS-20261113-01" or m["public_source_allowed"] is not True:
        raise ValueError("scope not original public keyless code")
    rows=m["files"]
    if not isinstance(rows,list) or len(rows)<9:raise ValueError("not enough actual source")
    names=set()
    for row in rows:
        if set(row)!={"path","size","sha256"}:raise ValueError("wrong metadata shape")
        p=row["path"]
        if not isinstance(p,str) or not p or p.startswith("/") or "\\" in p or any(x in (".","..","") for x in p.split("/")):
            raise ValueError("bad relative path")
        if p in names or p=="BUILD_MANIFEST.json":raise ValueError("duplicate or recursive manifest")
        names.add(p)
        f=root/p
        if not f.is_file() or f.is_symlink() or not f.resolve().is_relative_to(root.resolve()):
            raise ValueError("source missing/unsafe")
        raw=f.read_bytes()
        if len(raw)!=row["size"] or hashlib.sha256(raw).hexdigest()!=row["sha256"]:
            raise ValueError("source changed: "+p)
    actual={p.relative_to(root).as_posix() for p in root.rglob("*")
        if p.is_file() and p.name!="BUILD_MANIFEST.json"}
    if names!=actual:raise ValueError("extra/undeclared source file")
    return len(names)
if __name__=="__main__":
    try:print("P0D_CLUE_STRICT_PUBLIC_SOURCE_SHA256_PASS files=",verify())
    except Exception as e:
        print("P0D_CLUE_STRICT_SOURCE_FAIL",e,file=sys.stderr)
        raise
