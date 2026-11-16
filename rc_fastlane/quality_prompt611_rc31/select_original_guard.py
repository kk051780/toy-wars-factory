#!/usr/bin/env python3
"""GQ611 original Guard single-source selection into current EGGRUMBLE RC31.

This script never writes official RC: it prepares/rechecks a sibling Rojo project.
It uses the exact original #482 Guard and exact already-tested #611 patch.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROUTE=("ServerScriptService","EGGRUMBLE_InteractionGuard")
N=31
ORIGINAL_BLOB="ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe"
SELECTED_BLOB="5153bdee57f21328676e72c1b4439e404ab04ab7"
FLAG="PROMPT_CONFIGURED_REACH_611"
NAME="GQ611_SELECTED_INTERACTION_GUARD.luau"
RECEIPT="GQ611_ONE_GUARD_RC31_RECEIPT.json"

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def author(verify:Path):
    spec=importlib.util.spec_from_file_location("gq611_original_verifier",verify)
    if spec is None or spec.loader is None:
        raise ValueError("RED_MISSING_AUTHOR_VERIFIER")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    if m.EXPECTED_GIT_BLOB!=ORIGINAL_BLOB:
        raise ValueError("RED_ORIGINAL_AUTHOR_LOCK_CHANGED")
    return m

def flat(project:Path):
    project=project.resolve(strict=True)
    d=json.loads(project.read_text(encoding="utf8"))
    out={}
    def visit(tree,route=()):
        for key,node in tree.items():
            if key.startswith("$"):
                continue
            if not isinstance(node,dict):
                raise ValueError("RED_PROJECT_INVALID_NODE")
            k=route+(key,)
            if "$path" in node:
                if set(node)!={"$path"} or k in out:
                    raise ValueError("RED_DUPLICATE_OR_COMPLEX_SCRIPT")
                out[k]=(project.parent/node["$path"]).resolve(strict=True)
            else:
                visit(node,k)
    visit(d["tree"])
    if len(out)!=N or len({k[-1] for k in out})!=N or ROUTE not in out:
        raise ValueError("RED_EXPECT_EXACT31_AND_ONE_GUARD")
    return d,out

def candidate_bytes(original:bytes,selected:bytes,verifier:Path):
    m=author(verifier)
    if blob(original)!=ORIGINAL_BLOB or blob(selected)!=SELECTED_BLOB:
        raise ValueError("RED_PINNED_GUARD_AUTHOR_BLOB_CHANGED")
    if m.select(original.decode("utf8")).encode("utf8")!=selected:
        raise ValueError("RED_CANDIDATE_NOT_AUTHOR_PATCH")
    return m

def project_prepare(base:Path,out:Path,original_path:Path,
                    selected_path:Path,verifier:Path):
    if out.exists() or out.parent.resolve()!=base.resolve().parent:
        raise ValueError("RED_OUTPUT_EXISTS_OR_DIFFERENT_DIRECTORY")
    d,mapping=flat(base)
    original=original_path.read_bytes()
    selected=selected_path.read_bytes()
    verifier_mod=candidate_bytes(original,selected,verifier)
    if mapping[ROUTE].read_bytes()!=original:
        raise ValueError("RED_CURRENT_RC_GUARD_DRIFT_OR_ALREADY_SELECTED")
    newfile=out.parent/NAME
    if newfile.exists():
        raise ValueError("RED_OUTPUT_GUARD_ALREADY_EXISTS")
    newfile.write_bytes(selected)
    copyproj=copy.deepcopy(d)
    copyproj["tree"][ROUTE[0]][ROUTE[1]]["$path"]=NAME
    out.write_text(json.dumps(copyproj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,now=flat(out)
    if set(mapping)!=set(now) or [k for k in mapping if mapping[k].read_bytes()!=now[k].read_bytes()]!=[ROUTE]:
        raise ValueError("RED_ONE_GUARD_ONLY_OTHER30_CHANGED")
    # Verify selected source/return path and inverse rollback as exact source bytes.
    verifier_mod.check(original_path,selected_path)
    report={
        "feature_id":FLAG,
        "script_count":N,
        "only_changed_script":"/".join(ROUTE),
        "other_30_byte_exact":True,
        "source_lock_original_blob":ORIGINAL_BLOB,
        "source_lock_selected_blob":SELECTED_BLOB,
        "original_guard_sha256":digest(original),
        "selected_guard_sha256":digest(selected),
        "off_rollback_guard_byte_exact":True,
        "real_rojo_exact":"NOT_RUN",
        "official_rc_adopted":False,
        "studio_2client":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "owner_fun":"NOT_TESTED"
    }
    (out.parent/RECEIPT).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ611_CURRENT_RC31_ONE_GUARD_SOURCE_LOCK_30_UNCHANGED_OFF_EXACT_PASS")

def project_verify(base:Path,out:Path,place:Path,original_path:Path,
                   selected_path:Path,verifier:Path):
    _,old=flat(base)
    _,new=flat(out)
    original=original_path.read_bytes()
    selected=selected_path.read_bytes()
    author_mod=candidate_bytes(original,selected,verifier)
    author_mod.check(original_path,selected_path)
    if old[ROUTE].read_bytes()!=original or new[ROUTE].read_bytes()!=selected:
        raise ValueError("RED_OLD_OR_SELECTED_GUARD_BYTES_MISMATCH")
    if set(old)!=set(new) or [k for k in old if old[k].read_bytes()!=new[k].read_bytes()]!=[ROUTE]:
        raise ValueError("RED_CHANGED_OTHER_THAN_ONE_GUARD")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.attrib.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"):
            continue
        props=item.find("Properties")
        if props is None:
            raise ValueError("RED_MISSING_EMBEDDED_SCRIPT_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        content=props.findtext("ProtectedString[@name='Source']")
        if content is None:
            content=props.findtext("string[@name='Source']")
        if not name or content is None or name in embedded:
            raise ValueError("RED_EMBEDDED_DUPLICATE_OR_EMPTY_SCRIPT")
        embedded[name]=(kind,content.replace("\r\n","\n"))
    if len(embedded)!=N or set(embedded)!={k[-1] for k in new}:
        raise ValueError("RED_EMBEDDED_COUNT_OR_NAME_MISMATCH")
    for route,path in new.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else
              "ModuleScript")
        source=path.read_text(encoding="utf8").replace("\r\n","\n")
        if embedded[route[-1]]!=(kind,source):
            raise ValueError("RED_ROJO_SOURCE_CLASS_MISMATCH_"+route[-1])
    receipt_path=out.parent/RECEIPT
    r=json.loads(receipt_path.read_text())
    if not r["other_30_byte_exact"] or not r["off_rollback_guard_byte_exact"]:
        raise ValueError("RED_GUARD_SOURCE_RECEIPT_INCOMPLETE")
    r.update(real_rojo_exact="31/31",place_sha256=digest(place.read_bytes()),
             place_bytes=place.stat().st_size,source_class_exact=True)
    receipt_path.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ611_RC31_TRUE_NATIVE_ROJO31_SOURCE_CLASS_AND_ROLLBACK_PASS",r["place_bytes"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    for k in ("base","out","original","selected","verifier"):
        p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="prepare":
        project_prepare(a.base,a.out,a.original,a.selected,a.verifier)
    else:
        if a.place is None:
            p.error("--place required")
        project_verify(a.base,a.out,a.place,a.original,a.selected,a.verifier)
if __name__=="__main__":
    main()
