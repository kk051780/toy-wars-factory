#!/usr/bin/env python3
"""GQ8 castle 3-prompt membership fence on one canonical V3 31-Source Host.

Existing egg deposit GQ586 and all server Rules/egg authority remain unchanged.
A stale human or stale round may not siege, decorate or steal through a prompt.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
FEATURE="GQ8_CASTLE_PROMPT_CURRENT_MATCH_20261117"
PAIR=(
 ('  if joined[p.UserId]~=session.mode or not session.rules then return end',
  '  if joined[p.UserId]~=session.mode or sessions[session.mode]~=session\n'
  '   or not session.rules or type(session.isCurrentHuman)~="function"\n'
  '   or session.isCurrentHuman(p)~=true then return end'),
 ('  if not session.rules or tostring(p.UserId)~=entry.id then return end',
  '  if not session.rules or tostring(p.UserId)~=entry.id\n'
  '   or sessions[session.mode]~=session or type(session.isCurrentHuman)~="function"\n'
  '   or session.isCurrentHuman(p)~=true then return end'),
 ('  if not session.rules or joined[p.UserId]~=session.mode then return end',
  '  if not session.rules or joined[p.UserId]~=session.mode\n'
  '   or sessions[session.mode]~=session or type(session.isCurrentHuman)~="function"\n'
  '   or session.isCurrentHuman(p)~=true then return end')
)
FILE="GQ8_CASTLE_PROMPT_SESSION_HOST.server.luau"
RECEIPT="GQ8_CASTLE_PROMPT_SESSION_RECEIPT.json"

def sha(data): return hashlib.sha256(data).hexdigest()

def mapping(project):
    tree=json.loads(project.read_text(encoding="utf-8"))
    files={}
    def walk(node,p=()):
        for name,value in node.items():
            if name.startswith("$"):continue
            if not isinstance(value,dict):raise ValueError("RED_SCRIPT_MAPPING")
            route=p+(name,)
            if "$path" in value:
                if set(value)!={"$path"} or route in files:raise ValueError("RED_DUPLICATE_SCRIPT")
                files[route]=(project.parent/value["$path"]).resolve(strict=True)
            else:walk(value,route)
    walk(tree["tree"])
    if len(files)!=31 or len({p[-1] for p in files})!=31 or HOST not in files:
        raise ValueError("RED_SINGLE_HOST_31_REQUIRED")
    return tree,files

def patch(before):
    if "GQ_DEPOSIT_CURRENT_MATCH_586" not in before:
        raise ValueError("RED_ORIGINAL_DEPOSIT_586_MISSING")
    if before.count("session.isCurrentHuman=function(player:Player):boolean")!=1:
        raise ValueError("RED_ORIGINAL_HOST_MEMBERSHIP_AUTHORITY")
    for a,b in PAIR:
        if before.count(a)!=1 or b in before:
            raise ValueError("RED_CASTLE_PROMPT_ORIGINAL_ANCHOR_DRIFT")
    changed=before
    for a,b in PAIR: changed=changed.replace(a,b,1)
    if unpatch(changed)!=before:raise ValueError("RED_NOT_REVERSIBLE")
    if changed.count("prompt(door,")!=1 or changed.count("prompt(deco,")!=1 or changed.count("prompt(vault,")!=1:
        raise ValueError("RED_CASTLE_PROMPT_AUTHORITY_DRIFT")
    return changed

def unpatch(src):
    for _,b in PAIR:
        if src.count(b)!=1:raise ValueError("RED_SELECTED_CASTLE_FENCE_DRIFT")
    before=src
    for a,b in PAIR:before=before.replace(b,a,1)
    return before

def verify_delta(base,selected):
    _,old=mapping(base)
    _,new=mapping(selected)
    if set(old)!=set(new):raise ValueError("RED_SCRIPT_SET")
    diff=[x for x in old if old[x].read_bytes()!=new[x].read_bytes()]
    if diff!=[HOST]:raise ValueError("RED_ONLY_HOST_MAY_CHANGE")
    before=old[HOST].read_text(encoding="utf-8")
    after=new[HOST].read_text(encoding="utf-8")
    if patch(before)!=after or unpatch(after)!=before:raise ValueError("RED_HOST_ROLLBACK")
    return before,after,new

def prepare(base,out):
    base=base.resolve(strict=True);out=out.resolve()
    if out.exists() or out.parent!=base.parent or (out.parent/FILE).exists():
        raise ValueError("RED_OUT_COLLISION")
    obj,files=mapping(base)
    before=files[HOST].read_text(encoding="utf-8")
    after=patch(before)
    (out.parent/FILE).write_text(after,encoding="utf-8")
    project=copy.deepcopy(obj)
    project["tree"][HOST[0]][HOST[1]]["$path"]=FILE
    out.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    verify_delta(base,out)
    receipt={
       "feature_id":FEATURE,"source_count":31,
       "scope":"3 existing castle prompts, current server session only",
       "changed_script":HOST[-1],"other30_byte_exact":True,"off_byte_exact":True,
       "original_host_sha256":sha(before.encode()),"selected_host_sha256":sha(after.encode()),
       "no_game_combat_remote_score_store_scripts":True,
       "canonical_project_unmodified":True,"engine_android_fun":"NOT_TESTED",
       "formal_rc_adopted":False
    }
    (out.parent/RECEIPT).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ8_CASTLE_3_PROMPTS_ONE_HOST_OTHER30_OFF_EXACT_PASS")

def verify(base,out,place):
    before,after,files=verify_delta(base.resolve(strict=True),out.resolve(strict=True))
    found={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_ROJO_PROPS")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in found:raise ValueError("RED_ROJO_SOURCE")
        found[name]=(kind,source.replace("\r\n","\n"))
    if len(found)!=31 or set(found)!={route[-1] for route in files}:raise ValueError("RED_NOT_REAL_ROJO31")
    for route,file in files.items():
        kind="Script" if file.name.endswith(".server.luau") else ("LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if found[route[-1]]!=(kind,file.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_CLASS_SOURCE_"+route[-1])
    receipt_path=out.parent/RECEIPT
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if sha(before.encode())!=receipt["original_host_sha256"] or sha(after.encode())!=receipt["selected_host_sha256"]:
        raise ValueError("RED_RECEIPT_SOURCE")
    receipt.update({"native":"31/31","rojo":"31/31","place_bytes":place.stat().st_size,"place_sha256":sha(place.read_bytes())})
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print("GQ8_CASTLE_PROMPT_CURRENT_SESSION_ROJO_SOURCE_CLASS31_PASS",receipt["place_bytes"])

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("action",choices=("prepare","verify"))
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--place",type=Path)
    q=a.parse_args()
    if q.action=="prepare":prepare(q.base,q.out)
    else:
        if not q.place:a.error("verify requires --place")
        verify(q.base,q.out,q.place)
