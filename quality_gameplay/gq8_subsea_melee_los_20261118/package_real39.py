#!/usr/bin/env python3
"""Portable, byte-exact true39 source + Rojo handoff for the *authenticated* #220 B.

Does not issue a writer grant, publish, merge, or CAS the canonical RC.
All 39 real selected Luau sources are copied rather than reimplemented.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ORIGINAL36=36
SELECTED39=39
ITEM=("ServerScriptService","EGGRUMBLE_FieldItemPickups")
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
REALM=("ServerScriptService","EGGRUMBLE_RealmBattleCore")
HUD=("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls")
STAGES={
    ("ServerScriptService","GQ802_StageManifestPolicy"),
    ("ServerScriptService","GQ802_StageTileBlueprintPolicy"),
    ("ServerScriptService","GQ802_StageTileVisualRenderer"),
}
CHANGED={ITEM,HOST,REALM,HUD}

def git_blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def source_class(path:Path)->tuple[str,str]:
    if path.name.endswith(".server.luau"):
        return ".server.luau","Script"
    if path.name.endswith(".client.luau"):
        return ".client.luau","LocalScript"
    if path.name.endswith(".luau"):
        return ".luau","ModuleScript"
    raise ValueError("RED_UNSUPPORTED_SCRIPT_CLASS_"+path.name)

def flatten(project:Path)->tuple[dict,dict[tuple[str,...],Path]]:
    p=project.resolve(strict=True)
    doc=json.loads(p.read_text(encoding="utf8"))
    if not isinstance(doc.get("tree"),dict):
        raise ValueError("RED_BAD_ROJO_PROJECT")
    sources={}
    def walk(node:dict,route:tuple[str,...]=()):
        for name,child in node.items():
            if name.startswith("$"):
                continue
            if not re.fullmatch(r"[A-Za-z0-9_]+",name):
                raise ValueError("RED_INVALID_SOURCE_NAME_"+name)
            if not isinstance(child,dict):
                raise ValueError("RED_NOT_ROJO_NODE")
            key=route+(name,)
            if "$path" in child:
                if key in sources:
                    raise ValueError("RED_DUPLICATE_SOURCE_ROUTE")
                sources[key]=(p.parent/child["$path"]).resolve(strict=True)
            else:
                walk(child,key)
    walk(doc["tree"])
    return doc,sources

def prepare(project39:Path,original36:Path,off31:Path,out:Path,head:str)->dict:
    if not re.fullmatch(r"[a-f0-9]{40}",head):
        raise ValueError("RED_UNKNOWN_SOURCE_HEAD")
    original36=original36.resolve(strict=True)
    project39=project39.resolve(strict=True)
    off31=off31.resolve(strict=True)
    out=out.resolve()
    if out.exists() or out.parent==project39.parent or project39==out:
        raise ValueError("RED_OUTPUT_MUST_BE_FRESH_STANDALONE_FOLDER")
    document,selected=flatten(project39)
    _,canonical=flatten(original36)
    _,old31=flatten(off31)
    if len(selected)!=SELECTED39 or len(canonical)!=ORIGINAL36 or len(old31)!=31:
        raise ValueError("RED_TRUE_SOURCE_COUNT_MISMATCH")
    if set(selected)-set(canonical)!=STAGES or set(canonical)-set(selected):
        raise ValueError("RED_DUPLICATE_OR_MISSING_STAGE_ROUTES")
    changed={route for route in canonical
             if selected[route].read_bytes()!=canonical[route].read_bytes()}
    if changed!=CHANGED:
        raise ValueError("RED_UNAUTHORIZED_OR_MISSING_REAL_SCRIPT_OVERLAY_"+repr(changed))
    if len(set(canonical)-changed)!=32:
        raise ValueError("RED_NON_TARGET_32_CHANGED")
    if ITEM not in old31 or HOST not in old31:
        raise ValueError("RED_OFF31_SINGLETON_ABSENT")
    # Source paths are derived ONLY from model route and original file class;
    # never use user-provided relative traversal or duplicate names.
    container=out.parent
    if container.exists() and any(container.iterdir()):
        raise ValueError("RED_REUSED_PACKAGE_DIRECTORY")
    container.mkdir(parents=True,exist_ok=True)
    contents=copy.deepcopy(document)
    contents["name"]="EGGRUMBLE_SOURCE39_PORTABLE_PREP_NOT_OFFICIAL"
    ledger=[]
    for route,origfile in sorted(selected.items()):
        suffix,cls=source_class(origfile)
        payload=origfile.read_bytes()
        if len(payload)<10:
            raise ValueError("RED_EMPTY_SOURCE")
        relative=Path("sources").joinpath(*route[:-1],route[-1]+suffix)
        dest=container/relative
        if dest.exists():
            raise ValueError("RED_DUPLICATE_PACKAGE_SOURCE")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(payload)
        node=contents["tree"]
        for seg in route:node=node[seg]
        node["$path"]=relative.as_posix()
        ledger.append({
            "route":"/".join(route),
            "class":cls,
            "path":relative.as_posix(),
            "sha256":hashlib.sha256(payload).hexdigest(),
            "git_blob":git_blob(payload),
            "bytes":len(payload),
            "origin":"existing_36_script_overlay" if route in CHANGED else
                     "upstream_original_stage_module" if route in STAGES else
                     "official_original36_unchanged",
        })
    out.write_text(json.dumps(contents,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    _,portable=flatten(out)
    if set(portable)!=set(selected) or len(portable)!=SELECTED39:
        raise ValueError("RED_PORTABLE_ROUTE_SET")
    for route,src in selected.items():
        if portable[route].read_bytes()!=src.read_bytes():
            raise ValueError("RED_PORTABLE_SOURCE_INEXACT_"+"/".join(route))
        if source_class(portable[route])[1]!=source_class(src)[1]:
            raise ValueError("RED_PORTABLE_CLASS_DRIFT")
    receipt={
        "directive_id":"OWNER_LATEST_LINEAGE_SINGLE_RC_DRI_20261118_2104_JST",
        "candidate_head":head,
        "formal_rc_source_adoption":"NOT_PERFORMED_BLOCKED_AUTH",
        "format":"REAL39_EXACT_SOURCE_AND_CLASS_B_PORTABLE_V1",
        "source_count":SELECTED39,
        "existing_script_overlays":["/".join(route) for route in sorted(CHANGED)],
        "original36_unmodified_source_count":32,
        "original36_unmodified_git_blobs":{
            "/".join(route):git_blob(canonical[route].read_bytes())
            for route in sorted(set(canonical)-CHANGED)
        },
        "new_stage_modules":["/".join(route) for route in sorted(STAGES)],
        "source_author_refs":[792,796,797,795,812,803,811],
        "stage_physical_random_tiles":False,
        "off36_source_count":ORIGINAL36,
        "off31_source_count":31,
        "off36_rollback":"original unchanged 36 Rojo source/Class project separately pinned",
        "off31_rollback":"original 31 source/Class project separately pinned",
        "sources":ledger,
        "no_github_main_rc_write":True,
        "no_new_damage_store_remote_authority":True,
        "studio_2client":"NOT_TESTED",
        "android_15min":"NOT_TESTED",
        "art_fun_owner":"NO_GO",
    }
    (out.parent/"SOURCE39_B_HANDOFF_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8"
    )
    print("GQ8_B_HANDOFF_PORTABLE_REAL39_SCRIPT_BYTES_EXACT_CLASS_PASS",
          len(portable),sum(item["bytes"] for item in ledger))
    return receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--project39",type=Path,required=True)
    p.add_argument("--official36",type=Path,required=True)
    p.add_argument("--off31",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--candidate-head",required=True)
    a=p.parse_args()
    prepare(a.project39,a.official36,a.off31,a.out,a.candidate_head)

if __name__=="__main__":
    main()
