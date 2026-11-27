#!/usr/bin/env python3
"""#824 + #822 V2: genuine single-owner Real44 -> Real49 combined MUSOU + reactive INVUL.
Composition is a source selection of proven #815, #825 and #830 author routes; it
does NOT start a second damage/combat/swarm/host server. Fail closed on source drift.
"""
import argparse,copy,hashlib,importlib.util,json,os,re
from pathlib import Path
from compose_real47 import flatten,SWARM,COMBAT,NEW as MUSOU_NEW

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
INVUL_POLICY=("ServerScriptService","EGGRUMBLE_InvulnerabilityPolicy")
INVUL_RUNTIME=("ServerScriptService","EGGRUMBLE_InvulRuntime")
NEW=set(MUSOU_NEW)|{INVUL_POLICY,INVUL_RUNTIME}
CHANGED={SWARM,COMBAT,HOST}
FEATURE="GQ8_MUSOU_INVUL_REAL49_COMPOSITE_20261119"

def sha(data):return hashlib.sha256(data).hexdigest()

def exact_once(t,old,new,label):
 n=t.count(old)
 if n!=1:raise ValueError("RED_"+label+"_EXPECTED_ONE_FOUND_"+str(n))
 return t.replace(old,new,1)

def import_owner(path):
 spec=importlib.util.spec_from_file_location("original_invul_composer",str(path.resolve(strict=True)))
 mod=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(mod)
 if sum(len(x) for x in mod.SITES.values())!=13:
  raise ValueError("RED_INVUL_13_SITE_INVENTORY_CHANGED")
 if mod.HOST!=HOST:raise ValueError("RED_INVUL_HOST_MOVED")
 return mod

def patch_invul_original(route,body,owner):
 sites=owner.SITES.get(route[-1])
 if not sites:return body,0
 count=0
 for victim,base_amount,kind,attacker in sites:
  amount=base_amount
  if route==COMBAT and victim=="enemyHum" and base_amount=="damage*duel*mark":
   # Real47 already places MUSOU bonus on the original single PvP damage site.
   amount="damage*duel*mark*musou"
  original=f"{victim}:TakeDamage({amount})"
  replacement=(f"{victim}:TakeDamage(InvulRuntime.filterDamage("
               f"{victim},{amount},\"{kind}\",{attacker}))")
  body=exact_once(body,original,replacement,"DAMAGE_ANCHOR_"+route[-1]+"_"+victim)
  count+=1
 if route==HOST:
  body=exact_once(body,owner.ORIG_REQUIRE,
    owner.ORIG_REQUIRE+"\n"+owner.REQUIRE,"HOST_INVUL_RUNTIME_REQUIRE")
  if body.count(owner.EQUIP)!=2:raise ValueError("RED_INVUL_EQUIP_OWNER_TWO")
  body,n=re.subn(r"(?m)^([ \t]*)SevenRoleCombat\.equip\(session,p,role\)[ \t]*$",
    lambda m:m.group(0)+"\n"+m.group(1)+"InvulRuntime.attach(session,p,role)",body)
  if n!=2:raise ValueError("RED_INVUL_EQUIP_TWO_"+str(n))
 else:
  if body.count(owner.REQUIRE)>0:raise ValueError("RED_DOUBLE_INVUL_REQUIRE_"+route[-1])
  body=body.replace("\n","\n"+owner.REQUIRE+"\n",1)
 return body,count

def safety_interlock(sw,rt):
 old='''  -- Future #823 invul bridge must supply its server-owned Boolean before adoption;
  -- current Core44 does not yet provide a live invulnerability state.
  local invul=ch~=nil and ch:GetAttribute("EGGRUMBLE_ServerInvulnerable")==true'''
 new='''  -- ONLY the actual #830 V2 authoritative server-ledger snapshot can block MUSOU.
  -- The guard's ARMED stance is mutually exclusive too (not yet damage immunity).
  local defense=InvulRuntime.currentPolicySnapshot(user)
  local invul=defense.phase=="ARMED" or defense.phase=="AWAKENED"'''
 sw=exact_once(sw,old,new,"AUTHORITATIVE_INVUL_RUNTIME_NOT_CLIENT_ATTR")
 old2='''  local shield=ch~=nil and ch:FindFirstChildOfClass("ForceField")~=nil'''
 new2='''  local activeShieldUntil=user:GetAttribute("EGGRUMBLE_ShieldUntil")
  local shield=(ch~=nil and ch:FindFirstChildOfClass("ForceField")~=nil)
   or (type(activeShieldUntil)=="number" and activeShieldUntil>now)'''
 sw=exact_once(sw,old2,new2,"SINGLE_EXISTING_SHIELD")
 # Defense charging is refused when offense is already active. If offense is ARMED/active,
 # it must not rely on replicated Player attrs to decide.
 src='''   local now=os.clock()
   local ok,res=Policy.arm(ledger,context(p,r,now),"SKILL")'''
 dst='''   local now=os.clock()
   if session.swarm and session.swarm.musouActive
     and session.swarm.musouActive(p)==true then return end
   local ok,res=Policy.arm(ledger,context(p,r,now),"SKILL")'''
 rt=exact_once(rt,src,dst,"NO_INVUL_ARM_WHILE_MUSOU")
 # No new direct damage or score writer in either bridge.
 for txt,label in ((rt,"INVUL_RUNTIME"),(sw,"MUSOU_SWARM")):
  if label=="INVUL_RUNTIME":
   for no in ("TakeDamage(", "Humanoid.Health=", "UpdateAsync(", "RemoteEvent", "MarketplaceService"):
    if no in txt:raise ValueError("RED_NEW_HP_OR_COMMERCE_IN_"+label)
 return sw,rt

def compose(original44,real47,ownerpath,invpolicy,invruntime,out,receipt):
 original44=Path(original44).resolve(strict=True)
 real47=Path(real47).resolve(strict=True)
 invpolicy=Path(invpolicy).resolve(strict=True)
 invruntime=Path(invruntime).resolve(strict=True)
 owner=import_owner(Path(ownerpath))
 old_doc,old=flatten(original44)
 doc,selected=flatten(real47)
 if len(old)!=44 or len(selected)!=47 or set(selected)!=(set(old)|set(MUSOU_NEW)):
  raise ValueError("RED_SOURCE_BASE_LINEAGE_NOT_REAL44_PLUS_REAL47")
 for route,path in old.items():
  if route not in (SWARM,COMBAT) and path.read_bytes()!=selected[route].read_bytes():
   raise ValueError("RED_REAL47_UNEXPECTED_ORIGINAL_OWNER_CHANGE_"+"/".join(route))
 if not (invpolicy.read_bytes().startswith(b"--!strict")
    and b"GQ8_INVUL_REACTIVE_COUNTER_AWAKENING_V2" in invpolicy.read_bytes()):
  raise ValueError("RED_NOT_UPSTREAM_V2_POLICY")
 bodies={}
 hit_count=0
 for route in old:
  original=selected[route].read_text(encoding="utf8")
  amended,n=patch_invul_original(route,original,owner)
  hit_count+=n
  if amended!=original:bodies[route]=amended
 if hit_count!=13:raise ValueError("RED_DID_NOT_WIRE_ALL13")
 if set(bodies)!={("ServerScriptService",name) for name in owner.SITES}:
  raise ValueError("RED_ORIGINAL_7_DAMAGE_OWNERS_NOT_EXACT")
 # #830 did not have #825, hence required *two-way* mutual exclusion here.
 bodies[SWARM],real_rt=safety_interlock(bodies[SWARM],
                                       invruntime.read_text(encoding="utf8"))
 bodies[INVUL_POLICY]=invpolicy.read_text(encoding="utf8")
 bodies[INVUL_RUNTIME]=real_rt
 # Exactly 7 original source owners modified; no parallel Score, HP, Swarm or Host.
 out=Path(out).resolve()
 receipt=Path(receipt).resolve()
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 out.parent.mkdir(parents=True,exist_ok=True)
 patched_sources=out.parent/"composed49"
 patched_sources.mkdir(exist_ok=True)
 new_doc=copy.deepcopy(doc)
 server=new_doc["tree"]["ServerScriptService"]
 if INVUL_POLICY[-1] in server or INVUL_RUNTIME[-1] in server:
  raise ValueError("RED_DUPLICATE_INVUL_RUNTIME_POLICY")
 for route,body in bodies.items():
  is_added=route in (INVUL_POLICY,INVUL_RUNTIME)
  if is_added and route in selected:raise ValueError("RED_NEW_SOURCE_SHADOW")
  source=patched_sources.joinpath(*route[:-1],route[-1]+".luau")
  source.parent.mkdir(parents=True,exist_ok=True)
  source.write_text(body,encoding="utf8",newline="\n")
  node=new_doc["tree"]
  for part in route:node=node[part] if part in node else node.setdefault(part,{})
  node["$path"]=os.path.relpath(source,out.parent).replace(os.sep,"/")
 # relink all other original sources to their exact Real47 author paths,
 # because Real47 sits in a different directory from the Real49 project.
 def relink(node,route=()):
  for name,item in node.items():
   if name.startswith("$"):continue
   at=route+(name,)
   if "$path" in item:
    if at not in bodies:
     item["$path"]=os.path.relpath(selected[at],out.parent).replace(os.sep,"/")
   else:relink(item,at)
 relink(new_doc["tree"])
 new_doc["name"]="GQ8_ORIGINAL_MUSOU_INVUL_REAL49_PRIVATE_NOT_OFFICIAL"
 out.write_text(json.dumps(new_doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 _,new=flatten(out)
 if set(new)!=(set(old)|NEW) or len(new)!=49:raise ValueError("RED_NOT_49_ACTUAL_ROUTES")
 changed=[r for r in old if old[r].read_bytes()!=new[r].read_bytes()]
 if len(changed)!=7 or set(changed)!=set(bodies)-{INVUL_POLICY,INVUL_RUNTIME}:
  raise ValueError("RED_EXPECT_ONLY_ORIGINAL_SEVEN_DAMAGE_OWNERS")
 preserved=[r for r in old if r not in changed]
 if len(preserved)!=37:raise ValueError("RED_UNCHANGED_37_WRONG")
 for route in preserved:
  if new[route].read_bytes()!=old[route].read_bytes():
   raise ValueError("RED_UNEXPECTED_AUTHOR_CHANGE")
 for route in MUSOU_NEW:
  if new[route].read_bytes()!=selected[route].read_bytes():
   raise ValueError("RED_MUSOU_ORIGINAL_NEW_MODULE_CHANGED")
 if new[INVUL_POLICY].read_bytes()!=invpolicy.read_bytes():
  raise ValueError("RED_UPSTREAM_V2_POLICY_MUTATION")
 direct=sum(line.split("--",1)[0].count(":TakeDamage(")
  for route in new for line in new[route].read_text().splitlines())
 wrapped=sum(new[route].read_text().count(":TakeDamage(InvulRuntime.filterDamage(")
  for route in new)
 if direct!=13 or wrapped!=13:
  raise ValueError("RED_UNWRAPPED_OR_UNKNOWN_DIRECT_DAMAGE_SITE_"+str((direct,wrapped)))
 if new[SWARM].read_text().count("Musou.onConfirmedKO(")!=1:
  raise ValueError("RED_MUSOU_KO_OWNER_DUPLICATE")
 if new[COMBAT].read_text().count("enemyHum:TakeDamage(")!=1:
  raise ValueError("RED_PVP_DOUBLE_WRITER")
 if new[HOST].read_text().count("InvulRuntime.attach(session,p,role)")!=2:
  raise ValueError("RED_NOT_TWO_EXISTING_HOST_ATTACH")
 if new[INVUL_RUNTIME].read_text().count("session.swarm.musouActive(p)")==0:
  raise ValueError("RED_INVUL_ARM_OFFENSE_CONFLICT")
 if 'defense.phase=="ARMED" or defense.phase=="AWAKENED"' not in new[SWARM].read_text():
  raise ValueError("RED_MUSOU_DEFENSE_CONFLICT")
 data={
  "feature_id":FEATURE,"official_rc_adopted":False,"base":44,"selected":49,
  "original_damage_sites":13,"gated_damage_sites":wrapped,
  "original_changed":sorted("/".join(x) for x in changed),
  "original_byte_identical":37,
  "new_modules":sorted("/".join(x) for x in NEW),
  "new_damage_writer_count":0,
  "single_swarm_ko_fence":True,
  "offense_defense_mutual_exclusion":True,
  "source_sha256":{"/".join(k):sha(new[k].read_bytes()) for k in sorted(new)},
  "off44":"original44 exact source", "off46":"genuine #830 source",
  "off47":"original #825 source", "studio_2client":"NOT_TESTED","android15":"NOT_TESTED",
  "real_status_fall_knockback":"UNTESTED_AND_PARTIALLY_UNGATED"
 }
 receipt.parent.mkdir(parents=True,exist_ok=True)
 receipt.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
 print("GQ8_REAL49_SINGLE_AUTHOR_ALL13_PREHIT_MUSOU_KO_TWO_WAY_EXCLUSION_PASS")
 return new

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--original44",type=Path,required=True)
 ap.add_argument("--real47",type=Path,required=True)
 ap.add_argument("--invul-composer",type=Path,required=True)
 ap.add_argument("--invul-policy",type=Path,required=True)
 ap.add_argument("--invul-runtime",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 ap.add_argument("--receipt",type=Path,required=True)
 a=ap.parse_args()
 compose(a.original44,a.real47,a.invul_composer,a.invul_policy,
         a.invul_runtime,a.out,a.receipt)
