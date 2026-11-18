#!/usr/bin/env python3
"""Materialize self-contained private Rojo 49 with 37 byte-identical original44 sources."""
from pathlib import Path
import argparse,copy,hashlib,json,os
from compose_real49 import flatten,NEW
def digest(data):return hashlib.sha256(data).hexdigest()
def suffix(p):
 for ext in (".client.luau",".server.luau",".luau",".lua"):
  if p.name.endswith(ext):return ext
 raise ValueError("RED_UNKNOWN_SOURCE_CLASS_"+str(p))

def make(base:Path,current:Path,out:Path,receipt:Path):
 doc,old=flatten(base)
 selected,files=flatten(current)
 assert len(old)==44 and len(files)==49 and set(files)==set(old)|NEW
 unchanged=sum(files[r].read_bytes()==p.read_bytes() for r,p in old.items())
 if unchanged!=37:raise ValueError("RED_NOT_37_UNCHANGED_ORIGINAL")
 project=copy.deepcopy(selected)
 target=out.parent/"src49"
 target.mkdir(parents=True,exist_ok=True)
 packed={}
 for r,p in sorted(files.items()):
  f=target.joinpath(*r[:-1],r[-1]+suffix(p))
  f.parent.mkdir(parents=True,exist_ok=True)
  f.write_bytes(p.read_bytes())
  packed[r]=f
 def visit(tree,route=()):
  for name,item in tree.items():
   if name.startswith("$"):continue
   r=route+(name,)
   if "$path" in item:
    item["$path"]=os.path.relpath(packed[r],out.parent).replace(os.sep,"/")
   else:visit(item,r)
 visit(project["tree"])
 out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 _,check=flatten(out)
 if set(check)!=set(files) or len(check)!=49:raise ValueError("RED_PORTABLE_ROUTE_COUNT")
 if any(check[r].read_bytes()!=files[r].read_bytes() for r in files):
  raise ValueError("RED_PORTABLE_BYTE_MISMATCH")
 receipt.parent.mkdir(parents=True,exist_ok=True)
 receipt.write_text(json.dumps({
  "real49":49,"original44":44,"original44_unchanged":37,
  "feature":"MUSOU_PLUS_REACTIVE_INVUL_V2", "formal_rc_adopted":False,
  "sources":[{"route":"/".join(r),"size":p.stat().st_size,
             "sha256":digest(p.read_bytes())} for r,p in sorted(check.items())],
  "art":"NOT_STUDIO_TESTED","android":"NOT_TESTED",
 },indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 print("GQ8_REAL49_PORTABLE_ALL49_BYTE_EXACT_PASS")
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--original44",type=Path,required=True)
 ap.add_argument("--real49",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True)
 a=ap.parse_args()
 make(a.original44,a.real49,a.out,a.receipt)
