#!/usr/bin/env python3
"""Genuine existing31 -> additive visual-only VFX33, inverse OFF31 exact."""
import argparse
import copy
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
NEW={"EGGRUMBLE_ElementCueSpec": HERE/"EGGRUMBLE_ElementCueSpec.luau",
     "EGGRUMBLE_ElementCueView": HERE/"EGGRUMBLE_ElementCueView.client.luau"}

def files(project):
    p=Path(project).resolve(strict=True)
    doc=json.loads(p.read_text(encoding="utf-8"))
    result={}
    def walk(node,prefix=()):
        for k,v in node.items():
            if k.startswith("$"): continue
            if not isinstance(v,dict): raise ValueError("RED_INVALID_TREE")
            path=prefix+(k,)
            if "$path" in v:
                result[path]=(p.parent/v["$path"]).resolve(strict=True)
            else: walk(v,path)
    walk(doc["tree"])
    return doc,result

def compose(current31,dest,off=False):
    current31=Path(current31).resolve(strict=True)
    dest=Path(dest).resolve()
    if current31==dest or dest.exists(): raise ValueError("RED_OVERWRITE")
    original,base=files(current31)
    if len(base)!=31: raise ValueError("RED_NOT_GENUINE31")
    tree=original["tree"]
    starter=tree.get("StarterPlayer",{}).get("StarterPlayerScripts")
    if not isinstance(starter,dict): raise ValueError("RED_NO_PLAYER_SCRIPTS")
    if any(k in starter for k in NEW): raise ValueError("RED_ALREADY_VFX")
    doc=copy.deepcopy(original)
    doc["name"]="EGGRUMBLE_REAL_VFX33" if not off else "EGGRUMBLE_REAL_VFX_OFF31"
    def rebase(node,route=()):
        for k,v in node.items():
            if k.startswith("$"):continue
            at=route+(k,)
            if "$path" in v:
                v["$path"]=os.path.relpath(base[at],dest.parent).replace(os.sep,"/")
            else: rebase(v,at)
    rebase(doc["tree"])
    if not off:
        parent=doc["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        for name,source in NEW.items():
            parent[name]={"$path":os.path.relpath(source,dest.parent).replace(os.sep,"/")}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,after=files(dest)
    if len(after)!=(31 if off else 33): raise ValueError("RED_COUNT")
    for key,source in base.items():
        if key not in after or after[key].read_bytes()!=source.read_bytes():
            raise ValueError("RED_EXISTING_SOURCE_CHANGED_"+"/".join(key))
    if not off:
        for name,source in NEW.items():
            key=("StarterPlayer","StarterPlayerScripts",name)
            if after[key].read_bytes()!=source.read_bytes():
                raise ValueError("RED_VFX_SOURCE_CHANGED")
    print("GQ8_VFX_REAL_SOURCE_EXACT",len(after))
    return after

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--current31",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--off",action="store_true")
    a=parser.parse_args()
    compose(a.current31,a.out,a.off)
