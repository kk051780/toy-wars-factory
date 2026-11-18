#!/usr/bin/env python3
"""Immutable Real57 + 1 new pure two-profile escrow reducer => private Real58.
OFF57 and OFF55 are byte exact; no real trade settlement and no commerce.
"""
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten,klass
ROUTE=("ServerScriptService","GQ8_TradeEscrowReducer")
SOURCE="GQ8_TradeEscrowReducer.luau"
def compose(parent,receipt,out):
 if out.exists():raise ValueError("RED_OVERWRITE_OUTPUT")
 original,old=flatten(parent)
 j=json.loads(receipt.read_text(encoding="utf8"))
 if len(old)!=57 or j.get("source_on")!=57 or j.get("source_off")!=55 or j.get("original55_unchanged")!=55:
  raise ValueError("RED_UNVERIFIED_57_PARENT")
 ledger={}
 for row in j.get("scripts",[]):
  key=tuple(row["route"].split("/"))
  if key in ledger:raise ValueError("RED_PARENT_DUPLICATE_ROUTE")
  ledger[key]=row
 if set(old)!=set(ledger) or ROUTE in old:raise ValueError("RED_PARENT_ROUTE_DRIFT")
 for route,oldFile in old.items():
  row=ledger[route];data=oldFile.read_bytes()
  if row["bytes"]!=len(data) or row["sha256"]!=hashlib.sha256(data).hexdigest() or row["class"]!=klass(oldFile):
   raise ValueError("RED_PARENT_SOURCE_DRIFT_"+"/".join(route))
 out.mkdir(parents=True)
 project=copy.deepcopy(original);project["name"]="GQ8_REAL58_TRADE_ESCROW_PURE_REDUCER_NO_PERSISTENCE"
 entries=[]
 def put(route,data,ext,origin):
  d=out.joinpath("sources",*route[:-1],route[-1]+ext)
  d.parent.mkdir(parents=True,exist_ok=True)
  if d.exists():raise ValueError("RED_DUPLICATE_TARGET")
  d.write_bytes(data)
  node=project["tree"]
  for i,k in enumerate(route[:-1]):
   if k not in node:node[k]={} if i==0 else {"$className":"Folder"}
   node=node[k]
  node[route[-1]]={"$path":d.relative_to(out).as_posix()}
  entries.append({"route":"/".join(route),"class":klass(d),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"origin":origin})
 for route,script in sorted(old.items()):
  ext=".server.luau" if klass(script)=="Script" else ".client.luau" if klass(script)=="LocalScript" else ".luau"
  put(route,script.read_bytes(),ext,"unchanged_parent57")
 put(ROUTE,(Path(__file__).parent/SOURCE).read_bytes(),".luau","GQ8_TRADE_ESCROW_REDUCER_20261119")
 dst=out/"EGGRUMBLE_REAL58.project.json"
 dst.write_text(json.dumps(project,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 _,new=flatten(dst)
 if len(new)!=58 or set(new)!=set(old)|{ROUTE}:
  raise ValueError("RED_NOT_EXACT_58_ROUTES")
 if any(new[k].read_bytes()!=v.read_bytes() or klass(new[k])!=klass(v) for k,v in old.items()):
  raise ValueError("RED_PARENT_57_MUTATED")
 result={"schema":"GQ8_REAL58_ESCROW_REDUCER_PRIVATE_SOURCE_LEDGER_V1","source_on":58,
    "source_off":57,"source_off_original":55,"unchanged_parent57":57,
    "unchanged_original55":55,"new_sources":1,"actual_item_transfer":False,
    "persisted_store_connected":False,"robux":False,"published":False,
    "studio_2client":"NOT_TESTED","android15":"NOT_TESTED",
    "receipt57_sha256":hashlib.sha256(receipt.read_bytes()).hexdigest(),
    "sources":entries}
 (out/"B_REAL58_RECEIPT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
 print("GQ8_REAL58_ORIGINAL57_ALL57_UNCHANGED_PLUS_ESCROW_REDUCER_ONLY_PASS")
 return result
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--parent57",type=Path,required=True)
 p.add_argument("--receipt57",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 a=p.parse_args()
 compose(a.parent57,a.receipt57,a.out)
