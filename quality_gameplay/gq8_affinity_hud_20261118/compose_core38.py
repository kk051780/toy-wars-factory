#!/usr/bin/env python3
"""Compose real V3 selected core36 -> 38 with read-only affinity HUD, or exact OFF36.

Pure presentation: new ReplicatedStorage ModuleScript + StarterPlayerScripts LocalScript.
No edits to the original 36 script sources, game authority or routes.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"handoffs/EGGRUMBLE-AFFINITY-HUD-20261118"
MODULE=SOURCE/"AffinityGuidePolicy.luau"
CLIENT=SOURCE/"EGGRUMBLE_AffinityGuide.client.luau"
MOD_NAME="EGGRUMBLE_AffinityGuidePolicy"
CLIENT_NAME="EGGRUMBLE_AffinityGuide"

def inventory(project: Path):
    obj=json.loads(project.read_text(encoding="utf-8"))
    tree=obj.get("tree")
    if not isinstance(tree,dict): raise ValueError("RED_NO_ROJO_TREE")
    items={}
    def scan(node,route=()):
        for name,val in node.items():
            if name.startswith("$"): continue
            if not isinstance(val,dict): raise ValueError("RED_INVALID_ROJO_NODE")
            key=route+(name,)
            if "$path" in val:
                source=(project.parent/val["$path"]).resolve(strict=True)
                if key in items: raise ValueError("RED_DUPLICATE_ROUTE")
                items[key]=(source,copy.deepcopy(val))
            else: scan(val,key)
    scan(tree)
    return obj,items

def compose(project:Path,dest:Path,enabled:bool):
    project=project.resolve(strict=True);dest=dest.resolve()
    if dest==project or dest.exists(): raise ValueError("RED_OVERWRITE_ORIGINAL")
    base,old=inventory(project)
    if len(old)!=36: raise ValueError("RED_NOT_SELECTED_CORE36")
    names={key[-1] for key in old}
    if not {"EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_CombatFeel"}.issubset(names):
        raise ValueError("RED_MISSING_AUTHOR_GAME_CLIENT")
    if {MOD_NAME,CLIENT_NAME}&names: raise ValueError("RED_DUPLICATE_GUIDE_SCRIPT")
    if not MODULE.is_file() or not CLIENT.is_file(): raise ValueError("RED_NO_GUIDE_SOURCES")
    obj=copy.deepcopy(base)
    obj["name"]="EGGRUMBLE_AFFINITY_HUD_CORE38_GUIDE_ONLY" if enabled else base.get("name","OFF36")
    dest.parent.mkdir(parents=True,exist_ok=True)
    def rebase(node,route=()):
        for name,val in node.items():
            if name.startswith("$"): continue
            key=route+(name,)
            if "$path" in val:
                val["$path"]=os.path.relpath(old[key][0],dest.parent).replace(os.sep,"/")
            else: rebase(val,key)
    rebase(obj["tree"])
    expected={}
    if enabled:
        rep=obj["tree"].setdefault("ReplicatedStorage",{"$className":"ReplicatedStorage"})
        if not isinstance(rep,dict) or MOD_NAME in rep: raise ValueError("RED_MODULE_COLLISION")
        player=obj["tree"].get("StarterPlayer")
        scripts=player and player.get("StarterPlayerScripts")
        if not isinstance(scripts,dict) or CLIENT_NAME in scripts:
            raise ValueError("RED_NO_EXISTING_CLIENT_FOLDER_OR_COLLISION")
        rep[MOD_NAME]={"$path":os.path.relpath(MODULE,dest.parent).replace(os.sep,"/")}
        scripts[CLIENT_NAME]={"$path":os.path.relpath(CLIENT,dest.parent).replace(os.sep,"/")}
        expected={
            ("ReplicatedStorage",MOD_NAME):MODULE,
            ("StarterPlayer","StarterPlayerScripts",CLIENT_NAME):CLIENT,
        }
    dest.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,actual=inventory(dest)
    if len(actual)!=36+(2 if enabled else 0): raise ValueError("RED_WRONG_SCRIPT_COUNT")
    for key,(source,meta) in old.items():
        if key not in actual: raise ValueError("RED_MISSING_ORIGINAL_ROUTE")
        path,newmeta=actual[key]
        if source.read_bytes()!=path.read_bytes(): raise ValueError("RED_ORIGINAL_SOURCE_CHANGED")
        if meta.get("$className")!=newmeta.get("$className"):
            raise ValueError("RED_ORIGINAL_CLASS_CHANGED")
    if set(actual)-set(old)!=set(expected): raise ValueError("RED_NEW_ROUTE_SCOPE_CHANGED")
    for key,path in expected.items():
        if actual[key][0]!=path.resolve(): raise ValueError("RED_GUIDE_SOURCE_PATH")
    receipt={
        "profile":"ON38" if enabled else "OFF36",
        "feature_id":"BATTLE_AFFINITY_HUD_20261118",
        "selected_core36_byte_exact":True,
        "source_count":len(actual),
        "new_scripts":{"/".join(key):hashlib.sha256(path.read_bytes()).hexdigest() for key,path in expected.items()},
        "gameplay_hit_authority":"UNCHANGED",
        "studio":"NOT_TESTED","android":"NOT_TESTED",
        "rc":"NOT_OFFICIALLY_ADOPTED",
    }
    dest.with_suffix(".receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("GQ8_AFFINITY_HUD_CORE36_TO38_SOURCE_EXACT_PASS" if enabled else "GQ8_AFFINITY_HUD_OFF36_BYTE_EXACT_PASS")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--current36",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--off",action="store_true")
    a=p.parse_args()
    compose(a.current36,a.out,not a.off)
