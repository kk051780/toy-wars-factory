#!/usr/bin/env python3
"""Verify every compiled private Place source/class matches the 22 original/candidate files."""
import argparse, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def expected_scripts(project):
    p=project.parent
    tree=json.loads(project.read_text(encoding="utf-8"))["tree"]
    found={}
    def walk(branch):
        for name,node in branch.items():
            if name.startswith("$"): continue
            if "$path" in node:
                path=(p/node["$path"]).resolve(strict=True)
                kind="Script" if path.name.endswith(".server.luau") else (
                    "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
                assert name not in found
                found[name]=(kind,path.read_text(encoding="utf-8"))
            else:
                walk(node)
    walk(tree)
    assert len(found)==22, f"expected 22 source files, got {len(found)}"
    return found

def verify(project,place):
    expected=expected_scripts(project)
    root=ET.parse(place).getroot()
    actual={}
    for node in root.iter("Item"):
        kind=node.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"): continue
        props=node.find("Properties")
        if props is None: continue
        name=None;source=None
        for tag in props:
            if tag.get("name")=="Name": name=tag.text or ""
            if tag.get("name")=="Source": source=tag.text or ""
        if name in expected:
            assert name not in actual, f"duplicate script {name}"
            actual[name]=(kind,source)
    assert set(actual)==set(expected), f"missing/extra source: {set(expected)^set(actual)}"
    for name,(kind,src) in expected.items():
        otherKind,otherSrc=actual[name]
        assert kind==otherKind, f"{name} source CLASS mismatch {kind} vs {otherKind}"
        assert sha(src)==sha(otherSrc), f"{name} source text SHA mismatch"
    print("GQ_FIELD_EGG_PRIVATE22_ROJO_EXACT_PASS 22/22 classes+embedded text")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",required=True,type=Path)
    parser.add_argument("--place",required=True,type=Path)
    a=parser.parse_args()
    verify(a.project,a.place)
