#!/usr/bin/env python3
"""Compose GQ580 onto an actual current EGGRUMBLE V3 RC31 Rojo project.

Pure private QA: never writes authoritative RC. Retains exactly the original 30
other scripts and the existing selected BotActors except one reversible guard.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

BOT=("ServerScriptService","EGGRUMBLE_BotActors")
COUNT=31
ALLOWED={"ModuleScript","Script","LocalScript"}
APPROVED_TARGETING=b"nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)"

def mapping(path:Path):
    original=Path("rc_fastlane/select_gq541_original_neutral_fallback.py")
    m=importlib.machinery.SourceFileLoader("gq580_existing_rc_mapper",str(original.resolve(strict=True))).load_module()
    return m.flatten(path)

def source_patch():
    source=Path("_gq580_candidate/quality_gameplay/v3_ai_takeover_terminal_20261116/patch_takeover.py")
    return importlib.machinery.SourceFileLoader("gq580_original_guard",str(source.resolve(strict=True))).load_module()

def sha(raw:bytes):
    return hashlib.sha256(raw).hexdigest()

def verify_selected(base:Path, out:Path):
    _,initial=mapping(base)
    _,chosen=mapping(out)
    if len(initial)!=COUNT or len(chosen)!=COUNT or set(initial)!=set(chosen) or BOT not in initial:
        raise ValueError("RED RC31 project count/script paths mismatch")
    source=initial[BOT].read_bytes()
    target=chosen[BOT].read_bytes()
    if APPROVED_TARGETING not in source or source.count(APPROVED_TARGETING)!=1:
        raise ValueError("RED missing/duplicated #555 nearest-human selected AI")
    orig=source.decode("utf-8")
    new=source_patch().patch(orig).encode("utf-8")
    if target!=new or target==source:
        raise ValueError("RED selected AI not single original guard")
    for key in initial:
        if key!=BOT and initial[key].read_bytes()!=chosen[key].read_bytes():
            raise ValueError("RED changed other script "+"/".join(key))
    return initial,chosen,source,target

def compose(base:Path,out:Path):
    base=base.resolve(strict=True)
    out=out.resolve()
    if base==out or base.parent!=out.parent or out.exists():
        raise ValueError("RED require new sibling project path")
    old,initial=mapping(base)
    if len(initial)!=COUNT or BOT not in initial:
        raise ValueError("RED wrong original RC31 source manifest")
    before=initial[BOT].read_text(encoding="utf-8")
    if before.count(" session.takeover=function(id:string):boolean")!=1:
        raise ValueError("RED missing singleton takeover")
    if before.count(APPROVED_TARGETING.decode())!=1:
        raise ValueError("RED missing #555 nearest-target original code")
    after=source_patch().patch(before)
    new_bot=out.parent/"GQ580_ORIGINAL_BOT_ACTORS_SELECTED.luau"
    if new_bot.exists():
        raise ValueError("RED refusing overwrite of prior selected actor")
    new_bot.write_text(after,encoding="utf-8")
    changed=copy.deepcopy(old)
    changed["name"]="EGGRUMBLE_V3_GQ580_PRIVATE31_NONPUBLISH"
    changed["tree"]["ServerScriptService"]["EGGRUMBLE_BotActors"]["$path"]=new_bot.name
    out.write_text(json.dumps(changed,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    previous,selected,src,dst=verify_selected(base,out)
    data={"status":"PREMERGE_GQ580_PRIVATE31_NOT_OFFICIAL",
          "source_count":COUNT,"only_changed_runtime_script":"/".join(BOT),
          "others_byte_exact":30,"rollback_bot_exact":True,
          "original_gq555_selected":True,"original_before_sha256":sha(src),
          "selected_after_sha256":sha(dst),
          "original_bot_ref":"#484 + #531 + #555",
          "original_7role_castle_field_battle_neutral_item_lobby_score_preserved":True,
          "studio_android_fun_owner":"NOT_TESTED"}
    (out.parent/"GQ580_PRIVATE31_RECEIPT.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ580_PRIVATE31_SINGLE_BOT_30_PRESERVED_OFF_ROLLBACK_PASS")

def verify(base:Path,out:Path,place:Path):
    initial,selected,src,dst=verify_selected(base,out)
    scripts={}
    for e in ET.parse(place).iter("Item"):
        class_name=e.get("class")
        if class_name not in ALLOWED:
            continue
        props=e.find("Properties")
        if props is None:raise ValueError("RED no script props")
        name=props.findtext("string[@name='Name']")
        content=props.findtext("ProtectedString[@name='Source']")
        if content is None: content=props.findtext("string[@name='Source']")
        if not name or content is None or name in scripts:
            raise ValueError("RED duplicate or missing actual script Source")
        scripts[name]=(class_name,content.replace("\r\n","\n"))
    if len(scripts)!=COUNT or set(scripts)!={k[-1] for k in selected}:
        raise ValueError("RED actual Rojo script count mismatch")
    for key,path in selected.items():
        name=key[-1]
        cl="Script" if path.name.endswith(".server.luau") else ("LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if scripts[name]!=(cl,path.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED source/class changed in actual Rojo for "+name)
    data_path=out.parent/"GQ580_PRIVATE31_RECEIPT.json"
    data=json.loads(data_path.read_text(encoding="utf-8"))
    data.update({"native_compiled_scripts":COUNT,"real_rojo_exact":"31/31",
                 "place_bytes":place.stat().st_size,"place_sha256":sha(place.read_bytes()),
                 "formal_rc_adopted":False})
    data_path.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("GQ580_ACTUAL_LUAU31_AND_ROJO31_SOURCE_CLASS_EXACT",data["place_bytes"],data["place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=("compose","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.mode=="compose": compose(a.base,a.out)
    else:
        if a.place is None: p.error("verify requires --place")
        verify(a.base,a.out,a.place)
