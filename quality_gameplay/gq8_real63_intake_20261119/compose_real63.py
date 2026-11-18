#!/usr/bin/env python3
"""Compose one verifiable REAL64 private Place from four independent SAME-REAL55 author artifacts.

No existing gameplay author is replaced. The only allowed legacy edits are:
Host <- #840, Combat + InvulRuntime <- #841. Four #829, two #838,
one #840 and one #841 new routes are integrated independently.
Current certified source profile is Real59; trade adds 3, viral and counter add 1 each.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re
from pathlib import Path
import xml.etree.ElementTree as ET

ORIGINAL55 = "a6020867fac80fa3b2ca47478625873fc6f3678e"
ORIGINAL59_HEAD = "38d11f0bf311491ba76fe03f818948e5d4b06889"
FORMAL_REAL62_PARENT = "5a47e96f6b4766a9c59dd06b111bea53b73bd5ca"
OFFICIAL = "b15db4b9ad1f1f4c1f02fb0976eb3c2f6db8a6ff"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
INVUL=("ServerScriptService","EGGRUMBLE_InvulRuntime")
HUD={
 ("ReplicatedStorage","EGGRUMBLE_HudPresentationPolicy"),
 ("ServerScriptService","EGGRUMBLE_MapVisibilityPolicy"),
 ("ServerScriptService","EGGRUMBLE_MapIntelBridge"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime"),
}
TRADE={
 ("ServerScriptService","GQ8_TradeEscrowReducer"),
 ("ServerScriptService","GQ8_TradeJournalContract"),
 ("StarterPlayer","StarterPlayerScripts","GQ8_TradeReview"),
}
VIRAL={("StarterPlayer","StarterPlayerScripts","GQ8_ViralCapture")}
COUNTER={("ServerScriptService","EGGRUMBLE_InvulCounterNeutral")}
CLASS_SUFFIX={"Script":".server.luau","LocalScript":".client.luau","ModuleScript":".luau"}
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def klass(p:Path)->str:
 for k,e in CLASS_SUFFIX.items():
  if p.name.endswith(e) and (e!=".luau" or not p.name.endswith((".server.luau",".client.luau"))):return k
 raise ValueError("RED_UNKNOWN_CLASS_"+p.name)
def flatten(path:Path):
 root=json.loads(path.read_text(encoding="utf8"))
 found={}
 def walk(node,route=()):
  for k,v in node.items():
   if k.startswith("$"):continue
   if not isinstance(v,dict) or not re.fullmatch(r"[A-Za-z0-9_]+",k):raise ValueError("RED_BAD_ROUTE")
   key=route+(k,)
   if "$path" in v:
    if key in found:raise ValueError("RED_DUPLICATE")
    p=(path.parent/v["$path"]).resolve(strict=True)
    if not p.is_file():raise ValueError("RED_BAD_PATH")
    found[key]=(klass(p),p.read_bytes())
   else:walk(v,key)
 walk(root["tree"])
 return root,found
def from_xml(path:Path):
 src={}
 def recurse(item,route):
  props=item.find("Properties")
  name=props.findtext("string[@name='Name']") if props is not None else None
  if not name or not re.fullmatch(r"[A-Za-z0-9_]+",name):raise ValueError("RED_BAD_XML_NAME")
  route=route+(name,)
  cls=item.get("class")
  if cls in CLASS_SUFFIX:
   text=props.findtext("string[@name='Source']")
   if text is None:text=props.findtext("ProtectedString[@name='Source']")
   if text is None or route in src:raise ValueError("RED_XML_SOURCE")
   src[route]=(cls,text.replace("\r\n","\n").encode("utf8"))
  for x in item.findall("Item"):recurse(x,route)
 for x in ET.parse(path).getroot().findall("Item"):recurse(x,())
 return src
def receipt_verify(src,rows,label):
 listed={}
 for x in rows:
  k=tuple(x["route"].split("/"))
  if k in listed:raise ValueError("RED_RECEIPT_DUPLICATE_"+label)
  listed[k]=x
 if set(src)!=set(listed):raise ValueError("RED_RECEIPT_ROUTES_"+label)
 for k,(cls,b) in src.items():
  x=listed[k]
  if (("class" in x and cls!=x["class"]) or len(b)!=x["bytes"] or sha(b)!=x["sha256"]):
   raise ValueError("RED_RECEIPT_BYTES_"+label+"_"+"/".join(k))
def check_diff(base,candidate,allowed_modified,allowed_added,label):
 old=set(base);now=set(candidate)
 if now-old!=allowed_added or old-now:raise ValueError("RED_ROUTE_DIFF_"+label)
 for k in old:
  if base[k][0]!=candidate[k][0]:raise ValueError("RED_CLASS_CHANGED_"+label)
  changed=base[k][1]!=candidate[k][1]
  if changed!=(k in allowed_modified):raise ValueError("RED_ORIGINAL_DRIFT_"+label+"_"+"/".join(k))
 for k in allowed_added:
  if candidate[k][0] not in CLASS_SUFFIX:raise ValueError("RED_NEW_CLASS_"+label)
def put_project(doc,sources,out):
 output=copy.deepcopy(doc);output["name"]="GQ8_REAL64_COMBINED_PRIVATE_NOT_PUBLISHED"
 for route,(cls,b) in sorted(sources.items()):
  dest=out.joinpath("sources",*route[:-1],route[-1]+CLASS_SUFFIX[cls])
  dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():raise ValueError("RED_COLLISION")
  dest.write_bytes(b)
  node=output["tree"]
  for i,name in enumerate(route[:-1]):
   if name not in node:node[name]={} if i==0 else {"$className":"Folder"}
   node=node[name]
  node[route[-1]]={"$path":dest.relative_to(out).as_posix()}
 target=out/"EGGRUMBLE_REAL64.project.json"
 target.write_text(json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 _,check=flatten(target)
 if check!=sources:raise ValueError("RED_PROJECT_ROUNDTRIP")
 return target
def run(a):
 parent_doc,base=flatten(a.base55)
 r=json.loads(a.receipt55.read_text(encoding="utf8"))
 if len(base)!=55 or r.get("source_profile")!="eggrumble_v3_real55" or r.get("selected_official_branch_sha")!=ORIGINAL55 or r.get("official_rc_adopted") is not True:
  raise ValueError("RED_BASE_NOT_OFFICIAL_REAL55")
 receipt_verify(base,r["sources"],"BASE55")
 if not {HOST,COMBAT,INVUL}.issubset(base):raise ValueError("RED_BASE_SINGLETON_MISSING")
 trade_doc,trade=flatten(a.trade62)
 viral_doc,viral=flatten(a.viral56)
 counter_doc,counter=flatten(a.counter56)
 hud=from_xml(a.hud59)
 formal62=from_xml(a.formal62)
 if len(trade)!=62 or len(formal62)!=62 or len(viral)!=56 or len(counter)!=56 or len(hud)!=59:raise ValueError("RED_CANDIDATE_SOURCE_COUNT")
 rt=json.loads(a.trade_receipt.read_text(encoding="utf8"))
 rv=json.loads(a.viral_receipt.read_text(encoding="utf8"))
 rc=json.loads(a.counter_receipt.read_text(encoding="utf8"))
 rh=json.loads(a.hud_receipt.read_text(encoding="utf8"))
 rf=json.loads(a.formal62_receipt.read_text(encoding="utf8"))
 receipt_verify(trade,rt["on_sources"],"TRADE62")
 receipt_verify(viral,rv["sources"],"VIRAL56")
 receipt_verify(counter,rc["sources"],"COUNTER56")
 receipt_verify(hud,rh["on_sources"],"HUD59")
 receipt_verify(formal62,rf["on_sources"],"FORMAL62")
 if (rh.get("official_rc_head")!=ORIGINAL55 or rh.get("official_head")!=ORIGINAL59_HEAD or rh.get("official_rc_adopted") is not True or rh.get("baseline_real55_source_count")!=55 or
     set(tuple(x.split("/")) for x in rh["new_routes"])!=HUD):
  raise ValueError("RED_HUD_BASE_CONTRACT")
 if (rt.get("canonical_rc_sha")!=ORIGINAL59_HEAD or rt.get("official59_sources_byte_exact")!=59 or rt.get("official55_sources_byte_exact")!=55 or rv.get("parent")!=55 or rc.get("original55")!=55 or rf.get("baseline_official_head")!=FORMAL_REAL62_PARENT or rf.get("combined_count")!=62 or rf.get("host_class")!="Script" or rf.get("official_rc_adopted") is not True):
  raise ValueError("RED_AUTHOR_BASE_CONTRACT")
 check_diff(base,trade,set(),HUD|TRADE,"TRADE62")
 if set(formal62)!=set(trade):raise ValueError("RED_OFFICIAL62_ROUTES_CHANGED")
 for k in formal62:
  if formal62[k][1]!=trade[k][1] or (k!=HOST and formal62[k][0]!=trade[k][0]):
   raise ValueError("RED_OFFICIAL62_NOT_ORIGINAL_HUD_TRADE_"+"/".join(k))
 if formal62[HOST][0]!="Script":raise ValueError("RED_FORMAL_REAL62_HOST_NOT_RUNNABLE")
 for k in HUD:
  if hud[k]!=trade[k]:raise ValueError("RED_TRADE62_DROPPED_OFFICIAL59_HUD")
 check_diff(base,hud,set(),HUD,"HUD")
 check_diff(base,viral,{HOST},VIRAL,"VIRAL")
 check_diff(base,counter,{COMBAT,INVUL},COUNTER,"COUNTER")
 together=set(base)|HUD|TRADE|VIRAL|COUNTER
 if len(together)!=64 or len(HUD|TRADE|VIRAL|COUNTER)!=9:
  raise ValueError("RED_CROSSLANE_COLLISION")
 chosen=dict(trade)
 if base[HOST][0]!="ModuleScript" or viral[HOST][0]!="ModuleScript":
  raise ValueError("RED_REAL59_HOST_CLASS_EXPECTED_MODULESCRIPT")
 # Reuse PR844 original single-Host class-only startup correction while retaining PR840 notification bytes.
 chosen[HOST]=("Script",viral[HOST][1])
 for k in (COMBAT,INVUL):chosen[k]=counter[k]
 for candidate,added in ((hud,HUD),(viral,VIRAL),(counter,COUNTER)):
  for k in added:chosen[k]=candidate[k]
 if len(chosen)!=64:raise ValueError("RED_REAL64_COUNT")
 for k in formal62:
  if k not in {HOST,COMBAT,INVUL} and chosen[k]!=formal62[k]:
   raise ValueError("RED_FORMAL_REAL62_59_SOURCE_LOST_"+"/".join(k))
 for k in (HOST,COMBAT,INVUL):
  if chosen[k][0]!=formal62[k][0]:
   raise ValueError("RED_FORMAL_REAL62_CLASS_DRIFT")
 if chosen[HOST][0]!="Script" or chosen[HOST][1]!=viral[HOST][1]:
  raise ValueError("RED_HOST_STARTUP_OR_VIRAL_NOTIFICATION_LOST")
 for k in hud:
  if k not in {HOST,COMBAT,INVUL} and chosen[k]!=hud[k]:
   raise ValueError("RED_CURRENT_REAL59_56_SOURCES_NOT_PRESERVED")
 for k in base:
  if k not in {HOST,COMBAT,INVUL} and chosen[k]!=base[k]:raise ValueError("RED_52_ORIGINAL_CHANGED")
 if a.out.exists():raise ValueError("RED_OUTPUT_EXISTS")
 a.out.mkdir(parents=True)
 path=put_project(parent_doc,chosen,a.out)
 off62=a.out/"off62"
 off62.mkdir()
 offpath=put_project(parent_doc,formal62,off62)
 assert len(flatten(offpath)[1])==62,"RED_OFF62_ROUTE_COUNT"
 origin={}
 for k in chosen:
  origin[k]="VERIFIED_OFFICIAL55"
  if k==HOST:origin[k]="PR844_HOST_CLASS_SCRIPT_PLUS_PR840_HOST_EXACT_PATCH"
  if k in (COMBAT,INVUL):origin[k]="PR841_ORIGINAL_SINGLETON_EXACT_PATCH"
  if k in HUD:origin[k]="PR829_HUD_EXACT"
  if k in TRADE:origin[k]="PR838_TRADE_EXACT"
  if k in VIRAL:origin[k]="PR840_VIRAL_EXACT"
  if k in COUNTER:origin[k]="PR841_COUNTER_EXACT"
 report={
  "schema":"GQ8_CROSSLANE_REAL64_SOURCE_SELECTION_V1",
  "official_base_head":OFFICIAL,"original_real55_source_head":ORIGINAL55,"original_real59_source_head":ORIGINAL59_HEAD,"original_real62_parent_head":FORMAL_REAL62_PARENT,"current_candidate_head":"CI_GITHUB_SHA",
  "formal_rc_adopted":False,"selected_real_sources":64,
  "preserved_original_unchanged":52,"preserved_current_real59_unchanged":56,"preserved_current_real62_unchanged":59,"new_since_current_real62":2,"patched_existing_singletons":["/".join(x) for x in (HOST,COMBAT,INVUL)],
  "new_sources":9,"source_owners":{"HOST_AUTOSTART_CLASS":844,"HUD_FOG":829,"TRADE_REVIEW_JOURNAL_ESCROW":838,"VIRAL":840,"COUNTER":841},
  "new_gameplay_hp_owner":0,"new_castle_round_owner":0,"new_swarm_owner":0,
  "p0_single_host_autostart_class_fixed":True,
  "paid_trade":False,"robux":False,"publish":False,
  "real_studio_2client":"NOT_TESTED","real_android_15min":"NOT_TESTED","fun":"NOT_TESTED",
  "rollback":"Rebuild current formal Real62 source profile and verify exact OFF62 original Place",
  "sources":[{"route":"/".join(k),"class":v[0],"sha256":sha(v[1]),"bytes":len(v[1]),"origin":origin[k]} for k,v in sorted(chosen.items())]
 }
 (a.out/"REAL64_INTAKE_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_REAL64_CURRENT_FORMAL62_PLUS_2_59_UNCHANGED",path)
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for key in ("base55","receipt55","trade62","trade_receipt","formal62","formal62_receipt","viral56","viral_receipt",
             "counter56","counter_receipt","hud59","hud_receipt","out"):
  p.add_argument("--"+key.replace("_","-"),type=Path,required=True)
 run(p.parse_args())
