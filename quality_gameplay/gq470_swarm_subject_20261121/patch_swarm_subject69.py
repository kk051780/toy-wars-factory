#!/usr/bin/env python3
"""#470 FB008/015 REAL69 one-source cosmetic patch. A PREP ONLY; no formal writer."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
TARGET="ServerScriptService/EGGRUMBLE_SwarmCombat"
ORIGINAL_SHA="cc40d9902834b63db15bc8ff63a0be0f092cdc17e5a962d9669784f4e15dd75a"
FEATURE_ID="GQ470_FB008_FB015_SWARM_SUBJECT_DISTANCE_REAL69_20261121"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE="EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OLD=" h.NameDisplayDistance=0;h.HealthDisplayDistance=16"
NEW=(" -- "+FEATURE_ID+": existing labels use own distance settings.\n"
     " h.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.Subject\n"+OLD)

def need(ok:bool, reason:str)->None:
    if not ok: raise ValueError("RED_GQ470_SWARM_SUBJECT_"+reason)

def sha(data:bytes)->str: return hashlib.sha256(data).hexdigest()

def selected(root:Path)->dict[str,Path]:
    project=json.loads((root/PROJECT).read_text(encoding="utf-8"))
    found={}
    def walk(node,route=""):
        if not isinstance(node,dict):return
        if "$path" in node:
            rel=Path(node["$path"])
            need(not rel.is_absolute() and ".." not in rel.parts,"UNSAFE_SOURCE_PATH")
            need(route not in found,"DUPLICATE_ROUTE")
            dest=root/rel
            need(dest.is_file() and dest.resolve().is_relative_to(root.resolve()),"MISSING_SOURCE")
            found[route]=dest
        for k,v in node.items():
            if not k.startswith("$"): walk(v,f"{route}/{k}" if route else k)
    walk(project["tree"])
    return found

def patch(source:str)->str:
    need(source.count(OLD)==1 and FEATURE_ID not in source,"EXACT_ANCHOR_OR_ALREADY_PATCHED")
    first=source.find("local function soldier(")
    last=source.find("\nend",first)
    need(first>=0 and last>first,"SOLDIER_SCOPE")
    fragment=source[first:last]
    need(fragment.count(OLD)==1 and 'h=Instance.new("Humanoid")' in fragment
         and "h.Parent=m" in fragment and "DisplayDistanceType" not in fragment,
         "HUMANOID_SCOPE_DRIFT")
    updated=source.replace(OLD,NEW)
    need(updated.replace(NEW,OLD)==source and updated.count(FEATURE_ID)==1,"ROLLBACK_EXACT")
    need(len(updated.encode())-len(source.encode())<300,"ART_BUDGET")
    return updated

def selftest()->None:
    src=('local function soldier(p:Instance,at:Vector3,n:number):Model\n'
         ' local h=Instance.new("Humanoid")\n'+OLD+'\n h.Parent=m\nend')
    good=patch(src)
    need(good.replace(NEW,OLD)==src,"HAPPY_PATH")
    bad=[good,src.replace("NameDisplayDistance=0","NameDisplayDistance=10"),
         src.replace("HealthDisplayDistance=16","HealthDisplayDistance=0"),
         src.replace(OLD," h.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.Viewer\n"+OLD),
         src.replace("local function soldier(","local function other("),
         src.replace('Instance.new("Humanoid")','Instance.new("Part")'),
         src.replace("h.Parent=m","h.Parent=nil"),src+"\n"+OLD]
    for i,mutant in enumerate(bad):
        try:patch(mutant)
        except ValueError:continue
        raise AssertionError("RED_MUTATION_"+str(i))
    print("SWARM_SUBJECT_SOURCE_NEGATIVES_8_PASS")

def run(root:Path)->None:
    original=selected(root)
    receipt_file=root/RECEIPT
    receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
    need(receipt.get("build_head")==BASE and receipt.get("selected_source_count")==69
         and len(original)==69 and set(original)==set(receipt.get("source_hashes",{}))
         and set(original)==set(receipt.get("source_classes",{})),"WRONG_FORMAL_PARENT")
    original_sha={r:sha(p.read_bytes()) for r,p in original.items()}
    need(original_sha==receipt["source_hashes"] and original_sha[TARGET]==ORIGINAL_SHA
         and receipt["source_classes"][TARGET]=="ModuleScript","SHA_CLASS_LOCK")
    backup=root/"OFF69_SWARM_SUBJECT_EXACT"
    need((root/PLACE).is_file() and not backup.exists(),"PLACE_OR_ROLLBACK_ALREADY_EXISTS")
    before=original[TARGET].read_bytes()
    after=patch(before.decode("utf-8")).encode("utf-8")
    backup.mkdir()
    shutil.copytree(root/"sources",backup/"sources")
    for name in (PROJECT,RECEIPT,PLACE):shutil.copy2(root/name,backup/name)
    original[TARGET].write_bytes(after)
    changed=selected(root)
    updated_sha={r:sha(p.read_bytes()) for r,p in changed.items()}
    need(len(changed)==69 and {r for r in original_sha if original_sha[r]!=updated_sha[r]}=={TARGET},
         "ONLY_ONE_ORIGINAL_ROUTE_CHANGED")
    need(sha((backup/original[TARGET].relative_to(root)).read_bytes())==ORIGINAL_SHA,
         "ROLLBACK_SOURCE_SHA")
    receipt["source_hashes"][TARGET]=updated_sha[TARGET]
    receipt["build_head"]="A_UNAPPROVED_FROM_"+BASE
    meta={
      "feature_id":FEATURE_ID,"formal_parent":BASE,
      "source_route":TARGET,"original_sha256":ORIGINAL_SHA,
      "new_sha256":updated_sha[TARGET],
      "changed_sources":1,"original_unchanged":68,"new_scripts":0,"new_parts":0,
      "new_loops":0,"name_distance_studs":0,"health_distance_studs":16,
      "distance_type":"Subject","rollback":"OFF69_SWARM_SUBJECT_EXACT",
      "formal_adopted":False,"studio":"NOT_TESTED","android15":"NOT_TESTED",
      "actual_art_screenshots":0,"required_art_screenshots":32,
      "kid_fun":"NOT_TESTED","owner_accepted":False}
    receipt["gq470_swarm_subject_visual"]=meta
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (root/"GQ470_SWARM_SUBJECT_A_ONLY.json").write_text(json.dumps(meta,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ470_SWARM_SUBJECT_ONE_OF_69_SOURCE_ONLY_PASS",json.dumps(meta,sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:selftest()
    else:
        need(args.base is not None,"MISSING_BASE")
        run(args.base)
