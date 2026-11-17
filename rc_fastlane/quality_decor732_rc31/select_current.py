#!/usr/bin/env python3
"""GQ732 final selected31 source overlay: one original CastleRules ModuleScript."""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"rc_fastlane/quality_castle_prompt_session_20261117"))
sys.path.insert(0,str(ROOT/"quality_gameplay/gq732_duplicate_house"))
from select_castle import mapping
from select_duplicate_house import select,off,native
RULE=("ServerScriptService","EGGRUMBLE_CastleMatchRules")
NAME="GQ732_CASTLE_RULES_DECOR.luau"
RECEIPT="GQ732_DECOR_DUPLICATE_RC31_RECEIPT.json"
FEATURE="GQ732_CASTLE_DUPLICATE_DECOR_SLOT_20261117"
def sha(b:bytes):return hashlib.sha256(b).hexdigest()

def diff(base:Path,selected:Path):
    _,before=mapping(base);_,after=mapping(selected)
    if len(before)!=31 or set(before)!=set(after) or RULE not in before:
        raise ValueError("RED_GQ732_CURRENT31_SET")
    changed=[key for key in before if before[key].read_bytes()!=after[key].read_bytes()]
    if changed!=[RULE]:
        raise ValueError("RED_GQ732_SINGLE_RULES_OWNER")
    a=before[RULE].read_text(encoding="utf-8")
    b=after[RULE].read_text(encoding="utf-8")
    if "limit<=M.MAX_HERO_SLOTS" not in a or "#roster<=M.MAX_HERO_SLOTS" not in a:
        raise ValueError("RED_GQ732_PREVIOUS_16_ROSTER_MISSING")
    if select(a)!=b or off(b)!=a:
        raise ValueError("RED_GQ732_INVERSE_SOURCE")
    return after,a,b

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/NAME).exists():
        raise ValueError("RED_GQ732_OUTPUT_COLLISION")
    obj,files=mapping(base)
    original=files[RULE].read_text(encoding="utf-8")
    patched=select(original)
    (out.parent/NAME).write_text(patched,encoding="utf-8")
    doc=copy.deepcopy(obj)
    doc["name"]="EGGRUMBLE_V3_GQ732_DUPLICATE_DECOR_31"
    doc["tree"][RULE[0]][RULE[1]]["$path"]=NAME
    out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    files2,a,b=diff(base,out)
    (out.parent/"GQ732_CURRENT31_NATIVE.luau").write_text(native(b),encoding="utf-8")
    (out.parent/"GQ732_MUTANT_NATIVE.luau").write_text(native(a),encoding="utf-8")
    rec={"feature_id":FEATURE,"source_count":31,"original_source_count":31,
       "new_runtime_scripts":0,"changed_script":RULE[-1],"other30_byte_exact":True,
       "off_returns_previous_rc_exact":True,"old_rules_sha256":sha(a.encode()),
       "new_rules_sha256":sha(b.encode()),"source_class":"ModuleScript",
       "native":"PENDING","rojo":"PENDING","studio_android_fun":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n")
    print("GQ732_CURRENT31_ONE_DECOR_MODULE_OTHER30_BYTE_EXACT_OFF_PASS")

def verify(base:Path,out:Path,place:Path):
    files,a,b=diff(base.resolve(strict=True),out.resolve(strict=True))
    found={}
    for node in ET.parse(place).getroot().iter("Item"):
        kind=node.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=node.find("Properties")
        if props is None:raise ValueError("RED_GQ732_XML_NO_PROPS")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:src=props.findtext("string[@name='Source']")
        if not name or src is None or name in found:
            raise ValueError("RED_GQ732_DUPLICATE_SCRIPT")
        found[name]=(kind,src.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={path[-1] for path in files}:
        raise ValueError("RED_GQ732_BAD_ROJO_SCRIPT_SET")
    for key,path in files.items():
        kind=("Script" if path.name.endswith(".server.luau") else
              "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]]!=(kind,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ732_CLASS_OR_SOURCE_"+key[-1])
    recpath=out.parent/RECEIPT
    rec=json.loads(recpath.read_text(encoding="utf-8"))
    if rec["old_rules_sha256"]!=sha(a.encode()) or rec["new_rules_sha256"]!=sha(b.encode()):
        raise ValueError("RED_GQ732_ORIGINAL_SHA")
    rec.update(native="31/31",rojo="31/31",place_bytes=place.stat().st_size,
               place_sha256=sha(place.read_bytes()))
    recpath.write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n")
    print("GQ732_CURRENT31_REAL_ROJO31_CLASS_SOURCE_EXACT_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--place",type=Path)
    args=p.parse_args()
    if args.command=="prepare":prepare(args.base,args.out)
    else:
        if not args.place:p.error("verify requires --place")
        verify(args.base,args.out,args.place)
