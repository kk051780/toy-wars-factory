#!/usr/bin/env python3
"""Select original #523 field egg geometry into the existing 31-script Host only.

Strictly preserve the already-approved #551 host and other 30 real script bytes.
The #523 logic lives in its immutable original-author commit, never duplicated here.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path
import xml.etree.ElementTree as ET

ORIGINAL523="54ea74aa15e387d83512566715f44216ba8587a2"
HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
COUNT=31

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def mod(path:Path,name:str):
    return SourceFileLoader(name,str(path.resolve(strict=True))).load_module()

def compose(base:Path,out:Path,author:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if base==out or base.parent!=out.parent:raise ValueError("RED base or cross-directory project mutation")
    mapper=mod(Path("rc_fastlane/select_gq541_original_neutral_fallback.py"),"map541")
    patch=mod(author,"field_egg_523")
    if patch.ORIGINAL_COMMIT!="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9":
        raise ValueError("RED original #523 author changed base")
    old_map, old=mapper.flatten(base)
    if len(old)!=COUNT or HOST not in old:raise ValueError("RED original 31 single Host absent")
    before=old[HOST].read_text(encoding="utf-8")
    after=patch.patch(before)
    if after==before or after.replace(patch.ROWS_LINE,"",1).replace(patch.REPLACEMENT_LINE,patch.ORIGINAL_LINE,1)!=before:
        raise ValueError("RED #523 two-only reversible Host hunks")
    if after.count('local eggId="FIELD_"..i')!=1 or after.count("for i=1,24 do")!=1:
        raise ValueError("RED field egg count or authority")
    path=out.parent/"GQ523_ORIGINAL_FIELD_EGGS_HOST.server.luau"
    if path.exists() and path.read_text(encoding="utf-8")!=after:
        raise ValueError("RED existing GQ523 generated file drift")
    path.write_text(after,encoding="utf-8")
    selected=copy.deepcopy(old_map)
    selected["tree"]["ServerScriptService"][HOST[-1]]["$path"]=path.name
    out.write_text(json.dumps(selected,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    _,new=mapper.flatten(out)
    if len(new)!=COUNT or set(new)!=set(old) or [key for key in old if old[key].read_bytes()!=new[key].read_bytes()]!=[HOST]:
        raise ValueError("RED altered original 30 other sources")
    result={"source_count":COUNT,"only_changed_script":"/".join(HOST),
            "other30_scripts_byte_exact":True,"rollback_to_previous_host_exact":True,
            "original523_head":ORIGINAL523,
            "previous_host_sha256":sha(before.encode()),"current_host_sha256":sha(after.encode()),
            "studio_android_owner":"NOT_TESTED","formal_rc_adopted":False}
    (out.parent/"GQ523_RC31_RECEIPT.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("GQ523_ORIGINAL_SINGLE_HOST_OTHER_30_BYTE_EXACT_ROLLBACK_PASS")

def verify(base:Path,out:Path,place:Path,author:Path):
    mapper=mod(Path("rc_fastlane/select_gq541_original_neutral_fallback.py"),"map541_verify")
    patch=mod(author,"field_egg_523_verify")
    _,old=mapper.flatten(base)
    _,new=mapper.flatten(out)
    if [key for key in old if old[key].read_bytes()!=new[key].read_bytes()]!=[HOST]:
        raise ValueError("RED other source changed")
    source=old[HOST].read_text(encoding="utf-8")
    if new[HOST].read_text(encoding="utf-8")!=patch.patch(source):raise ValueError("RED source selection drift")
    found={}
    for element in ET.parse(place).iter("Item"):
        cls=element.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=element.find("Properties")
        if props is None:raise ValueError("RED missing props")
        name=props.findtext("string[@name='Name']")
        raw=props.findtext("ProtectedString[@name='Source']")
        if raw is None:raw=props.findtext("string[@name='Source']")
        if not name or raw is None or name in found:raise ValueError("RED duplicate/missing source")
        found[name]=(cls,raw.replace("\r\n","\n"))
    if set(found)!={key[-1] for key in new} or len(found)!=COUNT:raise ValueError("RED names/count mismatch")
    for key,p in new.items():
        cls="Script" if p.name.endswith(".server.luau") else "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript"
        if found[key[-1]]!=(cls,p.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED real Rojo Source/Class mismatch for "+key[-1])
    receipt=out.parent/"GQ523_RC31_RECEIPT.json"
    meta=json.loads(receipt.read_text())
    meta["rojo31_source_class_exact"]="31/31"
    meta["private_place_bytes"]=place.stat().st_size
    meta["private_place_sha256"]=sha(place.read_bytes())
    receipt.write_text(json.dumps(meta,sort_keys=True,indent=2)+"\n")
    print("GQ523_TRUE_REAL_ROJO31_SOURCE_CLASS_EXACT_PASS",meta["private_place_bytes"],meta["private_place_sha256"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("compose","verify"))
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--author",required=True,type=Path)
    p.add_argument("--place",type=Path)
    args=p.parse_args()
    if args.action=="compose":compose(args.base,args.out,args.author)
    else:
        if args.place is None:p.error("--place required")
        verify(args.base,args.out,args.place,args.author)

if __name__=="__main__":main()
