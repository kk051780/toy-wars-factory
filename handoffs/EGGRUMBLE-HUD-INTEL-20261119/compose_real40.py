#!/usr/bin/env python3
"""GQ828: actual exact Core36 Place -> isolated Real40 ON + exact OFF36.
Never edits any original 36-source body or GitHub formal RC branch.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

CORE_SHA="f77b4d4393d9e9b19b65566413432a7a9f13962b"
CLASSES={"Script":".server.luau","LocalScript":".client.luau","ModuleScript":".luau"}
PREFIX=Path(__file__).resolve().parent
ADDITIONS={
 "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy":
     ("ModuleScript","HudPresentationPolicy.luau"),
 "ServerScriptService/EGGRUMBLE_MapVisibilityPolicy":
     ("ModuleScript","MapVisibilityPolicy.luau"),
 "ServerScriptService/EGGRUMBLE_MapIntelBridge":
     ("Script","EGGRUMBLE_MapIntelBridge.server.luau"),
 "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime":
     ("LocalScript","EGGRUMBLE_HudIntelRuntime.client.luau"),
}
def digest(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
def contents(root):
    original={}
    classes={}
    def recurse(item,prefix):
        properties=item.find("Properties")
        name=properties.findtext("string[@name='Name']") if properties is not None else None
        if not name or not re.fullmatch(r"[A-Za-z0-9_]+",name):
            raise ValueError("RED_INVALID_MODEL_ROUTE")
        route=prefix+(name,)
        if route in classes: raise ValueError("RED_DUPLICATE_ROUTE")
        cls=item.get("class")
        classes[route]=cls
        if cls in CLASSES:
            src=properties.findtext("string[@name='Source']")
            if src is None:
                src=properties.findtext("ProtectedString[@name='Source']")
            if src is None: raise ValueError("RED_MISSING_SOURCE")
            original[route]=(cls,src.replace("\r\n","\n"))
        for child in item.findall("Item"):
            recurse(child,route)
    for item in root.findall("Item"):
        recurse(item,())
    return original,classes

def project_for(sources, classes, target:Path, name:str):
    sources_dir=target/"sources"
    sources_dir.mkdir(parents=True,exist_ok=False)
    tree={"$className":"DataModel"}
    routing=[]
    for route,(cls,src) in sorted(sources.items()):
        node=tree
        for j,part in enumerate(route):
            node=node.setdefault(part,{})
            if j<len(route)-1:
                node.setdefault("$className",classes.get(route[:j+1]) or "Folder")
        leaf=sources_dir/(route[-1]+CLASSES[cls])
        if leaf.exists(): raise ValueError("RED_DUPLICATE_SCRIPT_FILENAME")
        leaf.write_text(src,encoding="utf8",newline="\n")
        node["$path"]="sources/"+leaf.name
        routing.append({"route":"/".join(route),"class":cls,
                        "sha256":digest(leaf),"bytes":leaf.stat().st_size})
    path=target/(name+".project.json")
    path.write_text(json.dumps({"name":name,"tree":tree},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return path,routing

def run(place:Path,receipt:Path,out:Path):
    record=json.loads(receipt.read_text(encoding="utf8"))
    assert record.get("build_sha")==CORE_SHA, "RED_NOT_OFFICIAL_SAME_HEAD_BUILD"
    assert record.get("selected_in_formal_rc_branch") is True, "RED_NOT_OFFICIAL"
    assert record.get("source_count")==36,"RED_SOURCE_COUNT"
    assert record.get("place_sha256")==digest(place),"RED_PLACE_BYTES_DRIFT"
    source,classes=contents(ET.parse(place).getroot())
    if len(source)!=36:raise ValueError("RED_REAL36_SOURCE_NOT_PRESENT")
    before={k:(v[0],v[1].encode("utf8")) for k,v in source.items()}
    assert ("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview") in before
    assert ("ServerScriptService","EGGRUMBLE_SwarmCombat") in before
    if out.exists():raise ValueError("RED_REFUSE_OVERWRITE_BUILD")
    out.mkdir(parents=True)
    off=out/"off36";off.mkdir()
    offProject,offIndex=project_for(source,classes,off,"GQ828_OFF36")
    combined=dict(source)
    for route,(cls,filename) in ADDITIONS.items():
        t=tuple(route.split("/"))
        if t in combined:raise ValueError("RED_NEW_SCRIPT_COLLISION_"+route)
        path=PREFIX/filename
        if not path.exists():raise ValueError("RED_MISSING_REAL_SCRIPT_"+filename)
        combined[t]=(cls,path.read_text(encoding="utf8"))
        classes[t]=cls
        for i in range(1,len(t)):
            prefix=t[:i]
            classes.setdefault(prefix, "Folder" if len(prefix)>1 else prefix[0])
    assert len(combined)==40
    for k,v in before.items():
        assert (combined[k][0],combined[k][1].encode("utf8"))==v,"RED_EXISTING_SOURCE_OVERWRITE"
    assert len({x[-1] for x in combined})==40,"RED_DUPLICATE_SCRIPT_NAMES"
    on=out/"on40";on.mkdir()
    onProject,onIndex=project_for(combined,classes,on,"GQ828_REAL40_HUD_MAP")
    metadata={
      "feature":"GQ8_HUD_INTEL_FOG_20261119","base_rc":CORE_SHA,
      "original_place_sha256":digest(place),
      "original36_source_preserved":True,
      "new_sources":[*ADDITIONS],"source_count":40,
      "native":"PENDING","rojo":"PENDING","off36":"PENDING",
      "official_rc_adopted":False,"studio_2client":"NOT_TESTED",
      "android15":"NOT_TESTED","fun":"NOT_TESTED","purchases_enabled":False,
      "new_remote":"EGGRUMBLE_MapIntelUpdate_V1 one-way FireClient only",
      "rollback":"OFF36 project exact original36 sources",
      "on_sources":onIndex,"off_sources":offIndex,
      "on_project":str(onProject),"off_project":str(offProject),
    }
    (out/"SOURCE_SELECTION_RECEIPT.json").write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("GQ828_EXACT_ORIGINAL36_PRESERVED_REAL40_SELECTED_PASS",digest(place))

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--place",type=Path,required=True)
    parser.add_argument("--receipt",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    opt=parser.parse_args()
    run(opt.place,opt.receipt,opt.out)
