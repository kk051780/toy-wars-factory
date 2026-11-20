#!/usr/bin/env python3
"""GQ470 FB015 near-only AI hero tag, on real selected REAL69 BotActors.

Source-locked A PREP only. No change to AI decisions, egg, damage or scoring.
Studio/Android/art remain NOT_TESTED regardless of source and build QA.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

BASE="da5ca812b4852f78ffd54a49617e7d4cede75d15"
TARGET="ServerScriptService/EGGRUMBLE_BotActors"
ORIGINAL_SHA="b09627fd0995ba5938f8af5950a53462ab5df82ed91be776c9368da7a1164693"
MARK="GQ470_FB015_NEAR_BOT_TAG_REAL69_20261120"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
EDITS=(
 (' label.Name="BotObjective";label.Size=UDim2.fromOffset(180,50)',
  ' -- '+MARK+': hide long-range oversized developer ID, show only nearby tactics.\n label.Name="BotObjective";label.Size=UDim2.fromOffset(104,24)'),
 (' label.StudsOffset=Vector3.new(0,3.3,0);label.AlwaysOnTop=false;label.Parent=head',
  ' label.StudsOffset=Vector3.new(0,2.7,0);label.MaxDistance=22\n label.AlwaysOnTop=false;label.Parent=head'),
 (' text.Size=UDim2.fromScale(1,1);text.TextScaled=true;text.TextWrapped=true',
  ' text.Size=UDim2.fromScale(1,1);text.TextScaled=true;text.TextWrapped=false'),
 (' text.BackgroundColor3=Color3.fromRGB(20,30,44);text.BackgroundTransparency=.25',
  ' text.BackgroundTransparency=1'),
 (' text.Text=id.."\\n出陣";text.Parent=label',
  ' text.Text=(if team=="RED" then "赤軍" elseif team=="BLUE" then "青軍" else "AI");text.Parent=label'),
 (' hum.Name="Humanoid";hum.RequiresNeck=false;hum.MaxHealth=100;hum.Health=100',
  ' hum.Name="Humanoid";hum.RequiresNeck=false;hum.MaxHealth=100;hum.Health=100\n hum.NameDisplayDistance=0;hum.HealthDisplayDistance=18'),
 ('          ui.Text=id.."\\n"..(if goHome then "🥚 卵を帰還" elseif collectField then "🥚 野外卵を回収" elseif hasEgg then "🥚 敵城に潜入" else "⚔ 城攻め")',
  '          ui.Text=(if me.team=="RED" then "赤軍" elseif me.team=="BLUE" then "青軍" else "AI").."・"..\n           (if goHome then "帰還" elseif collectField then "回収" elseif hasEgg then "潜入" else "攻城")'),
)

def need(ok:bool,reason:str)->None:
 if not ok: raise ValueError("RED_GQ470_BOT_TAG_"+reason)

def digest(data:bytes)->str:
 return hashlib.sha256(data).hexdigest()

def selected(root:Path)->dict[str,Path]:
 project=json.loads((root/PROJECT).read_text(encoding="utf8"))
 out={}
 def visit(node,route=""):
  if not isinstance(node,dict): return
  if "$path" in node: out[route]=root/node["$path"]
  for k,v in node.items():
   if not k.startswith("$"):visit(v,route+"/"+k if route else k)
 visit(project["tree"])
 return out

def patch(src:str)->str:
 need(MARK not in src,"DUPLICATE")
 need('assert(RunService:IsStudio(),"preview bot actors are Studio-only")' in src,"REAL_STUDIO_BOT_OWNER")
 need("Router.navigate" in src and "SiegePacing.allow" in src,"KEEP_REAL_AI")
 for before,after in EDITS:
  need(src.count(before)==1,"ANCHOR_DRIFT")
  src=src.replace(before,after)
 need(src.count(MARK)==1 and "label.MaxDistance=22" in src,"NEAR_ONLY")
 need("ui.Text=id.." not in src and 'text.Text=id.."\\n' not in src,"NO_INTERNAL_IDS")
 need("NameDisplayDistance=0;hum.HealthDisplayDistance=18" in src,"NAME_HEALTH_BUDGET")
 need("RemoteEvent" not in "".join(y for _,y in EDITS),"NO_NEW_AUTHORITY")
 return src

def selftest()->None:
 original='assert(RunService:IsStudio(),"preview bot actors are Studio-only")\nRouter.navigate SiegePacing.allow\n'
 for before,_ in EDITS: original+=before+"\n"
 modified=patch(original)
 need("label.Size=UDim2.fromOffset(104,24)" in modified,"SIZE")
 need("ui.Text=(if me.team" in modified,"DYNAMIC_TEAM_AND_EGG")
 for broken in (modified,original.replace(EDITS[0][0],""),
                original.replace(EDITS[-1][0],""),
                original.replace("Router.navigate","ROUTER_REMOVED"),
                original.replace("preview bot actors are Studio-only","changed")):
  try:patch(broken)
  except ValueError:pass
  else:raise AssertionError("MUTANT_NOT_RED")
 print("GQ470_BOT_TAG_P0_SOURCE_5_NEGATIVES_PASS")

def apply(root:Path)->None:
 paths=selected(root)
 receipt_path=root/RECEIPT
 receipt=json.loads(receipt_path.read_text(encoding="utf8"))
 need(len(paths)==69 and TARGET in paths,"REAL69_SELECTED_ROUTES")
 need(receipt.get("build_head")==BASE and len(receipt.get("source_hashes",{}))==69,"OFFICIAL_PARENT")
 old={k:digest(p.read_bytes()) for k,p in paths.items()}
 need(old==receipt["source_hashes"] and old[TARGET]==ORIGINAL_SHA,"ALL69_SOURCE_LOCK")
 save=root/"off69_bot_tag"
 need(not save.exists(),"ROLLBACK_ALREADY_EXISTS")
 shutil.copytree(root/"sources",save/"sources")
 for f in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):shutil.copy2(root/f,save/f)
 new=patch(paths[TARGET].read_text(encoding="utf8")).encode("utf8")
 paths[TARGET].write_bytes(new)
 now={k:digest(p.read_bytes()) for k,p in paths.items()}
 need(len(now)==69 and {k for k in old if old[k]!=now[k]}=={TARGET},"ONE_SOURCE_68_PRESERVED")
 need(digest((save/paths[TARGET].relative_to(root)).read_bytes())==ORIGINAL_SHA,"OFF_EXACT")
 receipt["source_hashes"][TARGET]=digest(new)
 receipt["build_head"]="PREP_BOT_TAG_FROM_"+BASE
 receipt["gq470_fb015_bot_tag"]={
  "feature_id":MARK,"formal_parent":BASE,"route":TARGET,
  "original_source_sha256":ORIGINAL_SHA,"changed_source_sha256":digest(new),
  "other_selected_routes_byte_exact":68,"source_count":69,
  "tag_pixels":[104,24],"tag_max_studs":22,"near_hp_studs":18,
  "new_gameplay_authority":False,"extra_ui_instances":0,
  "rollback":"off69_bot_tag","studio":"NOT_TESTED","android":"NOT_TESTED",
  "human_art":"NOT_TESTED","owner_accepted":False}
 receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
 print("GQ470_BOT_TAG_REAL69_ONE_SOURCE_68_EXACT_OFF69_PASS")

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--base",type=Path);p.add_argument("--self-test",action="store_true")
 a=p.parse_args()
 if a.self_test:selftest()
 else:
  need(a.base is not None,"MISSING_OFFICIAL_ARTIFACT")
  apply(a.base)
