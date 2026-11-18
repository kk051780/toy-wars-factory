#!/usr/bin/env python3
"""Source-select exact #801 finisher and one #482 single-Swarm replacement on verified Real42.
No additional controller, HP/KO/score/Remote/Store authority or official RC write.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re
from pathlib import Path

ORIGINAL_SWARM_BLOB="dd6b5f695310d425a661e8e5c8c1a1f1d185a7f6"
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


def patch_latest_real42_swarm(original:str,candidate:str)->str:
 """Keep all original Real42 intermediary author fixes; patch only scoped neutral species cues."""
 def replace_once(old:str,new:str,label:str):
  nonlocal original
  count=original.count(old)
  if count!=1:raise ValueError("RED_"+label+"_ANCHOR_"+str(count))
  original=original.replace(old,new,1)
 require='local ImpactFeedback=require(script.Parent:WaitForChild("EGGRUMBLE_ImpactFeedback"))'
 replace_once(require,require+'\nlocal TweenService=game:GetService("TweenService")\nlocal NeutralFinisherPolicy=require(script.Parent:WaitForChild("EGGRUMBLE_NeutralFinisherPolicy"))',"FINISHER_POLICY_REQUIRE")
 start='-- Original #482 Swarm remains the ONLY neutral spawner/HP/KO authority.'
 end='local SWARM_RANGE=240'
 if candidate.count(start)!=1 or candidate.count(end)!=1:raise ValueError("RED_CANDIDATE_PALETTE")
 palette=candidate.split(start,1)[1].split(end,1)[0]
 replace_once('local NEUTRAL_SPEED=7\n'+end,'local NEUTRAL_SPEED=7\n'+start+palette+end,"SPECIES_PALETTE")
 a='local function soldier(parent:Instance,at:Vector3):Model'
 b='local function labelKo(p:Player,n:number)'
 if candidate.count('local function soldier(')!=1 or candidate.count(b)!=1:
  raise ValueError("RED_CANDIDATE_SOLDIER")
 new_soldier=candidate.split('local function soldier(',1)[1].split(b,1)[0]
 new_soldier='local function soldier('+new_soldier
 if original.count(a)!=1 or original.count(b)!=1:raise ValueError("RED_CURRENT_SOLDIER")
 old_soldier=a+original.split(a,1)[1].split(b,1)[0]
 if 'local function piece(' not in original or 'h.MaxHealth=NEUTRAL_HEALTH' not in old_soldier:
  raise ValueError("RED_SOLDIER_NOT_SINGLE_OWNER")
 replace_once(old_soldier,new_soldier,"SOLDIER_ONLY")
 replace_once('local ended=false','local ended=false\n  local spawnSerial=0\n  local hitSerial=0',"SPAWN_SERIAL_COUNTER")
 replace_once('local constructed,model=pcall(soldier,all,at)',
  'spawnSerial+=1\n   local constructed,model=pcall(soldier,all,at,spawnSerial)',"ADOPT_EXISTING_BUDGET_SPAWNER")
 # Preserve previous KO credit when a blocked Humanoid:TakeDamage causes no HP loss.
 replace_once('    h:SetAttribute("LastAttackerId",id)\n',
  '    local oldAttacker=h:GetAttribute("LastAttackerId")\n    h:SetAttribute("LastAttackerId",id)\n',
  "FAILED_DAMAGE_CREDIT_RESTORE")
 cue_start='    local before=h.Health'
 cue_end='    ImpactFeedback.hit('
 if candidate.count(cue_start)!=1 or candidate.count(cue_end)!=1:
  raise ValueError("RED_CANDIDATE_HIT_CUE")
 new_hit=cue_start+candidate.split(cue_start,1)[1].split(cue_end,1)[0]
 replace_once('    h:TakeDamage(damage)\n    local user=Players:GetPlayerByUserId(tonumber(id) or -1)\n',
  new_hit,"REAL_KO_CUE")
 replace_once('local travel=math.min(NEUTRAL_SPEED*.38,best)',
  'local actualSpeed=tonumber(m:GetAttribute("EGGRUMBLE_NeutralSpeed")) or NEUTRAL_SPEED\n       local travel=math.min(actualSpeed*.38,best)',"SWARM_PERSONALITY_SPEED")
 if original.count('h:TakeDamage(damage)')!=1 or original.count('function Swarm.start(session:any)')!=1:
  raise ValueError("RED_DUPLICATE_DAMAGE_OR_SWARM")
 for keep in ("KoFence.mayCredit(session,id,m,all)","neutralBudget:acquire","SpawnPacing.step","EncounterFair","Melee"):
  if keep not in original:raise ValueError("RED_LOST_EXISTING_AUTHOR_SOURCE_"+keep)
 if original.count('NeutralFinisherPolicy.select(')!=1:
  raise ValueError("RED_MISSING_REAL_SERVER_HIT_FINISH_CUE")
 return original

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
 source=patch_latest_real42_swarm(before[SWARM].read_text(encoding="utf-8"),swarm_candidate.read_text(encoding="utf-8"))
 if source.count("h:TakeDamage(damage)")!=1 or source.count("function Swarm.start(session:any)")!=1:
  raise ValueError("RED_DUPLICATE_HP_OR_SPAWNER")
 if source.count("NeutralFinisherPolicy.select(")!=1 or "assert(#SPECIES_IDS==8" not in source:
  raise ValueError("RED_EIGHT_SPECIES_SERVER_RECEIPT")
 if any(w in source for w in ("RemoteEvent","DataStoreService","MarketplaceService")):
  raise ValueError("RED_NEW_REMOTE_STORE_OWNER")
 if "assert(RunService:IsStudio()" not in source or "lineOfSightToNeutral(origin,attacker,model)" not in source:
  raise ValueError("RED_REMOVED_AUTH_GUARD")
 if git_blob(source.encode("utf-8"))==ORIGINAL_SWARM_BLOB:
  raise ValueError("RED_NO_ACTUAL_GAMEPLAY_EDIT")

 out.parent.mkdir(parents=True,exist_ok=True)
 new_swarm_path=out.parent/"EGGRUMBLE_SwarmCombat_Real43.luau"
 new_swarm_path.write_text(source,encoding="utf-8",newline="\n")
 new=copy.deepcopy(doc)
 def relink(node,key=()):
  for name,item in node.items():
   if name.startswith("$"):continue
   route=key+(name,)
   if "$path" in item:
    selected=new_swarm_path if route==SWARM else before[route]
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
 if after[SWARM].read_bytes()!=new_swarm_path.read_bytes() or after[FINISHER].read_bytes()!=policy_original.read_bytes():
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
  "original_real42_swarm_blob":ORIGINAL_SWARM_BLOB,
  "preserved_author_policies":["KoFence","Melee","SpawnPacing","EncounterFair","neutralBudget"],
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
