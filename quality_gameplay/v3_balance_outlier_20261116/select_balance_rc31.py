#!/usr/bin/env python3
"""Fail-closed PRIVATE canonical31 parity check plus standalone BalanceMetrics QA.

Important: the #487 BalanceMetrics module is NOT one of the canonical 31
in-game Source slots. Never inject it as the 32nd script or claim gameplay
integration. Build a 31/31 byte-identical clone for regression evidence only.
"""
import argparse
import copy
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

MODULE = "EGGRUMBLE_BalanceMetrics"
CLASSES = {"Script", "LocalScript", "ModuleScript"}

def flattened(path: Path):
    lib = importlib.machinery.SourceFileLoader(
        "canonical_gq555_selector", "rc_fastlane/select_gq555_original_bot_nearest.py").load_module()
    return lib.flatten(path)

def prepare(base: Path, out: Path):
    tree, sources = flattened(base)
    if len(sources) != 31 or any(route[-1] == MODULE for route in sources):
        raise ValueError("RED: expected 31 canonical scripts WITHOUT QA-only BalanceMetrics")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise ValueError("RED: cannot silently overwrite prepared parity project")
    doc = copy.deepcopy(tree)
    doc["name"] = "GQ568_PRIVATE_CANONICAL_31_SOURCE_PARITY_NO_RUNTIME_CHANGE"
    def remap(node, prefix=()):
        for key,val in node.items():
            if key.startswith("$"):
                continue
            route=prefix+(key,)
            if "$path" in val:
                val["$path"] = os.path.relpath(sources[route],out.parent).replace(os.sep,"/")
            else:
                remap(val,route)
    remap(doc["tree"])
    out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,after=flattened(out)
    if len(after)!=31 or set(after)!=set(sources):
        raise ValueError("RED: canonical script count or source routes changed")
    for route in sources:
        if after[route].read_bytes()!=sources[route].read_bytes():
            raise ValueError("RED: original Source modified " + "/".join(route))
    receipt={
       "source_count":31,"preserved_source_bytes":"31/31",
       "changed_original_scripts":0,"added_gameplay_script":False,
       "qa_balance_module_not_in_canonical":True,
       "standalone_balance_qa_attached_to_native_ci":True,
       "official_rc_modified":False,"runtime_or_studio_adoption":False
    }
    (out.parent/"GQ568_PARITY_RECEIPT.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ568_PRIVATE_ORIGINAL31_ZERO_CHANGE_PASS")
    return receipt

def verify(base: Path, project: Path, place: Path):
    _,source=flattened(base)
    _,actual=flattened(project)
    if len(source)!=31 or len(actual)!=31 or set(source)!=set(actual):
        raise ValueError("RED: source count mismatch")
    for route in source:
        if source[route].read_bytes()!=actual[route].read_bytes():
            raise ValueError("RED: modified canonical source " + "/".join(route))
    found={}
    for node in ET.parse(place).getroot().iter("Item"):
        cls=node.get("class")
        if cls not in CLASSES:
            continue
        props=node.find("Properties")
        if props is None:
            raise ValueError("RED: missing Roblox properties")
        name=props.findtext("string[@name='Name']")
        contents=props.findtext("ProtectedString[@name='Source']")
        if contents is None:
            contents=props.findtext("string[@name='Source']")
        if not name or contents is None or name in found:
            raise ValueError("RED: missing, empty or duplicate Script source")
        found[name]=(cls,contents.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={key[-1] for key in source}:
        raise ValueError("RED: script mismatch in real Place")
    for route,path in actual.items():
        cls="Script" if path.name.endswith(".server.luau") else (
            "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED: Source/Class mismatch: " + "/".join(route))
    receipt={
        "source_class_exact":"31/31",
        "unchanged_canonical_sources":"31/31",
        "added_gameplay_scripts":0,
        "qa_balance_patch_is_outside_place":True,
        "actual_private_place_bytes":place.stat().st_size,
        "actual_private_place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),
        "formal_rc_written":False,"studio_android_owner":"NOT_TESTED"
    }
    (project.parent/"GQ568_ROJO_RECEIPT.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("GQ568_PRIVATE_31_ORIGINAL_SOURCE_CLASS_EXACT_PASS",receipt["actual_private_place_bytes"])
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--place",type=Path)
    args=p.parse_args()
    if args.command=="prepare":
        prepare(args.base,args.out)
    else:
        if not args.place:
            p.error("--place is required")
        verify(args.base,args.out,args.place)

if __name__=="__main__":
    main()
