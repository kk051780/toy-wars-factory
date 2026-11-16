#!/usr/bin/env python3
"""GQ527: select original author server-only siege pacing into ONE existing BotActors.

No new Script, ModuleScript or Game owner in canonical 31. This adapter inlines
the immutable pure original author's policy in the existing BotActors module;
the author module remains unmodified/read-only. All other30 source bytes and
OFF inverse of the one Bot source must remain bit-for-bit exact.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

TARGET = "EGGRUMBLE_BotActors"
AUTHOR_HEAD = "57c38d393aee43badd575db3ee44eacf3bd3306e"
MODULE_BLOB = "976f1eb047a275db0dedc42c394c09be4143a4e2"
MODULE_NAME = "EGGRUMBLE_BotSiegePacing.luau"
OUTPUT_NAME = "GQ527_CURRENT_SINGLE_BOT_ACTORS.luau"
RECEIPT = "GQ527_CURRENT31_SIEGE_SOURCE_EXACT_RECEIPT.json"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+bytes([0])+data).hexdigest()

def mapping(project:Path):
    project=project.resolve(strict=True)
    obj=json.loads(project.read_text(encoding="utf8"))
    files={}
    def walk(node,route=()):
        for key,value in node.items():
            if key.startswith("$"):continue
            if not isinstance(value,dict):raise ValueError("RED_BAD_PROJECT_NODE")
            path=route+(key,)
            if "$path" in value:
                if set(value)!={"$path"} or path in files:raise ValueError("RED_DUPLICATE_SOURCE")
                files[path]=(project.parent/value["$path"]).resolve(strict=True)
            else:
                walk(value,path)
    walk(obj["tree"])
    if len(files)!=31 or len({key[-1] for key in files})!=31:
        raise ValueError("RED_SOURCE_NOT31")
    targets=[key for key in files if key[-1]==TARGET]
    if len(targets)!=1:raise ValueError("RED_NOT_SINGLE_ORIGINAL_BOT")
    if any(key[-1]=="EGGRUMBLE_SiegePacing" for key in files):
        raise ValueError("RED_DUPLICATE_SIEGE_AUTHORITY")
    return obj,files,targets[0]

def author(author:Path,module:Path):
    if module.name!=MODULE_NAME or blob(module.read_bytes())!=MODULE_BLOB:
        raise ValueError("RED_ORIGINAL_SIEGE_MODULE_BLOB")
    data=module.read_text(encoding="utf8")
    if data.count("local Pace = {}")!=1 or data.count("return Pace")!=1:
        raise ValueError("RED_AUTHOR_SIEGE_MODULE_DRIFT")
    if data.count("Pace.MIN_SECONDS_PER_CASTLE = 7.0")!=1:
        raise ValueError("RED_SIEGE_LIMIT_NOT_AUTHOR_7SEC")
    spec=importlib.util.spec_from_file_location("gq527_original_author",author)
    if spec is None or spec.loader is None:raise ValueError("RED_ORIGINAL_AUTHOR_STAGE_IMPORT")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in ("OLD_REQUIRE","OLD_GATE","OLD_DAMAGE","NEW_GATE","NEW_DAMAGE"):
        if not isinstance(getattr(mod,attr,None),str):raise ValueError("RED_AUTHOR_ANCHOR_DRIFT")
    return mod,data

def transform(before:str,mod,policy:str):
    if "SiegePacing.allow(" in before or "local SiegePacing=(function()" in before:
        raise ValueError("RED_SIEGE_ALREADY_SELECTED")
    for s in (mod.OLD_REQUIRE,mod.OLD_GATE,mod.OLD_DAMAGE):
        if before.count(s)!=1:raise ValueError("RED_SIEGE_ORIGINAL_CURRENT_BOT_DRIFT")
    block="local SiegePacing=(function()\n"+policy+"\nend)()"
    after=before.replace(mod.OLD_REQUIRE,mod.OLD_REQUIRE+"\n"+block,1)
    after=after.replace(mod.OLD_GATE,mod.NEW_GATE,1)
    after=after.replace(mod.OLD_DAMAGE,mod.NEW_DAMAGE,1)
    if after.count("SiegePacing.allow(session,enemy.id,id,now)")!=1:
        raise ValueError("RED_AUTHOR_SIEGE_ALLOW_NOT_ONCE")
    if after.count("SiegePacing.cancelFailed(session,enemy.id,id,now)")!=1:
        raise ValueError("RED_AUTHOR_FAILED_DAMAGE_ROLLBACK_NOT_ONCE")
    inverted=after.replace(mod.NEW_DAMAGE,mod.OLD_DAMAGE,1)
    inverted=inverted.replace(mod.NEW_GATE,mod.OLD_GATE,1)
    if inverted.count(mod.OLD_REQUIRE+"\n"+block)!=1:raise ValueError("RED_SIEGE_INLINE_ROLLBACK_DRIFT")
    inverted=inverted.replace(mod.OLD_REQUIRE+"\n"+block,mod.OLD_REQUIRE,1)
    if inverted!=before:raise ValueError("RED_BOT_OFF_ROLLBACK_BYTE_DRIFT")
    return after

def prepare(base:Path,out:Path,original_author:Path,policy:Path):
    base,out=base.resolve(strict=True),out.resolve()
    if out.exists() or out.parent!=base.parent or base==out:raise ValueError("RED_NOT_NEW_SIBLING")
    obj,old,target=mapping(base)
    mod,pure=author(original_author,policy)
    selected=transform(old[target].read_text(encoding="utf8"),mod,pure).encode("utf8")
    dest=out.parent/OUTPUT_NAME
    if dest.exists():raise ValueError("RED_BOT_SOURCE_OUTPUT_EXISTS")
    dest.write_bytes(selected)
    latest=copy.deepcopy(obj)
    node=latest["tree"]
    for key in target:node=node[key]
    node["$path"]=OUTPUT_NAME
    out.write_text(json.dumps(latest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,new,new_target=mapping(out)
    changed=[key for key in old if old[key].read_bytes()!=new[key].read_bytes()]
    if set(old)!=set(new) or new_target!=target or changed!=[target]:
        raise ValueError("RED_NOT_ONE_ORIGINAL_BOT_CHANGE")
    receipt={
        "original_pr":527,"original_author_head":AUTHOR_HEAD,
        "original_pure_policy_git_blob":MODULE_BLOB,
        "original_pure_policy_sha256":sha(policy.read_bytes()),
        "runtime_source_count":31,"new_runtime_scripts":0,
        "one_changed_existing_script":TARGET,
        "other_30_scripts_byte_exact":True,"off_original_bot_byte_exact":True,
        "previous_bot_sha256":sha(old[target].read_bytes()),"selected_bot_sha256":sha(selected),
        "pure_author_policy_inlined_in_bot":True,
        "mode_isolation":"TEAM_BATTLE_ROYALE","per_target_siege_seconds":7,
        "rojo_source_class_exact":"NOT_TESTED",
        "official_rc_adopted":False,"engine_android_fun_owner":"NOT_TESTED"}
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ527_ORIGINAL_AUTHOR_ONE_BOT_OTHER30_EXACT_OFF_ROLLBACK_PASS")

def verify(base:Path,out:Path,place:Path,original_author:Path,policy:Path):
    _,old,target=mapping(base);_,new,new_target=mapping(out)
    mod,pure=author(original_author,policy)
    selected=transform(old[target].read_text(encoding="utf8"),mod,pure)
    if set(old)!=set(new) or new_target!=target or new[target].read_text(encoding="utf8")!=selected:
        raise ValueError("RED_SOURCE_SELECTED_BOT_MISMATCH")
    if [k for k in old if old[k].read_bytes()!=new[k].read_bytes()]!=[target]:
        raise ValueError("RED_OTHER30_SOURCE_CHANGED")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        prop=item.find("Properties")
        if prop is None:raise ValueError("RED_ROJO_MISSING_PROPERTIES")
        name=prop.findtext("string[@name='Name']")
        text=prop.findtext("ProtectedString[@name='Source']")
        if text is None:text=prop.findtext("string[@name='Source']")
        if not name or text is None or name in embedded:raise ValueError("RED_ROJO_BAD_SOURCE")
        embedded[name]=(cls,text.replace("\r\n","\n"))
    if len(embedded)!=31 or {k[-1] for k in new}!=set(embedded):
        raise ValueError("RED_ROJO_SCRIPT_COUNT_OR_NAMES")
    for key,source in new.items():
        klass=("Script" if source.name.endswith(".server.luau") else
               "LocalScript" if source.name.endswith(".client.luau") else "ModuleScript")
        if embedded[key[-1]]!=(klass,source.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_CLASS_"+key[-1])
    receipt_path=out.parent/RECEIPT
    receipt=json.loads(receipt_path.read_text())
    if not receipt["other_30_scripts_byte_exact"] or not receipt["off_original_bot_byte_exact"]:
        raise ValueError("RED_OFF_ROLLBACK_RECEIPT")
    receipt.update(rojo_source_class_exact="31/31",actual_place_bytes=place.stat().st_size,
                   actual_place_sha256=sha(place.read_bytes()))
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("GQ527_REAL_ROJO31_ONE_BOT_SOURCE_CLASS_OFF_EXACT_PASS",receipt["actual_place_bytes"])

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("prepare","verify"))
    for key in ("base","out","original-author","policy"):
        parser.add_argument("--"+key,required=True,type=Path)
    parser.add_argument("--place",type=Path)
    a=parser.parse_args()
    kwargs=dict(base=a.base,out=a.out,original_author=a.original_author,policy=a.policy)
    if a.action=="prepare":prepare(**kwargs)
    else:
        if a.place is None:parser.error("--place required")
        verify(place=a.place,**kwargs)
