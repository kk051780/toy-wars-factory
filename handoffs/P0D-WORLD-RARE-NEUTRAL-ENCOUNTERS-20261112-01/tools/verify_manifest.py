"""Strict fully-keyless P0D_PUBLIC_SOURCE_V1 SHA256 full source, no hidden files."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
HEAD={"format","game_id","work_id","packet_id","public_source_allowed","files"}
def verify(root=ROOT,manifest=None):
    if manifest is None:
        manifest=json.loads((root/"BUILD_MANIFEST.json").read_text("utf-8"))
    if set(manifest)!=HEAD or manifest["format"]!="P0D_PUBLIC_SOURCE_V1":
        raise ValueError("manifest keys or format")
    if manifest["game_id"]!="TRAP_RAIDERS" or manifest["work_id"]!="p0d-siege-v19":
        raise ValueError("wrong game")
    if manifest["packet_id"]!="P0D-RARE-NEUTRAL-ENCOUNTERS-20261112-01" or manifest["public_source_allowed"] is not True:
        raise ValueError("wrong packet authority")
    listed=manifest["files"]
    if not isinstance(listed,list) or len(listed)<10:raise ValueError("not fully declared")
    seen=set()
    for row in listed:
        if set(row)!={"path","size","sha256"}:raise ValueError("file descriptor keys")
        name=row["path"]
        if (not isinstance(name,str) or not name or name.startswith("/") or
            "\\" in name or any(x in ("",".","..") for x in name.split("/"))):
            raise ValueError("unsafe relative source path")
        if name in seen or name=="BUILD_MANIFEST.json":raise ValueError("duplicate path")
        seen.add(name)
        file=root/name
        if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError("source missing/unsafe")
        raw=file.read_bytes()
        if len(raw)!=row["size"] or hashlib.sha256(raw).hexdigest()!=row["sha256"]:
            raise ValueError("source corruption "+name)
    actual={p.relative_to(root).as_posix() for p in root.rglob("*")
        if p.is_file() and p.name!="BUILD_MANIFEST.json"}
    if actual!=seen:raise ValueError("undeclared file")
    return len(seen)
if __name__=="__main__":
    try:print("RARE_NEUTRAL_PUBLIC_SOURCE_SHA256_PASS files=",verify())
    except Exception as exc:
        print("RARE_NEUTRAL_PUBLIC_SOURCE_SHA256_FAIL",exc,file=sys.stderr)
        raise
