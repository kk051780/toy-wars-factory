#!/usr/bin/env python3
"""Read back exact Script/LocalScript/ModuleScript SOURCE from a real Rojo Place."""
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

def expected_script_map(project_node, folder):
    out={}
    def walk(node):
        if not isinstance(node,dict):
            return
        if "$path" in node:
            p=Path(node["$path"])
            name=p.name
            if name.endswith(".server.luau"):
                script_name=name[:-len(".server.luau")]
                cls="Script"
            elif name.endswith(".client.luau"):
                script_name=name[:-len(".client.luau")]
                cls="LocalScript"
            else:
                assert name.endswith(".luau"), name
                script_name=name[:-len(".luau")]
                cls="ModuleScript"
            assert script_name not in out, "duplicate source script name"
            out[script_name] = (cls,(folder/p).read_text(encoding="utf-8"))
            return
        for v in node.values():
            walk(v)
    walk(project_node)
    return out

def verify(folder,place):
    project=json.loads((folder/"private_v3.project.json").read_text(encoding="utf-8"))
    receipt=json.loads((folder/"source_lock_receipt.json").read_text(encoding="utf-8"))
    expected=expected_script_map(project["tree"],folder)
    assert len(expected)==receipt["mapped_script_count"]
    actual={}
    tree=ET.parse(place)
    for item in tree.iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):
            continue
        props=item.find("Properties")
        assert props is not None
        name=next((x.text for x in props if x.attrib.get("name")=="Name"),None)
        source=next((x.text or "" for x in props if x.attrib.get("name")=="Source"),None)
        assert name not in actual,f"duplicate script {name}"
        actual[name]=(cls,source)
    assert set(actual)==set(expected),f"Script set drift missing={set(expected)-set(actual)}, extra={set(actual)-set(expected)}"
    for name in expected:
        assert actual[name]==expected[name],f"Script Source/Class drift {name}"
    prefix="GQ528_PRIVATE_"+receipt["mode"]+"_"+str(len(expected))+"_ROJO_SOURCE_EXACT_PASS"
    print(prefix,place.stat().st_size,hashlib.sha256(place.read_bytes()).hexdigest())
    return prefix

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--folder",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    a=p.parse_args()
    verify(a.folder,a.place)

if __name__=="__main__":
    main()
