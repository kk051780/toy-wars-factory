#!/usr/bin/env python3
"""GQ615: source-exact 31-script private RC overlay using the real official Place.

The official authenticated RC is never changed. Extract actual official
same-HEAD Place Script/LocalScript/ModuleScript sources, select ONE Host
presentation overlay, and build a source-exact Rojo replay. Preserve every
other object in the directly patched full Studio Place. Fail closed on drift.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from select_feedback import apply, FEATURE_ID

SCRIPT_TYPES={"Script","ModuleScript","LocalScript"}
HOST="EGGRUMBLE_LobbyCastleModesPreview"
EXPECTED=31

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def prop(node:ET.Element,name:str)->ET.Element|None:
    p=node.find("./Properties")
    if p is None:
        return None
    for kind in ("ProtectedString","string"):
        s=p.find(f"{kind}[@name='{name}']")
        if s is not None:
            return s
    return None

def walk(root:ET.Element):
    scripts={}
    items=[]
    def child(node:ET.Element,path:tuple):
        if node.tag!="Item":
            for sub in node:
                if sub.tag=="Item":
                    child(sub,path)
            return
        cls=node.attrib.get("class","")
        n=prop(node,"Name")
        if n is None or not n.text:
            raise ValueError("RED_NAMELESS_INSTANCE")
        name=n.text
        route=path+((name,cls),)
        items.append(route)
        if cls in SCRIPT_TYPES:
            source=prop(node,"Source")
            if source is None:
                raise ValueError("RED_SCRIPT_SOURCE_MISSING")
            if route in scripts:
                raise ValueError("RED_DUPLICATE_SCRIPT_ROUTE")
            scripts[route]=(node,source)
        for sub in node:
            if sub.tag=="Item":
                child(sub,route)
    child(root,())
    if len(scripts)!=EXPECTED:
        raise ValueError(f"RED_SCRIPT_COUNT_{len(scripts)}_NE_{EXPECTED}")
    matches=[route for route in scripts if route[-1]==(HOST,"Script")]
    if len(matches)!=1:
        raise ValueError("RED_NOT_SINGLE_SERVER_HOST")
    if len({r[-1][0] for r in scripts})!=EXPECTED:
        raise ValueError("RED_DUPLICATE_SCRIPT_NAME")
    return scripts,items,matches[0]

def script_map(root:ET.Element):
    scripts,items,route=walk(root)
    return {k:(k[-1][-1],(n.text or "").replace("\r\n","\n")) for k,(_,n) in scripts.items()},items,route

def source_only_project(root:ET.Element,out_dir:Path)->Path:
    mapping,_,_=script_map(root)
    project={"name":"GQ615_RC31_ACTUAL_OFFICIAL_SOURCE_EXACT_PRIVATE_REPLAY",
             "tree":{"$className":"DataModel"}}
    folder=out_dir/"source31"
    folder.mkdir(parents=True,exist_ok=False)
    for i,(route,(cls,source)) in enumerate(mapping.items(),1):
        parent=project["tree"]
        for name,kind in route[:-1]:
            entry=parent.get(name)
            if entry is None:
                entry={"$className":kind}
                parent[name]=entry
            if entry.get("$className")!=kind:
                raise ValueError("RED_DUPLICATE_PARENT_NAME_OR_CLASS")
            parent=entry
        name,kind=route[-1]
        if name in parent:
            raise ValueError("RED_DUPLICATE_ROJO_SCRIPT_ROUTE")
        suffix=(".server.luau" if kind=="Script" else
                ".client.luau" if kind=="LocalScript" else ".luau")
        safe=re.sub(r"[^A-Za-z0-9_-]","_",name)[:48]
        p=folder/f"{i:02d}_{safe}{suffix}"
        if p.exists():
            raise ValueError("RED_SCRIPT_FILE_COLLISION")
        p.write_text(source,encoding="utf-8",newline="\n")
        parent[name]={"$path":str(p.relative_to(out_dir)).replace("\\","/")}
    output=out_dir/"GQ615_CURRENT_SOURCE31.project.json"
    output.write_text(json.dumps(project,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return output

def ensure_official_receipt(receipt:Path,place:Path,official_head:str):
    proof=json.loads(receipt.read_text(encoding="utf-8"))
    if proof.get("github_commit_sha")!=official_head:
        raise ValueError("RED_OFFICIAL_RECEIPT_WRONG_HEAD")
    if proof.get("script_count")!=EXPECTED or proof.get("script_source_and_class_exact")!="31/31":
        raise ValueError("RED_OFFICIAL_SOURCE_EXACT_MISSING")
    if proof.get("place_sha256")!=sha(place.read_bytes()) or proof.get("place_size_bytes")!=place.stat().st_size:
        raise ValueError("RED_OFFICIAL_PLACE_SHA_OR_SIZE_NOT_AUTHENTICATED")
    if proof.get("status","").startswith("RC_PREMERGE_"):
        raise ValueError("RED_OFFICIAL_PR_NOT_PUSH_ARTIFACT")
    return proof

def prepare(official:Path,receipt:Path,out:Path,head:str,run:int,zip_bytes:int):
    if out.exists():
        raise ValueError("RED_OUTPUT_MUST_BE_EMPTY")
    out.mkdir(parents=True,exist_ok=False)
    ensure_official_receipt(receipt,official,head)
    original=ET.parse(official)
    oldmap,olditems,hostroute=script_map(original.getroot())
    old=oldmap[hostroute][1]
    modified=apply(old)
    if modified==old:
        raise ValueError("RED_HOST_EMPTY_PATCH")
    selected=copy.deepcopy(original)
    sources,_,_=walk(selected.getroot())
    sources[hostroute][1].text=modified
    newmap,newitems,newroute=script_map(selected.getroot())
    if olditems!=newitems or hostroute!=newroute or set(oldmap)!=set(newmap):
        raise ValueError("RED_TREE_INSTANCE_OR_SCRIPT_DRIFT")
    changed=[k for k in oldmap if oldmap[k]!=newmap[k]]
    if changed!=[hostroute]:
        raise ValueError("RED_OTHER30_SOURCES_CHANGED")
    if newmap[hostroute][1]!=modified or newmap[hostroute][0]!="Script":
        raise ValueError("RED_WRONG_HOST")
    # Exact inverse on the selected production current Host, not the older #482.
    undone=modified
    from select_feedback import CHANGES
    for old_hunk,new_hunk in reversed(CHANGES):
        if old_hunk==new_hunk:
            continue
        if undone.count(new_hunk)!=1:
            raise ValueError("RED_INVERSE_ANCHOR_COLLISION")
        undone=undone.replace(new_hunk,old_hunk,1)
    if undone!=old:
        raise ValueError("RED_ROLLBACK_CURRENT_HOST_NOT_BYTE_EXACT")
    candidate=out/"GQ615_FULL_OFFICIAL_PLACE_HOST_ONLY_PRIVATE.rbxlx"
    selected.write(candidate,encoding="utf-8",xml_declaration=True)
    actual=ET.parse(candidate)
    written,items_written,_=script_map(actual.getroot())
    if written!=newmap or items_written!=olditems:
        raise ValueError("RED_SERIALIZED_SELECTED_PLACE_SCRIPT_OR_TREE_DRIFT")
    project=source_only_project(actual.getroot(),out)
    proof={
        "feature_id":FEATURE_ID,
        "source":"Official same-HEAD V3 canonical Place, NOT standalone #482",
        "source_rc_head":head,"source_rc_workflow_run":run,
        "official_provider_zip_bytes":zip_bytes,
        "original_official_place_sha256":sha(official.read_bytes()),
        "original_official_place_bytes":official.stat().st_size,
        "selected_private_place_sha256":sha(candidate.read_bytes()),
        "selected_private_place_bytes":candidate.stat().st_size,
        "selected_host_sha256_before":sha(old.encode("utf-8")),
        "selected_host_sha256_after":sha(modified.encode("utf-8")),
        "scripts":EXPECTED,"changed_existing_sources":1,"unchanged_other_sources":30,
        "changed_script":"/".join(a for a,_ in hostroute),
        "other_instances_preserved":True,
        "exact_host_inverse_rollback":True,
        "new_game_remote_score_store_authorities":0,
        "studio_tested":False,"android_tested":False,"owner_accepted":False,
        "formal_rc_adopted":False,
        "rojo_31_source_class_verified":False,
        "S1_main_unmodified":True,
        "primary_profile_unmodified":True
    }
    (out/"GQ615_PRIVATE31_RECEIPT.json").write_text(
        json.dumps(proof,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ615_OFFICIAL_PLACE_ONE_CURRENT_HOST_ONLY_OTHER30_BYTE_EXACT_PASS",head,run)
    print("GQ615_SELECTED_PROJECT",project)

def verify(out:Path,rojo:Path):
    proof_path=out/"GQ615_PRIVATE31_RECEIPT.json"
    proof=json.loads(proof_path.read_text(encoding="utf-8"))
    selected=ET.parse(out/"GQ615_FULL_OFFICIAL_PLACE_HOST_ONLY_PRIVATE.rbxlx")
    replay=ET.parse(rojo)
    sources,full_items,_=script_map(selected.getroot())
    built,_,_=script_map(replay.getroot())
    if sources!=built:
        bad=[str(k) for k in sources if sources[k]!=built.get(k)]
        raise ValueError("RED_ROJO_REPLAY_SOURCE_CLASS_ROUTE_DRIFT "+repr(bad[:4]))
    if len(built)!=EXPECTED:
        raise ValueError("RED_ROJO_NOT_31")
    proof["rojo_31_source_class_verified"]=True
    proof["rojo_private_replay_bytes"]=rojo.stat().st_size
    proof["rojo_private_replay_sha256"]=sha(rojo.read_bytes())
    proof_path.write_text(json.dumps(proof,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ615_PRIVATE_RC31_REAL_ROJO_ALL_SOURCE_CLASS_PATH_EXACT_PASS",len(built))
    print("GQ615_PRIVATE_RC31_ACTUAL_PLACE_BYTES",proof["selected_private_place_bytes"])

def harness(source_file:Path,out:Path):
    selected=source_file.read_text(encoding="utf-8")
    start="local function refreshQueueBoard(mode:string)\n"
    end="\nlocal function getCastlePoint(mode:string,index:number)"
    if selected.count(start)!=1 or selected.count(end)!=1:
        raise ValueError("RED_QUEUE_FUNCTION_NOT_SINGLE")
    code=selected.split(start,1)[1].split(end,1)[0]
    cases=r'''
local now=100
local function time():number return now end
local MODE_SEATS=16
local COUNTDOWN=12
local queues={TEAM={},BATTLE_ROYALE={}}
local sessions={}
local queueStartedAt={}
local queueBoards={TEAM={Text=""},BATTLE_ROYALE={Text=""}}
local function refreshQueueBoard(mode:string)
__ACTUAL_FUNCTION_BODY__
refreshQueueBoard("TEAM")
refreshQueueBoard("BATTLE_ROYALE")
assert(string.find(queueBoards.TEAM.Text,"1人でも開始",1,true))
assert(string.find(queueBoards.BATTLE_ROYALE.Text,"1人でも開始",1,true))
queueStartedAt.TEAM=100
table.insert(queues.TEAM,{})
refreshQueueBoard("TEAM")
assert(string.find(queueBoards.TEAM.Text,"1/16人",1,true))
assert(string.find(queueBoards.TEAM.Text,"12秒",1,true))
now=105
refreshQueueBoard("TEAM")
assert(string.find(queueBoards.TEAM.Text,"7秒",1,true))
assert(string.find(queueBoards.BATTLE_ROYALE.Text,"1人でも開始",1,true))
for i=2,16 do table.insert(queues.TEAM,{}) end
refreshQueueBoard("TEAM")
assert(string.find(queueBoards.TEAM.Text,"16/16人",1,true))
sessions.TEAM={}
refreshQueueBoard("TEAM")
assert(string.find(queueBoards.TEAM.Text,"試合中",1,true))
sessions.TEAM=nil
queues.TEAM={}
queueStartedAt.TEAM=nil
refreshQueueBoard("TEAM")
assert(string.find(queueBoards.TEAM.Text,"1人でも開始",1,true))
queueStartedAt.BATTLE_ROYALE=104
table.insert(queues.BATTLE_ROYALE,{})
now=106
refreshQueueBoard("BATTLE_ROYALE")
assert(string.find(queueBoards.BATTLE_ROYALE.Text,"1/16人",1,true))
assert(string.find(queueBoards.BATTLE_ROYALE.Text,"10秒",1,true))
print("GQ615_REAL_QUEUE_TEXT_NATIVE_10_CASES_PASS")
'''
    cases=cases.replace("__ACTUAL_FUNCTION_BODY__",code)
    out.write_text(cases,encoding="utf-8")
    print("GQ615_ACTUAL_SOURCE_QUEUE_NATIVE_CASES_GENERATED")

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="command",required=True)
    p=sub.add_parser("prepare")
    p.add_argument("--official-place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    p.add_argument("--rc-head",required=True)
    p.add_argument("--run-id",type=int,required=True)
    p.add_argument("--zip-bytes",type=int,required=True)
    p=sub.add_parser("verify")
    p.add_argument("--out-dir",type=Path,required=True)
    p.add_argument("--rojo-place",type=Path,required=True)
    p=sub.add_parser("harness")
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if a.command=="prepare":
        prepare(a.official_place,a.receipt,a.out_dir,a.rc_head,a.run_id,a.zip_bytes)
    elif a.command=="verify":
        verify(a.out_dir,a.rojo_place)
    else:
        harness(a.source,a.out)
if __name__=="__main__":
    main()
