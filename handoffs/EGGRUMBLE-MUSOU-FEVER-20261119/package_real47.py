#!/usr/bin/env python3
"""Create a self-contained 47-source portable Rojo candidate, preserving original44 identity."""
from pathlib import Path
import argparse,copy,hashlib,json,os
from compose_real47 import flatten,SWARM,COMBAT,NEW

def sha256(b):return hashlib.sha256(b).hexdigest()

def make(original:Path,current:Path,out:Path,receipt:Path):
 before,old=flatten(original)
 proposed,actual=flatten(current)
 assert len(old)==44 and len(actual)==47
 assert set(actual)==set(old)|set(NEW)
 for route,path in old.items():
  if route not in (SWARM,COMBAT):
   if path.read_bytes()!=actual[route].read_bytes():
    raise ValueError("RED_CHANGED_EXISTING_44_ROUTE_"+"/".join(route))
 doc=copy.deepcopy(proposed)
 folder=out.parent/"sources"
 folder.mkdir(parents=True,exist_ok=True)
 source_entries={}
 def suffix(path):
  x=path.name
  if x.endswith(".client.luau"):return ".client.luau"
  if x.endswith(".server.luau"):return ".server.luau"
  if x.endswith(".luau"):return ".luau"
  if x.endswith(".lua"):return ".lua"
  raise ValueError("RED_UNKNOWN_SOURCE_EXTENSION_"+x)
 for route,source in sorted(actual.items()):
  target=folder.joinpath(*route[:-1],route[-1]+suffix(source))
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(source.read_bytes())
  source_entries[route]=target
 def rewrite(nodes,r=()):
  for key,value in nodes.items():
   if key.startswith("$"):continue
   route=r+(key,)
   if "$path" in value:
    value["$path"]=os.path.relpath(source_entries[route],out.parent).replace(os.sep,"/")
   else:rewrite(value,route)
 rewrite(doc["tree"])
 out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 _,check=flatten(out)
 assert len(check)==47
 for route,source in actual.items():
  if source.read_bytes()!=check[route].read_bytes():
   raise ValueError("RED_PORTABLE_SOURCE_MISMATCH_"+"/".join(route))
 receipt.write_text(json.dumps({
  "source_count":47,"unchanged_existing":42,
  "original44_source_count":44,
  "source_sha256":{"/".join(route):sha256(path.read_bytes()) for route,path in sorted(check.items())},
  "official_rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED",
  "safety":"OFF=exact original44 compiled Place; modified only original Swarm + SevenRoleCombat",
 },indent=2,ensure_ascii=False)+"\n")
 print("GQ8_MUSOU_REAL47_SELF_CONTAINED_PORTABLE_SOURCE_PASS",len(check))
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--original44",type=Path,required=True)
 p.add_argument("--real47",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--receipt",type=Path,required=True)
 a=p.parse_args()
 make(a.original44,a.real47,a.out,a.receipt)
