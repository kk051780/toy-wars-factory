#!/usr/bin/env python3
"""GQ822 V2 original Real44 -> private Real46 (source-only rehearsal).

Reuse every original 44 script from #815 / real44 portable artifact byte-exact
except the seven original TakeDamage owner sources and one existing Host.
No old Combat/AI/Swarm/Realm/Guardian logic duplicated; mutate 13 exact calls
in place to pass the computed delta through a shared pre-HP gate.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
RUNTIME=ROOT/"EGGRUMBLE_InvulRuntime.luau"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
POLICY_NAME="EGGRUMBLE_InvulnerabilityPolicy"
RUNTIME_NAME="EGGRUMBLE_InvulRuntime"
REQUIRE='local InvulRuntime=require(script.Parent:WaitForChild("EGGRUMBLE_InvulRuntime"))'
ORIG_REQUIRE='local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
EQUIP="SevenRoleCombat.equip(session,p,role)"
# Exact accepted original Real44 human/mixed/BOT/neutral damage owners, from
# read-only QA #827. Unknown extra or mutated calls fail closed.
SITES={
 "EGGRUMBLE_SevenRoleCombat":(
  ("h","damage*duel*mark","PLAYER","p.UserId"), # NPC bot victim; no player => passthrough
  ("enemyHum","damage*duel*mark","PLAYER","p.UserId"),
  ("h","tick","ENVIRONMENT",'"STATUS_DOT"')),
 "EGGRUMBLE_BotActors":(
  ("nearestHumanoid","BOT_HERO_DAMAGE","NEUTRAL",'"BOT_ACTOR"'),
  ("targetHumanoid","BOT_HERO_DAMAGE","NEUTRAL",'"BOT_ACTOR"')),
 "EGGRUMBLE_SwarmCombat":(
  ("h","effectiveDamage","PLAYER",'"SWARM_ATTACKER"'), # neutral victim bypass
  ("candidate.victim.humanoid","Melee.DAMAGE","NEUTRAL",'"SWARM_MELEE"')),
 "EGGRUMBLE_NeutralStoneGiant":(("h","28","BOSS",'"STONE_GIANT"'),),
 "EGGRUMBLE_LobbyCastleModesPreview":(
  ("closest.hum","Policy.CONFIG[kind].damage","ENVIRONMENT",'"LOBBY_HAZARD"'),),
 "EGGRUMBLE_RealmBattleCore":(
  ("pilotHumanoid","18","ENVIRONMENT",'"REALM_PILOT"'),
  ("h","6","ENVIRONMENT",'"REALM_FIELD"')),
 "EGGRUMBLE_CastleGuardianRuntime":(
  ("foe.hum","c.damage","NEUTRAL",'"GUARDIAN_ATTACK"'),
  ("hum","math.min(damage,45)","NEUTRAL",'"GUARDIAN_COUNTER"')),
}
assert sum(len(v) for v in SITES.values())==13
def flatten(project):
 project=Path(project).resolve(strict=True)
 doc=json.loads(project.read_text(encoding="utf-8"))
 found={}
 def walk(node,route=()):
  for key,entry in node.items():
   if key.startswith("$"):continue
   if not isinstance(entry,dict):raise ValueError("RED_BAD_PROJECT_TREE")
   at=route+(key,)
   if "$path" in entry:
    if at in found:raise ValueError("RED_ROUTE_DUP")
    found[at]=(project.parent/entry["$path"]).resolve(strict=True)
   else:walk(entry,at)
 walk(doc["tree"])
 return doc,found
def exact_blob(data):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def source_suffix(file):
 for suffix in (".server.luau",".client.luau",".luau"):
  if file.name.endswith(suffix):return suffix
 raise ValueError("RED_BAD_SOURCE_CLASS_"+file.name)
def patched(source,sites,which):
 text=source
 for victim,amount,kind,attacker in sites:
  old=f"{victim}:TakeDamage({amount})"
  if text.count(old)!=1:
   raise ValueError("RED_MISSING_OR_DUPLICATE_EXISTING_HIT_"+which+"_"+old)
  replacement=(f"{victim}:TakeDamage(InvulRuntime.filterDamage("
    f"{victim},{amount},\"{kind}\",{attacker}))")
  text=text.replace(old,replacement,1)
 return text
def compose(original44,policy_src,out):
 original44=Path(original44).resolve(strict=True)
 policy_src=Path(policy_src).resolve(strict=True)
 out=Path(out).resolve()
 if out.exists() or out in (original44,policy_src):raise ValueError("RED_REFUSE_SOURCE_OVERWRITE")
 doc,files=flatten(original44)
 if len(files)!=44:raise ValueError("RED_NOT_REAL44")
 server=doc["tree"].get("ServerScriptService")
 if not isinstance(server,dict) or POLICY_NAME in server or RUNTIME_NAME in server:
  raise ValueError("RED_DUPLICATE_SERVER_POLICY_RUNTIME")
 name_to_route={r[-1]:r for r in files}
 if any(k not in name_to_route for k in SITES):raise ValueError("RED_MISSING_AUTHOR_DAMAGE_OWNER")
 if HOST not in files:raise ValueError("RED_NO_HOST")
 count_old_damage=sum(line.split("--",1)[0].count(":TakeDamage(")
  for source in files.values() for line in source.read_text(encoding="utf-8").splitlines())
 if count_old_damage!=13:
  raise ValueError("RED_UNKNOWN_UNAUDITED_DIRECT_DAMAGE_ROUTE_"+str(count_old_damage))
 originalHost=files[HOST].read_text(encoding="utf-8")
 if originalHost.count(ORIG_REQUIRE)!=1 or originalHost.count(EQUIP)!=2:
  raise ValueError("RED_UNEXPECTED_AUTHOR_HOST")
 if REQUIRE in originalHost:raise ValueError("RED_ALREADY_GATE")
 p=policy_src.read_bytes()
 if not p.startswith(b"--!strict") or b"GQ8_INVUL_REACTIVE_COUNTER_AWAKENING_V2" not in p:
  raise ValueError("RED_NOT_ORIGINAL_V2_POLICY")
 out.parent.mkdir(parents=True,exist_ok=True)
 model=copy.deepcopy(doc);model["name"]="GQ822_REAL44_ORIGINAL_OWNER_PREHIT_GATE46_PRIVATE_NOT_RC"
 target_dir=out.parent/"source46"
 target_dir.mkdir(exist_ok=True)
 overwritten={}
 sites_written=0
 for route,file in files.items():
  original=file.read_text(encoding="utf-8")
  body=original
  if route[-1] in SITES:
   body=patched(body,SITES[route[-1]],route[-1])
   sites_written+=len(SITES[route[-1]])
   if route==HOST:
    if body.count(ORIG_REQUIRE)!=1 or body.count(EQUIP)!=2:
     raise ValueError("RED_HOST_SIGNATURE_AFTER_PATCH")
    body=body.replace(ORIG_REQUIRE,ORIG_REQUIRE+"\n"+REQUIRE,1)
    body,n=re.subn(r"(?m)^([ \t]*)SevenRoleCombat\.equip\(session,p,role\)[ \t]*$",
      lambda match:match.group(0)+"\n"+match.group(1)+"InvulRuntime.attach(session,p,role)",body)
    if n!=2:raise ValueError("RED_NOT_TWO_EQUIP_HOOKS")
   else:
    if body.count(REQUIRE)>0:raise ValueError("RED_ALREADY_GATE")
    body=body.replace("\n","\n"+REQUIRE+"\n",1)
   overwritten["/".join(route)]=hashlib.sha256(body.encode()).hexdigest()
  # All non-selected original source files are copied byte-for-byte.
  target=target_dir.joinpath(*route[:-1],route[-1]+source_suffix(file))
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_text(body,encoding="utf-8")
  node=model["tree"]
  for k in route:node=node[k]
  node["$path"]=os.path.relpath(target,out.parent).replace(os.sep,"/")
 if sites_written!=13 or len(overwritten)!=7:
  raise ValueError("RED_13_GATES_NOT_ALL_SEVEN_ORIGINAL_OWNERS")
 for name,source in ((POLICY_NAME,policy_src),(RUNTIME_NAME,RUNTIME)):
  target=target_dir/"ServerScriptService"/(name+".luau")
  target.write_bytes(source.read_bytes())
  server=model["tree"]["ServerScriptService"]
  server[name]={"$path":os.path.relpath(target,out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n")
 _,new=flatten(out)
 if len(new)!=46 or set(new)-set(files)!={( "ServerScriptService",POLICY_NAME),("ServerScriptService",RUNTIME_NAME)}:
  raise ValueError("RED_NOT_SINGLE_46_SOURCE")
 unaffected=[route for route in files if "/".join(route) not in overwritten]
 if len(unaffected)!=37 or any(new[route].read_bytes()!=files[route].read_bytes() for route in unaffected):
  raise ValueError("RED_ORIGINAL37_BYTES_CHANGED")
 for route,file in files.items():
  if route[-1] not in SITES:continue
  text=new[route].read_text(encoding="utf-8")
  for victim,amount,kind,attacker in SITES[route[-1]]:
   newcall=f"{victim}:TakeDamage(InvulRuntime.filterDamage({victim},{amount},\"{kind}\",{attacker}))"
   if text.count(newcall)!=1:raise ValueError("RED_GATE_NOT_APPLIED_ON_ORIGINAL_HIT")
  if text.count(REQUIRE)!=1:raise ValueError("RED_MULTIPLE_GATE_OWNERS")
 host=new[HOST].read_text()
 if host.count("InvulRuntime.attach(session,p,role)")!=2:raise ValueError("RED_FREE_ACTIVATION_NOT_ATTACHED")
 receipt={
  "feature_id":"GQ822_REAL44_TO46_V2_PREHIT_GATE_STAGE1",
  "original44":44,"candidate46":46,"original_unmodified_source_count":len(unaffected),
  "existing_modified_source_count":7,"original_direct_hit_sites_guarded":sites_written,
  "all_original13_take_damage_sites_guarded":True,
  "original_unknown_indirect_health_writes_cleared":False,
  "original_full_CC_and_fall_elimination_guarded":False,
  "new_HP_damage_writer_count":0,
  "new_FreeSkill_tools_per_current_avatar":1,
  "feature_scope":"raw 13 direct TakeDamage original source sites; free skill only",
  "source_policy_blob":exact_blob(p),"author_policy_pr":823,
  "original_host_only_one":True,"original_combat_swarm_game_roles_preserved":True,
  "studio2client":"NOT_TESTED","android15":"NOT_TESTED",
  "official_rc_adopted":False,"primary_rich51_unchanged":True,
  "off44":"Rebuild unmodified exact original Real44 project; no canonical RC write",
  "changed_sources":sorted(overwritten),
 }
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print("GQ822_ORIGINAL_REAL44_DIRECT13_PREHIT_GATE_REAL46_SOURCE_EXACT_PASS")
 return out
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--original44",type=Path,required=True)
 p.add_argument("--policy",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 compose(a.original44,a.policy,a.out)
