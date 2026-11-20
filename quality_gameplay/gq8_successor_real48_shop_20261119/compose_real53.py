#!/usr/bin/env python3
"""No re-authoring: true certified Real49 Musou+V2 Invul+Curse -> original four GQ805 shop routes.
This is ONE immutable source selection for a PRIVATE Real53. No game HP/Store/Remote owners added.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,os
from pathlib import Path
from compose_real48 import BLOBS,CANDIDATE,flatten,klass,blob

ROOT49=49
REAL53=53
ORIGINAL44=44
ALLOWED_NEW={
 ("ServerScriptService","EGGRUMBLE_MusouFeverPolicy"),
 ("ServerScriptService","EGGRUMBLE_InvulnerabilityPolicy"),
 ("ServerScriptService","EGGRUMBLE_InvulRuntime"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_MusouAuraClient"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_MusouAuraController"),
}
SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
COMBAT=("ServerScriptService","EGGRUMBLE_SevenRoleCombat")
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
CURSE=("ServerScriptService","EGGRUMBLE_CurseConversionPolicy")

def digest(b:bytes)->str:
 return hashlib.sha256(b).hexdigest()

def check_parent(parent49:Path,receipt49:Path,original44:Path):
 doc,old=flatten(parent49)
 _,base=flatten(original44)
 if len(old)!=ROOT49 or len(base)!=ORIGINAL44 or set(base)-set(old):
  raise ValueError("RED_REAL49_ORIGINAL44_ROUTE_COUNT")
 if set(old)-set(base)!=ALLOWED_NEW:
  raise ValueError("RED_REAL49_OTHER_NEW_AUTHORITY")
 data=json.loads(receipt49.read_text(encoding="utf8"))
 if data.get("real49")!=ROOT49 or data.get("original44")!=ORIGINAL44:
  raise ValueError("RED_REAL49_AUTHOR_RECEIPT")
 if data.get("original44_unchanged")!=37:
  raise ValueError("RED_ORIGINAL44_UNCHANGED_COUNT")
 ledger={}
 for item in data.get("sources",[]):
  route=tuple(item["route"].split("/"))
  if route in ledger or len(item.get("sha256",""))!=64:
   raise ValueError("RED_AUTHOR_RECEIPT_DUPLICATE_OR_SHA")
  ledger[route]=item
 if set(ledger)!=set(old):raise ValueError("RED_AUTHOR_SOURCE_LEDGER_MISSING_ROUTE")
 for route,file in old.items():
  b=file.read_bytes()
  if len(b)!=ledger[route]["size"] or digest(b)!=ledger[route]["sha256"]:
   raise ValueError("RED_AUTHOR_REAL49_BYTES_DRIFT_"+"/".join(route))
 unchanged={r for r in base if base[r].read_bytes()==old[r].read_bytes()}
 if len(unchanged)!=37 or any(r in unchanged for r in (SWARM,COMBAT,HOST)):
  raise ValueError("RED_NOT_ORIGINAL_SEVEN_OWNER_MODIFICATIONS")
 if not {SWARM,COMBAT,HOST,CURSE}.issubset(old):
  raise ValueError("RED_MISSING_AUTHOR_REAL_GAMEPLAY")
 if old[SWARM].read_text(encoding="utf8").count("Musou.onConfirmedKO(")!=1:
  raise ValueError("RED_NOT_ONE_ORIGINAL_KO_RECEIPT")
 invul=old[("ServerScriptService","EGGRUMBLE_InvulRuntime")].read_text(encoding="utf8")
 swarm=old[SWARM].read_text(encoding="utf8")
 if ("session.swarm.musouActive(p)" not in invul
   or 'defense.phase=="ARMED" or defense.phase=="AWAKENED"' not in swarm):
  raise ValueError("RED_BOTH_MODES_NOT_MUTUALLY_EXCLUSIVE")
 hits=sum(
  line.split("--",1)[0].count(":TakeDamage(InvulRuntime.filterDamage(")
  for route,file in old.items()
  for line in file.read_text(encoding="utf8").splitlines())
 if hits!=13:
  raise ValueError("RED_AUTHOR_ORIGINAL_THIRTEEN_PREHIT_ROUTES_"+str(hits))
 for route in ALLOWED_NEW:
  if route[-1].startswith("EGGRUMBLE_MusouAura") and klass(old[route]) not in ("LocalScript","ModuleScript"):
   raise ValueError("RED_AURA_SCRIPT_CLASS")
 if not any("EGGRUMBLE_MUSOU_AWAKEN" in old[COMBAT].read_text(encoding="utf8") for _ in [0]):
  raise ValueError("RED_MUSOU_TOOL_UNWIRED")
 return doc,old,base,unchanged

def compose(parent49:Path,receipt49:Path,original44:Path,inputs:dict,out:Path):
 out=out.resolve()
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 doc,old,base,unchanged=check_parent(parent49,receipt49,original44)
 if set(CANDIDATE)&set(old):raise ValueError("RED_SHOP_ROUTE_ALREADY_PRESENT")
 if set(inputs)!=set(BLOBS):raise ValueError("RED_NOT_FOUR_ORIGINAL_SHOP_INPUTS")
 for name,path in inputs.items():
  if blob(path.read_bytes())!=BLOBS[name]:
   raise ValueError("RED_ORIGINAL_808_816_GIT_BLOB_CHANGED_"+name)
  body=path.read_text(encoding="utf8")
  # Check executable source, not a truthful source comment such as
  # "Does not call MarketplaceService" in the original #808 view module.
  executable="\n".join(line.split("--",1)[0] for line in body.splitlines())
  if any(x in executable for x in ("RemoteEvent","DataStoreService","MarketplaceService",
                              "ProcessReceipt","PromptProductPurchase",
                              "PromptGamePassPurchase","FireServer(")):
   raise ValueError("RED_SHOP_PAYMENT_OR_REMOTE_OWNER_"+name)
 view=inputs["client"].read_text(encoding="utf8")
 if "robuxEnabled=false" not in view or "View.mount(" not in view or "Catalog.list()" not in view:
  raise ValueError("RED_SHOP_ORIGINAL_READ_ONLY_VIEW_LOST")
 out.mkdir(parents=True)
 target=copy.deepcopy(doc)
 target["name"]="EGGRUMBLE_PRIVATE_REAL53_MUSOU_INVUL_CURSE_LOBBY_NOT_OFFICIAL"
 log=[]
 def insert(route,data,ext,origin):
  f=out.joinpath("sources",*route[:-1],route[-1]+ext)
  f.parent.mkdir(parents=True,exist_ok=True)
  if f.exists():raise ValueError("RED_SOURCE_OUTPUT_COLLISION")
  f.write_bytes(data)
  node=target["tree"]
  for depth,part in enumerate(route[:-1]):
   if part not in node:node[part]={} if depth==0 else {"$className":"Folder"}
   node=node[part]
  node[route[-1]]={"$path":os.path.relpath(f,out).replace(os.sep,"/")}
  log.append({"route":"/".join(route),"class":klass(f),"bytes":len(data),
              "sha256":digest(data),"origin":origin})
 for route,source in sorted(old.items()):
  cls=klass(source)
  ext=".server.luau" if cls=="Script" else ".client.luau" if cls=="LocalScript" else ".luau"
  insert(route,source.read_bytes(),ext,"verified_exact_real49")
 for route,(name,ext) in sorted(CANDIDATE.items()):
  insert(route,inputs[name].read_bytes(),ext,"original_816" if name in ("server","client") else "original_808")
 outproject=out/"EGGRUMBLE_REAL53.project.json"
 outproject.write_text(json.dumps(target,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 _,selected=flatten(outproject)
 if len(selected)!=REAL53 or set(selected)!=(set(old)|set(CANDIDATE)):
  raise ValueError("RED_REAL53_ROUTE_COUNT_OR_COLLISION")
 for route,source in old.items():
  if source.read_bytes()!=selected[route].read_bytes() or klass(source)!=klass(selected[route]):
   raise ValueError("RED_CHANGED_REAL49_ORIGINAL_"+"/".join(route))
 for route,(name,ext) in CANDIDATE.items():
  if selected[route].read_bytes()!=inputs[name].read_bytes():
   raise ValueError("RED_CHANGED_ORIGINAL_SHOP_"+name)
 if klass(selected[("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopView")])!="ModuleScript":
  raise ValueError("RED_SHOPVIEW_WRONG_ROBLOX_CLASS")
 if (sum(route[-1]=="EGGRUMBLE_SwarmCombat" for route in selected)!=1
  or sum(route[-1]=="EGGRUMBLE_SevenRoleCombat" for route in selected)!=1
  or sum(route[-1]=="EGGRUMBLE_LobbyCastleModesPreview" for route in selected)!=1):
  raise ValueError("RED_DUPLICATE_GAMEPLAY_SINGLETON")
 report={"schema":"GQ8_REAL53_PRIVATE_MUSOU_INVUL_CURSE_READONLY_SHOP",
   "original49_sources_unchanged":49,"added_original_shop_sources":4,
   "original44_unchanged_within49":37,"selected_script_count":53,
   "actual_original_invul_prehit_routes":13,
   "all_original_curserole_musou_invul_untouched":True,
   "shop_authored_modules":"original_808_816",
   "transactions_enabled":False,"official_rc_adopted":False,
   "rollback":"Select original49 exactly; remove four original GQ805 routes",
   "studio2client":"NOT_TESTED","android15":"NOT_TESTED","fun":"NO_GO",
   "parent49_project_sha256":digest(parent49.read_bytes()),
   "sources":log}
 (out/"B_REAL53_INTAKE_RECEIPT.json").write_text(
   json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_REAL53_EXACT_ORIGINAL49_PLUS_FOUR_READONLY_SHOP_SOURCES_PASS")
 return report

if __name__=="__main__":
 pa=argparse.ArgumentParser()
 pa.add_argument("--original49",required=True,type=Path)
 pa.add_argument("--receipt49",required=True,type=Path)
 pa.add_argument("--original44",required=True,type=Path)
 for x in BLOBS:pa.add_argument("--"+x,required=True,type=Path)
 pa.add_argument("--out",required=True,type=Path)
 a=pa.parse_args()
 compose(a.original49,a.receipt49,a.original44,
         {x:getattr(a,x) for x in BLOBS},a.out)
