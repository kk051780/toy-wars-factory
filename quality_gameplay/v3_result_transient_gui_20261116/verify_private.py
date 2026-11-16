#!/usr/bin/env python3
"""Read back genuine PRIVATE Rojo XML and verify 22/23 Script source/class exactly."""
import argparse, hashlib, json
from pathlib import Path
from xml.etree import ElementTree as ET

def verify(folder:Path,place:Path):
 project=json.loads((folder/"private.project.json").read_text())
 receipt=json.loads((folder/"receipt.json").read_text())
 expected={}
 def visit(node):
  for name,value in node.items():
   if not isinstance(value,dict): continue
   if "$path" in value:
    file=folder/value["$path"]
    cls="Script" if file.name.endswith(".server.luau") else (
        "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
    if name in expected:raise AssertionError("duplicate expected script "+name)
    expected[name]=(cls,file.read_text(encoding="utf-8"))
   else:visit(value)
 visit(project["tree"])
 assert len(expected)==receipt["count"]
 actual={}
 for item in ET.parse(place).iter("Item"):
  cls=item.attrib.get("class")
  if cls not in ("Script","ModuleScript","LocalScript"):continue
  props=item.find("Properties")
  if props is None:raise AssertionError("missing script properties")
  name=next((p.text for p in props if p.attrib.get("name")=="Name"),None)
  source=next((p.text or "" for p in props if p.attrib.get("name")=="Source"),None)
  if name in actual:raise AssertionError("duplicate script "+str(name))
  actual[name]=(cls,source)
 if set(expected)!=set(actual):raise AssertionError("source set mismatch")
 for k,v in expected.items():
  if actual[k]!=v:raise AssertionError("Source/Class drift "+k)
 result={"mode":receipt["mode"],"source_count":len(expected),
         "place_bytes":place.stat().st_size,
         "place_sha256":hashlib.sha256(place.read_bytes()).hexdigest()}
 (folder/"place_proof.json").write_text(json.dumps(result,indent=2)+"\n")
 print(f"GQ_RESULT_PRIVATE_{result['mode']}_{len(expected)}_ROJO_SOURCE_EXACT_PASS place_bytes={result['place_bytes']} sha256={result['place_sha256']}")

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--folder",type=Path,required=True);p.add_argument("--place",type=Path,required=True)
 a=p.parse_args();verify(a.folder,a.place)
