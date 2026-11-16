#!/usr/bin/env python3
"""Generate a single 21-source PRIVATE Rojo Place map; no official RC mutations."""
import argparse, hashlib, json, os, xml.etree.ElementTree as ET
from pathlib import Path

PROJECT=Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_V3_STUDIO.project.json")
SLOT="EGGRUMBLE_SevenRoleCombat"

def mapped(data:dict,project_dir:Path):
    result={}
    def walk(obj):
        for name,child in obj.items():
            if name.startswith("$") or not isinstance(child,dict): continue
            if "$path" in child:
                assert name not in result, "duplicate script "+name
                file=(project_dir/child["$path"]).resolve(strict=True)
                kind="LocalScript" if file.name.endswith(".client.luau") else ("Script" if file.name.endswith(".server.luau") else "ModuleScript")
                result[name]=(kind,file)
            else: walk(child)
    walk(data["tree"])
    return result

def compose(project_output:Path,candidate:Path,receipt:Path):
    source_project=PROJECT.resolve(strict=True)
    original=json.loads(source_project.read_text(encoding="utf-8"))
    current=mapped(original,source_project.parent)
    assert len(current)==21, "original author project drift"
    assert SLOT in current
    assert current[SLOT][0]=="ModuleScript"
    candidate=candidate.resolve(strict=True)
    project_output.parent.mkdir(parents=True,exist_ok=True)
    target=json.loads(json.dumps(original))
    def walk(obj):
        for name,child in obj.items():
            if name.startswith("$") or not isinstance(child,dict): continue
            if "$path" in child:
                prior=current[name][1]
                select=candidate if name==SLOT else prior
                child["$path"]=os.path.relpath(select,project_output.parent).replace(os.sep,"/")
            else: walk(child)
    walk(target["tree"])
    target["name"]="EGGRUMBLE_GQ_HUMAN_STEALTH_PRIVATE_21_NOT_RC"
    resolved=mapped(target,project_output.parent.resolve())
    assert len(resolved)==21
    assert all(resolved[name][1]==(candidate if name==SLOT else old[1])
               for name,old in current.items())
    project_output.write_text(json.dumps(target,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    data={"status":"SOURCE_PRIVATE_NOT_OFFICIAL_RC","script_count":21,
          "author_original_game_head":"fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
          "original_source_unchanged":20,"original_source_overlay":1,
          "no_new_game_remote_store":True,"production_adopted":False,
          "source_sha256":{name:hashlib.sha256(file.read_bytes()).hexdigest()
                           for name,(_,file) in resolved.items()},
          "rollback":"select original author #482 EGGRUMBLE_SevenRoleCombat source"}
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ_HUMAN_STEALTH_PRIVATE_21_SOURCE_MAP_PASS")

def verify(project:Path,place:Path,receipt:Path):
    project=project.resolve(strict=True)
    current=mapped(json.loads(project.read_text(encoding="utf-8")),project.parent)
    data=json.loads(receipt.read_text(encoding="utf-8"))
    assert len(current)==data["script_count"]==21
    actual={}
    tree=ET.fromstring(place.read_bytes())
    for node in tree.iter("Item"):
        kind=node.attrib.get("class")
        if kind not in ("Script","LocalScript","ModuleScript"):continue
        props=node.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        assert name not in actual,name
        content=props.findtext("ProtectedString[@name='Source']")
        if content is None:content=props.findtext("string[@name='Source']")
        assert content is not None,name
        actual[name]=(kind,content.replace("\r\n","\n"))
    assert set(actual)==set(current), (sorted(set(current)-set(actual)), sorted(set(actual)-set(current)))
    for name,(kind,file) in current.items():
        assert kind==actual[name][0],name
        assert file.read_text(encoding="utf-8").replace("\r\n","\n")==actual[name][1],name
        assert hashlib.sha256(file.read_bytes()).hexdigest()==data["source_sha256"][name],name
    data["private_place_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    data["native_21_source_pending_or_completed_by_workflow"]=True
    data["rojo_source_exact"]=True
    receipt.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ_HUMAN_STEALTH_PRIVATE_ROJO_21_OF_21_EXACT_PASS",place.stat().st_size)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",required=True,type=Path)
    ap.add_argument("--candidate",type=Path)
    ap.add_argument("--receipt",required=True,type=Path)
    ap.add_argument("--verify-place",type=Path)
    a=ap.parse_args()
    if a.verify_place:verify(a.project,a.verify_place,a.receipt)
    else:
        assert a.candidate
        compose(a.project,a.candidate,a.receipt)
if __name__=="__main__":main()
