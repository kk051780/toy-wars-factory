#!/usr/bin/env python3
"""Source-select one original PR868 exploration Script on top of exact formal REAL65.
This is source composition only; Studio, Android, FUN and Owner acceptance remain untested.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from pathlib import Path

ROUTE="ServerScriptService/EGGRUMBLE_LegacyExplorationBridge"
PATH="sources/ServerScriptService/EGGRUMBLE_LegacyExplorationBridge.server.luau"

def check(value,reason):
    if not value:
        raise ValueError("RED_REAL66_"+reason)

def routes(project):
    found={}
    def walk(node,prefix=()):
        if "$path" in node:
            key="/".join(prefix)
            check(key not in found,"DUPLICATE_ROUTE")
            found[key]=node["$path"]
            return
        for name,child in node.items():
            if isinstance(child,dict) and not name.startswith("$"):
                walk(child,(*prefix,name))
    walk(project["tree"])
    return found

def digest(content):
    return hashlib.sha256(content).hexdigest()

def integrate(project_path,receipt_path,source_path,out_project,out_receipt):
    check(out_project!=project_path and out_receipt!=receipt_path,"DO_NOT_OVERWRITE_OFF65")
    base=json.loads(project_path.read_text(encoding="utf8"))
    receipt=json.loads(receipt_path.read_text(encoding="utf8"))
    original=routes(base)
    check(len(original)==65 and receipt["new_selected_source_count"]==65
          and len(receipt["sources"])==65,"EXPECTED_REAL65")
    check(set(original)=={x["route"] for x in receipt["sources"]},"EXACT_ORIGINAL_ROUTE_SET")
    check(ROUTE not in original,"NO_DUPLICATE_EXPLORATION")
    root=project_path.parent
    old={}
    for row in receipt["sources"]:
        b=(root/original[row["route"]]).read_bytes()
        check(row["sha256"]==digest(b) and row["bytes"]==len(b),"SOURCE_DRIFT")
        check(row["class"] in ("Script","LocalScript","ModuleScript"),"SOURCE_CLASS")
        old[row["route"]]=b
    data=source_path.read_bytes()
    check(data.startswith(b"--!strict"),"BRIDGE_STRICT")
    check(b"GQ8_LEGACY_RC85_86_EXPLORATION_INTAKE_20261119" in data,"ORIGINAL_PR868_MARKER")
    check(data.count(b'"REALM",')==4 and data.count(b'"SHARD",')==6,"4_REALMS_6_SHARDS")
    check(b"RunService:IsStudio()" in data and b"RespectCanCollide=true" in data,"STUDIO_ONLY_WALL_SAFE")
    check(not (root/PATH).exists(),"NEW_ROUTE_PATH_EXISTS")
    candidate=copy.deepcopy(base)
    candidate["name"]="EGGRUMBLE_REAL66_SINGLE_CANONICAL_PRIVATE_STUDIO"
    candidate["tree"]["ServerScriptService"]["EGGRUMBLE_LegacyExplorationBridge"]={"$path":PATH}
    selected=routes(candidate)
    check(len(selected)==66 and set(selected)==set(original)|{ROUTE},"REAL66_ONLY_ADDED_ONE")
    check(all(selected[k]==v for k,v in original.items()),"PRIOR65_PATH_CHANGED")
    for name,content in old.items():
        check((root/original[name]).read_bytes()==content,"PRIOR65_CONTENT_CHANGED")
    output_source=root/PATH
    output_source.parent.mkdir(parents=True,exist_ok=True)
    output_source.write_bytes(data)
    candidate_receipt=copy.deepcopy(receipt)
    candidate_receipt.update({
        "schema":"GQ8_REAL66_SINGLE_CANONICAL_SOURCE_SELECTION_V1",
        "source_profile":"eggrumble_v3_real66",
        "parent_source_profile":"eggrumble_v3_real65",
        "parent_selected_source_count":65,
        "new_selected_source_count":66,
        "formal_rc_adopted":False,
        "source_native":"PENDING",
        "rojo_source_class":"PENDING",
        "legacy_exploration":{
            "source_pr":868,"source_script":ROUTE,"script_class":"Script",
            "unchanged_original_source_count":65,"added_source_count":1,
            "realms":4,"shards":6,"bridge_sha256":digest(data),
            "studio_only":True,"no_other_gameplay_authority":True,
            "studio_single":"NOT_TESTED","studio_2client":"NOT_TESTED",
            "android15min":"NOT_TESTED","fun":"NO_GO","art":"NO_GO",
            "rollback":"Re-select existing EGGRUMBLE_REAL65.project.json and exact original 65 sources"
        },
        "sources":sorted([*receipt["sources"],{
            "route":ROUTE,"class":"Script","sha256":digest(data),"bytes":len(data)
        }],key=lambda x:x["route"])
    })
    out_project.write_text(json.dumps(candidate,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    out_receipt.write_text(json.dumps(candidate_receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    check(len(routes(json.loads(out_project.read_text(encoding="utf8"))))==66,"OUTPUT_ROUTE_COUNT")
    check(len(routes(json.loads(project_path.read_text(encoding="utf8"))))==65,"OFF65_PROJECT_CHANGED")
    print("GQ8_REAL66_EXACT_65_PLUS_ONE_PR868_ORIGINAL_SOURCE_PASS")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    for name in ("project","receipt","source","out_project","out_receipt"):
        a.add_argument("--"+name.replace("_","-"),required=True,type=Path)
    p=a.parse_args()
    integrate(p.project,p.receipt,p.source,p.out_project,p.out_receipt)
