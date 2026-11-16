#!/usr/bin/env python3
"""Independent source/class exact check on unpublished PRIVATE 27-source Rojo Place."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def verify(out: Path)->dict:
    project=json.loads((out/"EGGRUMBLE_V3_PRIVATE27.project.json").read_text(encoding="utf-8"))
    receipt=json.loads((out/"SOURCE_RECEIPT_27.json").read_text(encoding="utf-8"))
    if receipt.get("source_count")!=27 or receipt.get("guard_sites")!=21:
        raise ValueError("incomplete full-8-domain private source")
    if receipt.get("official_rc_adopted") is not False or receipt.get("enabled_in_public_server") is not False:
        raise ValueError("RC/public authorization must be disabled")
    expected={}
    def map_sources(tree):
        for name,value in tree.items():
            if name.startswith("$") or not isinstance(value,dict): continue
            if "$path" in value:
                path=out/value["$path"]
                if not path.is_file() or name in expected:
                    raise ValueError(f"missing or duplicated source {name}")
                klass="LocalScript" if path.name.endswith(".client.luau") else (
                    "Script" if path.name.endswith(".server.luau") else "ModuleScript")
                expected[name]=(klass,path.read_text(encoding="utf-8").replace("\r\n","\n"))
            else:map_sources(value)
    map_sources(project["tree"])
    if len(expected)!=27:
        raise ValueError(f"expected 27 source nodes, found {len(expected)}")
    place=out/"EGGRUMBLE_V3_PRIVATE27_UNPUBLISHED.rbxlx"
    actual={}
    for obj in ET.fromstring(place.read_bytes()).iter("Item"):
        klass=obj.get("class")
        if klass not in {"Script","LocalScript","ModuleScript"}:continue
        prop=obj.find("Properties")
        if prop is None:continue
        name=prop.findtext("string[@name='Name']")
        code=prop.findtext("ProtectedString[@name='Source']")
        if code is None:code=prop.findtext("string[@name='Source']")
        if name is None or code is None or name in actual:
            raise ValueError(f"unknown, empty or duplicate embedded Source: {name}")
        actual[name]=(klass,code.replace("\r\n","\n"))
    if expected!=actual:
        raise ValueError(json.dumps({
            "missing":sorted(set(expected)-set(actual)),
            "extra":sorted(set(actual)-set(expected)),
            "changed":[k for k in expected.keys()&actual.keys() if expected[k]!=actual[k]]
        }))
    path=out/"EGGRUMBLE_V3_PRIVATE27_UNPUBLISHED.rbxlx"
    info={
        "source_exact": "PASS_27_OF_27",
        "original_count":26, "separate_private_gate_count":1,
        "private_place_bytes":path.stat().st_size,
        "private_place_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "official_rc_integrated":False,"studio_runtime":"NOT_TESTED","android":"NOT_TESTED"}
    (out/"PLACE_RECEIPT_27.json").write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return info

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    print(json.dumps(verify(args.out),ensure_ascii=False))
