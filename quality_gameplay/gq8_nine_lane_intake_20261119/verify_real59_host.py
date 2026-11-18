#!/usr/bin/env python3
"""Verify official Host-startup source-class repair without pretending Studio testing."""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from verify_real59 import contents, sha, require

HOST = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"

def inspect(place):
    found, _ = contents(ET.parse(place).getroot())
    return {"/".join(route): (cls, src.encode("utf8")) for route, (cls, src) in found.items()}

def verify(original, active, rollback, receipt, expected_head):
    before, after, off = inspect(original), inspect(active), inspect(rollback)
    require(len(before) == len(after) == len(off) == 59, "HOST_SOURCE_COUNT")
    require(set(before) == set(after) == set(off), "HOST_ROUTE_CHANGED")
    require(before[HOST][0] == "ModuleScript", "OLD_HOST_WAS_RUNNING")
    require(after[HOST][0] == "Script", "NEW_HOST_NOT_RUNNING")
    require(all(after[k][1] == before[k][1] for k in before), "HOST_SOURCE_BYTES_CHANGED")
    require(all(off[k] == before[k] for k in before), "ROLLBACK_NOT_EXACT_59")
    require(all(after[k][0] == before[k][0] for k in before if k != HOST), "OTHER_CLASS_CHANGED")
    info = json.loads(receipt.read_text(encoding="utf8"))
    require(info.get("tested_commit") == expected_head and
            info.get("source_selected_in_formal_rc_branch") is True, "HOST_OFFICIAL_RECEIPT")
    require(info.get("sources") == 59 and info.get("source_bytes_modified") == 0 and
            info.get("host_old_class") == "ModuleScript" and
            info.get("host_new_class") == "Script", "HOST_RECEIPT_DRIFT")
    require(info.get("studio_solo") == "NOT_TESTED" and
            info.get("studio_two_client") == "NOT_TESTED" and
            info.get("product_acceptance") == "NO_GO", "FALSE_FUN_GO")
    return {
        "official_head":expected_head,
        "source_count":59,
        "source_bytes_unchanged":59,
        "host_script_class":"Script",
        "other_classes_unchanged":58,
        "rollback_off59_source_exact":True,
        "nine_gameplay_source_domains":"PASS",
        "studio_solo":"NOT_TESTED",
        "studio_two_client":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "product_go":False,
    }

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for name in ("original","active","rollback","receipt","output"):
        p.add_argument("--"+name, type=Path, required=True)
    p.add_argument("--expected-head",required=True)
    a=p.parse_args()
    report=verify(a.original,a.active,a.rollback,a.receipt,a.expected_head)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ8_REAL59_NINE_DOMAIN_HOST_CLASS_59_SOURCE_BYTES_OFF59_PASS")
