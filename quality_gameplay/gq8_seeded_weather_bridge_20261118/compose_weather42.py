#!/usr/bin/env python3
"""Source-select latest verified #815 real42 + already-tested weather bridge.

Does NOT modify #815 existing guardian/Host/Combat/Rules code or add a new
script. Takes only exact portable source from immutable successful run
44318289343 and adds the two original-source overlays to selected 42.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from patch_weather41 import (
    REALM,RENDER,STAGE_RENDER_BLOB,STORM_FENCE,
    flatten,gitblob,patch
)

SOURCE41_GUARDIAN_RUN=44318289343
EXPECTED_42_PLACE_SHA="a32b909a951074a72623a003c77ff43afa7c425e5aa907f45cf9f4423be3ee9a"
CHANGED={REALM,RENDER}

def compose(project:Path,receipt:Path,original_place:Path,out:Path):
    doc,source=flatten(project)
    evidence=json.loads(receipt.read_text(encoding="utf8"))
    if len(source)!=42 or evidence.get("source_count")!=42 or evidence.get("feature")!="GQ815_GUARDIAN_RUNTIME_REAL42":
        raise ValueError("RED_NOT_GUARDIAN42_AUTHOR")
    if hashlib.sha256(original_place.read_bytes()).hexdigest()!=EXPECTED_42_PLACE_SHA:
        raise ValueError("RED_NOT_ACTUAL_42_AUTHOR_PLACE")
    entries={tuple(x["route"].split("/")):x for x in evidence["sources"]}
    if len(entries)!=42 or set(entries)!=set(source):
        raise ValueError("RED_GUARDIAN42_ROUTE_OR_RECEIPT")
    for r,path in source.items():
        b=path.read_bytes()
        e=entries[r]
        if hashlib.sha256(b).hexdigest()!=e["sha256"] or len(b)!=e["bytes"]:
            raise ValueError("RED_GUARDIAN42_UNTRUSTED_SOURCE_"+"/".join(r))
    if gitblob(source[RENDER].read_bytes())!=STAGE_RENDER_BLOB:
        raise ValueError("RED_STAGE_RENDER_811_ALREADY_CHANGED")
    if STORM_FENCE not in source[REALM].read_text("utf8"):
        raise ValueError("RED_REALM_STORM_FENCE_ALREADY_MISSING")
    if out.exists():raise ValueError("RED_REFUSE_OUTPUT_OVERWRITE")
    updated_render,updated_realm=patch(
        source[RENDER].read_text("utf8"),source[REALM].read_text("utf8"))
    out.parent.mkdir(parents=True,exist_ok=True)
    new_paths={}
    for route,value,ext in ((REALM,updated_realm,".server.luau"),
                             (RENDER,updated_render,".luau")):
        target=out.parent/("GQ8_Weather42_"+route[-1]+ext)
        if target.exists():raise ValueError("RED_OUTPUT_COLLISION")
        target.write_text(value,encoding="utf8",newline="\n")
        new_paths[route]=target
    selected=copy.deepcopy(doc)
    selected["name"]="GQ8_GUARDIAN42_STAGE_REALM_SEEDED_WEATHER_PRIVATE_NOT_RC"
    def rebase(node,route=()):
        for name,val in node.items():
            if name.startswith("$"):continue
            key=route+(name,)
            if "$path" in val:
                path=new_paths.get(key,source[key])
                val["$path"]=os.path.relpath(path,out.parent).replace(os.sep,"/")
            else:rebase(val,key)
    rebase(selected["tree"])
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,actual=flatten(out)
    diffs={r for r in source if actual[r].read_bytes()!=source[r].read_bytes()}
    if len(actual)!=42 or diffs!=CHANGED or set(actual)!=set(source):
        raise ValueError("RED_NOT_TWO_EXISTING_SOURCE_42")
    for route in set(source)-CHANGED:
        if source[route].read_bytes()!=actual[route].read_bytes():
            raise ValueError("RED_LOST_GUARDIAN_OR_BATTLE_SOURCE")
    report={
        "feature_id":"GQ8_SEEDED_WEATHER_GUARDIAN42_20261118",
        "source_count":42,"source_base_run":SOURCE41_GUARDIAN_RUN,
        "base_real42_place_sha256":EXPECTED_42_PLACE_SHA,
        "changes":[ "/".join(r) for r in sorted(diffs) ],
        "unchanged_existing_42_scripts":40,
        "guardian_host_combat_castle_item_swarm_unchanged":True,
        "weather_damage_owner":"SINGLE_EXISTING_REALM",
        "weather_schedule_seed":"SINGLE_EXISTING_803_811_HOST",
        "formal_rc_adopted":False,
        "studio_2client":"NOT_TESTED","android15min":"NOT_TESTED",
        "owner_fun":"NO_GO",
        "rollback":"Use exact #815 portable42 from run44318289343; no changed old scripts",
    }
    out.with_suffix(".receipt.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("GQ8_SEEDED_WEATHER_REAL42_TWO_SOURCE_EXACT_WITH_GUARDIANS_PASS")
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--real42",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    compose(a.real42,a.receipt,a.place,a.out)
