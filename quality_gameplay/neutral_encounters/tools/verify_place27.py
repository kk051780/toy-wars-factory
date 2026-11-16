#!/usr/bin/env python3
"""Source-exact Rojo XML verification for unpublished EGGRUMBLE 27-script candidate."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def walk(project: Path, node, chain=()):
    if isinstance(node,dict):
        if "$path" in node:
            p=(project.parent/node["$path"]).resolve(strict=True)
            yield (chain[-1], p, chain)
        else:
            for name, child in node.items():
                if not name.startswith("$"):
                    yield from walk(project,child,chain+(name,))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--place",type=Path,required=True)
    args=ap.parse_args()
    project=args.project.resolve(strict=True)
    place=args.place.resolve(strict=True)
    tree=json.loads(project.read_text(encoding="utf-8"))["tree"]
    receipt=json.loads((project.parent/"ENCOUNTER_SOURCE_RECEIPT.json").read_text(encoding="utf-8"))
    expected={}
    for name,p,chain in walk(project,tree):
        assert name not in expected,name
        expected_class=("Script" if p.name.endswith(".server.luau") else
          "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
        expected[name]=(expected_class,p.read_text(encoding="utf-8").replace("\r\n","\n"))
        assert hashlib.sha256(p.read_bytes()).hexdigest()==receipt["source_sha256"][name],name
    assert len(expected)==27
    assert receipt["original_scripts_exact_unchanged"]==25
    actual={}
    for node in ET.parse(place).getroot().iter("Item"):
        cls=node.attrib.get("class")
        if cls not in ("Script","LocalScript","ModuleScript"):continue
        props=node.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        assert name and name not in actual,name
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        assert source is not None,("missing Lua Source",name)
        actual[name]=(cls,source.replace("\r\n","\n"))
    assert actual==expected, {
      "missing":sorted(set(expected)-set(actual)),
      "extra":sorted(set(actual)-set(expected)),
      "different":sorted(k for k in set(actual)&set(expected) if actual[k]!=expected[k])
    }
    data=place.read_bytes()
    report={"status":"PRIVATE_SOURCE_EXACT_27_PASS_NOT_RC",
            "script_count":27,"place_bytes":len(data),
            "place_sha256":hashlib.sha256(data).hexdigest(),
            "official_rc_adoption":0,"studio":"NOT_TESTED","android":"NOT_TESTED"}
    (place.parent/"PLACE_27_RECEIPT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("EGGRUMBLE_PRIVATE_PLACE_27_SOURCE_EXACT_PASS",len(data),report["place_sha256"])
if __name__=="__main__":main()
