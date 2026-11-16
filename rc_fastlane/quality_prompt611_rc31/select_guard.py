#!/usr/bin/env python3
"""GQ611: adopt ONLY the original #611 prompt reach Guard in the real current31 Rojo graph.

This is an integration adapter, NOT a second author of Guard gameplay.
Requires immutable original #482 + selected #611 author Git blobs.
All 30 other selected Script Source bytes, paths, and class identities are unchanged.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_482="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
AUTHOR_611="f41246191d35f64fe6c1c097999562f37ccaa1fc"
ORIGINAL_BLOB="ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe"
SELECTED_BLOB="5153bdee57f21328676e72c1b4439e404ab04ab7"
ROUTE=("ServerScriptService","EGGRUMBLE_InteractionGuard")
SELECTED_FILENAME="GQ611_SINGLE_EXISTING_GUARD.luau"
RECEIPT="GQ611_RC31_SOURCE_EXACT_RECEIPT.json"

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def scan(project:Path):
    project=project.resolve(strict=True)
    data=json.loads(project.read_text(encoding="utf-8"))
    found={}
    def visit(node,parts=()):
        if not isinstance(node,dict):raise ValueError("RED_PROJECT_NODE_NOT_OBJECT")
        for name,value in node.items():
            if name.startswith("$"):continue
            key=parts+(name,)
            if not isinstance(value,dict):raise ValueError("RED_INVALID_ROJO_NODE")
            if "$path" in value:
                if set(value)!={"$path"} or key in found:
                    raise ValueError("RED_DUPLICATE_SCRIPT_NODE")
                p=(project.parent/value["$path"]).resolve(strict=True)
                found[key]=p
            else:
                visit(value,key)
    visit(data["tree"])
    if len(found)!=31 or len({key[-1] for key in found})!=31 or ROUTE not in found:
        raise ValueError("RED_RC31_GUARD_AUTHORITY_AND_SOURCE_COUNT")
    if sum(key[-1]=="EGGRUMBLE_InteractionGuard" for key in found)!=1:
        raise ValueError("RED_DUPLICATE_GUARD_AUTHORITY")
    return data,found

def locked(original:Path,selected:Path)->tuple[bytes,bytes]:
    old=original.read_bytes()
    new=selected.read_bytes()
    if gitblob(old)!=ORIGINAL_BLOB:raise ValueError("RED_ORIGINAL482_GUARD_BLOB_DRIFT")
    if gitblob(new)!=SELECTED_BLOB:raise ValueError("RED_ORIGINAL611_SELECTED_GUARD_BLOB_DRIFT")
    for anchor in (
        b"local function configuredReach(part:BasePart,verb:string):number?",
        b"if selected then return nil end",
        b"if (near-root.Position).Magnitude>reach+EXCESS_RADIUS then return false end",
        b"if not positionValid(actor,part,verb) then return false end",
    ):
        if new.count(anchor)!=1:raise ValueError("RED_ORIGINAL611_AUTHORITY_ANCHOR")
    if b"reach+EXCESS_RADIUS" in old or b"MAX_DISTANCE+EXCESS_RADIUS" in new:
        raise ValueError("RED_GUARD_ALREADY_PATCHED_OR_UNSAFE_OLD_ALLOWANCE")
    return old,new

def prepare(base:Path,original:Path,selected:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.exists() or out.parent!=base.parent or out==base:
        raise ValueError("RED_OUTPUT_MUST_BE_FRESH_SIBLING")
    tree,oldmap=scan(base)
    old,new=locked(original,selected)
    if oldmap[ROUTE].read_bytes()!=old:raise ValueError("RED_CURRENT_RC_GUARD_NOT_ORIGINAL482")
    target=out.parent/SELECTED_FILENAME
    if target.exists():raise ValueError("RED_SELECTED_GUARD_OVERWRITE")
    target.write_bytes(new)
    current=copy.deepcopy(tree)
    current["tree"][ROUTE[0]][ROUTE[1]]["$path"]=SELECTED_FILENAME
    out.write_text(json.dumps(current,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,mapped=scan(out)
    if set(mapped)!=set(oldmap):raise ValueError("RED_RC_SCRIPT_LAYOUT_CHANGED")
    changed=[key for key in oldmap if mapped[key].read_bytes()!=oldmap[key].read_bytes()]
    if changed!=[ROUTE]:raise ValueError("RED_NON_GUARD_RUNTIME_SOURCE_CHANGED")
    # Exact OFF: reselect the previous actual-current immutable Guard; no second authority.
    if mapped[ROUTE].read_bytes()!=new or oldmap[ROUTE].read_bytes()!=old:
        raise ValueError("RED_GUARD_SELECTED_OR_OFF_NOT_EXACT")
    receipt={
        "author_original482":AUTHOR_482, "author_original611":AUTHOR_611,
        "original_guard_git_blob":ORIGINAL_BLOB,"selected_guard_git_blob":SELECTED_BLOB,
        "source_count":31,"changed_existing_script":"/".join(ROUTE),
        "other_30_script_bytes_exact":True,"off_rollback_previous_guard_exact":True,
        "prior_guard_sha256":digest(old),"selected_guard_sha256":digest(new),
        "new_scripts":0,"new_runtime_authorities":0,
        "studio_android_fun_owner":"NOT_TESTED","rc_intake_branch_write":False,
    }
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ611_CURRENT31_ONLY_ONE_ORIGINAL_GUARD_OTHER30_OFF_EXACT_PASS")

def verify(base:Path,out:Path,original:Path,selected:Path,place:Path):
    _,oldmap=scan(base)
    _,newmap=scan(out)
    old,new=locked(original,selected)
    if set(oldmap)!=set(newmap):raise ValueError("RED_ROJO_SOURCE_SET_CHANGED")
    for key in oldmap:
        if oldmap[key].read_bytes()!=newmap[key].read_bytes() and key!=ROUTE:
            raise ValueError("RED_OTHER30_RUNTIME_SOURCE_CHANGED")
    if oldmap[ROUTE].read_bytes()!=old or newmap[ROUTE].read_bytes()!=new:
        raise ValueError("RED_GUARD_BEFORE_AFTER_NOT_EXACT")
    actual={}
    for item in ET.parse(place).iter("Item"):
        klass=item.attrib.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_MISSING_SCRIPT_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or src is None or name in actual:
            raise ValueError("RED_MISSING_OR_DUPLICATE_SOURCE_IN_PLACE")
        actual[name]=(klass,src.replace("\r\n","\n"))
    if len(actual)!=31 or set(actual)!={key[-1] for key in newmap}:
        raise ValueError("RED_ACTUAL_ROJO_SCRIPT_COUNT_OR_ID")
    for route,path in newmap.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        expected=(kind,path.read_text(encoding="utf-8").replace("\r\n","\n"))
        if actual[route[-1]]!=expected:
            raise ValueError("RED_ACTUAL_ROJO_SCRIPT_SOURCE_OR_CLASS_"+route[-1])
    receipt_file=out.parent/RECEIPT
    rec=json.loads(receipt_file.read_text(encoding="utf-8"))
    if rec["selected_guard_sha256"]!=digest(new) or not rec["other_30_script_bytes_exact"]:
        raise ValueError("RED_INVALID_GUARD_RECEIPT")
    rec.update({"real_rojo_script_source_class_exact":"31/31",
        "place_bytes":place.stat().st_size,"place_sha256":digest(place.read_bytes())})
    receipt_file.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ611_ACTUAL_31_SOURCE_CLASS_GUARD_ROJO_EXACT_PASS",rec["place_bytes"],rec["place_sha256"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    for key in ("base","out","original","selected"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--place",type=Path)
    args=p.parse_args()
    if args.action=="prepare":
        prepare(args.base,args.original,args.selected,args.out)
    else:
        if args.place is None:p.error("--place required for verify")
        verify(args.base,args.out,args.original,args.selected,args.place)

if __name__=="__main__":main()
