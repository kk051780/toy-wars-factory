#!/usr/bin/env python3
"""GQ499 original-author 900s time-limit inline into existing RC31 Host ONLY.

No new Script/Module/Game/Remote/Score owner; all other30 current Source bytes
preserved. Source policy is taken byte-exact from old #499 fixed Git blob.
Source/Place verification is strict and reversible; does not move official RC.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HOST=("ServerScriptService","EGGRUMBLE_LobbyCastleModesPreview")
N=31
AUTHOR_BLOB="7d1b2dd8d341164a2d8759d5511d7aecaeedfdfa"
FLAG="MATCH_DEADLINE_DRAW_499"
FILE="GQ499_CURRENT31_DEADLINE_HOST.server.luau"
RECEIPT="GQ499_DEADLINE_CURRENT31_RECEIPT.json"
IMPORT_ANCHOR='local RoundReplay=require(script.Parent:WaitForChild("EGGRUMBLE_RoundReplay"))\n'
START_ANCHOR=" Rules.start(session.rules)\n"
START_ADDITION=""" -- GQ499 original-author 900s deadline; same Host, same Rules, no new Game.
 local deadlineId=mode..":"..tostring(session)
 local deadlineLease=Deadline.new(os.clock(),deadlineId)
 session.deadlineLease=deadlineLease
 task.spawn(function()
  while sessions[mode]==session and session.rules.phase=="ACTIVE" and session.world.Parent do
   local expired=Deadline.expire(session.rules,deadlineLease,os.clock(),deadlineId)
   if expired then
    session.refresh() -- existing result/round replay, no second scoreboard
    break
   end
   task.wait(.5)
  end
 end)
"""
def git_blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()
def flatten(project:Path):
    project=project.resolve(strict=True)
    j=json.loads(project.read_text(encoding="utf8"))
    found={}
    def walk(d,route=()):
        for name,node in d.items():
            if name.startswith("$"):continue
            if not isinstance(node,dict):raise ValueError("RED_INVALID_PROJECT")
            k=route+(name,)
            if "$path" in node:
                if set(node)!={"$path"} or k in found:raise ValueError("RED_DUPLICATE_AUTHORITY")
                found[k]=(project.parent/node["$path"]).resolve(strict=True)
            else:walk(node,k)
    walk(j["tree"])
    if len(found)!=N or len({k[-1] for k in found})!=N or HOST not in found:
        raise ValueError("RED_NOT_CURRENT_31_OR_HOST_MISSING")
    return j,found
def inline_policy(policy:Path):
    raw=policy.read_bytes()
    if git_blob(raw)!=AUTHOR_BLOB:raise ValueError("RED_ORIGINAL_499_AUTHOR_BLOB_DRIFT")
    source=raw.decode("utf8")
    if not source.startswith("--!strict\n") or not source.endswith("return Deadline\n"):
        raise ValueError("RED_ORIGINAL_AUTHOR_POLICY_SHAPE")
    if source.count('function Deadline.expire(')!=1 or source.count('state.winner="DRAW"')!=1:
        raise ValueError("RED_ORIGINAL_AUTHOR_LOGIC_MISSING")
    return source[len("--!strict\n"):-len("return Deadline\n")]
def overlay(old:str,policy:Path):
    body=inline_policy(policy)
    if FLAG in old or "local Deadline=" in old or "Deadline.expire(" in old:
        raise ValueError("RED_DUPLICATE_DEADLINE")
    for a in (IMPORT_ANCHOR,START_ANCHOR):
        if old.count(a)!=1:raise ValueError("RED_CURRENT_HOST_ANCHOR_DRIFT_"+a.strip())
    if old.index("session.refresh=function()")>old.index(START_ANCHOR):
        raise ValueError("RED_RESULT_REPLAY_NOT_READY")
    if 'RoundReplay.schedule(session,session.closeRound)' not in old or 'ResultService.showIfFinished(session,queue,mode)' not in old:
        raise ValueError("RED_PREEXISTING_RESULT_OR_REPLAY_MISSING")
    # Keep original #499 pure logic bytes as-is after top-level strict marker.
    added="\n-- "+FLAG+" BEGIN ORIGINAL #499 POLICY (signed blob "+AUTHOR_BLOB+")\n"+body+"-- "+FLAG+" END ORIGINAL POLICY\n"
    updated=old.replace(IMPORT_ANCHOR,IMPORT_ANCHOR+added,1)
    updated=updated.replace(START_ANCHOR,START_ANCHOR+START_ADDITION,1)
    if updated.replace(START_ADDITION,"",1).replace(added,"",1)!=old:
        raise ValueError("RED_NOT_EXACT_INVERSE")
    return updated,added
def prepare(base:Path,out:Path,policy:Path):
    if out.exists() or out.parent.resolve()!=base.parent.resolve():
        raise ValueError("RED_NONFRESH_SIBLING_PROJECT")
    j,old=flatten(base)
    before=old[HOST].read_bytes()
    after,added=overlay(before.decode("utf8"),policy)
    newpath=out.parent/FILE
    if newpath.exists():raise ValueError("RED_EXISTING_OUTPUT_HOST")
    newpath.write_bytes(after.encode("utf8"))
    d=copy.deepcopy(j)
    d["tree"][HOST[0]][HOST[1]]["$path"]=FILE
    out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,selected=flatten(out)
    changed=[k for k in old if old[k].read_bytes()!=selected[k].read_bytes()]
    if changed!=[HOST] or set(old)!=set(selected):
        raise ValueError("RED_MORE_THAN_ONE_HOST_CHANGED")
    r={"feature_id":FLAG,"source_count":N,"only_changed":"/".join(HOST),
       "original_policy_git_blob":AUTHOR_BLOB,"original_host_sha256":sha(before),
       "selected_host_sha256":sha(after.encode("utf8")),
       "other30_bytes_exact":True,"off_inverse_byte_exact":True,
       "real_rojo_exact":"NOT_RUN","formal_rc_adopted":False,
       "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED","owner_fun":"NO_GO"}
    (out.parent/RECEIPT).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("GQ499_ORIGINAL_POLICY_CURRENT31_HOST_ONLY_OFF_EXACT_PASS")
def verify(base:Path,out:Path,policy:Path,place:Path):
    _,old=flatten(base)
    _,selected=flatten(out)
    before=old[HOST].read_text(encoding="utf8")
    expected,_=overlay(before,policy)
    if selected[HOST].read_text(encoding="utf8")!=expected:
        raise ValueError("RED_SELECTED_HOST_NOT_EXACT_AUTHOR")
    if set(old)!=set(selected) or [k for k in old if old[k].read_bytes()!=selected[k].read_bytes()]!=[HOST]:
        raise ValueError("RED_OTHER_30_SOURCE_MUTATED")
    actual={}
    for item in ET.parse(place).getroot().iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_PLACE_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        code=props.findtext("ProtectedString[@name='Source']")
        if code is None:code=props.findtext("string[@name='Source']")
        if not name or code is None or name in actual:raise ValueError("RED_DUPLICATE_PLACE_SCRIPT")
        actual[name]=(cls,code.replace("\r\n","\n"))
    if len(actual)!=N or set(actual)!={k[-1] for k in selected}:raise ValueError("RED_PLACE_NOT31")
    for k,p in selected.items():
        cls=("Script" if p.name.endswith(".server.luau") else
             "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
        if actual[k[-1]]!=(cls,p.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_TRUE_ROJO_CLASS_SOURCE_"+k[-1])
    rpath=out.parent/RECEIPT
    r=json.loads(rpath.read_text())
    if r["original_host_sha256"]!=sha(old[HOST].read_bytes()) or r["selected_host_sha256"]!=sha(selected[HOST].read_bytes()):
        raise ValueError("RED_RECEIPT_SOURCE_MISMATCH")
    r.update(real_rojo_exact="31/31",place_bytes=place.stat().st_size,
             place_sha256=sha(place.read_bytes()))
    rpath.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("GQ499_REAL_RC31_NATIVE_ROJO_SOURCE_CLASS_EXACT_PASS",r["place_bytes"])
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("prepare","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--policy",type=Path,required=True)
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="prepare":prepare(a.base,a.out,a.policy)
    else:
        if a.place is None:p.error("verify requires --place")
        verify(a.base,a.out,a.policy,a.place)
if __name__=="__main__":main()
