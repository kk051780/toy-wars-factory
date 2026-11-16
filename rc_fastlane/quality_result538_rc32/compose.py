#!/usr/bin/env python3
"""Exact existing-author #538 SCORE result retry on the official RC31 Place.
A source-selective, unpublished RC32 *candidate*. One Result service authority,
the original 30 other Script Sources preserved, one pure Retry module added.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

OFFICIAL_HEAD="6ff632064ab5eca456161bb342b4a89aeb150717"
OFFICIAL_PLACE_SHA="883676cb13ebae0c528bdeaa8504d45a43facfb912cb9599fb443ceaa1b94e1e"
OFFICIAL_PLACE_BYTES=244344
AUTHOR538_HEAD="d56262dbe8309cf606877fe39a44cde7dda0d9b5"
AUTHOR538_RESULT_BLOB="b5ef844cff98173e3b2499b8aceca099f315adc4"
AUTHOR538_RETRY_BLOB="dbc5ff446b45e059967ae4d62455bab5e475dac7"
RESULT="EGGRUMBLE_MatchResultService"
RETRY="EGGRUMBLE_ResultRetry"

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def extraction(place:Path):
    result={}
    for element in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=element.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"): continue
        props=element.find("Properties")
        if props is None: raise ValueError("RED_SCRIPT_MISSING_PROPERTIES")
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        if not name or source is None or name in result:
            raise ValueError("RED_DUPLICATE_OR_MISSING_SCRIPT")
        result[name]=(cls,source.replace("\r\n","\n"))
    return result

def walk_project(project:dict):
    found={}
    def walk(node,prefix=()):
        for n,v in node.items():
            if n.startswith("$"): continue
            if not isinstance(v,dict):raise ValueError("RED_NON_SCRIPT_ROJO_ENTRY")
            route=prefix+(n,)
            if "$path" in v:
                if set(v)!={"$path"} or n in found:raise ValueError("RED_DUPLICATE_PROJECT_SCRIPT")
                found[n]=(route,v)
            else:walk(v,route)
    walk(project["tree"])
    return found

def kindname(kind:str,name:str)->str:
    return name+(".server.luau" if kind=="Script" else
                 ".client.luau" if kind=="LocalScript" else ".luau")

def read_official(place:Path,receipt_path:Path,project_path:Path):
    assert place.is_file() and receipt_path.is_file() and project_path.is_file()
    official=json.loads(receipt_path.read_text(encoding="utf-8"))
    if official.get("github_commit_sha")!=OFFICIAL_HEAD or not official.get("official_rc_commit_verified"):
        raise ValueError("RED_NOT_OFFICIAL_CANONICAL_SAME_HEAD")
    if official.get("script_count")!=31 or official.get("script_source_and_class_exact")!="31/31":
        raise ValueError("RED_NOT_EXACT_CURRENT_RC31")
    if official.get("original_author_540_added_in_same_537_host") is not True or not official.get("original_author_489_item_source_selected"):
        raise ValueError("RED_EXISTING_AUTHOR_LANES_MISSING")
    if place.stat().st_size!=OFFICIAL_PLACE_BYTES or sha(place.read_bytes())!=OFFICIAL_PLACE_SHA:
        raise ValueError("RED_CANONICAL_PLACE_DRIFT")
    if official.get("place_sha256")!=OFFICIAL_PLACE_SHA or official.get("place_size_bytes")!=OFFICIAL_PLACE_BYTES:
        raise ValueError("RED_CANONICAL_RECEIPT_DRIFT")
    project=json.loads(project_path.read_text(encoding="utf-8"))
    found=walk_project(project)
    src=extraction(place)
    if len(src)!=31 or set(src)!=set(found):
        raise ValueError("RED_CURRENT_31_NAME_MISMATCH")
    for n,(route,node) in found.items():
        oldname=Path(node["$path"]).name
        expected=("Script" if oldname.endswith(".server.luau") else
                  "LocalScript" if oldname.endswith(".client.luau") else "ModuleScript")
        if src[n][0]!=expected:
            raise ValueError("RED_CURRENT_31_CLASS_MISMATCH "+n)
    if blob(src[RESULT][1].encode())!=AUTHOR538_RESULT_BLOB:
        raise ValueError("RED_SCORE_AUTHOR_ORIGINAL_RESULT_CHANGED")
    if sum(n==RESULT for n in src)!=1 or RETRY in src:
        raise ValueError("RED_DUPLICATE_RESULT_OR_RETRY_AUTHORITY")
    for required in ("EGGRUMBLE_SwarmCombat","EGGRUMBLE_BotActors","EGGRUMBLE_SevenRoleCombat","EGGRUMBLE_LobbyCastleModesPreview","EGGRUMBLE_FieldItemPickups","EGGRUMBLE_ScoreBalance"):
        if required not in src:raise ValueError("RED_8_DOMAIN_SOURCE_ABSENT "+required)
    return project,found,src,official

def select(place:Path,receipt:Path,project_path:Path,author_root:Path,out:Path):
    old_doc,old_map,src,official=read_official(place,receipt,project_path)
    composer=author_root/"quality_gameplay/v3_result_transient_gui_20261116/compose_result.py"
    helper=author_root/"quality_gameplay/v3_result_transient_gui_20261116/EGGRUMBLE_ResultRetry.luau"
    if not composer.is_file() or not helper.is_file():raise ValueError("RED_MISSING_REAL_538_AUTHOR")
    if blob(helper.read_bytes())!=AUTHOR538_RETRY_BLOB:raise ValueError("RED_AUTHOR538_RETRY_CHANGED")
    spec=importlib.util.spec_from_file_location("original_gq538",composer)
    if not spec or not spec.loader:raise ValueError("RED_GQ538_IMPORT")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    if mod.AUTHOR_BLOB!=AUTHOR538_RESULT_BLOB:raise ValueError("RED_RESULT_AUTHOR_BLOB_CHANGING")
    result_on=mod.patch(src[RESULT][1].encode(),True)
    if mod.patch(src[RESULT][1].encode(),False)!=src[RESULT][1].encode():
        raise ValueError("RED_OFF_NOT_EXACT")
    if result_on==src[RESULT][1].encode() or result_on.count(b"ResultRetry.deliver(")!=1:
        raise ValueError("RED_UNIQUE_GQ538_HOOK_NOT_APPLIED")
    out.mkdir(parents=True,exist_ok=True)
    doc=json.loads(json.dumps(old_doc))
    nodes=walk_project(doc)
    for name,(kind,source) in src.items():
        data=result_on if name==RESULT else source.encode()
        filename=kindname(kind,name)
        (out/filename).write_bytes(data)
        nodes[name][1]["$path"]=filename
    retry_data=helper.read_bytes()
    (out/kindname("ModuleScript",RETRY)).write_bytes(retry_data)
    doc["name"]="EGGRUMBLE_V3_GQ538_AUTHOR32_PRIVATE_RC_INTAKE_NOT_OFFICIAL"
    doc["tree"]["ServerScriptService"][RETRY]={"$path":kindname("ModuleScript",RETRY)}
    project_out=out/"GQ538_RC32_CANDIDATE.project.json"
    project_out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    expected={name:(kind,((result_on.decode()) if name==RESULT else source)) for name,(kind,source) in src.items()}
    expected[RETRY]=("ModuleScript",retry_data.decode())
    if len(walk_project(doc))!=32:raise ValueError("RED_CANDIDATE_NOT_32_SOURCES")
    source_receipt={
      "source_base_rc_head":OFFICIAL_HEAD,
      "source_base_place_sha256":OFFICIAL_PLACE_SHA,
      "source_author538_head":AUTHOR538_HEAD,
      "original_31_script_count":31,
      "candidate_script_count":32,
      "unchanged_original_script_count":30,
      "existing_single_result_service":True,
      "original_score_balance_unchanged":True,
      "original_8_domain_game_sources_preserved":True,
      "added_pure_retry_helper":True,
      "original_result_source_blob":AUTHOR538_RESULT_BLOB,
      "original_retry_source_blob":AUTHOR538_RETRY_BLOB,
      "source_sha256":{name:sha(source.encode()) for name,(kind,source) in expected.items()},
      "source_class":{name:kind for name,(kind,source) in expected.items()},
      "official_rc_integration":False,
      "owner_accepted":False,
      "studio_android":"NOT_TESTED",
      "rollback":"drop this derived project; exact original RC31 artifact is unchanged"
    }
    (out/"GQ538_RC32_RECEIPT.json").write_text(json.dumps(source_receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ538_CURRENT_REAL_OFFICIAL31_TO_32_AUTHOR_SOURCE_PASS",len(expected),len(src)-1)

def verify(project_path:Path,receipt_path:Path,place:Path):
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    doc=json.loads(project_path.read_text(encoding="utf-8"))
    paths=walk_project(doc)
    actual=extraction(place)
    if len(actual)!=32 or set(paths)!=set(actual):
        raise ValueError("RED_ROJO32_SCRIPT_SET_MISMATCH")
    for name,(route,node) in paths.items():
        source=(project_path.parent/node["$path"]).read_text(encoding="utf-8").replace("\r\n","\n")
        kind=("Script" if node["$path"].endswith(".server.luau") else
              "LocalScript" if node["$path"].endswith(".client.luau") else "ModuleScript")
        if actual[name]!=(kind,source):
            raise ValueError("RED_ROJO32_SOURCE_CLASS_MISMATCH "+name)
        if receipt["source_sha256"][name]!=sha(source.encode()):
            raise ValueError("RED_ROJO32_RECEIPT_MISMATCH "+name)
    receipt["private_place_bytes"]=place.stat().st_size
    receipt["private_place_sha256"]=sha(place.read_bytes())
    receipt["private_rojo_source_class_exact"]="32/32"
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ538_RC32_TRUE_ROJO_SOURCE_CLASS_EXACT_PASS",len(actual),place.stat().st_size,receipt["private_place_sha256"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--official-place",required=True,type=Path)
    p.add_argument("--official-receipt",required=True,type=Path)
    p.add_argument("--official-project",required=True,type=Path)
    p.add_argument("--author-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--built-place",type=Path)
    a=p.parse_args()
    if a.built_place:
        verify(a.out/"GQ538_RC32_CANDIDATE.project.json",a.out/"GQ538_RC32_RECEIPT.json",a.built_place)
    else:
        select(a.official_place,a.official_receipt,a.official_project,a.author_root,a.out)
if __name__=="__main__":main()
