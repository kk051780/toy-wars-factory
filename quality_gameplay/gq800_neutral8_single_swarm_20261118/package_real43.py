#!/usr/bin/env python3
"""Portable 43 original-source bytes without second Swarm: private B intake only."""
from __future__ import annotations
import argparse,copy,hashlib,json,re
from pathlib import Path
from compose_real43 import flatten,SWARM,FINISHER,CASTLE,ORIGINAL_SWARM_BLOB,AUTHOR_FINISHER_BLOB,git_blob

def pack(original42:Path,real43:Path,out:Path,head:str):
 if not re.fullmatch(r"[0-9a-f]{40}",head):raise ValueError("RED_BAD_HEAD")
 old,base=flatten(original42);doc,current=flatten(real43)
 if len(base)!=42 or len(current)!=43 or set(current)!=set(base)|{FINISHER}:
  raise ValueError("RED_NOT_ORIGINAL42_PLUS_FINISHER")
 if {route for route in base if base[route].read_bytes()!=current[route].read_bytes()}!={SWARM}:
  raise ValueError("RED_REAL42_OTHER_SOURCE_OVERWRITE")
 if git_blob(base[SWARM].read_bytes())!=ORIGINAL_SWARM_BLOB:
  raise ValueError("RED_WRONG_ORIGINAL_REAL42_SWARM")
 if git_blob(current[FINISHER].read_bytes())!=AUTHOR_FINISHER_BLOB:
  raise ValueError("RED_WRONG_ORIGINAL_AUTHOR_801_FINISHER")
 if current[CASTLE].read_bytes()!=base[CASTLE].read_bytes():
  raise ValueError("RED_NEW_CASTLE_AUTHORITY")
 out=Path(out).resolve()
 if out.parent.exists():raise ValueError("RED_REFUSE_OVERWRITE_PORTABLE")
 out.parent.mkdir(parents=True)
 new=copy.deepcopy(doc)
 new["name"]="GQ800_GENUINE_PORTABLE_REAL43_ONLY_NOT_FORMAL_RC"
 receipts=[]
 def selected_suffix(file:Path)->str:
  name=file.name
  if name.endswith(".client.luau"):return ".client.luau"
  if name.endswith(".server.luau"):return ".server.luau"
  if name.endswith(".luau"):return ".luau"
  raise ValueError("RED_NOT_LUAU_SCRIPT")
 for route,original in sorted(current.items()):
  path=Path("sources").joinpath(*route[:-1],route[-1]+selected_suffix(original))
  dest=out.parent/path
  dest.parent.mkdir(parents=True,exist_ok=True)
  data=original.read_bytes()
  dest.write_bytes(data)
  node=new["tree"]
  for name in route:node=node[name]
  node["$path"]=path.as_posix()
  receipts.append({"route":"/".join(route),"path":path.as_posix(),
   "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
   "origin":"existing_42_exact" if route in base and route!=SWARM else
    ("existing_single_swarm_scoped_overlay" if route==SWARM else "unchanged_original_801_policy")})
 out.write_text(json.dumps(new,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,portable=flatten(out)
 if set(portable)!=set(current) or any(portable[k].read_bytes()!=v.read_bytes() for k,v in current.items()):
  raise ValueError("RED_PORTABLE_REAL43_SOURCE_DRIFT")
 receipt={"schema":"GQ800_REAL43_PORTABLE_GENUINE_B_INTAKE_V1",
  "head":head,"source_count":43,"previous_source_count":42,
  "previous_unchanged_sources":41,
  "modified_original":["/".join(SWARM)],"added":["/".join(FINISHER)],
  "exact_real42_swarm_git_blob":ORIGINAL_SWARM_BLOB,
  "parent_weather42_run":44319450066,
  "parent_weather42_place_sha256":"ecb52ec035f0013d6fd9e19c599bce5fb0f272037e7e091346e3dc38523417d1",
  "original_author_801_git_blob":AUTHOR_FINISHER_BLOB,
  "no_second_game_remote_store_swarm_hp_ko_owner":True,
  "official_rc_adopted":False,"studio_2client":"NOT_TESTED",
  "android15":"NOT_TESTED","owner_fun":"NO_GO",
  "rollback":"Restore #796 exact seeded-weather Guardian42 portable Real42 from run44319450066; preserve other newer formally accepted sources",
  "sources":receipts}
 (out.parent/"B_PORTABLE43_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
 print("GQ800_PORTABLE43_SOURCE_CLASS_PRECHECK_PASS",sum(x["bytes"] for x in receipts))
 return receipt
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--real43",required=True,type=Path)
 p.add_argument("--real42",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--candidate-head",required=True)
 a=p.parse_args()
 pack(a.real42,a.real43,a.out,a.candidate_head)
