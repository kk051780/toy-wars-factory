#!/usr/bin/env python3
"""Source-select exact #801 finisher and one #482 single-Swarm replacement on verified Real42.
No additional controller, HP/KO/score/Remote/Store authority or official RC write.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re
from pathlib import Path

ORIGINAL_SWARM_BLOB="fea147ac51411e626b410d172aad5cd72615bd45"
AUTHOR_FINISHER_BLOB="42f512c4aaa389e0027be774c327e1f5a106aabf"
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
FINISHER=("ServerScriptService","EGGRUMBLE_NeutralFinisherPolicy")
CASTLE=("ServerScriptService","EGGRUMBLE_CastleMatchRules")

def git_blob(data:bytes)->str:
 return hashlib.sha1(("blob %d"%len(data)).encode()+bytes([0])+data).hexdigest()

def flatten(project:Path):
 project=Path(project).resolve(strict=True)
 doc=json.loads(project.read_text(encoding="utf-8"))
 found={}
 def visit(node,path=()):
  for name,item in node.items():
   if name.startswith("$"):continue
   route=path+(name,)
   if "$path" in item:
    if route in found:raise ValueError("RED_DUPLICATE_SOURCE_ROUTE")
    found[route]=(project.parent/item["$path"]).resolve(strict=True)
   else:visit(item,route)
 visit(doc["tree"])
 return doc,found

def compose(before_project:Path,swarm_candidate:Path,policy_original:Path,out:Path):
 before_project=Path(before_project).resolve(strict=True)
 swarm_candidate=Path(swarm_candidate).resolve(strict=True)
 policy_original=Path(policy_original).resolve(strict=True)
 out=Path(out).resolve()
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 doc,before=flatten(before_project)
 if len(before)!=42 or SWARM not in before or FINISHER in before or CASTLE not in before:
  raise ValueError("RED_NOT_REAL42_SINGLE_SWARM_SOURCE")
 if git_blob(before[SWARM].read_bytes())!=ORIGINAL_SWARM_BLOB:
  raise ValueError("RED_ORIGINAL_SWARM_WRITER_CHANGED_REBASE_REQUIRED")
 if git_blob(policy_original.read_bytes())!=AUTHOR_FINISHER_BLOB:
  raise ValueError("RED_UPSTREAM_801_POLICY_BLOB_DRIFT")
 source=swarm_candidate.read_text(encoding="utf-8")
 if source.count("h:TakeDamage(damage)")!=1 or source.count("function Swarm.start(session:any)")!=1:
  raise ValueError("RED_DUPLICATE_HP_OR_SPAWNER")
 if source.count("NeutralFinisherPolicy.select(")!=1 or "assert(#SPECIES_IDS==8" not in source:
  raise ValueError("RED_EIGHT_SPECIES_SERVER_RECEIPT")
 if any(w in source for w in ("RemoteEvent","DataStoreService","MarketplaceService")):
  raise ValueError("RED_NEW_REMOTE_STORE_OWNER")
 if "assert(RunService:IsStudio()" not in source or "lineOfSightToNeutral(origin,attacker,model)" not in source:
  raise ValueError("RED_REMOVED_AUTH_GUARD")
 if git_blob(swarm_candidate.read_bytes())==ORIGINAL_SWARM_BLOB:
  raise ValueError("RED_NO_ACTUAL_GAMEPLAY_EDIT")

 out.parent.mkdir(parents=True,exist_ok=True)
 new=copy.deepcopy(doc)
 def relink(node,key=()):
  for name,item in node.items():
   if name.startswith("$"):continue
   route=key+(name,)
   if "$path" in item:
    selected=swarm_candidate if route==SWARM else before[route]
    item["$path"]=os.path.relpath(selected,out.parent).replace(os.sep,"/")
   else:relink(item,route)
 relink(new["tree"])
 new["tree"]["ServerScriptService"][FINISHER[-1]]={
  "$path":os.path.relpath(policy_original,out.parent).replace(os.sep,"/")}
 new["name"]="GQ800_REAL43_SINGLE_SWARM_NEUTRAL8_SOURCE_PREP_NOT_OFFICIAL"
 out.write_text(json.dumps(new,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,after=flatten(out)
 if set(after)!=(set(before)|{FINISHER}) or len(after)!=43:
  raise ValueError("RED_NOT_REAL43_SINGLETON")
 if after[SWARM].read_bytes()!=swarm_candidate.read_bytes() or after[FINISHER].read_bytes()!=policy_original.read_bytes():
  raise ValueError("RED_PATCH_POLICY_SELECTION")
 for route,original in before.items():
  if route!=SWARM and after[route].read_bytes()!=original.read_bytes():
   raise ValueError("RED_MODIFIED_EXISTING_AUTHORITY_"+"/".join(route))
 if after[CASTLE].read_bytes()!=before[CASTLE].read_bytes():
  raise ValueError("RED_CASTLE_HP_OWNER_CHANGED")
 receipt={
  "feature":"GQ800_NEUTRAL8_SINGLE_SWARM_RUNTIME_20261118",
  "original_source_count":42,"candidate_source_count":43,
  "modified_existing_source":["/".join(SWARM)],
  "new_original_author_source":["/".join(FINISHER)],
  "remaining_original42_byte_exact":41,
  "original_swarm_blob":ORIGINAL_SWARM_BLOB,
  "upstream_801_policy_blob":AUTHOR_FINISHER_BLOB,
  "real_sieges_and_guardians_preserved":True,
  "single_swarm_and_single_hp_ko_owner":True,
  "official_rc_adopted":False,"studio_2client":"NOT_TESTED",
  "android":"NOT_TESTED","art_fun":"NO_GO",
  "rollback":"Exact original Real42 portable original; no independent new Swarm instance"}
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("GQ800_ORIGINAL_REAL42_TO43_SINGLE_SWARM_NATIVE_ROJO_SELECT_READY")
 return receipt

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--original42",required=True,type=Path)
 p.add_argument("--candidate-swarm",required=True,type=Path)
 p.add_argument("--original-policy",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args()
 compose(a.original42,a.candidate_swarm,a.original_policy,a.out)
