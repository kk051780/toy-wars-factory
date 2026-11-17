#!/usr/bin/env python3
"""Select the GQ8 boss spawn-health fix into the EXISTING canonical V3 31-source Place.

Fail closed unless the current selected boss is byte-exact already-accepted GQ518,
plus source-locked original authors. Nothing edits the author sources or 30 peers.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"rc_fastlane"/"quality_decor732_rc31"))
from select_current import mapping
from select_health import base_518,apply,undo,verify as source_verify

FEATURE="GQ8_BOSS_INITIAL_HEALTH_20261118"
TARGET=("ServerScriptService","EGGRUMBLE_NeutralStoneGiant")
SELECTED="GQ8_BOSS_INITIAL_HEALTH_SELECTED_SOURCE.luau"
RECEIPT="GQ8_BOSS_INITIAL_HEALTH_RC31_RECEIPT.json"

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def validate(base:Path,out:Path,original:Path,author:Path):
    obj,a=mapping(base)
    _,b=mapping(out)
    if len(a)!=31 or set(a)!=set(b) or TARGET not in a:
        raise ValueError("RED_GQ8_HEALTH_SOURCE_SET")
    parent=a[TARGET].read_bytes()
    if parent!=base_518(original.read_bytes(),author):
        raise ValueError("RED_GQ8_HEALTH_SELECTED_BOSS_PARENT_NOT_GQ518")
    patched=b[TARGET].read_bytes()
    source_verify(parent,patched)
    if patched!=apply(parent) or undo(patched)!=parent:
        raise ValueError("RED_GQ8_HEALTH_INVERSE")
    changed=[k for k in a if a[k].read_bytes()!=b[k].read_bytes()]
    if changed!=[TARGET]:
        raise ValueError("RED_GQ8_HEALTH_ONLY_ONE_BOSS_SCRIPT")
    return b,parent,patched

def prepare(base:Path,out:Path,original:Path,author:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or base.parent!=out.parent or (out.parent/SELECTED).exists():
        raise ValueError("RED_GQ8_HEALTH_OUTPUT_COLLISION")
    project,files=mapping(base)
    if len(files)!=31 or TARGET not in files:
        raise ValueError("RED_GQ8_HEALTH_PARENT_MISSING")
    parent=files[TARGET].read_bytes()
    if parent!=base_518(original.read_bytes(),author):
        raise ValueError("RED_GQ8_HEALTH_EXPECTED_GQ518_PARENT_MISMATCH")
    candidate=apply(parent)
    (out.parent/SELECTED).write_bytes(candidate)
    new=copy.deepcopy(project)
    new["name"]="EGGRUMBLE_V3_GQ8_BOSS_HEALTH_INITIAL31"
    new["tree"][TARGET[0]][TARGET[1]]["$path"]=SELECTED
    out.write_text(json.dumps(new,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    validate(base,out,original,author)
    receipt={"feature_id":FEATURE,"source_count":31,"changed_existing_source":TARGET[1],
             "other30_byte_exact":True,"inverse_off_restores_gq518":True,
             "parent_gq518_sha256":sha(parent),"selected_sha256":sha(candidate),
             "new_game_or_remote_or_store":0,"new_boss_scripts":0,
             "native":"PENDING","rojo":"PENDING","studio_android_fun":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ8_BOSS_HEALTH_CANONICAL31_ONE_BOSS_ONLY_OTHER30_EXACT")

def verify(base:Path,out:Path,original:Path,author:Path,place:Path):
    selected,parent,patched=validate(base.resolve(strict=True),out.resolve(strict=True),original,author)
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ8_HEALTH_ROJO_PROPS")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in found:raise ValueError("RED_GQ8_HEALTH_ROJO_DUP")
        found[name]=(klass,source.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={k[-1] for k in selected}:
        raise ValueError("RED_GQ8_HEALTH_ROJO_COUNT")
    for key,path in selected.items():
        klass=("Script" if path.name.endswith(".server.luau") else
               "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]]!=(klass,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ8_HEALTH_ROJO_SOURCE_CLASS_"+key[-1])
    receipt_path=out.parent/RECEIPT
    rec=json.loads(receipt_path.read_text(encoding="utf-8"))
    if rec["parent_gq518_sha256"]!=sha(parent) or rec["selected_sha256"]!=sha(patched):
        raise ValueError("RED_GQ8_HEALTH_RECEIPT_CHANGED")
    rec.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
               place_sha256=sha(place.read_bytes()))
    receipt_path.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print("GQ8_BOSS_HEALTH_CANONICAL31_NATIVE_ROJO_CLASS_SOURCE_EXACT")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("prepare","verify"))
    parser.add_argument("--base",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--original",required=True,type=Path)
    parser.add_argument("--gq518-author",required=True,type=Path)
    parser.add_argument("--place",type=Path)
    a=parser.parse_args()
    if a.command=="prepare":prepare(a.base,a.out,a.original,a.gq518_author)
    else:
        if not a.place:parser.error("--place required")
        verify(a.base,a.out,a.original,a.gq518_author,a.place)
