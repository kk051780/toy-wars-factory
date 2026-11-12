"""Full exact test-only keyless packet integrity. No hidden unreviewed code."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
REQUIRED={"format","game_id","work_id","packet_id","public_source_allowed","files"}
def verify(root=ROOT):
 m=json.loads((root/"BUILD_MANIFEST.json").read_text("utf-8"))
 if set(m)!=REQUIRED or m["format"]!="P0D_PUBLIC_SOURCE_V1":
  raise ValueError("bad manifest header")
 if m["game_id"]!="TRAP_RAIDERS" or m["work_id"]!="p0d-siege-v19" or     m["packet_id"]!="P0D-RARE-BOOK-FULL-SERVER-QA-20261112-01" or     m["public_source_allowed"] is not True:
  raise ValueError("wrong game scope")
 records=m["files"]
 if not isinstance(records,list) or len(records)<4:raise ValueError("missing proof files")
 names=set()
 for row in records:
  if set(row)!={"path","size","sha256"}:raise ValueError("bad file schema")
  name=row["path"]
  if not isinstance(name,str) or not name or name.startswith("/") or "\\" in name or     any(x in (".","..","") for x in name.split("/")):raise ValueError("unsafe path")
  if name in names or name=="BUILD_MANIFEST.json":raise ValueError("duplicate")
  names.add(name)
  file=root/name
  if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
   raise ValueError("source missing/unsafe")
  data=file.read_bytes()
  if len(data)!=row["size"] or hashlib.sha256(data).hexdigest()!=row["sha256"]:
   raise ValueError("source hash/length mismatch "+name)
 actual={p.relative_to(root).as_posix() for p in root.rglob("*")
   if p.is_file() and p.name!="BUILD_MANIFEST.json"}
 if actual!=names:raise ValueError("undeclared source file")
 return len(names)
if __name__=="__main__":
 try:print("RARE_BOOK_FULL_SERVER_SHA256_ALL_PASS count=",verify())
 except Exception as e:
  print("RARE_BOOK_FULL_SERVER_SHA256_FAIL",e,file=sys.stderr)
  raise
