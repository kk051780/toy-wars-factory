#!/usr/bin/env python3
"""Fail-closed selected-source audit for all 48 original RC85/RC86 feature flags.

This proves original flag inventory and identifies current selected-source analogues.
It does NOT claim full legacy behavior, Studio usability, Android or owner acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

FORMAL="rc/p0d-s1-kids-rc01"
PROFILE="REAL69"
MAX_FLAGS=48
KNOWN_GAPS={"SIX_SKILL_DURABLE","SAVED_PVE_MASTERY","SAVED_BEAST_EVOLUTION","SCOUT_SPECIES_V1"}
NON_RUNTIME={"P0D_URGENT_READY_900_V1","P0D_PRIVATE_HORDE_ENGINE_EVIDENCE_V1"}

def require(ok,why):
    if not ok: raise ValueError("RED_RC85_RC86_48_FLAG_TRUTH_"+why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load_manifest(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    require(data["schema"]=="EGGRUMBLE_RC85_RC86_REAL69_48_FLAG_TRUTH_V1","MANIFEST_SCHEMA")
    require(data["formal_branch"]==FORMAL and data["selected_profile"]==PROFILE,"TARGET")
    entries=data["entries"]
    require(len(entries)==MAX_FLAGS,"EXACT_48")
    names=[e["id"] for e in entries]
    require(len(set(names))==MAX_FLAGS,"DUPLICATE_FLAG_ID")
    require(sha("\n".join(sorted(names)).encode())==data["legacy"]["flag_id_sha256"],"LEGACY_48_ID_DIGEST")
    require(data["legacy"]["flag_id_sha256"]=="ada1dbb65bc821c366cedf6b2ae52e834b7b81ce70f06a48373da1f1604c0fbb","IMMUTABLE_ORIGINAL_FLAG_DIGEST")
    require(set(n for n in names if n in KNOWN_GAPS)==KNOWN_GAPS,"GAP_INVENTORY")
    require(set(n for n in names if n in NON_RUNTIME)==NON_RUNTIME,"QA_ONLY_INVENTORY")
    return data

def inspect(base,manifest):
    sources=project_scan(base,"EGGRUMBLE_REAL69.project.json")
    receipt=json.loads((base/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_text(encoding="utf-8"))
    require(len(sources)==69 and len(receipt["source_hashes"])==69,"REAL69_COUNT")
    require(receipt.get("selected_source_count")==69 and receipt.get("source_profile")=="REAL69","SOURCE_PROFILE")
    require(receipt.get("official_branch")==FORMAL,"FORMAL_BRANCH")
    require(receipt.get("legacy_48_all_ported") is False,"FALSE_FULL_PARITY_CLAIM")
    require(all(receipt["source_hashes"].get(k)==x["sha256"] for k,x in sources.items()),"SOURCE_RECEIPT_DRIFT")
    require(all(receipt["source_classes"].get(k)==x["class"] for k,x in sources.items()),"CLASS_RECEIPT_DRIFT")
    require(not any("TrapRaidersS1/" in k for k in sources),"DUPLICATE_LEGACY_GAME_AUTHORITY")
    results=[]
    summary={"MARKER_SOURCE_PRESENT":0,"SOURCE_ANALOGUE_ONLY":0,
             "EVIDENCE_GAP":0,"NON_RUNTIME_LEGACY_FLAG":0}
    for flag in manifest["entries"]:
        name=flag["id"]
        routes=flag.get("current_routes",[])
        marker=flag.get("source_marker")
        if name in NON_RUNTIME:
            require(not routes and marker is None,"QA_HAS_GAME_RUNTIME_"+name)
            status="NON_RUNTIME_LEGACY_FLAG"
        elif name in KNOWN_GAPS:
            require(not routes and marker is None,"GAP_HAS_UNPROVEN_MAPPING_"+name)
            status="EVIDENCE_GAP"
        else:
            require(bool(routes) and len(set(routes))==len(routes),"MISSING_ROUTE_MAPPING_"+name)
            require(all(k in sources for k in routes),"REGRESSED_ROUTE_"+name)
            if marker:
                require(any(marker.encode() in sources[k]["source"] for k in routes),
                        "REGRESSED_PORT_MARKER_"+name)
                status="MARKER_SOURCE_PRESENT"
            else:
                status="SOURCE_ANALOGUE_ONLY"
        summary[status]+=1
        results.append({
            "feature_id":name,
            "current_evidence":status,
            "current_routes":routes,
            "source_marker":marker,
            "source_sha256":{k:sources[k]["sha256"] for k in routes},
            "original_rc85_rc86_full_semantic_parity":"NOT_PROVEN",
            "studio_solo":"NOT_TESTED",
            "studio_2client":"NOT_TESTED",
            "android_15min":"NOT_TESTED",
            "owner_acceptance":"NO_GO",
        })
    require(sum(summary.values())==MAX_FLAGS,"ACCOUNTING")
    return {"schema":"EGGRUMBLE_RC85_RC86_SINGLE_RC_FLAG_TRUTH_REPORT_V1",
      "official_branch":FORMAL,
      "official_head":receipt.get("build_head"),
      "profile":PROFILE,
      "source_count":69,
      "original_legacy_flags":MAX_FLAGS,
      "summary":summary,
      "flag_inventory_verified":True,
      "all_48_semantic_parity":"NOT_PROVEN",
      "real69_native_rojo":"REQUIRES_INDEPENDENT_SAME_HEAD_CI",
      "product_quality":"NO_GO",
      "flags":results}

def self_test():
    m=load_manifest(HERE/"legacy48.json")
    assert len(m["entries"])==48
    assert len([e for e in m["entries"] if e.get("source_marker")])>=11
    assert len([e for e in m["entries"] if e["id"] in KNOWN_GAPS])==4
    assert len([e for e in m["entries"] if e["id"] in NON_RUNTIME])==2
    changed=json.loads(json.dumps(m))
    changed["entries"][0]["id"]="MUTATED_FLAG"
    try: load_manifest_data(changed)
    except ValueError as exc: assert "LEGACY_48_ID_DIGEST" in str(exc)
    else: raise AssertionError("MUTANT_NOT_REJECTED")
    print("REAL69_ORIGINAL_RC85_RC86_48FLAG_MANIFEST_MUTATION_TEST_PASS")

def load_manifest_data(data):
    # Keep this secondary mutational guard equivalent to the stable check.
    names=[e["id"] for e in data["entries"]]
    require(len(names)==MAX_FLAGS and len(set(names))==MAX_FLAGS,"MUTATED_COUNT")
    require(sha("\n".join(sorted(names)).encode())==data["legacy"]["flag_id_sha256"],
            "LEGACY_48_ID_DIGEST")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=pathlib.Path)
    p.add_argument("--report",type=pathlib.Path)
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test()
    else:
        require(a.base is not None and a.report is not None,"REQUIRED_ARGUMENTS")
        out=inspect(a.base,load_manifest(HERE/"legacy48.json"))
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
        print("EGGRUMBLE_REAL69_48_FLAGS_ALL_ACCOUNTED",
              json.dumps(out["summary"],sort_keys=True))
