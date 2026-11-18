#!/usr/bin/env python3
"""Correct single-canonical-lineage: official candidate REAL59 HUD/Fog + 3 scoped trade
components => REAL62 private companion. Never select high REAL count as proof.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq8_successor_real48_shop_20261119"))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"handoffs"/"EGGRUMBLE-HUD-INTEL-20261119"))
from compose_real40 import contents,project_for,digest
from compose_real48 import flatten,klass
OFFICIAL59="5a47e96f6b4766a9c59dd06b111bea53b73bd5ca"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
ADDS={
 ("ServerScriptService","GQ8_TradeJournalContract"):("ModuleScript","GQ8_TradeJournalContract.luau"),
 ("ServerScriptService","GQ8_TradeEscrowReducer"):("ModuleScript","GQ8_TradeEscrowReducer.luau"),
 ("StarterPlayer","StarterPlayerScripts","GQ8_TradeReview"):("LocalScript","GQ8_TradeReview.client.luau"),
}
HUD_SOURCE={
 ("ReplicatedStorage","EGGRUMBLE_HudPresentationPolicy"):"HudPresentationPolicy.luau",
 ("ServerScriptService","EGGRUMBLE_MapVisibilityPolicy"):"MapVisibilityPolicy.luau",
 ("ServerScriptService","EGGRUMBLE_MapIntelBridge"):"EGGRUMBLE_MapIntelBridge.server.luau",
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_HudIntelRuntime"):"EGGRUMBLE_HudIntelRuntime.client.luau",
}
def compose(parent59:Path,receipt59:Path,host59:Path,hostReceipt:Path,official55:Path,out:Path):
 if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
 receipt=json.loads(receipt59.read_text(encoding="utf8"))
 if (receipt.get("selected59_place_sha256")!=digest(parent59) or
    receipt.get("baseline55_exact_sources_unchanged") is not True or
    len(receipt.get("on_sources",[]))!=59 or len(receipt.get("off_sources",[]))!=55):
  raise ValueError("RED_REAL59_PARENT_NOT_SHA_VERIFIED")
 preHost,preClasses=contents(ET.parse(parent59).getroot())
 original,classes=contents(ET.parse(host59).getroot())
 hostRecord=json.loads(hostReceipt.read_text(encoding="utf8"))
 base55,classes55=contents(ET.parse(official55).getroot())
 if (hostRecord.get("host_old_class")!="ModuleScript" or
     hostRecord.get("host_new_class")!="Script" or hostRecord.get("source_bytes_modified")!=0):
  raise ValueError("RED_UNVERIFIED_P0_HOST_CLASS_FIX_RECEIPT")
 if (len(preHost)!=59 or len(original)!=59 or len(base55)!=55
     or set(preHost)!=set(original) or not set(base55).issubset(original)
     or preClasses.get(HOST)!="ModuleScript" or classes.get(HOST)!="Script"):
  raise ValueError("RED_REAL59_HOST_OR_ORIGINAL55_COUNT_CLASS")
 for key,item in preHost.items():
  if original[key]!=item or (key!=HOST and preClasses[key]!=classes[key]):
   raise ValueError("RED_P0_HOST_FIX_ALTERED_SOURCE_OR_UNRELATED_CLASS_"+"/".join(key))
 for k,item in base55.items():
  if original[k]!=item or (k!=HOST and classes.get(k)!=classes55.get(k)):
   raise ValueError("RED_OFFICIAL55_ORIGINAL_SOURCE_DRIFT_"+"/".join(k))
 onReceipts={tuple(s["route"].split("/")):s for s in receipt["on_sources"]}
 if set(onReceipts)!=set(original):raise ValueError("RED_REAL59_RECEIPT_ROUTE_MISMATCH")
 for key,(cls,source) in original.items():
  row=onReceipts[key]
  expectedClass="ModuleScript" if key==HOST else cls
  if row["class"]!=expectedClass or row["sha256"]!=hashlib.sha256(source.encode("utf8")).hexdigest():
   raise ValueError("RED_REAL59_SOURCE_BLOB_DRIFT_"+"/".join(key))
 for key,filename in HUD_SOURCE.items():
  f=Path("handoffs/EGGRUMBLE-HUD-INTEL-20261119")/filename
  if key not in original or original[key][1]!=f.read_text(encoding="utf8").replace("\r\n","\n"):
   raise ValueError("RED_OFFICIAL59_HUD_FOG_DRIFT_"+"/".join(key))
 for key in ADDS:
  if key in original:raise ValueError("RED_COLLIDING_TRADE_SOURCE_"+"/".join(key))
 if len({x[-1] for x in set(original)|set(ADDS)})!=62:
  raise ValueError("RED_DUPLICATE_NAME")
 out.mkdir(parents=True)
 off=out/"off59";off.mkdir()
 offProject,offRoutes=project_for(original,classes,off,"GQ8_REAL59_HOST_ACTIVE_CANDIDATE_NOT_OFFICIAL")
 plus=dict(original)
 for route,(cls,filename) in ADDS.items():
  source=(HERE/filename).read_text(encoding="utf8").replace("\r\n","\n")
  plus[route]=(cls,source)
  classes[route]=cls
  for i in range(1,len(route)):
   p=route[:i];classes.setdefault(p,"Folder" if len(p)>1 else p[0])
 if len(plus)!=62 or any(plus[key]!=val for key,val in original.items()):
  raise ValueError("RED_REAL59_BLOB_REPLACED")
 on=out/"on62";on.mkdir()
 onProject,onRoutes=project_for(plus,classes,on,"GQ8_REAL62_OFFICIAL59_HUD_PLUS_TRADE_NO_GRANT")
 _,actualOff=flatten(offProject)
 _,actualOn=flatten(onProject)
 if len(actualOff)!=59 or len(actualOn)!=62:raise ValueError("RED_FINAL_ROUTE_COUNT")
 if any(actualOff[k].read_bytes()!=actualOn[k].read_bytes() or klass(actualOff[k])!=klass(actualOn[k]) for k in actualOff):
  raise ValueError("RED_OFF59_CHANGED")
 result={"schema":"GQ8_REAL62_OFFICIAL59_PLUS_TRADE_3_PRIVATE_COMBINED_V1",
  "canonical_rc_sha":OFFICIAL59,
  "parent_profile":"eggrumble_v3_real59","parent_count":59,"selected_count":62,
  "official55_sources_byte_exact":55,"official59_sources_byte_exact":59,
  "added_trade_sources":3,
  "on_project":str(onProject),"off_project":str(offProject),
  "parent_real59_sha256":digest(parent59),"official_real55_sha256":digest(official55),
  "host59_activated_place_sha256":digest(host59),
  "host59_activated_source_class":True,"original59_host_class_was":"ModuleScript",
  "on_sources":onRoutes,"off_sources":offRoutes,
  "new_routes":["/".join(k) for k in ADDS],
  "feature_union":"HUD_FOG_829 plus TRADE_UI_JOURNAL_ESCROW_838",
  "no_new_remote":True,"no_new_datastore":True,"live_trade":False,
  "paid_item_trade":False,"robux":False,"roblox_publish":False,
  "studio_2client":"NOT_TESTED","android15":"NOT_TESTED",
  "official_rc_adopted":False,"rollback":"OFF59 exact parent profile",
  }
 (out/"B_REAL62_RECEIPT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_REAL62_OFFICIAL_REAL59_AND_ORIGINAL_REAL55_ALL_BYTE_EXACT_PLUS_3_TRADE_ONLY_PASS")
 return result
if __name__=="__main__":
 ap=argparse.ArgumentParser()
 ap.add_argument("--real59",type=Path,required=True)
 ap.add_argument("--receipt59",type=Path,required=True)
 ap.add_argument("--host59",type=Path,required=True)
 ap.add_argument("--hostreceipt",type=Path,required=True)
 ap.add_argument("--official55",type=Path,required=True)
 ap.add_argument("--out",type=Path,required=True)
 a=ap.parse_args()
 compose(a.real59,a.receipt59,a.host59,a.hostreceipt,a.official55,a.out)
