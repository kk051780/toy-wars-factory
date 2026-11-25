#!/usr/bin/env python3
"""GQ8: human-only castle siege burst pacing. Patch one current Host, 30 remain exact.

No duplicate Game, enemy AI, item scoring, cooldown shared between games, Remote or Store.
The original castle current-session/caller membership checks still run first.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, sys
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path("rc_fastlane/quality_rc81_hit042_v3").resolve()))
from select_hit042 import flatten, class_for

FEATURE="GQ8_HUMAN_SIEGE_PER_ATTACKER_COOLDOWN_20261117"
SCRIPT="EGGRUMBLE_LobbyCastleModesPreview"
MARK="-- GQ8_HUMAN_SIEGE_PACING_BEGIN"
ANCHOR_FUNCTION="local function createWorldCastle(session:any,entry:any,index:number)\n"
HELPER='''-- GQ8_HUMAN_SIEGE_PACING_BEGIN
-- Only server-confirmed prompt siege is paced, per human and per target castle.
-- The table is attached to each instance of createWorldCastle, so a replay cannot inherit it.
local SIEGE_ATTACK_COOLDOWN=1.0
local function siegeAttackReady(lastByAttacker:{[string]:number},attackerId:string,now:number):boolean
 if type(now)~="number" or now~=now or now<0 or now==math.huge then return false end
 local previous=lastByAttacker[attackerId]
 return previous==nil or (now>=previous and now-previous>=SIEGE_ATTACK_COOLDOWN)
end
-- GQ8_HUMAN_SIEGE_PACING_END
'''
ANCHOR_PROMPT=' prompt(door,"攻城攻撃","敵城を攻める",function(p)\n'
REPLACE_PROMPT=' local lastHumanSiegeAt:{[string]:number}={}\n'+ANCHOR_PROMPT
ANCHOR_ATTACK='''  local ok,res=pcall(function() return Rules.damageCastle(state,entry.id,from,120) end)
  if not ok then return end
  session.refresh()'''
REPLACE_ATTACK='''  local now=os.clock()
  if not siegeAttackReady(lastHumanSiegeAt,from,now) then return end
  local ok,res=pcall(function() return Rules.damageCastle(state,entry.id,from,120) end)
  if not ok then return end
  lastHumanSiegeAt[from]=now -- commit only after a valid server-authoritative hit
  session.refresh()'''
NAME="GQ8_HUMAN_SIEGE_PACED_HOST.server.luau"
RECEIPT="GQ8_HUMAN_SIEGE_RC31_RECEIPT.json"

def one(src:str,needle:str,replacement:str,label:str)->str:
 if src.count(needle)!=1:raise ValueError("RED_"+label+"_ANCHOR_COUNT_"+str(src.count(needle)))
 return src.replace(needle,replacement,1)

def patch(src:str)->str:
 if MARK in src:raise ValueError("RED_DUPLICATE_SIEGE")
 for required in (
  'sessions[session.mode]~=session',
  'or session.isCurrentHuman(p)~=true then return end',
  'prompt(door,"攻城攻撃"',
  'if state.phase~="ACTIVE" then return end',
  "local from=tostring(p.UserId)",
  'Rules.damageCastle(state,entry.id,from,120)',
 ):
  if required not in src:raise ValueError("RED_MISSING_PRIOR_CASTLE_SESSION_"+required)
 out=one(src,ANCHOR_FUNCTION,HELPER+ANCHOR_FUNCTION,"CREATE_CASTLE")
 out=one(out,ANCHOR_PROMPT,REPLACE_PROMPT,"DOOR")
 out=one(out,ANCHOR_ATTACK,REPLACE_ATTACK,"SIEGE_DAMAGE")
 if unpatch(out)!=src:raise ValueError("RED_NONREVERSIBLE")
 if out.count('Rules.damageCastle(state,entry.id,from,120)')!=1:
  raise ValueError("RED_SECOND_CASTLE_DAMAGE")
 return out

def unpatch(src:str)->str:
 src=one(src,REPLACE_ATTACK,ANCHOR_ATTACK,"INVERSE_ATTACK")
 src=one(src,REPLACE_PROMPT,ANCHOR_PROMPT,"INVERSE_PROMPT")
 src=one(src,HELPER+ANCHOR_FUNCTION,ANCHOR_FUNCTION,"INVERSE_HELPER")
 return src

def mapped(project:Path):
 root,files=flatten(project)
 routes=[r for r in files if r[-1]==SCRIPT]
 if len(routes)!=1:raise ValueError("RED_ONE_CANONICAL_HOST")
 return root,files,routes[0]

def prepare(base:Path,out:Path)->None:
 if out.exists():raise ValueError("RED_SELECTED_EXISTS")
 project,files,target=mapped(base)
 before=files[target].read_bytes()
 after=patch(before.decode("utf-8")).encode("utf-8")
 selected=out.parent/NAME
 if selected.exists():raise ValueError("RED_SELECTED_HOST_EXISTS")
 selected.write_bytes(after)
 edit=copy.deepcopy(project)
 edit["name"]="GQ8_HUMAN_SIEGE_PACED_RC31"
 def walk(tree,p=()):
  for key,v in tree.items():
   if key.startswith("$"):continue
   route=p+(key,)
   if "$path" in v:
    v["$path"]=os.path.relpath(selected if route==target else files[route],out.parent).replace(os.sep,"/")
   else:walk(v,route)
 walk(edit["tree"])
 out.write_text(json.dumps(edit,ensure_ascii=False,indent=2)+"\n")
 _,nextFiles,nextHost=mapped(out)
 if set(nextFiles)!=set(files) or nextHost!=target:raise ValueError("RED_ROUTE_DRIFT")
 different=[r for r in files if files[r].read_bytes()!=nextFiles[r].read_bytes()]
 if different!=[target]:raise ValueError("RED_OTHER30_MUTATED")
 if unpatch(nextFiles[target].read_text(encoding="utf-8")).encode("utf-8")!=before:
  raise ValueError("RED_NO_EXACT_OFF_ROLLBACK")
 print("GQ8_HUMAN_SIEGE_CURRENT31_SINGLE_HOST_OTHER30_EXACT_OFF_PASS")

def native(project:Path,out:Path,mutant:Path)->None:
 _,files,route=mapped(project)
 src=files[route].read_text(encoding="utf-8")
 needle="local function siegeAttackReady(lastByAttacker:{[string]:number},attackerId:string,now:number):boolean\n"
 if src.count(needle)!=1 or src.count("local SIEGE_ATTACK_COOLDOWN=1.0")!=1:
  raise ValueError("RED_MISSING_REAL_SELECTED_PACE_POLICY")
 policy="local SIEGE_ATTACK_COOLDOWN=1.0\n"+needle+src.split(needle,1)[1].split("\nend\n",1)[0]+"\nend\n"
 cases='''local hit={}
assert(siegeAttackReady(hit,"RED_A",100))
hit.RED_A=100
assert(not siegeAttackReady(hit,"RED_A",100))
assert(not siegeAttackReady(hit,"RED_A",100.10))
assert(not siegeAttackReady(hit,"RED_A",100.99))
assert(siegeAttackReady(hit,"RED_A",101))
assert(siegeAttackReady(hit,"BLUE_B",100.1))
assert(not siegeAttackReady(hit,"RED_A",99))
assert(not siegeAttackReady(hit,"RED_A",-1))
assert(not siegeAttackReady(hit,"RED_A",math.huge))
assert(not siegeAttackReady(hit,"RED_A",0/0))
local accepted={}
local function attempt(id,now,serverSuccess)
 if not siegeAttackReady(accepted,id,now) then return false end
 if not serverSuccess then return false end
 accepted[id]=now
 return true
end
assert(not attempt("S1",3,false))
assert(attempt("S1",3.1,true))
assert(not attempt("S1",3.2,true))
assert(attempt("S2",3.2,true))
assert(attempt("S1",4.11,true))
assert(not attempt("S1",4.2,true))
local newRound={}
assert(siegeAttackReady(newRound,"S1",4.2))
print("GQ8_HUMAN_SIEGE_SELECTED_SOURCE_NATIVE_17_CASES_PASS")
'''
 out.write_text(policy+cases)
 mutant.write_text(policy.replace("now-previous>=SIEGE_ATTACK_COOLDOWN","now-previous>=.1",1)+cases)
 print("GQ8_HUMAN_SIEGE_NATIVE_FIXTURE_AND_RATE_BYPASS_MUTANT_CREATED")

def scripts(place:Path):
 out={}
 for node in ET.parse(place).getroot().iter("Item"):
  cls=node.get("class")
  if cls not in ("Script","LocalScript","ModuleScript"):continue
  p=node.find("Properties")
  if p is None:raise ValueError("RED_NO_ROJO_PROPERTIES")
  name=p.findtext("string[@name='Name']")
  src=p.findtext("ProtectedString[@name='Source']")
  if src is None:src=p.findtext("string[@name='Source']")
  if not name or src is None or name in out:raise ValueError("RED_ROJO_DUPLICATE_SCRIPT")
  out[name]=(cls,src.replace("\r\n","\n"))
 return out

def verify(base:Path,out:Path,place:Path)->None:
 _,old,oldroute=mapped(base);_,new,newroute=mapped(out)
 if len(old)!=31 or len(new)!=31 or set(old)!=set(new) or oldroute!=newroute:
  raise ValueError("RED_SCRIPT_SET_OR_ROUTE")
 for route in old:
  previous=old[route].read_bytes();current=new[route].read_bytes()
  if route==oldroute:
   if current!=patch(previous.decode("utf-8")).encode("utf-8"):
    raise ValueError("RED_SIEGE_PATCH_DIFFERENT")
   if unpatch(current.decode("utf-8")).encode("utf-8")!=previous:
    raise ValueError("RED_SIEGE_ROLLBACK_DIFFERENT")
  elif previous!=current:raise ValueError("RED_OTHER30_MUTATED")
 actual=scripts(place)
 if len(actual)!=31 or set(actual)!={r[-1] for r in new}:raise ValueError("RED_ROJO_NOT31")
 for r,p in new.items():
  expected=(class_for(p),p.read_text(encoding="utf-8").replace("\r\n","\n"))
  if actual[r[-1]]!=expected:raise ValueError("RED_ROJO_CLASS_SOURCE_"+r[-1])
 receipt={
  "feature_id":FEATURE,"source_count":31,"one_existing_host_changed":True,
  "other30_byte_exact":True,"off_exact":True,"cooldown_seconds":1.0,
  "per_target_castle_per_human":True,"no_cooldown_before_server_success":True,
  "new_game_remote_store_score_authority":0,"native":"SAME_HEAD_CI",
  "rojo":"31/31","studio_two_client":"NOT_TESTED","android_15":"NOT_TESTED",
  "balance_measurement":"NOT_TESTED","owner_fun":"NO_GO",
  "canonical_place_bytes":place.stat().st_size,
  "canonical_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()
 }
 (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print("GQ8_HUMAN_SIEGE_SELECTED31_ACTUAL_ROJO_EXACT_AND_OFF_PASS",receipt["canonical_place_bytes"])

def selftest():
 before='''local function createWorldCastle(session:any,entry:any,index:number)
 -- session.isCurrentHuman=function(player:Player):boolean
 local x="sessions[session.mode]~=session"
 local y="or session.isCurrentHuman(p)~=true then return end"
 local z=if state.phase~="ACTIVE" then return end
 local f="local from=tostring(p.UserId)"
 prompt(door,"攻城攻撃","敵城を攻める",function(p)
  local ok,res=pcall(function() return Rules.damageCastle(state,entry.id,from,120) end)
  if not ok then return end
  session.refresh()
end)
'''
 changed=patch(before)
 assert unpatch(changed)==before
 assert changed.count(MARK)==1
 assert changed.count("lastHumanSiegeAt[from]=now")==1
 assert changed.count('Rules.damageCastle(state,entry.id,from,120)')==1
 for tampered in (changed,before.replace(ANCHOR_ATTACK,""),before.replace(ANCHOR_FUNCTION,"")):
  try:patch(tampered)
  except ValueError:pass
  else:raise AssertionError("RED_MUTANT_ACCEPTED")
 try:unpatch(before)
 except ValueError:pass
 else:raise AssertionError("RED_OLD_HOST_UNPATCH_ACCEPTED")
 print("GQ8_HUMAN_SIEGE_PATCH_DRIFT_INVERSE_TESTS_PASS")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("mode",choices=["selftest","prepare","native","verify"])
 p.add_argument("--base",type=Path)
 p.add_argument("--out",type=Path)
 p.add_argument("--place",type=Path)
 p.add_argument("--mutant",type=Path)
 a=p.parse_args()
 if a.mode=="selftest":selftest();return
 if not a.base or not a.out:p.error("--base and --out required")
 if a.mode=="prepare":prepare(a.base.resolve(strict=True),a.out.resolve())
 if a.mode=="native":
  if not a.mutant:p.error("--mutant required")
  native(a.base.resolve(strict=True),a.out.resolve(),a.mutant.resolve())
 if a.mode=="verify":
  if not a.place:p.error("--place required")
  verify(a.base.resolve(strict=True),a.out.resolve(strict=True),a.place.resolve(strict=True))
if __name__=="__main__":main()
