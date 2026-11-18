#!/usr/bin/env python3
"""Verify exact author-made Realm34 + Regen33 + Mage32 in one OFF31-reversible Host.
QA ONLY. Do not change a canonical gameplay script or commit to the formal RC.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re
from pathlib import Path

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
MAGE=("ServerScriptService","EGGRUMBLE_MageRevive")
REGEN=("ServerScriptService","EGGRUMBLE_NaturalRegen")
POLICY=("ServerScriptService","EGGRUMBLE_PassiveRegenPolicy")
REALM={
 ("ServerScriptService","EGGRUMBLE_LandSeaSkyTraversal"),
 ("ServerScriptService","EGGRUMBLE_RealmBattleCore"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls"),
}
COMBAT_IMPORT='local SevenRoleCombat=require(script.Parent:WaitForChild("EGGRUMBLE_SevenRoleCombat"))'
MAGE_IMPORT='local MageRevive=require(script.Parent:WaitForChild("EGGRUMBLE_MageRevive"))'
REGEN_IMPORT='local NaturalRegen=require(script.Parent:WaitForChild("EGGRUMBLE_NaturalRegen"))'
EQUIP_PATTERN=r"(?m)^([ \t]*)SevenRoleCombat\.equip\(session,p,role\)[ \t]*$"
EXPECTED_MAGE_GIT_BLOB="c75c2db439a5a68f2bc866ad42562fc16687849d"
CURRENT_RC="261b75d0a7093db5c13db3b95dad9a2911f78689"

def flatten(filename):
 p=Path(filename).resolve(strict=True)
 model=json.loads(p.read_text(encoding="utf-8"))
 if not isinstance(model.get("tree"),dict):raise ValueError("RED_PROJECT")
 found={}
 def visit(node,route=()):
  for name,entry in node.items():
   if name.startswith("$"):continue
   if not isinstance(entry,dict):raise ValueError("RED_PROJECT_NODE")
   key=route+(name,)
   if "$path" in entry:
    if key in found:raise ValueError("RED_DUPLICATE_ROUTE")
    found[key]=(p.parent/entry["$path"]).resolve(strict=True)
   else:visit(entry,key)
 visit(model["tree"])
 return model,found

def sha(path):
 return hashlib.sha256(path.read_bytes()).hexdigest()

def gitblob(path):
 body=path.read_bytes()
 return hashlib.sha1(b"blob "+str(len(body)).encode()+b"\x00"+body).hexdigest()

def inject_mage(host):
 if host.count(COMBAT_IMPORT)!=1 or MAGE_IMPORT in host:
  raise ValueError("RED_HOST_COMBAT_OR_MAGE_IMPORT")
 modified=host.replace(COMBAT_IMPORT,COMBAT_IMPORT+"\n"+MAGE_IMPORT,1)
 modified,n=re.subn(EQUIP_PATTERN,lambda m:m.group(0)+"\n"+m.group(1)+"MageRevive.attach(session,p,role)",modified)
 if n!=2:raise ValueError("RED_MAGE_TWO_EQUIP_HOOKS")
 return modified

def contract(regen_source, mage_source):
 # Important concurrency bridge: downed flag applied by Mage must disable Regen.
 required_regen=(
  'p:GetAttribute("EGGRUMBLE_Downed")==true',
  'h:GetAttribute("EGGRUMBLE_Downed")==true',
  "Policy.regenDelta(health,actualMax,clock,e.lastDamage,",
  "elapsed,true,true,burning,downed)",
  "h.Health=math.min(actualMax,health+delta)",
 )
 required_mage=(
  'e.player:SetAttribute("EGGRUMBLE_Downed",true)',
  'e.humanoid:SetAttribute("EGGRUMBLE_Downed",true)',
  'p:SetAttribute("EGGRUMBLE_Downed",false)',
  'e.humanoid:SetAttribute("EGGRUMBLE_Downed",false)',
  'table.insert(e.connections,h.Died:Connect(function() stop(p) end))',
  'table.insert(e.connections,session.world.Destroying:Connect(function() stop(p) end))',
  "if not current(e) then stop(p);return end",
  "e.humanoid.Health=math.max(e.humanoid.Health,e.humanoid.MaxHealth*REVIVE_FRACTION)",
 )
 for anchor in required_regen:
  if regen_source.count(anchor)!=1:raise ValueError("RED_REGEN_DOWNED_INTERFACE:"+anchor)
 for anchor in required_mage:
  if mage_source.count(anchor)!=1:raise ValueError("RED_MAGE_LIFECYCLE_INTERFACE:"+anchor)
 # Existing protected 'low health' design must not be falsely reported as lethal intercept.
 if "newHP>0 and newHP<previous" not in mage_source:
  raise ValueError("RED_NONLETHAL_BOUNDARY_DRIFT")
 return True

def compose(original31,combined36,mage32,out):
 original31=Path(original31).resolve(strict=True)
 combined36=Path(combined36).resolve(strict=True)
 mage32=Path(mage32).resolve(strict=True)
 out=Path(out).resolve()
 if out.exists() or out in (original31,combined36,mage32):
  raise ValueError("RED_REFUSE_OVERWRITE")
 _,base=flatten(original31)
 model,stage=flatten(combined36)
 _,mage=flatten(mage32)
 if len(base)!=31 or len(stage)!=36 or len(mage)!=32:
  raise ValueError("RED_SOURCE_COUNTS")
 if COMBAT not in base or HOST not in base or HOST not in stage:
  raise ValueError("RED_AUTHORITY_MISSING")
 if set(stage)!=set(base)|REALM|{REGEN,POLICY}:
  raise ValueError("RED_REALM_REGEN_ROUTES")
 if set(mage)!=set(base)|{MAGE}:
  raise ValueError("RED_MAGE_SOURCE_ROUTES")
 if gitblob(mage[MAGE])!=EXPECTED_MAGE_GIT_BLOB:
  raise ValueError("RED_AUTHOR_MAGE_BLOB")
 for route in base:
  if route!=HOST and (sha(stage[route])!=sha(base[route]) or sha(mage[route])!=sha(base[route])):
   raise ValueError("RED_ORIGINAL_MUTATION:"+"/".join(route))
 if sha(stage[COMBAT])!=sha(base[COMBAT]):
  raise ValueError("RED_DUPLICATED_COMBAT")
 orig=base[HOST].read_text(encoding="utf-8")
 regen_host=stage[HOST].read_text(encoding="utf-8")
 mage_host=mage[HOST].read_text(encoding="utf-8")
 if inject_mage(orig)!=mage_host:
  raise ValueError("RED_MAGE_AUTHOR_HOST_DRIFT")
 if regen_host.count(REGEN_IMPORT)!=1 or regen_host.count("NaturalRegen.attach(session,p,role)")!=2:
  raise ValueError("RED_REGEN_HOST_HOOKS")
 back=regen_host.replace(REGEN_IMPORT+"\n","",1)
 back,n=re.subn(r"(?m)^[ \t]*NaturalRegen\.attach\(session,p,role\)\n","",back)
 if n!=2 or back!=orig:
  raise ValueError("RED_REGEN_AUTHOR_HOST_DRIFT")
 contract(stage[REGEN].read_text(encoding="utf-8"),mage[MAGE].read_text(encoding="utf-8"))
 new_host=inject_mage(regen_host)
 if new_host.count(MAGE_IMPORT)!=1 or new_host.count("MageRevive.attach(session,p,role)")!=2:
  raise ValueError("RED_HOST_MAGE_DUP")
 if new_host.count(REGEN_IMPORT)!=1 or new_host.count("NaturalRegen.attach(session,p,role)")!=2:
  raise ValueError("RED_HOST_REGEN_DUP")
 out.parent.mkdir(parents=True,exist_ok=True)
 target_host=out.parent/"GQ8_REAL37_SingleHost.server.luau"
 target_host.write_text(new_host,encoding="utf-8")
 model=copy.deepcopy(model)
 model["name"]="GQ8_REAL37_REALM_REGEN_MAGE_REHEARSAL_NOT_OFFICIAL"
 def rebase(node,route=()):
  for name,entry in node.items():
   if name.startswith("$"):continue
   key=route+(name,)
   if "$path" in entry:
    entry["$path"]=os.path.relpath(target_host if key==HOST else stage[key],out.parent).replace(os.sep,"/")
   else:rebase(entry,key)
 rebase(model["tree"])
 server=model["tree"]["ServerScriptService"]
 if "EGGRUMBLE_MageRevive" in server:raise ValueError("RED_MAGE_ALREADY_ADDED")
 server["EGGRUMBLE_MageRevive"]={"$path":os.path.relpath(mage[MAGE],out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,selected=flatten(out)
 if len(selected)!=37 or set(selected)!=set(stage)|{MAGE}:
  raise ValueError("RED_NOT_REAL37")
 for route in stage:
  if route!=HOST and sha(selected[route])!=sha(stage[route]):
   raise ValueError("RED_COMBINED36_SOURCE_DRIFT")
 if sha(selected[MAGE])!=sha(mage[MAGE]) or selected[HOST].read_text(encoding="utf-8")!=new_host:
  raise ValueError("RED_MAGE_SOURCE_DRIFT")
 receipt={
  "feature_id":"GQ8_CROSSLANE_REALM_REGEN_MAGE37_QA_20261118",
  "formal_rc_head_at_selection":CURRENT_RC,
  "formal_rc_written":False, "playable_engine_accepted":False,
  "source_count":37, "inverse_off_source_count":31,
  "baseline_except_single_host_exact":30,
  "original_author_refs":{"realm764":"c51de1ed4feb7a7500ada95d21282402053ef988",
    "regen775":"5b82f300e6dee08ea1ac20ccd1449db0cd73dbc3",
    "mage777":"2f4c1e43a7802929de3f633370b32791f7bf8d96",
    "crosslane780":"8f7984c1a9db2c016321d16d47a3ea8d1b5081df"},
  "selected_sha256":{"/".join(k):sha(v) for k,v in sorted(selected.items())},
  "regen_downed_suppression_source_contract":True,
  "mage_protected_low_hp_not_lethal_0_revive":True,
  "host_unique_imports_and_2_equip_hooks_each":True,
  "rollback":"restore exact official original31; drop six new modules/scripts and replace Host with exact original",
  "studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NO_GO",
 }
 out.with_suffix(".receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("GQ8_CROSSLANE_REALM_REGEN_MAGE37_REAL_SOURCE_COMPOSE_PASS")
 return out

if __name__=="__main__":
 ap=argparse.ArgumentParser()
 for name in ("original31","combined36","mage32","out"):ap.add_argument("--"+name,required=True,type=Path)
 a=ap.parse_args()
 compose(a.original31,a.combined36,a.mage32,a.out)
