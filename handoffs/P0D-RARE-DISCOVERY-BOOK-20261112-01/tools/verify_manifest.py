"""Strict keyless full SHA256 source integrity contract for owner-only Studio packet."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
KEYS={"format","game_id","work_id","packet_id","public_source_allowed","files"}
def verify(root=ROOT):
    m=json.loads((root/"BUILD_MANIFEST.json").read_text(encoding="utf-8"))
    if set(m)!=KEYS or m["format"]!="P0D_PUBLIC_SOURCE_V1":
        raise ValueError("bad source manifest header")
    if m["game_id"]!="TRAP_RAIDERS" or m["work_id"]!="p0d-siege-v19" or        m["packet_id"]!="P0D-RARE-DISCOVERY-BOOK-20261112-01" or        m["public_source_allowed"] is not True:
        raise ValueError("source authority mismatch")
    rows=m["files"]
    if not isinstance(rows,list) or len(rows)<9:raise ValueError("missing source files")
    names=set()
    for row in rows:
        if set(row)!={"path","size","sha256"}:raise ValueError("file descriptor keys")
        name=row["path"]
        if not isinstance(name,str) or not name or name.startswith("/") or             "\\" in name or any(p in ("",".","..") for p in name.split("/")):
            raise ValueError("unsafe relative source")
        if name in names or name=="BUILD_MANIFEST.json":raise ValueError("source duplicate")
        names.add(name)
        file=root/name
        if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError("missing/external file")
        data=file.read_bytes()
        if len(data)!=row["size"] or hashlib.sha256(data).hexdigest()!=row["sha256"]:
            raise ValueError("source sha mismatch: "+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob("*")
        if p.is_file() and p.name!="BUILD_MANIFEST.json"}
    if names!=actual:raise ValueError("undeclared source or missing declared path")
    return len(names)
if __name__=="__main__":
    try:print("RARE_BOOK_PUBLIC_SOURCE_FULL_SHA256_PASS files=",verify())
    except Exception as e:
        print("RARE_BOOK_PUBLIC_SOURCE_FULL_SHA256_FAIL",e,file=sys.stderr)
        raise
