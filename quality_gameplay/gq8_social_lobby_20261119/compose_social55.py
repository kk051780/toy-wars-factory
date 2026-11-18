#!/usr/bin/env python3
"""Immutable latest verified #826 Real53 + two nonoverlap social/trade source routes => Real55.
No newer Combat/Host/Realm/Swarm/Store ownership. OFF53 exact original Place.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten,klass
FEATURE="GQ8_LOBBY_SOCIAL_TRADE_20261119"
ROUTES={
 ("ServerScriptService","GQ8_LobbySocialPlaza"):("GQ8_LobbySocialPlaza.server.luau","Script"),
 ("ReplicatedStorage","GQ8Trade","GQ8_TradePolicy"):("GQ8_TradePolicy.luau","ModuleScript")
}
def compose(parent53,receipt53,out):
    if out.exists():raise ValueError("RED_REFUSE_OVERWRITE")
    old_project,old=flatten(parent53)
    receipt=json.loads(receipt53.read_text(encoding="utf8"))
    if len(old)!=53 or receipt.get("selected_script_count")!=53:
        raise ValueError("RED_LATEST_REAL53_SOURCE_COUNT")
    records={}
    for x in receipt.get("sources",[]):
        key=tuple(x["route"].split("/"))
        if key in records:raise ValueError("RED_PARENT53_DUPLICATE")
        records[key]=x
    if set(old)!=set(records) or set(old)&set(ROUTES):
        raise ValueError("RED_PARENT53_RECEIPT_COLLISION")
    for key,source in old.items():
        b=source.read_bytes();row=records[key]
        if len(b)!=row["bytes"] or hashlib.sha256(b).hexdigest()!=row["sha256"] or klass(source)!=row["class"]:
            raise ValueError("RED_PARENT53_BYTES_DRIFT_"+"/".join(key))
    required={
      ("ServerScriptService","EGGRUMBLE_MusouFeverPolicy"),
      ("ServerScriptService","EGGRUMBLE_InvulnerabilityPolicy"),
      ("ServerScriptService","EGGRUMBLE_InvulRuntime"),
      ("ServerScriptService","EGGRUMBLE_CurseConversionPolicy"),
      ("ServerScriptService","EGGRUMBLE_SwarmCombat"),
      ("ServerScriptService","EGGRUMBLE_SevenRoleCombat"),
      ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview"),
      ("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopCatalog"),
      ("ReplicatedStorage","GQ805Shop","EGGRUMBLE_LobbyShopView"),
      ("ServerScriptService","GQ805_LobbyGuildShop"),
    }
    if not required.issubset(old):
        raise ValueError("RED_LATEST_REAL53_NOT_SELECTED")
    selected=copy.deepcopy(old_project)
    selected["name"]="GQ8_PRIVATE_REAL55_LATEST_MUSOU_INVUL_CURSE_GUILD_SHOP_SOCIAL_TRADE"
    out.mkdir(parents=True)
    ledger=[]
    def put(route,b,ext,origin):
        dest=out.joinpath("sources",*route[:-1],route[-1]+ext)
        if dest.exists():raise ValueError("RED_ROUTE_COLLISION")
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
        node=selected["tree"]
        for depth,section in enumerate(route[:-1]):
            if section not in node:
                node[section]={} if depth==0 else {"$className":"Folder"}
            node=node[section]
        node[route[-1]]={"$path":dest.relative_to(out).as_posix()}
        ledger.append({"route":"/".join(route),"class":klass(dest),
            "sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"origin":origin})
    for route,path in sorted(old.items()):
        cls=klass(path)
        ext=".server.luau" if cls=="Script" else ".client.luau" if cls=="LocalScript" else ".luau"
        put(route,path.read_bytes(),ext,"verified_exact_parent53")
    for route,(filename,cls) in sorted(ROUTES.items()):
        body=(Path(__file__).parent/filename).read_bytes()
        ext=".server.luau" if cls=="Script" else ".luau"
        put(route,body,ext,FEATURE)
    proj=out/"EGGRUMBLE_REAL55.project.json"
    proj.write_text(json.dumps(selected,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    _,on=flatten(proj)
    if len(on)!=55 or set(on)!=(set(old)|set(ROUTES)):
        raise ValueError("RED_REAL55_COMPOSE_INCONSISTENT")
    for key,source in old.items():
        if on[key].read_bytes()!=source.read_bytes() or klass(on[key])!=klass(source):
            raise ValueError("RED_PARENT53_MUTATED_"+"/".join(key))
    for key in ROUTES:
        if "GQ8" not in "/".join(key):raise ValueError("RED_UNSCOPED_NEW_SCRIPT")
    report={"schema":FEATURE,"latest_parent_pr":826,
        "parent53_immutable_head":"96ac3b4caa2f649f98c9e093c864c39555f3616a",
        "parent53_native_rojo_proof_run":44390823718,
        "parent53_source_count":53,"selected_real55_count":55,"added_source_count":2,
        "original53_byte_exact":True,"new_store_owner":0,"new_remote_owner":0,
        "actual_trade_settlement_enabled":False,"paid_item_trading_enabled":False,
        "formal_rc_adopted":False,"studio2client":"NOT_TESTED",
        "android15":"NOT_TESTED","fun":"NO_GO",
        "rollback":"Select original verified Real53 project and exact OFF53 Place",
        "sources":ledger}
    (out/"B_REAL55_RECEIPT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ8_REAL55_IMMUTABLE_PARENT53_PLUS_2_SOCIAL_TRADE_SOURCE_PASS")
if __name__=="__main__":
    pa=argparse.ArgumentParser()
    pa.add_argument("--parent53",required=True,type=Path)
    pa.add_argument("--receipt53",required=True,type=Path)
    pa.add_argument("--out",required=True,type=Path)
    a=pa.parse_args();compose(a.parent53,a.receipt53,a.out)
