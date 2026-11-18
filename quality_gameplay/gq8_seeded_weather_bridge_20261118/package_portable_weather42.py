#!/usr/bin/env python3
"""Self-contained EXACT 42-source intake packet for sole authenticated #220 B.

Select only already-verified original #815 Guardian42 + one existing Realm and
one existing StageRenderer weather bridge. NO change to official branch or
Studio publishing. The portable project works WITHOUT other artifact folders.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from patch_weather41 import REALM,RENDER,flatten,gitblob

ONLY_CHANGED={REALM,RENDER}

def script_class(path:Path)->tuple[str,str]:
    if path.name.endswith(".server.luau"):return ".server.luau","Script"
    if path.name.endswith(".client.luau"):return ".client.luau","LocalScript"
    if path.name.endswith(".luau"):return ".luau","ModuleScript"
    raise ValueError("RED_BAD_RUNTIME_SOURCE_CLASS:"+str(path))

def package(selected:Path,original:Path,out:Path):
    if out.exists() or out.parent.exists():
        raise ValueError("RED_REFUSE_OVERWRITE_PORTABLE42_OUTPUT")
    doc,new=flatten(selected)
    _,old=flatten(original)
    if len(new)!=42 or len(old)!=42 or set(new)!=set(old):
        raise ValueError("RED_ORIGINAL_GUARDIAN42_SOURCE_IDENTITY")
    changed={r for r in new if new[r].read_bytes()!=old[r].read_bytes()}
    if changed!=ONLY_CHANGED:
        raise ValueError("RED_PORTABLE_WEATHER42_NOT_EXACT_TWO_CHANGED")
    for route in new:
        if not all(re.fullmatch(r"[A-Za-z0-9_]+",x) for x in route):
            raise ValueError("RED_UNSAFE_ROBLOX_ROUTE")
    product=copy.deepcopy(doc)
    product["name"]="GQ8_GUARDIAN42_SEEDED_WEATHER_PORTABLE_TO_B_NOT_FORMAL"
    out.parent.mkdir(parents=True)
    rows=[]
    for route,src in sorted(new.items()):
        suffix,cls=script_class(src)
        rel=Path("sources").joinpath(*route[:-1],route[-1]+suffix)
        target=out.parent/rel
        if target.exists():
            raise ValueError("RED_DUPLICATE_PORTABLE_SOURCE")
        target.parent.mkdir(parents=True,exist_ok=True)
        data=src.read_bytes()
        target.write_bytes(data)
        node=product["tree"]
        for element in route:node=node[element]
        node["$path"]=rel.as_posix()
        rows.append({
            "route":"/".join(route),
            "path":rel.as_posix(),"class":cls,"bytes":len(data),
            "sha256":hashlib.sha256(data).hexdigest(),"git_blob":gitblob(data),
            "origin":"weather_overlay_existing_source" if route in changed
               else "unchanged_original_guardian42_source"
        })
    out.write_text(json.dumps(product,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,again=flatten(out)
    if len(again)!=42 or set(again)!=set(new):
        raise ValueError("RED_PORTABLE42_ROUTE_CHANGE")
    for route,src in new.items():
        if again[route].read_bytes()!=src.read_bytes() or script_class(again[route])!=script_class(src):
            raise ValueError("RED_PORTABLE42_BYTES_OR_CLASS_CHANGE")
    receipt={
        "feature_id":"GQ8_GUARDIAN42_WEATHER_PORTABLE_INTAKE",
        "script_count":42,"original_guardian42_scripts":42,
        "modified_original_scripts":sorted("/".join(x) for x in changed),
        "untouched_original_scripts":40,
        "all_selected_source_bytes":sum(r["bytes"] for r in rows),
        "new_server_authorities":0,"new_remotes":0,
        "original_guardian42_immutable":True,
        "weather_controller":"EXISTING_REALM_ONLY",
        "studio_2client":"NOT_TESTED",
        "android15":"NOT_TESTED",
        "fun_owner":"NO_GO",
        "formal_rc_cas":False,
        "rollback":"Use #815 exact original guardian42 portable42 to drop the 2 weather changes",
        "sources":rows
    }
    manifest=out.parent/"B_PORTABLE42_WEATHER_SOURCE_RECEIPT.json"
    manifest.write_text(json.dumps(receipt,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ8_DRI_PORTABLE_WEATHER42_SOURCE_BYTES_CLASS_ROUTE_EXACT",receipt["all_selected_source_bytes"])
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--selected",type=Path,required=True)
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    package(a.selected,a.original,a.out)
