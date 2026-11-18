#!/usr/bin/env python3
"""Verified GQ8 join: already-certified #780 REALM+REGEN36 + #777 MAGE32 -> 37.

This is a source selection rehearsal only. It does not alter a canonical branch,
rewrite earlier workers' source, establish a second Combat/HP owner or publish.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
MAGE=("ServerScriptService","EGGRUMBLE_MageRevive")
REALM={
 ("ServerScriptService","EGGRUMBLE_LandSeaSkyTraversal"),
 ("ServerScriptService","EGGRUMBLE_RealmBattleCore"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls")}
REGEN={
 ("ServerScriptService","EGGRUMBLE_NaturalRegen"),
 ("ServerScriptService","EGGRUMBLE_PassiveRegenPolicy")}
BASE_COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
MAGE_REQUIRE='local MageRevive=require(script.Parent:WaitForChild("EGGRUMBLE_MageRevive"))'
MAGE_CALL="MageRevive.attach(session,p,role)"
REG_REQUIRE='local NaturalRegen=require(script.Parent:WaitForChild("EGGRUMBLE_NaturalRegen"))'
REG_CALL="NaturalRegen.attach(session,p,role)"
ORIG_REQUIRE='local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
EQUIP_RE=r"(?m)^([ \t]*)SevenRoleCombat\.equip\(session,p,role\)[ \t]*$"

def flatten(project):
 project=Path(project).resolve(strict=True)
 model=json.loads(project.read_text(encoding="utf-8"))
 if not isinstance(model.get("tree"),dict):
  raise ValueError("RED_INVALID_PROJECT")
 result={}
 def scan(node,route=()):
  for k,v in node.items():
   if k.startswith("$"):continue
   if not isinstance(v,dict):raise ValueError("RED_INVALID_NODE")
   r=route+(k,)
   if "$path" in v:
    if r in result:raise ValueError("RED_DUPLICATE_ROUTE")
    result[r]=(project.parent/v["$path"]).resolve(strict=True)
   else:scan(v,r)
 scan(model["tree"])
 return model,result

def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def base_from_addon(hosttext, require, call):
 if hosttext.count(require)!=1 or hosttext.count(call)!=2:
  raise ValueError("RED_AUTHOR_HOST_HOOK_SIGNATURE")
 revert=hosttext.replace(require+"\n","",1)
 revert,n=re.subn(r"(?m)^[ \t]*"+re.escape(call)+r"[ \t]*\n","",revert)
 if n!=2:raise ValueError("RED_NOT_TWO_AUTHOR_HOOKS")
 return revert

def compose(original31,combined36,mage32,out):
 original31=Path(original31).resolve(strict=True)
 combined36=Path(combined36).resolve(strict=True)
 mage32=Path(mage32).resolve(strict=True)
 out=Path(out).resolve()
 if out in (original31,combined36,mage32) or out.exists():
  raise ValueError("RED_OVERWRITE")
 base_model,base=flatten(original31)
 merged_model,s36=flatten(combined36)
 _,mage=flatten(mage32)
 base_set=set(base)
 if len(base)!=31 or len(s36)!=36 or len(mage)!=32:
  raise ValueError("RED_BAD_SOURCE_COUNT")
 if {HOST,BASE_COMBAT,("ServerScriptService","EGGRUMBLE_SwarmCombat")}-base_set:
  raise ValueError("RED_MISSING_ORIGINAL_COMBAT_HOST")
 if set(s36)!=base_set|REALM|REGEN or set(mage)!=base_set|{MAGE}:
  raise ValueError("RED_ADDON_ROUTE_COLLISION")
 for r in base_set:
  if r!=HOST and (sha(s36[r])!=sha(base[r]) or sha(mage[r])!=sha(base[r])):
   raise ValueError("RED_MUTATED_ORIGINAL_"+"/".join(r))
 original=base[HOST].read_text(encoding="utf-8")
 host36=s36[HOST].read_text(encoding="utf-8")
 host32=mage[HOST].read_text(encoding="utf-8")
 if base_from_addon(host36,REG_REQUIRE,REG_CALL)!=original:
  raise ValueError("RED_UNREVIEWED_REGEN_HOST_PATCH")
 if base_from_addon(host32,MAGE_REQUIRE,MAGE_CALL)!=original:
  raise ValueError("RED_UNREVIEWED_MAGE_HOST_PATCH")
 if host36.count(ORIG_REQUIRE)!=1 or original.count(ORIG_REQUIRE)!=1:
  raise ValueError("RED_UNMATCHED_CANONICAL_HOST")
 # Only add the exact author Mage require and two author Mage attach statements.
 host37=host36.replace(ORIG_REQUIRE,ORIG_REQUIRE+"\n"+MAGE_REQUIRE,1)
 host37,n=re.subn(EQUIP_RE,
  lambda m:m.group(0)+"\n"+m.group(1)+MAGE_CALL,
  host37)
 if n!=2 or host37.count(REG_CALL)!=2 or host37.count(MAGE_CALL)!=2:
  raise ValueError("RED_DOUBLE_OR_MISSING_HOOK")
 # Proof the added Mage Host statements can be precisely removed to restore
 # the previously independently verified Realm+Regen36 Host byte-for-byte.
 if base_from_addon(host37,MAGE_REQUIRE,MAGE_CALL)!=host36:
  raise ValueError("RED_CANNOT_REVERSE_MAGICAL_HOST_PATCH")
 out.parent.mkdir(parents=True,exist_ok=True)
 host_out=out.parent/"EGGRUMBLE_LobbyCastleModesPreview.MageRegen.server.luau"
 host_out.write_text(host37,encoding="utf-8")
 model=copy.deepcopy(merged_model)
 model["name"]="EGGRUMBLE_REALM_REGEN_MAGE_COMBINED37_QA_PRIVATE"
 def rebase(node,route=()):
  for k,v in node.items():
   if k.startswith("$"):continue
   r=route+(k,)
   if "$path" in v:
    path=host_out if r==HOST else s36[r]
    v["$path"]=os.path.relpath(path,out.parent).replace(os.sep,"/")
   else:rebase(v,r)
 rebase(model["tree"])
 server=model["tree"].get("ServerScriptService")
 if not isinstance(server,dict) or MAGE[-1] in server:
  raise ValueError("RED_NOT_SINGLE_SERVER")
 server[MAGE[-1]]={"$path":os.path.relpath(mage[MAGE],out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,selected=flatten(out)
 if len(selected)!=37 or set(selected)!=base_set|REGEN|REALM|{MAGE}:
  raise ValueError("RED_WRONG_COMPOSITE_COUNT")
 for r in set(selected)-{HOST,MAGE}:
  if sha(selected[r])!=sha(s36[r]):
   raise ValueError("RED_REALM_REGEN_AUTHOR_DRIFT_"+"/".join(r))
 if sha(selected[MAGE])!=sha(mage[MAGE]):
  raise ValueError("RED_MAGE_AUTHOR_DRIFT")
 receipt={
  "feature_id":"GQ8_CROSSLANE_REALM_REGEN_MAGE_COMBINED37",
  "actual_sources":37,"original31":31,
  "source_pins":{"realm_regen_qa_pr":780,
                 "realm_regen_qa_sha":"8f7984c1a9db2c016321d16d47a3ea8d1b5081df",
                 "mage_runtime_pr":777,
                 "mage_runtime_sha":"2f4c1e43a7802929de3f633370b32791f7bf8d96"},
  "preserved_original30_byte_exact":True,
  "unchanged_prior36_other_than_original_host":True,
  "mage_author_source_byte_exact":True,
  "two_regen_hooks":2,"two_mage_hooks":2,
  "single_original_game_combat_host":True,
  "official_rc_written":False,"main_written":False,"publication_authorized":False,
  "studio2client_tested":False,"android_tested":False,
  "rollback":"Original genuine31 / remove all 6 add-ons; or verified combined36 / omit Mage only",
  "sources_sha256":{"/".join(r):sha(path) for r,path in sorted(selected.items())}
 }
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
 print("GQ8_REALM_REGEN_MAGE37_ORIGINAL30_BYTE_EXACT_REUSE_PASS")
 return out

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--original31",type=Path,required=True)
 p.add_argument("--combined36",type=Path,required=True)
 p.add_argument("--mage32",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 compose(a.original31,a.combined36,a.mage32,a.out)
