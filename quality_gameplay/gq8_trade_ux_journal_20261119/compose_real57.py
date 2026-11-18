#!/usr/bin/env python3
"""Immutable canonical Real55 + exactly 2 new independent trade sources => private Real57.
Real55 remains byte-identical and OFF55 Place must compare equal.
"""
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten,klass
COUNT=55
ROUTES={
 ("ServerScriptService","GQ8_TradeJournalContract"):("GQ8_TradeJournalContract.luau","ModuleScript"),
 ("StarterPlayer","StarterPlayerScripts","GQ8_TradeReview"):("GQ8_TradeReview.client.luau","LocalScript")
}
REQUIRED={
 ("ReplicatedStorage","GQ8Trade","GQ8_TradePolicy"),
 ("ServerScriptService","GQ8_LobbySocialPlaza"),
 ("ServerScriptService","EGGRUMBLE_MusouFeverPolicy"),
 ("ServerScriptService","EGGRUMBLE_InvulnerabilityPolicy"),
 ("ServerScriptService","EGGRUMBLE_CurseConversionPolicy"),
 ("ServerScriptService","GQ805_LobbyGuildShop"),
 ("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopView")
}
def compose(project55,receipt55,out):
    if out.exists():raise ValueError("RED_OUTPUT_ALREADY_EXISTS")
    original,old=flatten(project55)
    receipts=json.loads(receipt55.read_text(encoding="utf8"))
    if len(old)!=COUNT or receipts.get("selected_real55_count")!=COUNT or receipts.get("parent53_source_count")!=53:
        raise ValueError("RED_PARENT55_UNVERIFIED")
    mapped={}
    for row in receipts.get("sources",[]):
        key=tuple(row["route"].split("/"))
        if key in mapped:raise ValueError("RED_DUPLICATE_PARENT_RECEIPT")
        mapped[key]=row
    if set(mapped)!=set(old) or not REQUIRED.issubset(old) or set(ROUTES)&set(old):
        raise ValueError("RED_PARENT55_SOURCE_ROUTE_INVALID")
    for key,script in old.items():
        row=mapped[key];data=script.read_bytes()
        if row["class"]!=klass(script) or row["bytes"]!=len(data) or row["sha256"]!=hashlib.sha256(data).hexdigest():
            raise ValueError("RED_IMMUTABLE_PARENT_DRIFT_"+"/".join(key))
    out.mkdir(parents=True)
    selected=copy.deepcopy(original)
    selected["name"]="GQ8_REAL57_TRADE_REVIEW_DURABLE_JOURNAL_CONTRACT_PRIVATE_NO_SETTLEMENT"
    ledger=[]
    def put(route,data,ext,origin):
        dst=out.joinpath("sources",*route[:-1],route[-1]+ext)
        dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():raise ValueError("RED_DUPLICATE_OUTPUT_SCRIPT")
        dst.write_bytes(data)
        node=selected["tree"]
        for n,key in enumerate(route[:-1]):
            if key not in node:node[key]={} if n==0 else {"$className":"Folder"}
            node=node[key]
        node[route[-1]]={"$path":dst.relative_to(out).as_posix()}
        ledger.append({"route":"/".join(route),"class":klass(dst),"bytes":len(data),
            "sha256":hashlib.sha256(data).hexdigest(),"origin":origin})
    for route,script in sorted(old.items()):
        cl=klass(script)
        ext=".server.luau" if cl=="Script" else ".client.luau" if cl=="LocalScript" else ".luau"
        put(route,script.read_bytes(),ext,"immutable_current55")
    for route,(name,cl) in sorted(ROUTES.items()):
        ext=".client.luau" if cl=="LocalScript" else ".luau"
        put(route,(Path(__file__).parent/name).read_bytes(),ext,"GQ8_TRADE_UX_JOURNAL_20261119")
    output=out/"EGGRUMBLE_REAL57.project.json"
    output.write_text(json.dumps(selected,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    _,checks=flatten(output)
    if len(checks)!=57 or set(checks)!=set(old)|set(ROUTES):
        raise ValueError("RED_SOURCE57_NOT_EXACT")
    for route,old_file in old.items():
        if checks[route].read_bytes()!=old_file.read_bytes() or klass(checks[route])!=klass(old_file):
            raise ValueError("RED_EXISTING55_CHANGED_"+"/".join(route))
    result={"schema":"GQ8_TRADE_UX_JOURNAL_PRIVATE_REAL57",
       "source_on":57,"source_off":55,"original55_unchanged":55,"new_sources":2,
       "no_commerce":True,"trade_settlement":False,"wallet_save":False,"robux":False,
       "parent55_candidate_ci":44392759736,
       "parent55_source_receipt_sha256":hashlib.sha256(receipt55.read_bytes()).hexdigest(),
       "rollback":"Select exact unmodified Real55 source profile OFF55",
       "official_rc_adopted":False,"studio2client":"NOT_TESTED","android15":"NOT_TESTED",
       "scripts":ledger}
    (out/"B_REAL57_RECEIPT.json").write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("GQ8_REAL57_IMMUTABLE_CURRENT55_PLUS_2_TRADE_SOURCES_PASS")
    return result
if __name__=="__main__":
    pa=argparse.ArgumentParser()
    pa.add_argument("--parent55",type=Path,required=True)
    pa.add_argument("--receipt55",type=Path,required=True)
    pa.add_argument("--out",type=Path,required=True)
    a=pa.parse_args();compose(a.parent55,a.receipt55,a.out)
