#!/usr/bin/env python3
"""GQ8 2026-11-18: bounded field-egg token creation in the existing 31-source Rules.

The stock game uses 24 starting eggs. Reject a malformed internal count before
allocating a proportional token table; preserve zero, 24, the full castle rules,
all other thirty game scripts, and exact feature-only rollback.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"rc_fastlane/quality_castle_prompt_session_20261117"))
from select_castle import mapping

RULE=("ServerScriptService","EGGRUMBLE_CastleMatchRules")
FEATURE="GQ8_FIELD_EGG_CREATION_LIMIT_20261118"
NAME="GQ8_FIELD_EGG_BUDGET_RULES.luau"
RECEIPT="GQ8_FIELD_EGG_BUDGET_RC31_RECEIPT.json"
CONST='M.DEFAULT_FIELD_EGGS=24\n'
CONST_ON='M.DEFAULT_FIELD_EGGS=24\nM.MAX_FIELD_EGGS=512 -- internal allocation bound, >21x ordinary 24-egg game\n'
BEFORE=' assert(type(m.fieldEggs)=="number" and m.fieldEggs>=0 and m.fieldEggs%1==0,"invalid egg count")'
AFTER=' assert(type(m.fieldEggs)=="number" and m.fieldEggs>=0 and m.fieldEggs%1==0 and m.fieldEggs<=M.MAX_FIELD_EGGS,"invalid egg count")'

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def patch(src:str)->str:
    if src.count(CONST)!=1 or src.count(BEFORE)!=1 or CONST_ON in src or AFTER in src:
        raise ValueError("RED_GQ8_EGG_BUDGET_ANCHOR_OR_DUPLICATE")
    result=src.replace(CONST, CONST_ON, 1).replace(BEFORE, AFTER, 1)
    if unpatch(result)!=src:
        raise ValueError("RED_GQ8_EGG_BUDGET_NON_INVERSE")
    return result

def unpatch(src:str)->str:
    if src.count(CONST_ON)!=1 or src.count(AFTER)!=1:
        raise ValueError("RED_GQ8_EGG_BUDGET_SELECTED_ANCHOR")
    return src.replace(AFTER,BEFORE,1).replace(CONST_ON,CONST,1)

CASES=r"""
local roster=M.makeRoster("TEAM",{10001,10002},2)
local function startEggs(n:number)
 return M.new("TEAM",roster,n)
end
local function mustReject(tag:string,n:number)
 local ok=pcall(function() startEggs(n) end)
 assert(not ok,"GQ8_FIELD_EGG_UNBOUNDED_ACCEPTED_"..tag)
end
local empty=startEggs(0)
assert(empty.fieldEggs==0 and empty.initialFieldEggs==0)
assert(M.auditEggConservation(empty).valid,"zero egg conservation")
local ordinary=startEggs(24)
assert(ordinary.fieldEggs==24 and M.auditEggConservation(ordinary).valid)
local limit=startEggs(512)
assert(limit.fieldEggs==512 and M.auditEggConservation(limit).valid)
mustReject("OVER_LIMIT_513",513)
mustReject("HUGE_1000000",1000000)
mustReject("NEGATIVE",-1)
mustReject("FRACTION",1.5)
assert(M.MAX_HERO_SLOTS==16 and #roster==2,"current16 roster boundary changed")
print("GQ8_FIELD_EGG_BUDGET_REAL_CASTLE_RULES_NATIVE_PASS")
"""
def native(src:str)->str:
    value=src.rstrip()
    if not value.endswith("\nreturn M") or value.count("\nreturn M")!=1:
        raise ValueError("RED_GQ8_EGG_BUDGET_NATIVE_TAIL")
    return value[:-len("return M")]+CASES

def diff(base:Path,out:Path):
    _,old=mapping(base)
    _,new=mapping(out)
    if len(old)!=31 or set(old)!=set(new) or RULE not in old:
        raise ValueError("RED_GQ8_FIELD_EGG_SOURCE_SET")
    changed=[k for k in old if old[k].read_bytes()!=new[k].read_bytes()]
    if changed!=[RULE]:
        raise ValueError("RED_GQ8_FIELD_EGG_OWNER_NOT_SINGLE_RULES")
    a=old[RULE].read_text(encoding="utf-8")
    b=new[RULE].read_text(encoding="utf-8")
    if '"duplicate decoration in this plot"' not in a or "M.MAX_HERO_SLOTS" not in a:
        raise ValueError("RED_GQ8_FIELD_EGG_MISSING_GQ732_OR_16CAP")
    if patch(a)!=b or unpatch(b)!=a:
        raise ValueError("RED_GQ8_FIELD_EGG_OFF_NOT_EXACT")
    return new,a,b

def prepare(base:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/NAME).exists():
        raise ValueError("RED_GQ8_FIELD_EGG_OUTPUT_COLLISION")
    doc,old=mapping(base)
    a=old[RULE].read_text(encoding="utf-8")
    b=patch(a)
    (out.parent/NAME).write_text(b,encoding="utf-8")
    updated=copy.deepcopy(doc)
    updated["name"]="EGGRUMBLE_V3_GQ8_FIELD_EGG_BUDGET_31"
    updated["tree"][RULE[0]][RULE[1]]["$path"]=NAME
    out.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    diff(base,out)
    (out.parent/"GQ8_FIELD_EGG_GOOD_NATIVE.luau").write_text(native(b),encoding="utf-8")
    (out.parent/"GQ8_FIELD_EGG_OLD_MUTANT_NATIVE.luau").write_text(native(a),encoding="utf-8")
    receipt={"feature_id":FEATURE,"source_count":31,"changed_script":RULE[-1],
      "old_sha256":sha(a.encode()),"new_sha256":sha(b.encode()),
      "other30_byte_exact":True,"rollback_exact":True,"existing_game_or_remote_created":0,
      "ordinary_field_eggs":24,"accepted_max_field_eggs":512,
      "native":"PENDING","rojo":"PENDING","studio_android_fun":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ8_FIELD_EGG_BUDGET_SINGLE_RULES_OTHER30_EXACT_OFF_PASS")

def verify(base:Path,out:Path,place:Path):
    files,a,b=diff(base.resolve(strict=True),out.resolve(strict=True))
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):
            continue
        props=item.find("Properties")
        if props is None:
            raise ValueError("RED_GQ8_EGG_XML_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        src=props.findtext("ProtectedString[@name='Source']")
        if src is None:
            src=props.findtext("string[@name='Source']")
        if not name or src is None or name in found:
            raise ValueError("RED_GQ8_EGG_DUPLICATE_SCRIPT")
        found[name]=(cls,src.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={route[-1] for route in files}:
        raise ValueError("RED_GQ8_EGG_ROJO_SOURCE_SET")
    for route,path in files.items():
        cls=("Script" if path.name.endswith(".server.luau") else
          "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_GQ8_EGG_ROJO_SOURCE_CLASS_"+route[-1])
    receipt_path=out.parent/RECEIPT
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["old_sha256"]!=sha(a.encode()) or receipt["new_sha256"]!=sha(b.encode()):
        raise ValueError("RED_GQ8_EGG_SHA_RECEIPT")
    receipt.update(native="31/31",rojo="31/31",
       place_sha256=sha(place.read_bytes()),place_bytes=place.stat().st_size)
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ8_FIELD_EGG_BUDGET_NATIVE31_REAL_ROJO31_SOURCE_CLASS_PASS")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("prepare","verify"))
    ap.add_argument("--base",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--place",type=Path)
    args=ap.parse_args()
    if args.action=="prepare":
        prepare(args.base,args.out)
    else:
        if not args.place:
            ap.error("verify requires --place")
        verify(args.base,args.out,args.place)
