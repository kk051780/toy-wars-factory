#!/usr/bin/env python3
"""GQ8 crosslane: genuine #815 private Real44 + exact #816/#808 read-only kiosk -> Real48.
No competing game, shop, wallet, combat, neutral, damage, score or Store authority.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re
from pathlib import Path

SOURCE44=44
SOURCE48=48
HEX40=re.compile(r"^[0-9a-f]{40}$")
SAFE=re.compile(r"^[A-Za-z0-9_]+$")
CANDIDATE={
 ("ServerScriptService","GQ805_LobbyGuildShop"):("server",".server.luau"),
 ("StarterPlayer","StarterPlayerScripts","GQ805_ShopKioskClient"):("client",".client.luau"),
 ("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopCatalog"):("catalog",".luau"),
 ("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopView"):("view",".luau"),
}
BLOBS={
 "server":"911ce453a91b0ff7be69e232028611e906e13d3d",
 "client":"59eeb7c8b78a136d6bcb89062afc4f5b9d539d83",
 "catalog":"f71eb575aacd61dd8ccb7719f7dae4caec5fedcd",
 "view":"f3cf10c8b0256896e9d194844deda91039429ddc",
}

def blob(data:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def klass(path:Path)->str:
 n=path.name
 if n.endswith(".server.luau"):return "Script"
 if n.endswith(".client.luau"):return "LocalScript"
 if n.endswith(".luau"):return "ModuleScript"
 raise ValueError("RED_SOURCE_CLASS_"+n)

def flatten(project:Path):
 project=project.resolve(strict=True)
 doc=json.loads(project.read_text(encoding="utf8"))
 found={}
 def walk(node,route=()):
  for name,child in node.items():
   if name.startswith("$"):continue
   if not SAFE.fullmatch(name) or not isinstance(child,dict):raise ValueError("RED_UNSAFE_ROUTE")
   key=route+(name,)
   if "$path" in child:
    if key in found or not isinstance(child["$path"],str):raise ValueError("RED_DUPLICATE_ROUTE")
    file=(project.parent/child["$path"]).resolve(strict=True)
    if not file.is_file():raise ValueError("RED_NOT_SOURCE")
    found[key]=file
   else:walk(child,key)
 walk(doc["tree"])
 return doc,found

def compose(project44:Path,receipt44:Path,inputs:dict,out:Path):
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 original,old=flatten(project44)
 receipt=json.loads(receipt44.read_text(encoding="utf8"))
 if len(old)!=SOURCE44 or receipt.get("candidate_source_count")!=SOURCE44:
  raise ValueError("RED_ORIGINAL_44_SOURCE_COUNT")
 if set(old)&set(CANDIDATE):raise ValueError("RED_EXISTING_SHOP_ROUTE_DUPLICATE")
 if not {("ServerScriptService","EGGRUMBLE_SwarmCombat"),
         ("ServerScriptService","EGGRUMBLE_CurseConversionPolicy"),
         ("ServerScriptService","EGGRUMBLE_FieldItemPickups"),
         ("ServerScriptService","EGGRUMBLE_CastleGuardianRuntime"),
         ("ServerScriptService","EGGRUMBLE_RealmBattleCore"),
         ("ServerScriptService","GQ802_StageTileVisualRenderer")}.issubset(old):
  raise ValueError("RED_MISSING_ORIGINAL_MULTILANE_RUNTIME")
 ledger=receipt.get("sources")
 if not isinstance(ledger,list) or len(ledger)!=SOURCE44:
  raise ValueError("RED_ORIGINAL_44_RECEIPT_INCOMPLETE")
 oldsha={}
 for item in ledger:
  route=tuple(item["route"].split("/"))
  if route in oldsha or not item.get("sha256"):raise ValueError("RED_DUPLICATE_RECEIPT")
  oldsha[route]=item
 if set(oldsha)!=set(old):raise ValueError("RED_ORIGINAL_RECEIPT_ROUTE_DRIFT")
 for route,file in old.items():
  item=oldsha[route]
  if len(file.read_bytes())!=item["bytes"] or hashlib.sha256(file.read_bytes()).hexdigest()!=item["sha256"]:
   raise ValueError("RED_SELECTED_44_SOURCE_DRIFT_"+"/".join(route))
 for name,source in inputs.items():
  if name not in BLOBS or blob(source.read_bytes())!=BLOBS[name]:
   raise ValueError("RED_ORIGINAL_808_OR_816_SOURCE_DRIFT_"+name)
 if set(inputs)!=set(BLOBS):raise ValueError("RED_MISSING_SHOP_SOURCE")
 client=inputs["client"].read_text(encoding="utf8")
 if not all(k in client for k in ("View.mount(","Catalog.list()","robuxEnabled=false","nil)")):
  raise ValueError("RED_PURCHASE_ENABLED")
 for unsafe in ("RemoteEvent","FireServer(","DataStoreService","ProcessReceipt","PromptProductPurchase","PromptGamePassPurchase"):
  for name,src in inputs.items():
   if unsafe in src.read_text(encoding="utf8"):raise ValueError("RED_SHOP_NEW_AUTHORITY_"+unsafe+"_"+name)
 out.mkdir(parents=True)
 selected=copy.deepcopy(original)
 selected["name"]="GQ8_REAL48_CURSE_AND_READONLY_GUILD_SHOP_NOT_FORMAL_RC"
 log=[]
 def add(route,data,suffix,origin):
  relative=Path("sources").joinpath(*route[:-1],route[-1]+suffix)
  file=out/relative
  if file.exists():raise ValueError("RED_OUTPUT_SCRIPT_COLLISION")
  file.parent.mkdir(parents=True,exist_ok=True)
  file.write_bytes(data)
  node=selected["tree"]
  for depth,part in enumerate(route[:-1]):
   if part not in node:
    node[part]={} if depth==0 else {"$className":"Folder"}
   node=node[part]
  node[route[-1]]={"$path":relative.as_posix()}
  log.append({"route":"/".join(route),"class":klass(file),"sha256":hashlib.sha256(data).hexdigest(),
              "git_blob":blob(data),"bytes":len(data),"origin":origin})
 for route,file in sorted(old.items()):
  suffix=".server.luau" if klass(file)=="Script" else (".client.luau" if klass(file)=="LocalScript" else ".luau")
  add(route,file.read_bytes(),suffix,"immutable_real44_original")
 for route,(name,suffix) in sorted(CANDIDATE.items()):
  add(route,inputs[name].read_bytes(),suffix,"exact_original_"+("808_policy" if name in ("catalog","view") else "816_additive"))
 portable=out/"EGGRUMBLE_REAL48.project.json"
 portable.write_text(json.dumps(selected,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 _,installed=flatten(portable)
 if len(installed)!=SOURCE48 or set(installed)!=(set(old)|set(CANDIDATE)):
  raise ValueError("RED_REAL48_ROUTES")
 for route,file in old.items():
  if file.read_bytes()!=installed[route].read_bytes() or klass(file)!=klass(installed[route]):
   raise ValueError("RED_ORIGINAL44_MUTATED_"+"/".join(route))
 for route,(name,suffix) in CANDIDATE.items():
  if inputs[name].read_bytes()!=installed[route].read_bytes():
   raise ValueError("RED_ADDITIVE_MUTATED_"+"/".join(route))
 if klass(installed[("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopView")])!="ModuleScript":
  raise ValueError("RED_SHOPVIEW_WRONG_ROBLOX_CLASS")
 report={"schema":"GQ8_TRUE_REAL48_CROSSLANE_INTAKE","on_source_count":48,
 "off_source_count":44,"original44_preserved":44,"added_new_runtime":2,
 "added_original808_modules":2,"one_swarm_host_damage_owner":True,
 "original808_author_sha":{k:BLOBS[k] for k in ("catalog","view")},
 "original816_runtime_sha":{k:BLOBS[k] for k in ("server","client")},
 "seller_purchases_enabled":False,"official_rc_adopted":False,
 "studio_2client":"NOT_TESTED","android15":"NOT_TESTED","fun":"NOT_TESTED",
 "rollback":"Select original portable44 unchanged; drop all four GQ805 routes",
 "scripts":log}
 (out/"B_REAL48_INTAKE_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_REAL48_SOURCE_PRESERVATION_AND_ROLLBACK_OFF44_PASS")
 return report

if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--original44",type=Path,required=True)
 parser.add_argument("--receipt44",type=Path,required=True)
 for name in BLOBS:parser.add_argument("--"+name,type=Path,required=True)
 parser.add_argument("--out",type=Path,required=True)
 args=parser.parse_args()
 compose(args.original44,args.receipt44,{k:getattr(args,k) for k in BLOBS},args.out)
