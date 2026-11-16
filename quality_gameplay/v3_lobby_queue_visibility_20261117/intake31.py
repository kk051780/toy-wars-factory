#!/usr/bin/env python3
"""GQ615 formal-ready ONE existing current Host overlay selector for canonical RC31.

Never directly writes official RC, game authority, main, or another author's
files. Emits a new sibling project and verifies true Rojo Source/Class/paths.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

from select_feedback import apply, CHANGES, FEATURE_ID

SCRIPT_COUNT=31
HOST="EGGRUMBLE_LobbyCastleModesPreview"
CLASSES={"Script","LocalScript","ModuleScript"}

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def mapping(project:Path):
    project=project.resolve(strict=True)
    obj=json.loads(project.read_text(encoding="utf-8"))
    if "tree" not in obj or not isinstance(obj["tree"],dict):
        raise ValueError("RED_RC31_PROJECT_INVALID")
    scripts={}
    def walk(node:dict,route:tuple=()):
        for key,value in node.items():
            if key.startswith("$"):
                continue
            if not isinstance(value,dict):
                raise ValueError("RED_INVALID_PROJECT_CHILD")
            here=route+(key,)
            if "$path" in value:
                if set(value)!={"$path"} or here in scripts:
                    raise ValueError("RED_DUPLICATE_SOURCE")
                scripts[here]=(project.parent/value["$path"]).resolve(strict=True)
            else:
                walk(value,here)
    walk(obj["tree"])
    hosts=[k for k in scripts if k[-1]==HOST]
    if len(scripts)!=SCRIPT_COUNT or len(hosts)!=1 or len({k[-1] for k in scripts})!=SCRIPT_COUNT:
        raise ValueError("RED_NOT_EXACT_31_AND_ONE_HOST")
    if scripts[hosts[0]].name.endswith(".server.luau") is False:
        raise ValueError("RED_HOST_NOT_SERVER_SCRIPT")
    return obj,scripts,hosts[0]

def restore(selected:str)->str:
    v=selected
    for a,b in reversed(CHANGES):
        if a==b:
            continue
        if v.count(b)!=1:
            raise ValueError("RED_CURRENT_HOST_INVERSE_DIFF_NOT_SINGLE")
        v=v.replace(b,a,1)
    return v

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.exists() or out==base:
        raise ValueError("RED_REFUSE_OVERWRITE_SOURCE")
    obj,old,host=mapping(base)
    before=old[host].read_text(encoding="utf-8")
    after=apply(before)
    if restore(after)!=before or after==before:
        raise ValueError("RED_INVERSE_ROLLBACK_WRONG_INPUT_HOST")
    out.parent.mkdir(parents=True,exist_ok=True)
    host_file=out.parent/"GQ615_CANONICAL_CURRENT_HOST_ONLY.server.luau"
    if host_file.exists():
        raise ValueError("RED_SELECTED_HOST_ALREADY_EXISTS")
    host_file.write_text(after,encoding="utf-8")
    project=copy.deepcopy(obj)
    def rebase(node:dict,route:tuple=()):
        for k,value in node.items():
            if k.startswith("$"):
                continue
            route2=route+(k,)
            if "$path" in value:
                file=host_file if route2==host else old[route2]
                value["$path"]=os.path.relpath(file,out.parent).replace(os.sep,"/")
            else:
                rebase(value,route2)
    rebase(project["tree"])
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,now,new_host=mapping(out)
    changed=[k for k in old if old[k].read_bytes()!=now[k].read_bytes()]
    if set(old)!=set(now) or new_host!=host or changed!=[host]:
        raise ValueError("RED_NOT_ONE_EXISTING_HOST_CHANGE")
    receipt={
        "feature_id":FEATURE_ID,"original_source_project":str(base),
        "selected_project":str(out),"source_count":31,
        "changed_existing_server_host":"/".join(host),
        "all_other30_byte_exact":True,
        "rollback_current_host_byte_exact":True,
        "original_host_sha256":sha(before.encode("utf-8")),
        "selected_host_sha256":sha(after.encode("utf-8")),
        "source_exact_rojo_verified":False,
        "official_rc_adopted":False,
        "studio_android_fun_owner":"NOT_TESTED"
    }
    (out.parent/"GQ615_DIRECT31_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ615_DIRECT_CURRENT_RC31_ONE_HOST_OTHER30_EXACT_ROLLBACK_PASS")

def embedded(place:Path):
    tree=ET.parse(place)
    items={}
    def find_text(n:ET.Element,key:str):
        props=n.find("Properties")
        if props is None:
            return None
        for tag in ("string","ProtectedString"):
            found=props.find(tag+f"[@name='{key}']")
            if found is not None:
                return found.text or ""
        return None
    def walk(n:ET.Element,route:tuple=()):
        if n.tag=="Item":
            kind=n.get("class")
            name=find_text(n,"Name")
            if not name:
                raise ValueError("RED_NAMELESS_ROJO_INSTANCE")
            route=route+(name,)
            if kind in CLASSES:
                source=find_text(n,"Source")
                if source is None or route in items:
                    raise ValueError("RED_BAD_EMBEDDED_SCRIPT")
                items[route]=(kind,source.replace("\r\n","\n"))
        for sub in n:
            if sub.tag=="Item":
                walk(sub,route)
    walk(tree.getroot())
    if len(items)!=SCRIPT_COUNT:
        raise ValueError("RED_NOT31_ROJO")
    return items

def verify(base:Path,out:Path,place:Path):
    _,before,host=mapping(base)
    _,after,second=mapping(out)
    if host!=second or set(before)!=set(after):
        raise ValueError("RED_SCRIPT_LAYOUT_CHANGED")
    if after[host].read_text(encoding="utf-8")!=apply(before[host].read_text(encoding="utf-8")):
        raise ValueError("RED_DIFF_NOT_ACTUAL_SELECTED_HOST")
    if [k for k in before if before[k].read_bytes()!=after[k].read_bytes()]!=[host]:
        raise ValueError("RED_OTHER30_SOURCE_MODIFIED")
    xml=embedded(place)
    if set(xml)!={k for k in after}:
        raise ValueError("RED_ROJO_SCRIPT_PATHS_NOT_EXACT")
    for route,src in after.items():
        kind=("Script" if src.name.endswith(".server.luau") else
              "LocalScript" if src.name.endswith(".client.luau") else "ModuleScript")
        expected=(kind,src.read_text(encoding="utf-8").replace("\r\n","\n"))
        if xml[route]!=expected:
            raise ValueError("RED_ROJO_SCRIPT_CLASS_OR_SOURCE_"+route[-1])
    rec=out.parent/"GQ615_DIRECT31_SOURCE_RECEIPT.json"
    proof=json.loads(rec.read_text())
    proof.update(source_exact_rojo_verified=True,
                 real_rojo_source_class_path="31/31",
                 private_rojo_place_sha256=sha(place.read_bytes()),
                 private_rojo_place_bytes=place.stat().st_size)
    rec.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n")
    print("GQ615_DIRECT_RC31_SOURCE_SELECT_REAL_ROJO_31_31_PASS")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("action",choices=("prepare","verify"))
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--place",type=Path)
    o=a.parse_args()
    if o.action=="prepare":prepare(o.base,o.out)
    else:
        if not o.place:
            a.error("--place needed")
        verify(o.base,o.out,o.place)
