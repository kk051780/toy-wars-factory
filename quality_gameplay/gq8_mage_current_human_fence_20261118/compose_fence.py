#!/usr/bin/env python3
"""Source-locked one-module repair to existing #777 Mage rescue. NO new Mage owner."""
from __future__ import annotations
import argparse,copy,hashlib,json,os
from pathlib import Path

ORIGINAL_MAGE_GIT_BLOB="c75c2db439a5a68f2bc866ad42562fc16687849d"
PATCHED_MAGE_GIT_BLOB="29a3ed1d3ee995b2014690d9b7cfd0a8aa4c66e3"
CURRENT_MARK=' local p=e.player\n if not p.Parent or p.Parent~=Players or not s.world'
ALLY_MARK='local function allyMage(s:any,target:Player,healer:Player):boolean\n if healer==target'
CURRENT_GUARD=' local p=e.player\n if type(s.isCurrentHuman)~="function" or not s.isCurrentHuman(p) then return false end\n if not p.Parent or p.Parent~=Players or not s.world'
ALLY_GUARD='local function allyMage(s:any,target:Player,healer:Player):boolean\n if type(s.isCurrentHuman)~="function" or not s.isCurrentHuman(target) or not s.isCurrentHuman(healer) then return false end\n if healer==target'
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
MAGE=("ServerScriptService","EGGRUMBLE_MageRevive")

def gitblob(body):
 return hashlib.sha1(b"blob "+str(len(body)).encode()+b"\x00"+body).hexdigest()

def patch_text(body):
 original=body.encode("utf-8")
 if gitblob(original)!=ORIGINAL_MAGE_GIT_BLOB:
  raise ValueError("RED_ORIGINAL_MAGE_AUTHOR_BLOB_CHANGED")
 if body.count(CURRENT_MARK)!=1 or body.count(ALLY_MARK)!=1:
  raise ValueError("RED_EXPECTED_SINGLE_ORIGINAL_RESCUE_GATES")
 changed=body.replace(CURRENT_MARK,CURRENT_GUARD,1).replace(ALLY_MARK,ALLY_GUARD,1)
 # Strict exact reversal and no unrelated original source mutation.
 recovered=changed.replace(CURRENT_GUARD,CURRENT_MARK,1).replace(ALLY_GUARD,ALLY_MARK,1)
 if recovered!=body or changed.count('s.isCurrentHuman(healer)')!=1 or changed.count('s.isCurrentHuman(p)')!=1:
  raise ValueError("RED_INVERSE_OR_MEMBERSHIP_DUPLICATE")
 return changed

def flatten(project):
 p=Path(project).resolve(strict=True)
 obj=json.loads(p.read_text(encoding="utf-8"))
 data={}
 def walk(tree,route=()):
  for name,child in tree.items():
   if name.startswith("$"):continue
   if not isinstance(child,dict):raise ValueError("RED_PROJECT_NODE")
   key=route+(name,)
   if "$path" in child:data[key]=(p.parent/child["$path"]).resolve(strict=True)
   else:walk(child,key)
 walk(obj["tree"])
 return obj,data

def compose(original31,mage32,original_mage,out):
 original31=Path(original31).resolve(strict=True)
 mage32=Path(mage32).resolve(strict=True)
 original_mage=Path(original_mage).resolve(strict=True)
 out=Path(out).resolve()
 if out.exists() or out in (original31,mage32):raise ValueError("RED_OUTPUT_OVERWRITE")
 original_model,original=flatten(original31)
 model,candidate=flatten(mage32)
 if len(original)!=31 or len(candidate)!=32 or set(candidate)!=set(original)|{MAGE}:
  raise ValueError("RED_UNEXPECTED_SOURCE_COUNT_OR_ROUTE")
 if MAGE not in candidate or HOST not in candidate:raise ValueError("RED_MAGE_OR_HOST")
 if candidate[MAGE].read_bytes()!=original_mage.read_bytes():
  raise ValueError("RED_ORIGINAL_MAGE_SOURCE_NOT_SELECTED")
 patched=patch_text(original_mage.read_text(encoding="utf-8"))
 candidate_pinned=Path(__file__).with_name("EGGRUMBLE_MageRevive_CurrentHuman.luau")
 if candidate_pinned.read_bytes()!=patched.encode("utf-8") or gitblob(candidate_pinned.read_bytes())!=PATCHED_MAGE_GIT_BLOB:
  raise ValueError("RED_PINNED_PATCHED_MAGE_BLOB_MISMATCH")
 for route in original:
  if route!=HOST and original[route].read_bytes()!=candidate[route].read_bytes():
   raise ValueError("RED_ORIGINAL31_SOURCE_DRIFT")
 new_script=out.parent/"EGGRUMBLE_MageRevive_CurrentHuman.luau"
 out.parent.mkdir(parents=True,exist_ok=True)
 new_script.write_text(patched,encoding="utf-8")
 obj=copy.deepcopy(model)
 def rebase(tree,route=()):
  for name,entry in tree.items():
   if name.startswith("$"):continue
   key=route+(name,)
   if "$path" in entry:entry["$path"]=os.path.relpath(new_script if key==MAGE else candidate[key],out.parent).replace(os.sep,"/")
   else:rebase(entry,key)
 rebase(obj["tree"])
 out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,merged=flatten(out)
 if len(merged)!=32 or set(merged)!=set(candidate):raise ValueError("RED_COMPOSE_COUNT")
 for key in candidate:
  if key!=MAGE and candidate[key].read_bytes()!=merged[key].read_bytes():
   raise ValueError("RED_UNRELATED_GAME_SOURCE_MUTATED")
 if merged[MAGE].read_text(encoding="utf-8")!=patched:raise ValueError("RED_PATCHED_SOURCE_NOT_SELECTED")
 receipt={
 "feature_id":"GQ8_MAGE_CURRENT_HUMAN_FENCE_20261118",
 "author_pr":777,"original_module_git_blob":ORIGINAL_MAGE_GIT_BLOB,
 "changed_original_game_sources":["EGGRUMBLE_MageRevive"],
 "old_host_from_author_unchanged":True,"new_remote_hp_score_store_game_owner":0,
 "one_current_human_guard":True,"one_healer_and_target_current_human_guard":True,
 "source_count":32,"inverse_original31_byte_exact":True,
 "source_sha256":hashlib.sha256(patched.encode("utf-8")).hexdigest(),
 "formal_rc_adopted":False,"studio_android_fun":"NOT_TESTED",
 "rollback":"unselect original Mage Module; select exact prior31 Script sources and Host"}
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("GQ8_MAGE_CURRENT_HUMAN_EXACT_AUTHOR32_SELECTED")
 return out

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 for p in ("original31","mage32","original_mage","out"):ap.add_argument("--"+p,required=True,type=Path)
 a=ap.parse_args()
 compose(a.original31,a.mage32,a.original_mage,a.out)
