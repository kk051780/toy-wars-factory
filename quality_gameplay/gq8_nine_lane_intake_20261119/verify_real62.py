#!/usr/bin/env python3
"""Independent current RC Real62 source-preservation and nine-domain game evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from verify_real59_host import inspect
from verify_real59 import require, sha, LANES

ADDED = {
    "ServerScriptService/GQ8_TradeJournalContract": "ModuleScript",
    "StarterPlayer/StarterPlayerScripts/GQ8_TradeReview": "LocalScript",
    "ServerScriptService/GQ8_TradeEscrowReducer": "ModuleScript",
}
HOST = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
AREAS = {n:list(routes) for n,routes in LANES.items()}
AREAS["items"] += ["ServerScriptService/GQ8_TradeJournalContract",
                   "ServerScriptService/GQ8_TradeEscrowReducer"]
AREAS["lobby"] += ["StarterPlayer/StarterPlayerScripts/GQ8_TradeReview"]
AREAS["ui"] += ["StarterPlayer/StarterPlayerScripts/GQ8_TradeReview"]
def verify(active59, real62, off59, receipt, expected_head):
    baseline=inspect(active59)
    selected=inspect(real62)
    restored=inspect(off59)
    info=json.loads(receipt.read_text(encoding="utf8"))
    require(len(expected_head)==40, "INVALID_HEAD")
    require(len(baseline)==59 and len(selected)==62 and len(restored)==59, "SOURCE_COUNTS")
    require(set(baseline)==set(restored), "OFF59_MISSING")
    require(all(baseline[k]==restored[k] for k in baseline), "OFF59_SOURCE_OR_CLASS_CHANGED")
    require(set(selected)==set(baseline)|set(ADDED), "TRADE_NEW_ROUTE_NOT_EXACT_3")
    require(all(selected[k]==baseline[k] for k in baseline), "ORIGINAL59_CLASS_OR_BYTES_CHANGED")
    require(baseline[HOST][0]=="Script" and selected[HOST][0]=="Script", "HOST_INACTIVE")
    for route,klass in ADDED.items():
        require(selected[route][0]==klass, "NEW_CLASS_"+route.replace("/","_"))
    require(info.get("tested_head")==expected_head and info.get("official_rc_adopted") is True,
            "OFFICIAL_HEAD_CLAIM")
    require(info.get("baseline_official_head")=="5a47e96f6b4766a9c59dd06b111bea53b73bd5ca" and
            info.get("baseline_count")==59 and info.get("combined_count")==62 and
            info.get("original59_exact") is True and info.get("host_class")=="Script" and
            info.get("host_active_source_preserved") is True, "PARENT_HOST_PROVENANCE")
    require(info.get("paid_trading") is False and info.get("actual_inventory_transfer") is False,
            "FALSE_LIVE_PAID_TRADE")
    require(info.get("native_rojo_source_class_off59")=="PASS" and
            info.get("studio")=="NOT_TESTED" and info.get("android")=="NOT_TESTED" and
            info.get("fun")=="NOT_TESTED", "FALSE_TESTED_PRODUCT_CLAIM")
    on=info.get("on_sources",[])
    off=info.get("off_sources",[])
    require(len(on)==62 and len(off)==59, "RECEIPT_COUNT")
    def index(rows):
        dst={}
        for row in rows:
            route=row.get("route")
            require(route not in dst, "DUPLICATE_LEDGER_ROUTE")
            dst[route]=row
        return dst
    on,off=index(on),index(off)
    require(set(on)==set(selected) and set(off)==set(baseline), "LEDGER_ROUTE_DRIFT")
    for route,(klass,blob) in selected.items():
        row=on[route]
        require(row.get("class")==klass and row.get("sha256")==sha(blob) and row.get("bytes")==len(blob),
                "SOURCE_HASH_CLASS_"+route.replace("/","_"))
        if route in baseline:
            require(row==off[route], "ORIGINAL_LEDGER_CHANGED_"+route.replace("/","_"))
    status={}
    for area,required in AREAS.items():
        require(all(route in selected for route in required), "MISSING_"+area)
        status[area]={"source_selected":True,"actual_roblox_studio":"NOT_TESTED",
                      "android_15min":"NOT_TESTED","art":"NOT_TESTED","fun":"NOT_TESTED"}
    require(len(status)==9,"DOMAIN_COUNT")
    return {
        "schema":"GQ8_INDEPENDENT_REAL62_9_DOMAIN_EXACT_SOURCE_RECEIPT_V1",
        "official_head":expected_head,"source_count":62,"original_exact_count":59,
        "host_class":"Script","source_additions":sorted(ADDED),
        "source_script_bytes_unchanged":59,"off59_source_and_class_exact":True,
        "nine_source_domains":9,"nine_studio_domains":0,
        "paid_inventory_transfer":False,"studio":"NOT_TESTED",
        "android_15min":"NOT_TESTED","fun":"NOT_TESTED","product_go":False,
        "areas":status,
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for name in ("active59","real62","off59","receipt","output"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--expected-head",required=True)
    a=p.parse_args()
    result=verify(a.active59,a.real62,a.off59,a.receipt,a.expected_head)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ8_INDEPENDENT_REAL62_SOURCE_59_EXACT_PLUS3_9DOMAIN_HOST_ROLLBACK_PASS")
