#!/usr/bin/env python3
"""OWNER #822 latest-lineage REAL55 -> REAL56, single Combat/Swarm preserved.

Two scoped overlays inside original Real55, plus one new Counter ModuleScript.
Strictly preserves 53 untouched official55 sources, BOTH original Musou+Invul
interlock and the original real 13 pre-hit damage gate. OFF55 byte exact.
No new HP/KO/Swarm/Score/remote/store writer.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os,re,importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parent
POLICY=("ServerScriptService","EGGRUMBLE_InvulnerabilityPolicy")
RUNTIME=("ServerScriptService","EGGRUMBLE_InvulRuntime")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
COUNTER=("ServerScriptService","EGGRUMBLE_InvulCounterNeutral")
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
FROZEN_RC="a6020867fac80fa3b2ca47478625873fc6f3678e"
OLD_RUNTIME_BLOB="2ada705fd09c2d49453ca1cd2e1e28bf0902f147"
ORIG_POLICY_BLOB="1c38af7f0ed65a7a90b65bbc98b0ab35d54c971c"
COUNTER_SRC=ROOT/"EGGRUMBLE_InvulCounterNeutral.luau"
ORIGINAL_PVP='enemyHum:TakeDamage(InvulRuntime.filterDamage(enemyHum,damage*duel*mark*musou,"PLAYER",p.UserId))'
GUARD_ORIGINAL='''   local now=os.clock()
   local ok,res=Policy.arm(ledger,context(p,r,now),"SKILL")'''
GUARD_MUSOU='''   local now=os.clock()
   if session.swarm and session.swarm.musouActive
     and session.swarm.musouActive(p)==true then return end
   local ok,res=Policy.arm(ledger,context(p,r,now),"SKILL")'''

def blob(data:bytes)->str:
 return hashlib.sha1(("blob "+str(len(data))+"\\0").encode().replace(b"\\0",b"\0")+data).hexdigest()
def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def flatten(project:Path):
 project=project.resolve(strict=True)
 doc=json.loads(project.read_text(encoding="utf-8"))
 out={}
 def walk(node,route=()):
  for k,v in node.items():
   if k.startswith("$"):continue
   r=route+(k,)
   if not isinstance(v,dict):raise ValueError("RED_BAD_PROJECT_NODE")
   if "$path" in v:
    if r in out:raise ValueError("RED_DUPLICATE_ROUTE")
    out[r]=(project.parent/v["$path"]).resolve(strict=True)
   else:walk(v,r)
 walk(doc["tree"])
 return doc,out
def suffix(path:Path):
 for ext in (".server.luau",".client.luau",".luau"):
  if path.name.endswith(ext):return ext
 raise ValueError("RED_UNSUPPORTED_ROBLOX_CLASS")
def exact(body,old,new,tag):
 if body.count(old)!=1:raise ValueError("RED_"+tag+"_COUNT_"+str(body.count(old)))
 return body.replace(old,new,1)
def original_relay(code_path:Path):
 spec=importlib.util.spec_from_file_location("original_counter47",str(code_path))
 if not spec or not spec.loader:raise ValueError("RED_NO_FIXED_COUNTER_AUTHOR")
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module.PVP_REPLACEMENT

def compose(parent55,receipt55,prior_runtime46,new_runtime,old_counter_author,out):
 parent55=Path(parent55).resolve(strict=True)
 receipt55=Path(receipt55).resolve(strict=True)
 prior_runtime46=Path(prior_runtime46).resolve(strict=True)
 new_runtime=Path(new_runtime).resolve(strict=True)
 old_counter_author=Path(old_counter_author).resolve(strict=True)
 out=Path(out).resolve()
 if out.exists() or out.parent.exists():raise ValueError("RED_REFUSE_REWRITE_PARENT")
 src_doc,src=flatten(parent55)
 receipt=json.loads(receipt55.read_text(encoding="utf-8"))
 if len(src)!=55 or set((POLICY,RUNTIME,COMBAT,SWARM,COUNTER))&set(src)!={POLICY,RUNTIME,COMBAT,SWARM}:
  raise ValueError("RED_NOT_EXISTING_55_SINGLETON")
 if receipt.get("source_profile")!="eggrumble_v3_real55" or receipt.get("selected_official_branch_sha")!=FROZEN_RC or receipt.get("official_rc_adopted") is not True:
  raise ValueError("RED_NOT_LATEST_ACTUAL_FORMAL55_RECEIPT")
 ledger={tuple(x["route"].split("/")):x for x in receipt.get("sources",[])}
 if set(ledger)!=set(src):raise ValueError("RED_MISSING_REAL55_SOURCE_PROVENANCE")
 for route,path in src.items():
  data=path.read_bytes();row=ledger[route]
  if digest(data)!=row["sha256"] or len(data)!=row["bytes"]:
   raise ValueError("RED_ORIGINAL55_AUTHOR_SOURCE_DRIFT_"+"/".join(route))
 if blob(prior_runtime46.read_bytes())!=OLD_RUNTIME_BLOB:
  raise ValueError("RED_HISTORICAL_46_RUNTIME_NOT_PINNED")
 if blob(src[POLICY].read_bytes())!=ORIG_POLICY_BLOB:
  raise ValueError("RED_ORIGINAL_V2_POLICY_NOT_SELECTED")
 old_rt=src[RUNTIME].read_text(encoding="utf-8")
 if old_rt.count(GUARD_MUSOU)!=1 or old_rt.count('session.swarm.musouActive(p)')!=1:
  raise ValueError("RED_MUSOU_INVUL_INTERLOCK_LOST")
 # TRUE selected Real55 Runtime must be #830 exact original plus one original
 # #825 interlock. If any other author changed it, stop instead of overwriting.
 if old_rt.replace(GUARD_MUSOU,GUARD_ORIGINAL,1).encode()!=prior_runtime46.read_bytes():
  raise ValueError("RED_REAL55_RUNTIME_NOT_EXACT_ORIGINAL_PLUS_MUSOU_INTERLOCK")
 new_rt=new_runtime.read_text(encoding="utf-8")
 if new_rt.count(GUARD_ORIGINAL)!=1 or "Counter.react(" not in new_rt or "claimPvPCounter(" not in new_rt:
  raise ValueError("RED_NOT_NEW_COUNTER_AUTHOR_RUNTIME")
 rt56=exact(new_rt,GUARD_ORIGINAL,GUARD_MUSOU,"PRESERVE_MUSOU_IN_COUNTER_RUNTIME")
 if rt56.count('session.swarm.musouActive(p)')!=1:
  raise ValueError("RED_REACTIVATED_DUAL_AWAKENING")
 # Genuine current Combat already owns Musou multiplier and original pre-hit
 # gate. This wraps ONLY its original human PvP damage site, not hero logic.
 original_hero=src[COMBAT].read_text(encoding="utf-8")
 if original_hero.count(ORIGINAL_PVP)!=1 or "claimPvPCounter(" in original_hero:
  raise ValueError("RED_REAL55_ORIGINAL_COMBAT_PVP_CHANGED")
 rewrite=original_relay(old_counter_author)
 if rewrite.count('damage*duel*mark,"PLAYER"')!=1:
  raise ValueError("RED_AUTHOR_COUNTER_NOT_SINGLE_PVP_SOURCE")
 rewrite=rewrite.replace('damage*duel*mark,"PLAYER"','damage*duel*mark*musou,"PLAYER"',1)
 new_hero=exact(original_hero,ORIGINAL_PVP,rewrite,"ONLY_ORIGINAL_PVP_HIT")
 if new_hero.count("atHum:TakeDamage(realDamage)")!=1 or new_hero.count("EGGRUMBLE_VisibleCounterTell")!=1:
  raise ValueError("RED_NOT_VISIBLE_SINGLETARGET_DELAYED_PVP")
 if len([l for l in new_hero.splitlines() if ":TakeDamage(" in l.split("--",1)[0]])!=len([l for l in original_hero.splitlines() if ":TakeDamage(" in l.split("--",1)[0]])+1:
  raise ValueError("RED_UNEXPECTED_HUMANOID_DAMAGE_COUNT")
 for original,amended in ((old_rt,rt56),(original_hero,new_hero)):
  if "EGGRUMBLE_" not in amended or len(amended)<=len(original):
   raise ValueError("RED_NOT_ADDITIVE_AUTHOR_OVERLAY")
 counter=COUNTER_SRC.read_bytes()
 if not counter.startswith(b"--!strict") or counter.count(b"session.swarm.damageFromPlayer(")!=1 or b"TakeDamage(" in counter:
  raise ValueError("RED_DUPLICATE_NEUTRAL_HP_WRITER")
 out.parent.mkdir(parents=True)
 out.mkdir()
 doc=copy.deepcopy(src_doc)
 doc["name"]="GQ822_REAL56_SAME_OFFICIAL55_MUSOU_INVUL_COUNTER_SINGLETON_PRIVATE"
 log=[]
 choose={RUNTIME:rt56.encode(),COMBAT:new_hero.encode(),COUNTER:counter}
 for route in sorted(set(src)|{COUNTER}):
  oldpath=src.get(route)
  if route==COUNTER:ext=".luau";data=counter
  else:
   ext=suffix(oldpath)
   data=choose.get(route,oldpath.read_bytes())
  dest=out.joinpath("sources",*route[:-1],route[-1]+ext)
  dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_bytes(data)
  node=doc["tree"]
  for part in route[:-1]:
   if part not in node:node[part]={}
   node=node[part]
  node[route[-1]]={"$path":dest.relative_to(out).as_posix()}
  log.append({"route":"/".join(route),"sha256":digest(data),"bytes":len(data),
   "origin":"exact_official55" if route in src and route not in (COMBAT,RUNTIME)
    else "original_singleton_scoped_addition"})
 project=out/"GQ822_REAL56.project.json"
 project.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 _,after=flatten(project)
 if len(after)!=56 or set(after)!=set(src)|{COUNTER}:
  raise ValueError("RED_REAL56_ROUTE_COUNT")
 for route,oldpath in src.items():
  if route not in (COMBAT,RUNTIME) and after[route].read_bytes()!=oldpath.read_bytes():
   raise ValueError("RED_REPLACED_EXISTING55_"+"/".join(route))
 if after[COMBAT].read_text().replace(rewrite,ORIGINAL_PVP,1)!=original_hero:
  raise ValueError("RED_ORIGINAL_COMBAT_CANNOT_REVERT_TO_55")
 if after[RUNTIME].read_bytes()!=rt56.encode():
  raise ValueError("RED_ORIGINAL_MUSOU_INTERLOCK_SOURCE_DRIFT")
 for route in (COMBAT,RUNTIME,SWARM):
  if list(after).count(route)!=1:raise ValueError("RED_DUPLICATE_SINGLETON")
 report={"feature_id":"GQ822_COUNTER_REAL55_TO56_SOURCE_ADOPTION_CANDIDATE",
  "formal_rc_expected_head":FROZEN_RC,"formal_rc_updated":False,
  "original55":55,"new56":56,"other53_byte_exact":True,
  "modified_singletons":["/".join(COMBAT),"/".join(RUNTIME)],
  "new_singleton_counter_module":"/".join(COUNTER),
  "policy_original823_blob":ORIG_POLICY_BLOB,
  "previous46_runtime_blob":OLD_RUNTIME_BLOB,
  "musou_guard_preserved":True,"prehit_gate_13_preserved":True,
  "new_parallel_combat_hp_swarm_writers":0,
  "pvp_one_original_combat_delayed_counter_site":1,
  "neutral_source_authority":"original Real55 Swarm.damageFromPlayer",
  "status":"SOURCE_PREP_NOT_OFFICIAL_RC","studio2client":"NOT_TESTED",
  "android15":"NOT_TESTED","full7_role_AA_counter_effects":"PARTIAL",
  "off55":"Select exact original verified same-official-head Real55 source/project",
  "sources":log}
 (out/"GQ822_REAL56_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
 print("GQ822_REAL55_CURRENT_HEAD_PLUS_SINGLE_COUNTER_REAL56_53_SOURCE_EXACT")
 return project

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--official55",type=Path,required=True)
 p.add_argument("--receipt55",type=Path,required=True)
 p.add_argument("--prior-runtime46",type=Path,required=True)
 p.add_argument("--counter-runtime",type=Path,required=True)
 p.add_argument("--counter-author-composer",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 compose(a.official55,a.receipt55,a.prior_runtime46,a.counter_runtime,a.counter_author_composer,a.out)
