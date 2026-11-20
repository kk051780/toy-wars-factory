#!/usr/bin/env python3
"""Independent GQ8 combined-source rehearsal: exact31 + owner Realm34 + owner Regen33.
Never writes canonical RC/main. Both upstream composers own their actual Luau.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
CORE={
 ("ServerScriptService","EGGRUMBLE_LandSeaSkyTraversal"),
 ("ServerScriptService","EGGRUMBLE_RealmBattleCore"),
 ("StarterPlayer","StarterPlayerScripts","EGGRUMBLE_RealmBattleControls"),
}
REGEN={
 ("ServerScriptService","EGGRUMBLE_NaturalRegen"),
 ("ServerScriptService","EGGRUMBLE_PassiveRegenPolicy"),
}

def flatten(project):
    path=Path(project).resolve(strict=True)
    model=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(model.get("tree"),dict):
        raise ValueError("RED_NOT_A_ROJO_PROJECT")
    found={}
    def walk(node,prefix=()):
        for name,child in node.items():
            if name.startswith("$"):continue
            if not isinstance(child,dict):raise ValueError("RED_BAD_NODE")
            route=prefix+(name,)
            if "$path" in child:
                if route in found:raise ValueError("RED_DUPLICATE_ROUTE")
                src=(path.parent/child["$path"]).resolve(strict=True)
                found[route]=src
            else:
                walk(child,route)
    walk(model["tree"])
    return model,found

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compose(original31,regen33,realm34,out):
    original31=Path(original31).resolve(strict=True)
    out=Path(out).resolve()
    if out.exists() or out in (original31,Path(regen33).resolve(),Path(realm34).resolve()):
        raise ValueError("RED_REFUSE_OVERWRITE")
    _,base=flatten(original31)
    regen_model,regen=flatten(regen33)
    _,realm=flatten(realm34)
    if len(base)!=31 or len(regen)!=33 or len(realm)!=34:
        raise ValueError("RED_UNEXPECTED_SOURCE_COUNT")
    base_routes=set(base)
    if HOST not in base_routes:
        raise ValueError("RED_MISSING_SINGLE_HOST")
    if not {("ServerScriptService","EGGRUMBLE_SevenRoleCombat"),
            ("ServerScriptService","EGGRUMBLE_SwarmCombat")}.issubset(base_routes):
        raise ValueError("RED_MISSING_EXISTING_AUTHORITY")
    if set(regen)-base_routes!=REGEN or set(realm)-base_routes!=CORE:
        raise ValueError("RED_UNEXPECTED_ADDON_OR_DUPLICATE")
    if CORE & REGEN:
        raise ValueError("RED_ADDON_COLLISION")
    for route in base_routes:
        source=digest(base[route])
        if digest(realm[route])!=source:
            raise ValueError("RED_REALM_MUTATED_BASE_"+"/".join(route))
        if route!=HOST and digest(regen[route])!=source:
            raise ValueError("RED_REGEN_MUTATED_BASE_"+"/".join(route))
    host=regen[HOST].read_text(encoding="utf-8")
    original=base[HOST].read_text(encoding="utf-8")
    call='NaturalRegen.attach(session,p,role)'
    require='local NaturalRegen=require(script.Parent:WaitForChild("EGGRUMBLE_NaturalRegen"))'
    if host.count(call)!=2 or host.count(require)!=1 or call in original or require in original:
        raise ValueError("RED_MISSING_REGEN_HOST_RUNTIME")
    # Exact author Host transformation: no extras besides one import and two equip hooks.
    import re
    original_from_changed=host.replace(require+"\n","",1)
    original_from_changed,n=re.subn(r"(?m)^[ \t]*NaturalRegen\.attach\(session,p,role\)\n","",original_from_changed)
    if n!=2 or original_from_changed!=original:
        raise ValueError("RED_UNREVIEWED_HOST_CHANGE")
    # Assert existing unmodified single canonical authorities stay untouched.
    output=copy.deepcopy(regen_model)
    output["name"]="GQ8_REAL31_REALM34_REGEN33_COMBINED36_QA_NOT_OFFICIAL"
    out.parent.mkdir(parents=True,exist_ok=True)
    def rebase(node,route=()):
        for name,child in node.items():
            if name.startswith("$"):continue
            p=route+(name,)
            if "$path" in child:
                child["$path"]=os.path.relpath(regen[p],out.parent).replace(os.sep,"/")
            else:rebase(child,p)
    rebase(output["tree"])
    for route in sorted(CORE):
        node=output["tree"]
        for name in route:
            node=node.setdefault(name,{})
        if "$path" in node:raise ValueError("RED_EXISTING_ROUTE")
        node["$path"]=os.path.relpath(realm[route],out.parent).replace(os.sep,"/")
    out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,combined=flatten(out)
    if len(combined)!=36 or set(combined)!=base_routes|REGEN|CORE:
        raise ValueError("RED_NOT_REAL36")
    for route in base_routes:
        if digest(combined[route])!=digest(regen[route]):
            raise ValueError("RED_SELECTED_SOURCE_DRIFT")
    for route in CORE:
        if digest(combined[route])!=digest(realm[route]):
            raise ValueError("RED_REALM_SOURCE_DRIFT")
    evidence={
       "feature_id":"GQ8_CROSSLANE_REALM_REGEN_COMPOSITION_QA_20261118",
       "official_rc_written":False,"main_written":False,
       "baseline_scripts":31,"source_count":36,
       "sources_added":sorted("/".join(k) for k in CORE|REGEN),
       "single_existing_host":True,
       "single_existing_combat":True,
       "source_author_pins":{
         "realm_pr":764,"realm_head":"c51de1ed4feb7a7500ada95d21282402053ef988",
         "regen_pr":775,"regen_head":"5b82f300e6dee08ea1ac20ccd1449db0cd73dbc3",
         "regen_policy_parent_pr":773,
       },
       "original31_except_host_byte_exact":True,
       "all_realm_additions_author_byte_exact":True,
       "all_regen_additions_author_byte_exact":True,
       "base_source_sha256":{"/".join(k):digest(v) for k,v in sorted(base.items())},
       "actual_studio_2client":"NOT_TESTED",
       "android":"NOT_TESTED",
       "fun":"NOT_TESTED",
       "official_rc_adopted":False,
       "rollback":"Select original official31 project and omit all five additions"
    }
    out.with_suffix(".receipt.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ8_CROSSLANE_REALM_REGEN_COMBINED36_SOURCE_PROVENANCE_PASS")
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original31",type=Path,required=True)
    p.add_argument("--regen33",type=Path,required=True)
    p.add_argument("--realm34",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    compose(a.original31,a.regen33,a.realm34,a.out)
