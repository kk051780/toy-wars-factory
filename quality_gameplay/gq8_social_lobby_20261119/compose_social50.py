#!/usr/bin/env python3
"""Source-exact optional Real48 + 2 unique social/trade modules, OFF48 lossless."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten,klass
NAME="GQ8_LOBBY_SOCIAL_TRADE_20261119"
ROUTES={
 ("ServerScriptService","GQ8_LobbySocialPlaza"):("GQ8_LobbySocialPlaza.server.luau","Script"),
 ("ReplicatedStorage","GQ8Trade","GQ8_TradePolicy"):("GQ8_TradePolicy.luau","ModuleScript"),
}
def select(project,receipt,out):
    if out.exists():raise ValueError("REFUSE_OVERWRITE")
    doc,old=flatten(project)
    log=json.loads(receipt.read_text(encoding="utf8"))
    if len(old)!=48 or log.get("on_source_count")!=48:raise ValueError("RED_PARENT48_SOURCE_COUNT")
    original={tuple(x["route"].split("/")):x for x in log["scripts"]}
    if set(old)!=set(original) or set(old)&set(ROUTES):raise ValueError("RED_PARENT48_SOURCE_DRIFT")
    for route,source in old.items():
        b=source.read_bytes();r=original[route]
        if r["sha256"]!=hashlib.sha256(b).hexdigest() or r["bytes"]!=len(b) or r["class"]!=klass(source):
            raise ValueError("RED_PARENT48_IMMUTABILITY_"+"/".join(route))
    selected=copy.deepcopy(doc);selected["name"]="EGGRUMBLE_REAL50_SOCIAL_TRADE_PREVIEW_NOT_OFFICIAL"
    out.mkdir(parents=True)
    ledger=[]
    for route,src in sorted(old.items()):
        ending=".server.luau" if klass(src)=="Script" else (".client.luau" if klass(src)=="LocalScript" else ".luau")
        dest=out/"sources"/Path(*route[:-1])/(route[-1]+ending)
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(src.read_bytes())
        node=selected["tree"]
        for a in route[:-1]:
            node=node.setdefault(a,{"$className":"Folder"})
        node[route[-1]]={"$path":dest.relative_to(out).as_posix()}
        ledger.append({"route":"/".join(route),"sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"bytes":src.stat().st_size,"class":klass(src),"origin":"immutable_real48"})
    for route,(filename,cl) in ROUTES.items():
        src=Path(__file__).parent/filename
        dest=out/"sources"/Path(*route[:-1])/(route[-1]+filename[len("GQ8_"):])
        # filename above is only a portable file name; class is determined by its suffix.
        dest=out/"sources"/Path(*route[:-1])/(route[-1]+(".server.luau" if cl=="Script" else ".luau"))
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(src.read_bytes())
        if klass(dest)!=cl:raise ValueError("RED_NEW_CLASS")
        node=selected["tree"]
        for a in route[:-1]:node=node.setdefault(a,{"$className":"Folder"})
        node[route[-1]]={"$path":dest.relative_to(out).as_posix()}
        ledger.append({"route":"/".join(route),"sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"bytes":src.stat().st_size,"class":cl,"origin":NAME})
    proj=out/"EGGRUMBLE_REAL50.project.json"
    proj.write_text(json.dumps(selected,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    _,new=flatten(proj)
    if len(new)!=50 or set(new)!=set(old)|set(ROUTES):raise ValueError("RED_WRONG_SOURCE_ROUTES")
    for route,src in old.items():
        if src.read_bytes()!=new[route].read_bytes():raise ValueError("RED_OFF48_DRIFT")
    receipt50={"schema":NAME,"source_on":50,"source_off":48,
        "parent48_preserved":48,"new_sources":2,"new_store_authority":0,"new_remote_owner":0,
        "trade_settlement_enabled":False,"robux_enabled":False,
        "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
        "formal_rc_adopted":False,"rollback":"Select exact original Real48, drop only GQ8Trade and SocialPlaza",
        "scripts":ledger}
    (out/"B_REAL50_RECEIPT.json").write_text(json.dumps(receipt50,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ8_TRUE_REAL50_SOURCE_EXACT_AND_OFF48_PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent48",type=Path,required=True)
    p.add_argument("--receipt48",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();select(a.parent48,a.receipt48,a.out)
