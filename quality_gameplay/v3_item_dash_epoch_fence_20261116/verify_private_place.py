#!/usr/bin/env python3
"""Verify one real, unpublished private Rojo .rbxlx against exact 21/22 original source bytes."""
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

def read_expected(project: dict, folder: Path) -> dict:
    expected={}
    def visit(node):
        if not isinstance(node,dict): return
        if "$path" in node:
            p=Path(node["$path"])
            name=p.name.removesuffix(".server.luau").removesuffix(".client.luau").removesuffix(".luau")
            cls="Script" if p.name.endswith(".server.luau") else ("LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
            if name in expected: raise AssertionError(f"duplicate expected script {name}")
            expected[name]=(cls,(folder/p).read_text())
        else:
            for v in node.values(): visit(v)
    visit(project["tree"])
    return expected

def verify(folder: Path, place: Path) -> dict:
    manifest=json.loads((folder/"source_lock_receipt.json").read_text())
    project=json.loads((folder/"private_v3.project.json").read_text())
    expected=read_expected(project,folder)
    assert len(expected)==manifest["source_count"] in (21,22)
    found={}
    for item in ET.parse(place).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"): continue
        props=item.find("Properties")
        assert props is not None
        name=next((p.text for p in props if p.attrib.get("name")=="Name"),None)
        source=next((p.text or "" for p in props if p.attrib.get("name")=="Source"),None)
        assert name and name not in found, f"extra/duplicate script {name}"
        found[name]=(cls,source)
    assert set(found)==set(expected),f"source list mismatch missing={set(expected)-set(found)} extra={set(found)-set(expected)}"
    for name, entry in expected.items():
        assert found[name]==entry, f"class/source mismatch {name}"
    receipt={"script_count":len(found),"place_bytes":place.stat().st_size,
        "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest(),"enabled":manifest["enabled"],
        "formal_rc":False,"studio_tested":False}
    (folder/"place_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(f"GQ_DASH_PRIVATE_ROJO_{len(found)}_SOURCE_EXACT_PASS bytes={receipt['place_bytes']} sha256={receipt['place_sha256']}")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--folder",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    args=p.parse_args()
    verify(args.folder,args.place)
