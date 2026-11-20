#!/usr/bin/env python3
"""Produce a self-contained real42 original-scripts-unchanged package, no RC write."""
from __future__ import annotations
import argparse,copy,hashlib,json,os,re
from pathlib import Path
from compose_real42_guardians import flatten,H,C,G,N,R
def portable(real42:Path,old41:Path,dest:Path,commit:str):
 if not re.fullmatch(r"[a-f0-9]{40}",commit):raise ValueError("RED_UNPINNED_HEAD")
 doc,files=flatten(real42);_,previous=flatten(old41)
 if len(files)!=42 or len(previous)!=41 or set(files)!=set(previous)|{N}:
  raise ValueError("RED_NOT_REAL42")
 edits={x for x in previous if previous[x].read_bytes()!=files[x].read_bytes()}
 if edits!={H,C,G}:raise ValueError("RED_UNEXPECTED_ORIGINAL_CODE_CHANGE")
 dest=Path(dest).resolve()
 if dest.parent.exists():raise ValueError("RED_REFUSE_EXISTING_PORTABLE_DIR")
 dest.parent.mkdir(parents=True)
 new=copy.deepcopy(doc)
 sources=[]
 for route,src in sorted(files.items()):
  suffix=".client.luau" if route[0]=="StarterPlayer" else (
   ".server.luau" if route==H or route[-1].endswith("Core") or route[-1].endswith("Traversal") else ".luau")
  # The original source extension remains authoritative; use it for exact Roblox Class.
  name=src.name
  if name.endswith(".client.luau"):suffix=".client.luau"
  elif name.endswith(".server.luau"):suffix=".server.luau"
  elif src.name.endswith(".luau"):suffix=".luau"
  entry=Path("sources").joinpath(*route[:-1],route[-1]+suffix)
  file=dest.parent/entry
  file.parent.mkdir(parents=True,exist_ok=True)
  raw=src.read_bytes()
  file.write_bytes(raw)
  node=new["tree"]
  for key in route:node=node[key]
  node["$path"]=entry.as_posix()
  sources.append({"route":"/".join(route),"path":entry.as_posix(),
   "bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),
   "origin":"new_guardian_actor" if route==N else (
     "original_source_with_limited_guardian_hooks" if route in edits else "original41_byte_exact")})
 new["name"]="GQ815_REAL42_PORTABLE_SOURCE_ONLY_NOT_OFFICIAL"
 dest.write_text(json.dumps(new,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
 _,check=flatten(dest)
 for route,original in files.items():
  if check[route].read_bytes()!=original.read_bytes():
   raise ValueError("RED_PORTABLE_BYTE_MISMATCH")
 receipt={"feature":"GQ815_GUARDIAN_RUNTIME_REAL42",
  "candidate_head":commit,"source_count":42,
  "source_base":"immutable original PR796 REAL41 artifact ID14431340803",
  "existing_scripts_changed":["/".join(x) for x in sorted(edits)],
  "castle_rules_exact":previous[R].read_bytes()==files[R].read_bytes(),
  "new_remote_or_store":False,"formal_rc_adopted":False,
  "studio_2client":"NOT_TESTED","android15":"NOT_TESTED","sources":sources}
 (dest.parent/"GQ815_PORTABLE42_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("GQ815_PORTABLE42_EXACT_SOURCE_BYTES_MATCH",sum(x["bytes"] for x in sources))
 return receipt
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--real42",required=True,type=Path)
 p.add_argument("--real41",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path);p.add_argument("--candidate-head",required=True)
 a=p.parse_args();portable(a.real42,a.real41,a.out,a.candidate_head)
