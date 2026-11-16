#!/usr/bin/env python3
"""GQ582 original-author v3 -> v4 policy-only Combat source-select, 31 original sources.

No new Game/Combat/Remote/Store/Score. Real native Luau and Rojo31 validation
are required before the sole authenticated #220 expected-SHA nonforce CAS.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from select_original_zombie582 import COMBAT, scan, git_blob, digest

BASE_AUTHOR_HEAD = "aeb7cbed6e154849804d7d28bd53966410e50364"
GUARD_AUTHOR_HEAD = "5769b80ed21f5592adcca1936d2d3d04934f0089"
COMPOSER_BLOB = "c3de12e0859f1b4c7f230cc53be2348b194a31e5"
OLD_POLICY_BLOB = "6aa47b0baf7580f41e0e25f44acff91c18c56a81"
GUARD_POLICY_BLOB = "519feb38879633825fda314637c3814a4d983d05"
RUNTIME_BLOB = "7cc135ebedd6f72a5e34955f64fca60edd53a946"
OUTPUT_COMBAT = "GQ582_V4_GUARD_CURRENT_SINGLE_COMBAT.luau"
RECEIPT = "GQ582_V4_GUARD_RC31_SOURCE_EXACT_RECEIPT.json"

def only_one_composer(path:Path):
    if git_blob(path.read_bytes())!=COMPOSER_BLOB:
        raise ValueError("RED_AUTHOR_COMPOSER_BLOB_MISMATCH")
    spec=importlib.util.spec_from_file_location("gq582_guard_composer",path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

def locked_inline(composer:Path,old_policy:Path,new_policy:Path,runtime:Path):
    for path,sha in ((old_policy,OLD_POLICY_BLOB),(new_policy,GUARD_POLICY_BLOB),
                     (runtime,RUNTIME_BLOB)):
        if git_blob(path.read_bytes())!=sha:
            raise ValueError("RED_AUTHOR_BLOB_MISMATCH_"+path.name)
    mod=only_one_composer(composer)
    old=old_policy.read_text(encoding="utf8")
    new=new_policy.read_text(encoding="utf8")
    if "local GUARD_LEASH = 12" in old:
        raise ValueError("RED_BASE_ALREADY_LEASHED")
    for required in ("local GUARD_LEASH = 12", "distance(unit, guardAnchor) > GUARD_LEASH",
                     "distance(candidate, guardAnchor) <= GUARD_LEASH",
                     "Policy.GUARD_LEASH_STUDS = GUARD_LEASH"):
        if new.count(required)!=1:
            raise ValueError("RED_AUTHOR_GUARD_POLICY_DRIFT_"+required)
    runtime_src=runtime.read_text(encoding="utf8")
    suffix=mod.NEW_ZOMBIE+"return HeroCombat\n"
    seed=mod.HERO_ANCHOR+mod.OLD_ZOMBIE+"return HeroCombat\n"
    def inline(policy:str):
        generated=mod.compose(seed,policy,runtime_src)
        if not generated.startswith(mod.HERO_ANCHOR) or not generated.endswith(suffix):
            raise ValueError("RED_ORIGINAL_AUTHOR_INLINE_OR_ROLE_DRIFT")
        return generated[len(mod.HERO_ANCHOR):-len(suffix)]
    old_inline,new_inline=inline(old),inline(new)
    if old_inline==new_inline or old_inline.count("local ZombieCommander=")!=1:
        raise ValueError("RED_POLICY_UNCHANGED_OR_AUTHORITY_DUPLICATE")
    if new_inline.count("local ZombieCommander=")!=1:
        raise ValueError("RED_NEW_POLICY_DUPLICATED_AUTHORITY")
    return mod,old_inline,new_inline

def upgrade(old_combat:str,mod,old_inline:str,new_inline:str):
    if old_combat.count(old_inline)!=1 or old_combat.count(mod.NEW_ZOMBIE)!=1:
        raise ValueError("RED_CURRENT_COMBAT_NOT_ORIGINAL_V3_ONE_AUTHORITY")
    if new_inline in old_combat:
        raise ValueError("RED_GUARD_ALREADY_SELECTED")
    result=old_combat.replace(old_inline,new_inline,1)
    if (result.count(new_inline)!=1 or result.count(mod.NEW_ZOMBIE)!=1
        or result.replace(new_inline,old_inline,1)!=old_combat):
        raise ValueError("RED_GUARD_OFF_NOT_BYTE_EXACT")
    return result

def prepare(base:Path,out:Path,composer:Path,old_policy:Path,new_policy:Path,runtime:Path):
    if out.exists() or out.parent.resolve()!=base.parent.resolve():
        raise ValueError("RED_CANDIDATE_OUTPUT_EXISTING_OR_NOT_SIBLING")
    obj,existing=scan(base)
    mod,old_inline,new_inline=locked_inline(composer,old_policy,new_policy,runtime)
    before=existing[COMBAT].read_bytes()
    after=upgrade(before.decode("utf8"),mod,old_inline,new_inline).encode("utf8")
    source=out.parent/OUTPUT_COMBAT
    if source.exists():raise ValueError("RED_OUTPUT_SINGLE_COMBAT_EXISTS")
    source.write_bytes(after)
    selected=copy.deepcopy(obj)
    selected["tree"][COMBAT[0]][COMBAT[1]]["$path"]=OUTPUT_COMBAT
    out.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,latest=scan(out)
    if set(existing)!=set(latest) or len(existing)!=31:
        raise ValueError("RED_EXISTING31_LAYOUT_CHANGED")
    if sum(existing[k].read_bytes()!=latest[k].read_bytes() for k in existing)!=1:
        raise ValueError("RED_NOT_EXACT_ONE_SCRIPT_DELTA")
    if any(existing[k].read_bytes()!=latest[k].read_bytes() for k in existing if k!=COMBAT):
        raise ValueError("RED_OTHER30_SOURCE_BYTES_CHANGED")
    record={
        "kind":"GQ582_GUARD_V4_ONE_EXISTING_COMBAT_SOURCE_SELECT",
        "original_author_base_head":BASE_AUTHOR_HEAD,
        "original_author_guard_head":GUARD_AUTHOR_HEAD,
        "policy_old_blob":OLD_POLICY_BLOB,
        "policy_guard_blob":GUARD_POLICY_BLOB,
        "single_game_and_combat_authority":True,
        "previous_source_count":31,"new_source_count":31,
        "only_changed_source":"/".join(COMBAT),
        "other_30_original_scripts_byte_exact":True,
        "off_reselect_old_combat_byte_exact":True,
        "previous_combat_sha256":digest(before),
        "guard_combat_sha256":digest(after),
        "true_rojo_source_class_exact":"NOT_RUN",
        "official_rc_adopted":False,"studio_tested":False,"android_tested":False,
        "product_accepted":False
    }
    (out.parent/RECEIPT).write_text(json.dumps(record,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ582_GUARD_SINGLE_COMBAT_OTHER30_EXACT_AND_OFF_PASS")

def verify(base:Path,out:Path,place:Path,composer:Path,old_policy:Path,new_policy:Path,runtime:Path):
    _,existing=scan(base);_,latest=scan(out)
    mod,old_inline,new_inline=locked_inline(composer,old_policy,new_policy,runtime)
    after=upgrade(existing[COMBAT].read_text(encoding="utf8"),mod,old_inline,new_inline)
    if set(existing)!=set(latest) or latest[COMBAT].read_text(encoding="utf8")!=after:
        raise ValueError("RED_SELECTED_COMBAT_MISMATCH")
    if sum(existing[k].read_bytes()!=latest[k].read_bytes() for k in existing)!=1:
        raise ValueError("RED_WRONG_DELTA_COUNT")
    seen={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("ModuleScript","Script","LocalScript"):continue
        prop=item.find("Properties")
        if prop is None:raise ValueError("RED_NO_PROPS")
        name=prop.findtext("string[@name='Name']")
        source=prop.findtext("ProtectedString[@name='Source']")
        if source is None:source=prop.findtext("string[@name='Source']")
        if not name or source is None or name in seen:raise ValueError("RED_BAD_ROJO_SCRIPT")
        seen[name]=(cls,source.replace("\r\n","\n"))
    if len(seen)!=31 or {k[-1] for k in latest}!=set(seen):
        raise ValueError("RED_ROJO31_NAMES_OR_COUNT")
    for route,source in latest.items():
        kind=("Script" if source.name.endswith(".server.luau") else
              "LocalScript" if source.name.endswith(".client.luau") else "ModuleScript")
        if seen[route[-1]]!=(kind,source.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_CLASS_OR_SOURCE_"+route[-1])
    receipt=json.loads((out.parent/RECEIPT).read_text(encoding="utf8"))
    if (receipt["previous_combat_sha256"]!=digest(existing[COMBAT].read_bytes())
       or receipt["guard_combat_sha256"]!=digest(latest[COMBAT].read_bytes())):
        raise ValueError("RED_COMBAT_SHA_DRIFT")
    receipt.update({
        "true_rojo_source_class_exact":"31/31",
        "real_rojo_place_sha256":digest(place.read_bytes()),
        "real_rojo_place_size_bytes":place.stat().st_size,
        "other_30_script_bytes_verified":True,
        "off_rollback_verified":True,
        "official_rc_adopted":False
    })
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ582_GUARD_TRUE_ROJO31_SCRIPT_SOURCE_CLASS_EXACT_PASS",place.stat().st_size)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=("prepare","verify"))
    for name in ("base","out","composer","old-policy","new-policy","runtime"):
        ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--place",type=Path)
    args=ap.parse_args()
    kw=dict(base=args.base,out=args.out,composer=args.composer,old_policy=args.old_policy,
            new_policy=args.new_policy,runtime=args.runtime)
    if args.action=="prepare":prepare(**kw)
    else:
        if args.place is None:ap.error("--place required")
        verify(place=args.place,**kw)
