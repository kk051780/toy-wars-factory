#!/usr/bin/env python3
"""Source-select existing #538 actual Result retry into ONE current RC31 ResultService.
The original #538 Luau policy is inlined byte-exact except local table renaming
and the module-only return, so the total remains 31 original-author scripts.
All 30 other current RC scripts stay byte-identical. No second result, remote,
game, score authority, paid/publish action, or main write.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET

RESULT=("ServerScriptService","EGGRUMBLE_MatchResultService")
AUTHOR_RESULT_BLOB="b5ef844cff98173e3b2499b8aceca099f315adc4"
AUTHOR_RETRY_BLOB="dbc5ff446b45e059967ae4d62455bab5e475dac7"
AUTHOR538_HEAD="d56262dbe8309cf606877fe39a44cde7dda0d9b5"
INLINE_REQUIRE='local ResultRetry=require(script.Parent:WaitForChild("EGGRUMBLE_ResultRetry"))\n'

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def scan(project:Path):
    data=json.loads(project.read_text(encoding="utf-8"))
    seen={}
    def visit(node,path=()):
        for name,v in node.items():
            if name.startswith("$"):continue
            if not isinstance(v,dict):raise ValueError("RED_INVALID_PROJECT_NODE")
            key=path+(name,)
            if "$path" in v:
                if set(v)!={"$path"} or key in seen:raise ValueError("RED_MULTI_SOURCE_AUTHORITY")
                seen[key]=(project.parent/v["$path"]).resolve(strict=True)
            else:visit(v,key)
    visit(data["tree"])
    if len(seen)!=31 or len({x[-1] for x in seen})!=31 or RESULT not in seen:
        raise ValueError("RED_NOT_CURRENT_31_UNIQUE_GAME_SOURCES")
    return data,seen

def make_inline(result:bytes,author_python:Path,author_luau:Path)->bytes:
    if blob(result)!=AUTHOR_RESULT_BLOB:
        raise ValueError("RED_ORIGINAL487_RESULT_BLOB_DRIFT_OR_ALREADY_PATCHED")
    if blob(author_luau.read_bytes())!=AUTHOR_RETRY_BLOB:
        raise ValueError("RED_ORIGINAL538_RESULT_POLICY_DRIFT")
    spec=importlib.util.spec_from_file_location("original_gq538_result",author_python.resolve(strict=True))
    if not spec or not spec.loader:raise ValueError("RED_ORIGINAL538_AUTHOR_LOAD")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    if mod.AUTHOR_BLOB!=AUTHOR_RESULT_BLOB:raise ValueError("RED_ORIGINAL_RESULT_REFERENCE_CHANGED")
    authored=mod.patch(result,True).decode("utf-8")
    if authored.count(INLINE_REQUIRE)!=1 or authored.count("ResultRetry.deliver(")!=1:
        raise ValueError("RED_ORIGINAL_AUTHOR_PATCH_NOT_ONE_HOOK")
    original=author_luau.read_text(encoding="utf-8")
    if not original.startswith("--!strict\n") or original.count("local Retry = {}")!=1 or original.count("return Retry")!=1:
        raise ValueError("RED_ORIGINAL538_POLICY_STRUCTURE_CHANGED")
    if original.rstrip().splitlines()[-1]!="return Retry":
        raise ValueError("RED_ORIGINAL_POLICY_RETURN_IS_NOT_FINAL")
    body=original[len("--!strict\n"):]
    body=body[:body.rfind("return Retry")].rstrip()+"\n"
    body=body.replace("local Retry = {}","local ResultRetry = {}")
    body=re.sub(r"(?<![A-Za-z0-9_])Retry\.", "ResultRetry.", body)
    if body.count("local ResultRetry = {}")!=1 or body.count("function ResultRetry.deliver(")!=1:
        raise ValueError("RED_ORIGINAL538_POLICY_NOT_REUSABLE_INLINE")
    if "return Retry" in body or "local Retry = {}" in body:
        raise ValueError("RED_POLICY_OLD_SYMBOL_LEFT")
    selected=authored.replace(INLINE_REQUIRE,body+"\n",1)
    if selected.count("ResultRetry.deliver(")!=2: # definition and original single call
        raise ValueError("RED_RETRY_SERVICE_CALL_AUTHORITY_NOT_UNIQUE")
    if selected.count("ScoreBalance.build(")!=1 or selected.count("session.resultsDelivered=true")!=1:
        raise ValueError("RED_RESULT_SCORE_INVARIANT_CHANGED")
    if INLINE_REQUIRE in selected or "EGGRUMBLE_ResultRetry" in selected:
        raise ValueError("RED_UNWANTED_SECOND_MODULE_DEPENDENCY")
    return selected.encode("utf-8")

def prepare(base:Path,author_python:Path,author_luau:Path,out:Path):
    doc,mapping=scan(base)
    original=mapping[RESULT].read_bytes()
    selected=make_inline(original,author_python,author_luau)
    out=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    dest=out/"EGGRUMBLE_MatchResultService_538.luau"
    if dest.resolve()==mapping[RESULT].resolve():
        raise ValueError("RED_AUTHOR_RESULT_SOURCE_WRITE")
    dest.write_bytes(selected)
    project=json.loads(json.dumps(doc))
    def relink(node,path=()):
        for n,v in node.items():
            if n.startswith("$"):continue
            route=path+(n,)
            if "$path" in v:
                file=dest if route==RESULT else mapping[route]
                v["$path"]=os.path.relpath(file,out).replace(os.sep,"/")
            else:relink(v,route)
    relink(project["tree"])
    project["name"]="GQ538_ORIGINAL_AUTHOR_ONE_RESULT_PRIVATE31_NO_PUBLISH"
    new=out/"GQ538_FINAL_SELECTED31.project.json"
    new.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,actual=scan(new)
    for k in set(mapping)-{RESULT}:
        if actual[k].read_bytes()!=mapping[k].read_bytes():
            raise ValueError("RED_OTHER_30_ORIGINAL_AUTHORS_MODIFIED "+"/".join(k))
    if actual[RESULT].read_bytes()!=selected:
        raise ValueError("RED_ORIGINAL_RESULT_PATCH_MISSING")
    manifest={
      "original_base_project_sha256":sha(base.read_bytes()),
      "source_head538":AUTHOR538_HEAD,
      "source_count":31,
      "one_original_result_service":True,
      "no_extra_policy_module":True,
      "inlined_original_538_policy":True,
      "unchanged_original_source_count":30,
      "original_result_sha256":sha(original),
      "new_result_sha256":sha(selected),
      "real_original_luau_policy_git_blob":AUTHOR_RETRY_BLOB,
      "all_source_sha256":{"/".join(k):sha(v.read_bytes()) for k,v in sorted(actual.items())},
      "official_rc_adopted":False,
      "studio_android_owner":"NOT_TESTED",
      "rollback":"restore exactly the original ResultService from current base project and omit this one-hunk packaging"
    }
    (out/"GQ538_SELECTED31_RECEIPT.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ538_ORIGINAL_RESULT_INLINED_31_30_OTHER_AUTHORS_EXACT_PASS")

def verify(base:Path,selected:Path,author_python:Path,author_luau:Path,place:Path):
    _,before=scan(base)
    _,after=scan(selected)
    original=before[RESULT].read_bytes()
    expected=make_inline(original,author_python,author_luau)
    if after[RESULT].read_bytes()!=expected:raise ValueError("RED_WRONG_RESULT_OVERLAY")
    for k in set(before)-{RESULT}:
        if after[k].read_bytes()!=before[k].read_bytes():
            raise ValueError("RED_NON_RESULT_SOURCE_CHANGED")
    embedded={}
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        kind=item.attrib.get("class")
        if kind not in {"Script","LocalScript","ModuleScript"}:continue
        props=item.find("Properties")
        if props is None:raise ValueError("RED_MISSING_ITEM_PROPERTIES")
        n=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not n or source is None or n in embedded:
            raise ValueError("RED_DUPLICATE_OR_MISSING_EMBEDDED_SCRIPT")
        embedded[n]=(kind,source.replace("\r\n","\n"))
    if {k[-1] for k in after}!=set(embedded) or len(embedded)!=31:
        raise ValueError("RED_CANDIDATE_PLACE_SCRIPT_SET_CHANGED")
    for k,src in after.items():
        kind=("Script" if src.name.endswith(".server.luau") else
              "LocalScript" if src.name.endswith(".client.luau") else "ModuleScript")
        if embedded[k[-1]]!=(kind,src.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED_ROJO_SOURCE_OR_CLASS_DRIFT "+k[-1])
    receipt={
       "script_count":31,"rojo_source_class_exact":"31/31",
       "only_original_result_changed":True,
       "other_30_sources_byte_exact":True,
       "result_author_head":AUTHOR538_HEAD,
       "place_bytes":place.stat().st_size,
       "place_sha256":sha(place.read_bytes()),
       "source_selected_result_sha256":sha(expected),
       "original_result_sha256":sha(original),
       "official_rc_adopted":False
    }
    (selected.parent/"GQ538_ROJO31_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ538_REAL_ORIGINAL_RESULT_SINGLE_SOURCE_ROJO31_PASS",receipt["place_bytes"],receipt["place_sha256"])

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["prepare","verify"])
    ap.add_argument("--base",required=True,type=Path)
    ap.add_argument("--author-python",required=True,type=Path)
    ap.add_argument("--author-luau",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    ap.add_argument("--place",type=Path)
    a=ap.parse_args()
    if a.command=="prepare":prepare(a.base,a.author_python,a.author_luau,a.out)
    else:
        if a.place is None:ap.error("--place required")
        verify(a.base,a.out,a.author_python,a.author_luau,a.place)
