#!/usr/bin/env python3
"""Federate OTHER AUTHORS' live V3 Game/AI/ART/SCORE/neutral/item as SOURCE-only.
#501 and #494 own Swarm; #489 owns Item; #509 owns ONLY post-win Rules change.
Never replace a Game/Remote or write formal RC. All bytes verified before use.
"""
import argparse
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

RULES="EGGRUMBLE_CastleMatchRules"
ITEM="EGGRUMBLE_FieldItemPickups"
SWARM="EGGRUMBLE_SwarmCombat"
POLICIES={"EGGRUMBLE_NeutralEncounterFairness","EGGRUMBLE_NeutralSpawnPacing"}
ORIGINAL_RULES_BLOB="27da5ca1e9e6d9a7afe0674030e387f094ee7492"
PATCH_RULES_BLOB="ed87d70e7df94279af737871e8e439b9fc108d4f"
ITEM_AUTHOR_BLOB="107046cb0bf81fed9e3cba1699ada31571e44a22"
REQUIRED_8={
 "EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_ProceduralSkills",  # characters/skills
 "EGGRUMBLE_LobbyCastleModesPreview",                      # field/castles/lobby
 "EGGRUMBLE_AttackGeometry","EGGRUMBLE_SkillFX",             # combat
 "EGGRUMBLE_CastleMatchRules",                             # eggs and castle
 "EGGRUMBLE_SwarmCombat","EGGRUMBLE_NeutralStoneGiant",      # neutral
 "EGGRUMBLE_FieldItemPickups",                             # items
 "EGGRUMBLE_RoundReplay","EGGRUMBLE_ScoreBalance",         # lobby/balance
 "EGGRUMBLE_HeroSilhouetteArt","EGGRUMBLE_FlagshipFieldArt",  # art
}

def git_blob(p):
 return subprocess.check_output(["git","hash-object",str(p)],text=True).strip()

def digest(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()

def flatten(p):
 data=json.loads(p.read_text(encoding="utf-8"))
 out={}
 def walk(node,key=()):
  if not isinstance(node,dict):return
  if "$path" in node:
   assert len(node)==1 and key not in out,key
   out[key]=(p.parent/node["$path"]).resolve(strict=True)
  else:
   for name,val in node.items():
    if not name.startswith("$"):walk(val,key+(name,))
 walk(data["tree"])
 names={key[-1] for key in out}
 assert len(names)==len(out),"duplicate script name"
 return data,out

def class_for(p):
 return "Script" if p.name.endswith(".server.luau") else ("LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")

def require_receipt(path,data,base,dual):
 assert data["total_mapped"]==28
 assert data["unchanged_original26"]==25 and data["overlaid_original26"]==1
 for k,v in dual.items():
  assert data["mapped_sha256"]["/".join(k)]==digest(v),("parent receipt drift",k)
 assert len(base)==26 and len(dual)==28
 assert set(dual)-set(base)=={("ServerScriptService",p) for p in POLICIES}
 for k in base:
  if k[-1]!=SWARM:
   assert base[k].read_bytes()==dual[k].read_bytes(),("original author drift",k)
 assert dual[("ServerScriptService",SWARM)].read_bytes()!=base[("ServerScriptService",SWARM)].read_bytes()
 assert set(k[-1] for k in dual)>=REQUIRED_8

def main():
 a=argparse.ArgumentParser()
 sub=a.add_subparsers(dest="mode",required=True)
 b=sub.add_parser("compose")
 for arg in ("base26","dual28","patched_rules","original_item","out"):
  b.add_argument("--"+arg.replace("_","-"),type=Path,required=True)
 v=sub.add_parser("verify")
 v.add_argument("--project",type=Path,required=True)
 v.add_argument("--place",type=Path,required=True)
 args=a.parse_args()
 if args.mode=="verify": return verify(args.project.resolve(strict=True),args.place.resolve(strict=True))
 basefile=args.base26.resolve(strict=True)
 dualfile=args.dual28.resolve(strict=True)
 rules=args.patched_rules.resolve(strict=True)
 item=args.original_item.resolve(strict=True)
 out=args.out.resolve()
 assert out!=dualfile and not out.exists() and out.parent.is_dir()
 base_data,base=flatten(basefile)
 current_data,dual=flatten(dualfile)
 receipt=json.loads((dualfile.parent/"DUAL28_SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
 require_receipt(dualfile.parent,receipt,base,dual)
 assert git_blob(base[("ServerScriptService",RULES)])==ORIGINAL_RULES_BLOB
 assert git_blob(rules)==PATCH_RULES_BLOB
 assert git_blob(item)==ITEM_AUTHOR_BLOB
 assert dual[("ServerScriptService",RULES)].read_bytes()==base[("ServerScriptService",RULES)].read_bytes()
 assert dual[("ServerScriptService",ITEM)].read_bytes()==base[("ServerScriptService",ITEM)].read_bytes()
 current_data["name"]="EGGRUMBLE_V3_GQ_NEUTRAL_ITEM_POSTWIN_28_PRIVATE_NO_RC"
 for name,p in ((RULES,rules),(ITEM,item)):
  current_data["tree"]["ServerScriptService"][name]={"$path":os.path.relpath(p,out.parent).replace(os.sep,"/")}
 out.write_text(json.dumps(current_data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 _,result=flatten(out)
 assert len(result)==28 and set(result)==set(dual)
 changed={k for k in result if result[k].read_bytes()!=dual[k].read_bytes()}
 assert changed=={("ServerScriptService",RULES),("ServerScriptService",ITEM)},("writer collision",changed)
 # The prior #501 combined Swarm and its two original policies must be byte-for-byte unchanged.
 for name in [SWARM,*POLICIES]:
  assert result[("ServerScriptService",name)].read_bytes()==dual[("ServerScriptService",name)].read_bytes()
 for k in base:
  if k[-1] not in {RULES,ITEM,SWARM}:
   assert result[k].read_bytes()==base[k].read_bytes(),("unexpected author diff",k)
 assert sum(1 for k in base if result[k].read_bytes()==base[k].read_bytes())==23
 summary={
  "stage":"SOURCE_ONLY_PRIVATE_NO_RC",
  "feature_ids":["GQ-V3-EGG-TERMINAL-FREEZE-001","AUTHOR_489_ITEM_FAIRNESS","AUTHOR_494_501_NEUTRAL_POLICY"],
  "base_author_count":26,"script_count":28,"original_26_unchanged":23,
  "original_26_overlaid":["EGGRUMBLE_SwarmCombat #494+#501","EGGRUMBLE_FieldItemPickups #489","EGGRUMBLE_CastleMatchRules #509"],
  "extra_policies":sorted(POLICIES),"eight_area_sources_present":sorted(REQUIRED_8),
  "source_sha256":{"/".join(k):digest(p) for k,p in sorted(result.items())},
  "studio":"NOT_TESTED","android":"NOT_TESTED","owner_accepted":False,"official_rc_adopted":False,
  "rollback":"omit only #509 rules; #220 authenticated writer selects any approved source independently"
 }
 (out.parent/"FEDERATED28_RECEIPT.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("FEDERATED28_PROVENANCE_PASS 23 unchanged original + 3 author-owned patch selections + 2 policies")

def verify(project,place):
 _,mapped=flatten(project)
 receipt=json.loads((project.parent/"FEDERATED28_RECEIPT.json").read_text(encoding="utf-8"))
 assert len(mapped)==receipt["script_count"]==28
 expected={}
 for k,p in mapped.items():
  name=k[-1]
  assert receipt["source_sha256"]["/".join(k)]==digest(p),(name,"source receipt mismatch")
  expected[name]=(class_for(p),p.read_text(encoding="utf-8").replace("\r\n","\n"))
 actual={}
 for node in ET.fromstring(place.read_bytes()).iter("Item"):
  cls=node.attrib.get("class")
  if cls not in ("Script","LocalScript","ModuleScript"):continue
  props=node.find("Properties")
  assert props is not None
  name=props.findtext("string[@name='Name']")
  value=props.findtext("ProtectedString[@name='Source']")
  if value is None: value=props.findtext("string[@name='Source']")
  assert name and value is not None
  assert name not in actual,("duplicate Game/module",name)
  actual[name]=(cls,value.replace("\r\n","\n"))
 assert expected==actual,{"missing":sorted(set(expected)-set(actual)), "extra":sorted(set(actual)-set(expected)),
  "different":sorted(k for k in expected.keys()&actual.keys() if expected[k]!=actual[k])}
 receipt["place_bytes"]=place.stat().st_size
 receipt["place_sha256"]=digest(place)
 (project.parent/"FEDERATED28_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("FEDERATED28_ROJO_SOURCE_CLASS_EXACT_28_OF_28_PASS",receipt["place_bytes"],receipt["place_sha256"])

if __name__=="__main__":
 main()
