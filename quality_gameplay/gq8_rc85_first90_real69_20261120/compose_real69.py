#!/usr/bin/env python3
"""One additive V3 source-selected First90: actual REAL68 -> REAL69, no overwrite.

This is a Studio-only client UI adaptation of the legacy First90 goal, not
proof that all S1 First90 behavior or other old RC85/86 flags are ported.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import shutil
import sys
from typing import Any

HERE=pathlib.Path(__file__).parent
sys.path.insert(0,str(HERE.parent/"gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

NEW_ROUTE="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90"
NEW_REL="sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90.client.luau"
FEATURE="GQ8_RC85_FIRST90_REAL69_STUDIO_GUIDE_20261120"

def need(ok:bool,reason:str)->None:
    if not ok: raise ValueError("RED_GQ8_FIRST90_REAL69_"+reason)

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def src_check(raw:bytes)->None:
    s=raw.decode("utf-8")
    for token in (
        FEATURE, "if not RunService:IsStudio() then return end",
        "local DURATION=90", "local STEP1=22", "local STEP2=48",
        'player:GetAttribute("EGGRUMBLE_Role")',
        'player:GetAttribute("EGGRUMBLE_QueuedMode")',
        "player.CharacterAdded:Connect(attach)",
        "billboard:Destroy()", "characterConnection:Disconnect()",
        "if player:GetAttribute(\"EGGRUMBLE_Eliminated\")==true",
        "AlwaysOnTop=false", "MaxDistance=32",
    ):
        need(token in s,"MISSING_"+token[:32])
    for token in (
        "RemoteEvent", "FireServer(", "DataStoreService", "MarketplaceService",
        "TakeDamage(", "ProcessReceipt", "RenderStepped:Connect(",
        "Heartbeat:Connect(", "while true do", "ScreenGui",
    ):
        need(token not in s,"FORBIDDEN_"+token)
    need(s.count("task.spawn(function()")==1, "SINGLE_BOUNDED_CLIENT_TIMER")
    need(3000<len(raw)<9000,"SOURCE_BOUNDS")

def compose(base:pathlib.Path,out:pathlib.Path,feature:pathlib.Path,head:str)->dict[str,Any]:
    need(base.is_dir() and not out.exists(),"INPUT_OUTPUT_DIRECTORY")
    pfile=base/"EGGRUMBLE_REAL68.project.json"
    receipt=json.loads((base/"REAL68_LEGACY_INTAKE_RECEIPT.json").read_text())
    old=project_scan(base,pfile.name)
    need(len(old)==68 and len(set(old))==68,"ORIGINAL_68_UNIQUE")
    need(receipt.get("selected_source_count")==68
         and receipt.get("candidate_head")==head
         and len(receipt.get("source_hashes",{}))==68,"SOURCE_RECEIPT_HEAD")
    lod=receipt.get("rc86_gorogan_mobile_lod",{})
    need(lod.get("native_rojo")=="PASS_68_OF_68"
         and lod.get("all68_routes_preserved") is True,"RC86_GOROGAN_LOD_PARENT")
    need(all(receipt["source_hashes"].get(route)==data["sha256"]
             for route,data in old.items()),"BASELINE_RECEIPT_BYTES")
    need(NEW_ROUTE not in old,"ALREADY_SELECTED")
    raw=feature.read_bytes()
    src_check(raw)
    shutil.copytree(base,out)
    # A true OFF68 copy uses 68 exact ORIGINAL active sources, including latest
    # RC86 Gorogan LOD, NOT the earlier pre-LOD off68 source snapshot.
    off=out/"off_parent68"
    off.mkdir(exist_ok=False)
    pr=json.loads(pfile.read_text())
    for route,entry in old.items():
        old_path=entry["path"]
        dst=off/old_path
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes((base/old_path).read_bytes())
    (off/pfile.name).write_bytes(pfile.read_bytes())
    restored=project_scan(off,pfile.name)
    need(set(restored)==set(old)
         and all(restored[k]["sha256"]==old[k]["sha256"] for k in old),
         "OFF_PARENT68_EXACT")
    current=out/NEW_REL
    current.parent.mkdir(parents=True,exist_ok=True)
    current.write_bytes(raw)
    node=pr["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    need("EGGRUMBLE_LegacyFirst90" not in node,"ROUTE_DUPLICATE")
    node["EGGRUMBLE_LegacyFirst90"]={"$path":NEW_REL,"$className":"LocalScript"}
    pr["name"]="EGGRUMBLE_REAL69_ONE_V3_FIRST90_PRIVATE_STUDIO"
    (out/"EGGRUMBLE_REAL69.project.json").write_text(
        json.dumps(pr,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    final=project_scan(out,"EGGRUMBLE_REAL69.project.json")
    need(len(final)==69 and set(final)-set(old)=={NEW_ROUTE}
         and all(final[k]["sha256"]==old[k]["sha256"]
                 and final[k]["class"]==old[k]["class"]
                 and final[k]["path"]==old[k]["path"]
                 for k in old),"REAL68_68_OF_68_UNCHANGED")
    need(final[NEW_ROUTE]["class"]=="LocalScript"
         and final[NEW_ROUTE]["sha256"]==sha(raw),"REAL69_LOCAL_SCRIPT")
    selected={
        "schema":"GQ8_RC85_RC86_REAL65_TO_REAL69_FIRST90_NONLOSS_V1",
        "official_branch":"rc/p0d-s1-kids-rc01",
        "build_head":head,
        "source_profile":"REAL69",
        "selected_source_count":69,
        "old_68_selected_source_preserved":68,
        "old_68_bodies_byte_identical":68,
        "added_source_route":NEW_ROUTE,
        "added_source_class":"LocalScript",
        "feature_id":FEATURE,
        "feature_scope":"Studio-only first 90 sec nonblocking character bubble",
        "original_s1_first90_exact_semantic_parity":"NOT_PROVEN",
        "legacy_48_all_ported":False,
        "active_v3_gamehost_unchanged":True,
        "added_server_or_store_or_remote_writer":0,
        "old_rc86_lod_preserved":True,
        "off68_active_parent_source_exact":True,
        "old_off67_and_off68_rollback_preserved":True,
        "native_rojo":"PENDING",
        "studio_solo":"NOT_TESTED",
        "studio_two_client":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "fun_art":"NO_GO",
        "roblox_publish":False,
        "paid_trade":False,
        "source_hashes":{k:v["sha256"] for k,v in sorted(final.items())},
        "source_classes":{k:v["class"] for k,v in sorted(final.items())},
    }
    (out/"REAL69_LEGACY_INTAKE_RECEIPT.json").write_text(
        json.dumps(selected,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("REAL69_ONE_CANONICAL_FIRST90_ALL_68_SOURCES_BYTE_UNCHANGED_OFF68_READY")
    return selected

def selftest()->None:
    src_check((HERE/"EGGRUMBLE_LegacyFirst90.client.luau").read_bytes())
    source=(HERE/"EGGRUMBLE_LegacyFirst90.client.luau").read_bytes()
    for wrong in (source.replace(b"local DURATION=90",b"local DURATION=0"),
                  source+b"\nRemoteEvent\n",
                  source.replace(b"billboard:Destroy()",b"-- removed"),
                  source.replace(b"AlwaysOnTop=false",b"AlwaysOnTop=true")):
        try: src_check(wrong)
        except ValueError: pass
        else: raise AssertionError("NEGATIVE_MUTANT_PASSED")
    print("REAL69_FIRST90_CLIENT_ADAPTATION_4_NEGATIVE_GUARDS_PASS")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=pathlib.Path)
    ap.add_argument("--out",type=pathlib.Path)
    ap.add_argument("--source",type=pathlib.Path)
    ap.add_argument("--head")
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:selftest()
    else:
        need(bool(args.base and args.out and args.source and args.head),"ARGS")
        compose(args.base,args.out,args.source,args.head)
