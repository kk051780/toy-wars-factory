#!/usr/bin/env python3
"""GQ730 exact current31 one-ModuleScript finite decorative position overlay.
Read the TRUE selected31 after GQ500. Never replace 7-role/Host/Swarm/Item.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve()
sys.path.insert(0,str(HERE.parents[1]/"quality_castle_prompt_session_20261117"))
sys.path.insert(0,str(HERE.parents[2]/"quality_gameplay/gq730_finite_house"))
from select_castle import mapping
from select_finite_house import select, BEFORE, AFTER, HELPER, FUNCTION, make_harness

RULE=("ServerScriptService","EGGRUMBLE_CastleMatchRules")
FILE="GQ730_FINITE_CASTLE_RULES.luau"
RECEIPT="GQ730_FINITE_CASTLE_RULES_RECEIPT.json"
FEATURE="GQ730_FINITE_HOUSE_DECOR_COORDINATES_20261117"

def digest(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def verify_diff(base:Path,out:Path):
    _,old=mapping(base)
    _,new=mapping(out)
    if len(old)!=31 or set(old)!=set(new) or RULE not in old:
        raise ValueError("RED_GQ730_SOURCE_SET_OR_RULES")
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if changed!=[RULE]:
        raise ValueError("RED_GQ730_ONLY_CASTLE_RULES_CHANGE")
    before=old[RULE].read_text(encoding="utf-8")
    after=new[RULE].read_text(encoding="utf-8")
    if not ("limit<=M.MAX_HERO_SLOTS" in before and "#roster<=M.MAX_HERO_SLOTS" in before):
        raise ValueError("RED_GQ730_PREVIOUS_ROSTER16_MISSING")
    if select(before)!=after:
        raise ValueError("RED_GQ730_PATCH_INTEGRITY")
    if after.replace(HELPER,"",1).replace(AFTER,BEFORE,1)!=before:
        raise ValueError("RED_GQ730_OFF_NOT_EXACT")
    if not new[RULE].name.endswith(".luau") or new[RULE].name.endswith(".server.luau"):
        raise ValueError("RED_GQ730_RULES_MUST_BE_MODULE")
    return old,new,before,after

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/FILE).exists():
        raise ValueError("RED_GQ730_OUTPUT_COLLISION")
    project,files=mapping(base)
    if RULE not in files:raise ValueError("RED_GQ730_RULE_MISSING")
    original=files[RULE].read_text(encoding="utf-8")
    patched=select(original)
    (out.parent/FILE).write_text(patched,encoding="utf-8")
    candidate=copy.deepcopy(project)
    candidate["name"]="EGGRUMBLE_V3_GQ730_FINITE_HOUSE31_SOURCE_ONLY"
    candidate["tree"][RULE[0]][RULE[1]]["$path"]=FILE
    out.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,actual,_,_=verify_diff(base,out)
    folder=out.parent
    (folder/"GQ730_CURRENT31_NATIVE.luau").write_text(make_harness(patched),encoding="utf-8")
    (folder/"GQ730_MUTANT31_NATIVE.luau").write_text(make_harness(original),encoding="utf-8")
    receipt={"feature_id":FEATURE,"source_count":31,"game_source_increase":0,
        "changed_script":RULE[-1],"other30_byte_exact":True,"off_latest_gq500_exact":True,
        "old_source_sha256":digest(original.encode()),"new_source_sha256":digest(patched.encode()),
        "role16_and_other_previous_features_retained":True,"native":"PENDING","rojo":"PENDING",
        "formal_rc_adopted":False,"studio_android_fun":"NOT_TESTED"}
    (folder/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ730_TRUE_CURRENT31_ROSTER16_AND_OTHER30_BYTE_EXACT_PASS")

def verify(base:Path,out:Path,place:Path):
    old,new,before,after=verify_diff(base.resolve(strict=True),out.resolve(strict=True))
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_GQ730_XML_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in found:
            raise ValueError("RED_GQ730_ROJO_DUPLICATE")
        found[name]=(kind,source.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={key[-1] for key in new}:
        raise ValueError("RED_GQ730_ROJO_SOURCE_SET")
    for key,file in new.items():
        kind=("Script" if file.name.endswith(".server.luau") else
              "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]]!=(kind,file.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ730_ROJO_SOURCE_CLASS_"+key[-1])
    recpath=out.parent/RECEIPT
    rec=json.loads(recpath.read_text(encoding="utf-8"))
    if rec["old_source_sha256"]!=digest(before.encode()) or rec["new_source_sha256"]!=digest(after.encode()):
        raise ValueError("RED_GQ730_SOURCE_HASH")
    rec.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
               place_sha256=digest(place.read_bytes()))
    recpath.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print("GQ730_REAL_CURRENT31_ONE_RULES_ROJO31_CLASS_SOURCE_EXACT_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.command=="prepare":prepare(a.base,a.out)
    else:
        if not a.place:p.error("verify requires --place")
        verify(a.base,a.out,a.place)
