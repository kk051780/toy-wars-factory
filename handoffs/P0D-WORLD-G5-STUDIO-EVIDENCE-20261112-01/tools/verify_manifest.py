"""Strict keyless SHA256 manifest verifier for exactly owned nonproduction pack."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={"format","game_id","work_id","packet_id","public_source_allowed","files"}
def verify(root=ROOT):
    m=json.loads((root/"BUILD_MANIFEST.json").read_text("utf-8"))
    if set(m)!=REQUIRED or m["format"]!="P0D_PUBLIC_SOURCE_V1":
        raise ValueError("bad manifest top level")
    if m["game_id"]!="TRAP_RAIDERS" or m["work_id"]!="p0d-siege-v19":
        raise ValueError("wrong game")
    if m["packet_id"]!="P0D-WORLD-G5-STUDIO-EVIDENCE-20261112-01":
        raise ValueError("wrong package")
    if m["public_source_allowed"] is not True:raise ValueError("not public keyless")
    rows=m["files"]
    if not isinstance(rows,list) or len(rows)<8:raise ValueError("too few manifest files")
    seen=set()
    for r in rows:
        if set(r)!={"path","size","sha256"}:raise ValueError("invalid file keys")
        name=r["path"]
        if (not isinstance(name,str) or not name or name.startswith("/")
            or "\\" in name or any(x in (".","..","") for x in name.split("/"))):
            raise ValueError("unsafe path")
        if name in seen or name=="BUILD_MANIFEST.json":raise ValueError("duplicate/self")
        seen.add(name)
        p=root/name
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
            raise ValueError("path escapes root")
        raw=p.read_bytes()
        if len(raw)!=r["size"] or hashlib.sha256(raw).hexdigest()!=r["sha256"]:
            raise ValueError("hash/size corruption "+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and p.name!="BUILD_MANIFEST.json"}
    if actual!=seen:raise ValueError("extra or missing source")
    return len(seen)
if __name__=="__main__":
    try: print("G5_STUDIO_PROBE_PUBLIC_SOURCE_SHA256_PASS files=",verify())
    except Exception as err:
        print("G5_STUDIO_PROBE_SOURCE_MANIFEST_FAIL",err,file=sys.stderr)
        raise
