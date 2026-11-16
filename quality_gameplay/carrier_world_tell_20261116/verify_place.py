#!/usr/bin/env python3
"""Rojo .rbxlx EXACT Luau source/class readback for isolated GQ 23-source candidate."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def verify(project:Path,place:Path,receipt:Path):
    project=project.resolve(strict=True)
    place=place.resolve(strict=True)
    tree=json.loads(project.read_text(encoding="utf-8"))["tree"]
    expected={}
    def scan(node):
        for name,child in node.items():
            if name.startswith("$") or not isinstance(child,dict):
                continue
            if "$path" in child:
                source=(project.parent/child["$path"]).resolve(strict=True)
                typ=("Script" if source.name.endswith(".server.luau")
                     else ("LocalScript" if source.name.endswith(".client.luau") else "ModuleScript"))
                assert name not in expected, f"duplicate source {name}"
                expected[name]=(typ,source.read_text(encoding="utf-8").replace("\r\n","\n"))
            else:
                scan(child)
    scan(tree)
    assert len(expected)==23, f"wrong source count {len(expected)}"
    actual={}
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        typ=item.attrib.get("class")
        if typ not in ("Script","LocalScript","ModuleScript"):
            continue
        props=item.find("Properties")
        if props is None:
            continue
        name=props.findtext("string[@name='Name']")
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source=props.findtext("string[@name='Source']")
        assert name and source is not None and name not in actual, f"invalid/duplicate {name}"
        actual[name]=(typ,source.replace("\r\n","\n"))
    assert expected==actual, {
        "missing":sorted(set(expected)-set(actual)),
        "extra":sorted(set(actual)-set(expected)),
        "changed":sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k]),
    }
    old=json.loads(receipt.read_text(encoding="utf-8"))
    assert old["private_source_count"]==23
    assert old["official_rc_integrated"] is False
    old["private_place_bytes"]=place.stat().st_size
    old["private_place_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    old["rojo_source_class_exact"]=23
    old["real_roblox_studio_play"]="NOT_RUN"
    old["android_mobile"]="NOT_RUN"
    old["official_rc_adoption"]="NOT_RUN"
    receipt.write_text(json.dumps(old,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRIVATE_ROJO_SOURCE_CLASS_EXACT_23_OF_23_PASS",old["private_place_bytes"],old["private_place_sha256"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    verify(a.project,a.place,a.receipt)
