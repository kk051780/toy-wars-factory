#!/usr/bin/env python3
"""Replace ONLY original #582-v2 inline code with its verified #582-v3 author revision.

Input is actual current RC31 after accepted #515 and #582-v2. The one-Combat
post-#582-v3 selected project contains exactly 31 script sources, preserves
all other 30 current-original scripts byte-exact, and has an exact OFF backout.
No new Script/Remote/damage/Store/Score/Game source; no implicit RC admission.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from select_original_zombie582 import scan, COMBAT, git_blob, digest

AUTHOR_V2_HEAD="497ff09e7d148e591691f5b1e3f5c543d6794ee8"
AUTHOR_V3_HEAD="aeb7cbed6e154849804d7d28bd53966410e50364"
COMPOSER_V2_BLOB="d9491a682e1d66ab45451ed74857faaf328b5e20"
COMPOSER_V3_BLOB="c3de12e0859f1b4c7f230cc53be2348b194a31e5"
POLICY_BLOB="6aa47b0baf7580f41e0e25f44acff91c18c56a81"
RUNTIME_BLOB="7cc135ebedd6f72a5e34955f64fca60edd53a946"
OUTPUT_SCRIPT="GQ582_NEUTRAL_ID_CURRENT_SINGLE_COMBAT.luau"
RECEIPT_FILE="GQ582_V3_NEUTRAL_ID_RC31_RECEIPT.json"

def composer(path: Path, sha: str):
    if git_blob(path.read_bytes()) != sha:
        raise ValueError("RED_AUTHOR_COMPOSER_BLOB_DRIFT")
    spec=importlib.util.spec_from_file_location("locked_zombie_"+sha[:8],path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod

def locked_source(v2:Path,v3:Path,policy:Path,runtime:Path):
    for item,expected in ((policy,POLICY_BLOB),(runtime,RUNTIME_BLOB)):
        if git_blob(item.read_bytes()) != expected:
            raise ValueError("RED_ZOMBIE_DEPENDENCY_BLOB_DRIFT_"+item.name)
    a,b=composer(v2,COMPOSER_V2_BLOB),composer(v3,COMPOSER_V3_BLOB)
    if a.OLD_ZOMBIE != b.OLD_ZOMBIE or a.HERO_ANCHOR != b.HERO_ANCHOR:
        raise ValueError("RED_ZOMBIE_BASE_SKILL_DRIFT")
    p,r=policy.read_text(),runtime.read_text()
    def get_inline(mod):
        seed=mod.HERO_ANCHOR+mod.OLD_ZOMBIE+"return HeroCombat\n"
        generated=mod.compose(seed,p,r)
        suffix=mod.NEW_ZOMBIE+"return HeroCombat\n"
        if not generated.startswith(mod.HERO_ANCHOR) or not generated.endswith(suffix):
            raise ValueError("RED_ORIGINAL_AUTHOR_INLINE_SHAPE_DRIFT")
        return generated[len(mod.HERO_ANCHOR):-len(suffix)]
    first,second=get_inline(a),get_inline(b)
    if a.NEW_ZOMBIE==b.NEW_ZOMBIE:
        raise ValueError("RED_NO_NEW_AUTHOR_DELTA")
    # The policy/runtime inline is deliberately identical across this tiny v3
    # author revision. Only the ZOMBIE branch hunk may change.
    if "local neutralIds=setmetatable" in first:
        raise ValueError("RED_OLD_ALREADY_HAS_NEUTRAL_ID")
    for must in ("local neutralIds=setmetatable({}, {__mode=\"k\"})",
                 "local function neutralTargetId(enemy:Model):string",
                 "id=neutralTargetId(enemy),kind=\"NEUTRAL\"",
                 "session.isCurrentHuman(other)==true","theirHum.Health>0"):
        if must not in b.NEW_ZOMBIE:
            raise ValueError("RED_NEUTRAL_ID_AUTHOR_GUARD_MISSING_"+must)
    if 'id="N:"..tostring(enemy)' in b.NEW_ZOMBIE:
        raise ValueError("RED_DUPLICATE_NEUTRAL_NAME_NOT_FIXED")
    return a,b,first,second

def source_upgrade(current:str,a,b,old_inline:str,new_inline:str) -> str:
    if (current.count(old_inline)!=1 or current.count(a.NEW_ZOMBIE)!=1
        or current.count(b.NEW_ZOMBIE)!=0
        or (old_inline!=new_inline and current.count(new_inline)!=0)):
        raise ValueError("RED_CURRENT_RC_COMBAT_NOT_SOURCE_LOCKED_V2")
    selected=current.replace(old_inline,new_inline,1).replace(a.NEW_ZOMBIE,b.NEW_ZOMBIE,1)
    if selected.count(new_inline)!=1 or selected.count(b.NEW_ZOMBIE)!=1:
        raise ValueError("RED_ONE_ZOMBIE_V3_AUTHORITY")
    if selected.replace(new_inline,old_inline,1).replace(b.NEW_ZOMBIE,a.NEW_ZOMBIE,1)!=current:
        raise ValueError("RED_OFF_ROLLBACK_COMBAT_NOT_EXACT")
    return selected

def project_delta(base:Path,out:Path,v2:Path,v3:Path,policy:Path,runtime:Path):
    if out.exists() or out.parent.resolve()!=base.parent.resolve():
        raise ValueError("RED_OUTPUT_PATH_MUST_BE_NEW_SIBLING")
    obj,old=scan(base)
    a,b,f,g=locked_source(v2,v3,policy,runtime)
    src_before=old[COMBAT].read_bytes()
    src_after=source_upgrade(src_before.decode("utf8"),a,b,f,g).encode("utf8")
    path=out.parent/OUTPUT_SCRIPT
    if path.exists(): raise ValueError("RED_SELECTED_COMBAT_FILE_ALREADY_EXISTS")
    path.write_bytes(src_after)
    project=copy.deepcopy(obj)
    project["tree"][COMBAT[0]][COMBAT[1]]["$path"]=OUTPUT_SCRIPT
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,selected=scan(out)
    if set(selected)!=set(old): raise ValueError("RED_31_ROJO_LAYOUT_CHANGED")
    if sum(selected[k].read_bytes()!=old[k].read_bytes() for k in old)!=1:
        raise ValueError("RED_MORE_THAN_ONE_COMBAT_CHANGED")
    if any(selected[k].read_bytes()!=old[k].read_bytes() for k in old if k!=COMBAT):
        raise ValueError("RED_OTHER30_OLD_SOURCES_CHANGED")
    receipt={
        "author_v2":AUTHOR_V2_HEAD,"author_v3":AUTHOR_V3_HEAD,
        "source_count":31,"one_existing_combat_changed":True,
        "other30_script_bytes_identical":True,
        "off_rollback_old_combat_byte_exact":True,
        "preupgrade_combat_sha256":digest(src_before),
        "upgraded_combat_sha256":digest(src_after),
        "source_rojo_exact":"NOT_RUN",
        "private_premerge_only":True,
        "formal_rc_adopted":False,"studio_tested":False,"android_tested":False
    }
    (out.parent/RECEIPT_FILE).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ582_V3_NATIVE_SOURCE_ONE_COMBAT_30_OTHER_BYTES_AND_OFF_EXACT_PASS")

def verify(base:Path,out:Path,place:Path,v2:Path,v3:Path,policy:Path,runtime:Path):
    _,old=scan(base)
    _,new=scan(out)
    a,b,f,g=locked_source(v2,v3,policy,runtime)
    expected=source_upgrade(old[COMBAT].read_text(),a,b,f,g)
    if set(old)!=set(new) or new[COMBAT].read_text()!=expected:
        raise ValueError("RED_ONE_COMBAT_SOURCE_NOT_SELECTED")
    if sum(old[k].read_bytes()!=new[k].read_bytes() for k in old)!=1:
        raise ValueError("RED_OTHER30_SOURCE_MUTATION")
    actual={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"): continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_NO_PROPS")
        name=props.findtext("string[@name='Name']")
        text=props.findtext("ProtectedString[@name='Source']")
        if text is None:text=props.findtext("string[@name='Source']")
        if not name or text is None or name in actual:raise ValueError("RED_BAD_XML_SCRIPT")
        actual[name]=(cls,text.replace("\r\n","\n"))
    if len(actual)!=31 or {k[-1] for k in new}!=set(actual):
        raise ValueError("RED_31_SCRIPT_NAMES_OR_COUNT")
    for route,path in new.items():
        cls=("Script" if path.name.endswith(".server.luau") else
             "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if actual[route[-1]]!=(cls,path.read_text().replace("\r\n","\n")):
            raise ValueError("RED_TRUE_ROJO_SCRIPT_CLASS_OR_BYTES_"+route[-1])
    receipt=json.loads((out.parent/RECEIPT_FILE).read_text())
    if (receipt["preupgrade_combat_sha256"]!=digest(old[COMBAT].read_bytes())
        or receipt["upgraded_combat_sha256"]!=digest(new[COMBAT].read_bytes())):
        raise ValueError("RED_RECEIPT_COMBAT_HASH_DRIFT")
    receipt.update({"source_rojo_exact":"31/31",
       "place_sha256":digest(place.read_bytes()),"place_size_bytes":place.stat().st_size,
       "all_other30_source_bytes_verified":True,"private_premerge_only":True})
    (out.parent/RECEIPT_FILE).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ582_V3_CURRENT_RC31_NATIVE_ROJO31_CLASS_SOURCE_EXACT_PASS",receipt["place_size_bytes"])

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=["prepare","verify"])
    for name in ("base","out","v2","v3","policy","runtime"):
        ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--place",type=Path)
    args=ap.parse_args()
    if args.action=="prepare":project_delta(args.base,args.out,args.v2,args.v3,args.policy,args.runtime)
    else:
        if args.place is None:ap.error("verify requires --place")
        verify(args.base,args.out,args.place,args.v2,args.v3,args.policy,args.runtime)
