#!/usr/bin/env python3
"""Canonical genuine31 -> 32 using one Host require/equip hook, one MAGE rescue module.
Do not change original Combat, HP, KO, healing skill, Store, or score authority.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
MODULE=HERE/"EGGRUMBLE_MageRevive.luau"
HOST="EGGRUMBLE_LobbyCastleModesPreview"
NEW="EGGRUMBLE_MageRevive"
REQUIRE='local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
CALL=r"(?m)^([ \t]*)SevenRoleCombat\.equip\(session,p,role\)[ \t]*$"

def files(project:Path):
 model=json.loads(project.read_text(encoding="utf-8"))
 result={}
 def visit(node,route=()):
  for k,v in node.items():
   if k.startswith("$"):continue
   if not isinstance(v,dict):raise ValueError("RED_BAD_PROJECT")
   at=route+(k,)
   if "$path" in v:
    result[at]=(project.parent/v["$path"]).resolve(strict=True)
   else:visit(v,at)
 visit(model["tree"])
 return model,result

def compose(current31:Path,dest:Path,off:bool=False):
 current31=current31.resolve(strict=True)
 dest=dest.resolve()
 if current31==dest or dest.exists():raise ValueError("RED_OVERWRITE")
 model,before=files(current31)
 if len(before)!=31:raise ValueError("RED_NOT_CURRENT31")
 hostroutes=[k for k in before if k[-1]==HOST]
 if len(hostroutes)!=1:raise ValueError("RED_HOST_MISSING_OR_DUP")
 hostpath=hostroutes[0]
 if any(k[-1]==NEW for k in before):raise ValueError("RED_ALREADY_MAGE_RESCUE")
 if not any(k[-1]=="EGGRUMBLE_SevenRoleCombat" for k in before):
  raise ValueError("RED_MISSING_COMBAT")
 dest.parent.mkdir(parents=True,exist_ok=True)
 model=copy.deepcopy(model)
 model["name"]="EGGRUMBLE_REAL31_PLUS_MAGE_RESCUE32" if not off else "EGGRUMBLE_REAL31_OFF"
 def rebase(node,route=()):
  for k,v in node.items():
   if k.startswith("$"):continue
   at=route+(k,)
   if "$path" in v:
    v["$path"]=os.path.relpath(before[at],dest.parent).replace(os.sep,"/")
   else:rebase(v,at)
 rebase(model["tree"])
 if not off:
  host=before[hostpath].read_text(encoding="utf-8")
  if host.count(REQUIRE)!=1:raise ValueError("RED_HOST_COMBAT_REQUIRE_CHANGED")
  host=host.replace(REQUIRE,REQUIRE+'\nlocal MageRevive=require(script.Parent:WaitForChild("EGGRUMBLE_MageRevive"))')
  host,n=re.subn(CALL,lambda m:m.group(0)+'\n'+m.group(1)+'MageRevive.attach(session,p,role)',host)
  if n!=2:raise ValueError("RED_EXPECTED_TWO_EQUIP_HOOKS")
  outHost=dest.parent/"EGGRUMBLE_LobbyCastleModesPreview.Regen.server.luau"
  outHost.write_text(host,encoding="utf-8")
  # Original exact script route (name/class) retained; only content changed.
  node=model["tree"]
  for name in hostpath:node=node[name]
  node["$path"]=os.path.relpath(outHost,dest.parent).replace(os.sep,"/")
  server=model["tree"].get("ServerScriptService")
  if not isinstance(server,dict):raise ValueError("RED_NO_SERVER_CONTAINER")
  server[NEW]={"$path":os.path.relpath(MODULE,dest.parent).replace(os.sep,"/")}
 dest.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,after=files(dest)
 expected=31 if off else 32
 if len(after)!=expected:raise ValueError("RED_WRONG_SOURCE_COUNT")
 for path,source in before.items():
  if path not in after:raise ValueError("RED_ORIGINAL_SOURCE_MISSING")
  if off or path!=hostpath:
   if after[path].read_bytes()!=source.read_bytes():
    raise ValueError("RED_ORIGINAL_SOURCE_MUTATED_"+"/".join(path))
 receipt={
  "feature_id":"BATTLE_MAGE_REVIVE_20261118",
  "source_count":expected,
  "changed_existing_sources":[] if off else [HOST],
  "added_sources":[] if off else [NEW],
  "other30_original_byte_exact":True,
  "off31_byte_exact":off,
  "original31_sha256":{"/".join(k):hashlib.sha256(p.read_bytes()).hexdigest() for k,p in before.items()},
  "original_game_combat_swarm_store_score_unchanged":True,
  "studio_android_tested":False,
  "formal_rc_adopted":False,
 }
 dest.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("GQ8_MAGE_OFF31_ORIGINAL_SOURCE_EXACT" if off else "GQ8_MAGE_REAL32_HOST_ONLY_SOURCE_EXACT")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--current31",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 p.add_argument("--off",action="store_true")
 a=p.parse_args()
 compose(a.current31,a.out,a.off)
