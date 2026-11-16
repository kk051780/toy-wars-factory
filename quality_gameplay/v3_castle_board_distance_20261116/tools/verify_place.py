#!/usr/bin/env python3
"""Verify the real Rojo XML embeds exactly the 21 selected original/overlay sources."""
import argparse
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

def script_nodes(root):
    out = {}
    for item in root.iter("Item"):
        if item.attrib.get("class") not in ("Script","ModuleScript","LocalScript"):
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = props.find("string[@name='Name']")
        source = props.find("string[@name='Source']")
        if source is None:
            source = props.find("ProtectedString[@name='Source']")
        if name is None or source is None or name.text is None:
            raise RuntimeError("Incomplete Rojo script node: class=" + repr(item.attrib.get("class"))
                + " props=" + repr([(t.tag, t.attrib.get("name"), len(t.text or "")) for t in props])
                + " name=" + repr(name.text if name is not None else None)
                + " source=" + repr(source is not None))
        if name.text in out:
            raise RuntimeError(f"Duplicate script name: {name.text}")
        out[name.text] = (item.attrib["class"], source.text or "")
    return out

def mapped_sources(project: Path):
    data=json.loads(project.read_text(encoding="utf-8"))
    out={}
    def visit(node):
        for key,value in node.items():
            if isinstance(value,dict):
                if "$path" in value:
                    p=(project.parent/value["$path"]).resolve()
                    if not p.is_file():
                        raise RuntimeError(f"Missing mapped source: {p}")
                    if key in out:
                        raise RuntimeError(f"Duplicate project name {key}")
                    suffix=p.name
                    cls="LocalScript" if suffix.endswith(".client.luau") else "Script" if suffix.endswith(".server.luau") else "ModuleScript"
                    out[key]=(cls,p.read_text(encoding="utf-8"))
                else:
                    visit(value)
    visit(data["tree"])
    return out

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",required=True,type=Path)
    parser.add_argument("--place",required=True,type=Path)
    args=parser.parse_args()
    expected=mapped_sources(args.project)
    if len(expected)!=21:
        raise RuntimeError(f"Wrong script mapping count: {len(expected)}")
    actual=script_nodes(ET.parse(args.place).getroot())
    if set(actual)!=set(expected):
        raise RuntimeError(f"Rojo source names drift: missing={set(expected)-set(actual)}, extra={set(actual)-set(expected)}")
    for name,(cls,source) in expected.items():
        real_cls,real_source=actual[name]
        if (cls,source)!=(real_cls,real_source):
            raise RuntimeError(f"Rojo class or source drift: {name}: expected={cls}/{len(source)}, actual={real_cls}/{len(real_source)}")
    print(f"GQ_WORLD_BOARD_ROJO_SOURCE_EXACT=PASS {len(actual)}/{len(expected)} (PRIVATE, NOT FORMAL RC)")
