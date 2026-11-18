#!/usr/bin/env python3
"""Fix the canonical Real55 V3 host's runtime class; preserve all 55 source bytes."""
import argparse, hashlib, json, shutil
from pathlib import Path
from xml.etree import ElementTree as ET

HOST="ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
ORIGINAL="sources/ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.luau"
RUNNABLE="sources/ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview.server.luau"
OFFICIAL_SHA="a6020867fac80fa3b2ca47478625873fc6f3678e"

def flatten(project):
    found={}
    def rec(tree,prefix=""):
        for name,node in tree.items():
            if name.startswith("$") or not isinstance(node,dict): continue
            key=(prefix+"/"+name) if prefix else name
            if "$path" in node: found[key]=node["$path"]
            rec(node,key)
    rec(project["tree"])
    return found

def inspect(place,expected):
    found={}
    def visit(item,base):
        props=item.find("Properties")
        name=props.find("string[@name='Name']")
        assert name is not None and name.text
        key=(base+"/"+name.text) if base else name.text
        kind=item.attrib["class"]
        if kind in ("Script","LocalScript","ModuleScript"):
            source=props.find("ProtectedString[@name='Source']")
            if source is None: source=props.find("string[@name='Source']")
            assert key not in found
            found[key]=(kind,(source.text or "") if source is not None else "")
        for ch in item.findall("Item"):visit(ch,key)
    for item in ET.parse(place).getroot().findall("Item"):visit(item,"")
    assert len(found)==55,("SOURCE_COUNT",len(found))
    kind,content=found[HOST]
    assert kind==expected,("P0_HOST_NOT_AUTOSTARTED",kind,expected)
    assert "local function startSession(" in content
    assert "EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW" in content
    assert "Players.PlayerAdded:Connect" in content
    for key,(cls,source) in found.items():
        if key!=HOST:assert "EGGRUMBLE_LobbyCastleModesPreview" not in source,("UNEXPECTED_HOST_IMPORT",key)
    return hashlib.sha256(content.encode()).hexdigest()

def repair(root,out):
    project=json.loads((root/"EGGRUMBLE_REAL55.project.json").read_text())
    receipt=json.loads((root/"B_REAL55_RECEIPT.json").read_text())
    original=flatten(project)
    assert len(original)==55 and original[HOST]==ORIGINAL
    assert receipt["selected_official_branch_sha"]==OFFICIAL_SHA
    assert receipt["selected_real55_count"]==55
    before=inspect(root/"EGGRUMBLE_REAL55.rbxlx","ModuleScript")
    assert hashlib.sha256((root/ORIGINAL).read_bytes()).hexdigest()==before
    for key,src in original.items():
        dst=out/(RUNNABLE if key==HOST else src)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/src,dst)
        assert (root/src).read_bytes()==dst.read_bytes(),("BYTE_DRIFT",key)
    project["name"]="EGGRUMBLE_REAL55_HOST_ACTIVE_CANDIDATE_NOT_OFFICIAL"
    project["tree"]["ServerScriptService"]["EGGRUMBLE_LobbyCastleModesPreview"]["$path"]=RUNNABLE
    selected=flatten(project)
    assert len(selected)==55
    assert [name for name in original if original[name]!=selected[name]]==[HOST]
    (out/"EGGRUMBLE_REAL55_HOST_ACTIVE.project.json").write_text(json.dumps(project,indent=2)+"\n")
    result={"feature_id":"GQ8_REAL55_HOST_RUNTIME_AUTOSTART_P0_20261119",
            "base_official_sha":OFFICIAL_SHA,"source_count":55,
            "source_bytes_changed":0,"other_54_sources_byte_exact":True,
            "old_host_class":"ModuleScript","new_host_class":"Script",
            "host_source_sha256":before,"formal_rc_adopted":False,
            "studio_solo":"NOT_TESTED","studio_2client":"NOT_TESTED",
            "android_15min":"NOT_TESTED","fun":"NO_GO",
            "public_publish":False,"paid_trade":False}
    (out/"HOST_ACTIVE_RECEIPT.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--verify",type=Path)
    p.add_argument("--original",action="store_true")
    a=p.parse_args()
    if a.verify:
        print(inspect(a.verify,"ModuleScript" if a.original else "Script"))
    else:
        assert a.base is not None and a.out is not None
        print(json.dumps(repair(a.base,a.out)))
