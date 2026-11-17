#!/usr/bin/env python3
"""Select EXACT authored #524 ninja/TRAPPER warp-clearance into current RC31 Combat."""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
import xml.etree.ElementTree as ET
FEATURE="GQ524_NINJA_TRAPPER_WARP_CLEARANCE_20261117"
NAME="EGGRUMBLE_SevenRoleCombat"
AUTHOR_HEAD="f90875e14446ba86b1c668ba43efa37fbc74be20"
ORIGINAL_BLOB="66e666418b7c23d41f87faa5d61eb6e2770a463e"
FILE="GQ524_AUTHOR_SAFE_WARP_COMBAT.luau"
RECEIPT="GQ524_SAFE_WARP_RC31_RECEIPT.json"

def mapping(path):
    path=path.resolve(strict=True)
    project=json.loads(path.read_text(encoding="utf-8"))
    found={}
    def walk(node,key=()):
        for name,entry in node.items():
            if name.startswith("$"):continue
            if not isinstance(entry,dict):raise ValueError("RED_BAD_PROJECT_TREE")
            route=key+(name,)
            if "$path" in entry:
                if set(entry)!={"$path"} or route in found:raise ValueError("RED_BAD_SOURCE_MAP")
                found[route]=(path.parent/entry["$path"]).resolve(strict=True)
            else:walk(entry,route)
    walk(project["tree"])
    keys=[k for k in found if k[-1]==NAME]
    if len(found)!=31 or len({k[-1] for k in found})!=31 or len(keys)!=1 or keys[0][-2]!="ServerScriptService":
        raise ValueError("RED_NOT_ONE_COMBAT_IN_31")
    return project,found,keys[0]

def author(path):
    spec=importlib.util.spec_from_file_location("gq524_original_author_patch",path.resolve(strict=True))
    if spec is None or spec.loader is None:raise ValueError("RED_AUTHOR_IMPORT")
    P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
    raw=P.ORIGINAL.read_bytes()
    if P.EXPECTED_GIT_BLOB!=ORIGINAL_BLOB or P.git_blob_sha(raw)!=ORIGINAL_BLOB:
        raise ValueError("RED_ORIGINAL_AUTHOR_COMBAT_BLOB")
    expected=P.patch(raw).decode("utf-8")
    original=raw.decode("utf-8")
    for before,after in ((P.OLD,P.NEW),(P.OLD_NINJA,P.NEW_NINJA),(P.OLD_ESPER,P.NEW_ESPER)):
        if original.count(before)!=1 or expected.count(after)!=1:
            raise ValueError("RED_AUTHOR_PATCH_ANCHORS_CHANGED")
    return P

def patch(src,P):
    """Recognize an ALREADY integrated original #524 source and attest exact code.

    The original authored safeMove plus NINJA/TRAPPER callsites predate this
    candidate. Never repeat an already-present source change.
    """
    changes=((P.OLD,P.NEW),(P.OLD_NINJA,P.NEW_NINJA),(P.OLD_ESPER,P.NEW_ESPER))
    for i,(old,new) in enumerate(changes):
        if src.count(old)!=0 or src.count(new)!=1:
            raise ValueError(f"RED_GQ524_PARTIAL_OR_MISSING_AUTHORIGINAL_WARP idx={i} old={src.count(old)} new={src.count(new)}")
    if src.count("local function safeMove(")!=1:
        raise ValueError("RED_GQ524_DUPLICATE_MOVE_OWNER")
    if "GetPartBoundsInBox" not in src or "TacticalBattlefield" not in src:
        raise ValueError("RED_GQ524_AUTHOR_COLLISION_OR_ARENA_MISSING")
    return src

def pair(base,out,P):
    _,before,k=mapping(base)
    _,after,k2=mapping(out)
    if k!=k2 or set(before)!=set(after):raise ValueError("RED_WARP_OWNER_MAP")
    old=before[k].read_text(encoding="utf-8")
    new=after[k].read_text(encoding="utf-8")
    if patch(old,P)!=old or new!=old:raise ValueError("RED_GQ524_EXISTING_AUTHOR_SOURCE_NOOP")
    changed=[name for name in before if before[name].read_bytes()!=after[name].read_bytes()]
    if changed!=[]:raise ValueError("RED_EXISTING31_SCRIPT_WAS_CHANGED")
    return after,old,new

def prepare(base,out,author_file):
    P=author(author_file)
    project,original,key=mapping(base)
    old=original[key].read_text(encoding="utf-8")
    new=patch(old,P)
    dest=out.parent/FILE
    receipt=out.parent/RECEIPT
    if out.exists() or dest.exists() or receipt.exists() or base.parent.resolve()!=out.parent.resolve():
        raise ValueError("RED_WARP_OUTPUT_COLLISION")
    dest.write_text(new,encoding="utf-8")
    selected=copy.deepcopy(project)
    entry=selected["tree"]
    for part in key:entry=entry[part]
    entry["$path"]=FILE
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    pair(base,out,P)
    receipt.write_text(json.dumps({
        "feature_id":FEATURE,"original_pr":524,"author_head":AUTHOR_HEAD,"author_original_combat_blob":ORIGINAL_BLOB,
        "base_project":base.name,"selected_project":out.name,
        "script_count":31,"changed_script_count":0,"all31_byte_exact":True,
        "existing_author_code_already_present":True,"inverse_off_exact":True,"new_runtime_scripts":0,
        "old_sha256":hashlib.sha256(old.encode()).hexdigest(),
        "selected_sha256":hashlib.sha256(new.encode()).hexdigest(),
        "native":"PENDING","rojo":"PENDING","studio_android_owner":"NOT_TESTED"
    },sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ524_ORIGINAL_AUTHOR_3_ANCHORS_SINGLE_COMBAT_OFF_EXACT_PASS")

def verify(base,out,author_file,place):
    P=author(author_file)
    mapped,old,new=pair(base,out,P)
    actual={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_WARP_SCRIPT_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        s=props.findtext("ProtectedString[@name='Source']")
        if s is None:s=props.findtext("string[@name='Source']")
        if not name or s is None or name in actual:raise ValueError("RED_WARP_ROJO_DUPLICATE")
        actual[name]=(kind,s.replace("\r\n","\n"))
    if len(actual)!=31 or set(actual)!={k[-1] for k in mapped}:
        raise ValueError("RED_WARP_ROJO31_SCRIPT_SET")
    for k,f in mapped.items():
        kind=("Script" if f.name.endswith(".server.luau") else
              "LocalScript" if f.name.endswith(".client.luau") else "ModuleScript")
        if actual[k[-1]]!=(kind,f.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_WARP_ROJO_SOURCE_CLASS_"+k[-1])
    path=out.parent/RECEIPT
    rec=json.loads(path.read_text(encoding="utf-8"))
    if rec["old_sha256"]!=hashlib.sha256(old.encode()).hexdigest() or rec["selected_sha256"]!=hashlib.sha256(new.encode()).hexdigest():
        raise ValueError("RED_WARP_SOURCE_SHA_DRIFT")
    rec.update(native="31/31",rojo="31/31",place_sha256=hashlib.sha256(place.read_bytes()).hexdigest(),place_bytes=place.stat().st_size)
    path.write_text(json.dumps(rec,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ524_NATIVE_ROJO31_EXACT_OTHER30_OFF_PASS",rec["place_bytes"])

def mutant(source,out):
    s=source.read_text(encoding="utf-8")
    token="if part.CanCollide then return false end"
    if s.count(token)!=1 or "GetPartBoundsInBox" not in s:raise ValueError("RED_WARP_MUTANT_INPUT")
    out.write_text(s.replace(token,"if false then return false end",1),encoding="utf-8")
    print("GQ524_EXPECTED_SOLID_DESTINATION_MUTANT_CREATED")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("prepare","verify","mutant"))
    for s in ("base","out","author","place","source"):p.add_argument("--"+s,type=Path)
    a=p.parse_args()
    if a.command=="prepare":prepare(a.base,a.out,a.author)
    elif a.command=="verify":verify(a.base,a.out,a.author,a.place)
    else:mutant(a.source,a.out)
