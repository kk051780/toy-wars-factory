#!/usr/bin/env python3
"""Read back genuine Rojo .rbxlx Lua script bodies and exact 28 source-class map."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

project = Path(sys.argv[1]).resolve(strict=True)
place = Path(sys.argv[2]).resolve(strict=True)
manifest = json.loads(project.read_text(encoding="utf-8"))
base = project.parent
actual = {}
for item in ET.fromstring(place.read_bytes()).iter("Item"):
    klass = item.attrib.get("class")
    if klass not in ("Script", "LocalScript", "ModuleScript"):
        continue
    props = item.find("Properties")
    if props is None:
        continue
    name = props.findtext("string[@name='Name']")
    src = props.findtext("ProtectedString[@name='Source']")
    if src is None:
        src = props.findtext("string[@name='Source']")
    if name:
        assert name not in actual, ("DUPLICATE_NAME_IN_XML", name)
        actual[name] = (klass, (src or "").replace("\r\n","\n"))
expected = {}
def walk(node, parent=()):
    for name, entry in node.items():
        if name.startswith("$") or not isinstance(entry, dict):
            continue
        if "$path" in entry:
            assert name not in expected, ("DUPLICATE_NAME_IN_MAP", name)
            source = (base / entry["$path"]).resolve(strict=True).read_text(encoding="utf-8").replace("\r\n","\n")
            klass = "LocalScript" if entry["$path"].endswith(".client.luau") else ("Script" if entry["$path"].endswith(".server.luau") else "ModuleScript")
            expected[name] = (klass, source)
        else:
            walk(entry,parent+(name,))
walk(manifest["tree"])
assert len(expected)==28 and len(actual)==28, ("SOURCE_COUNT",len(expected),len(actual))
assert expected.keys()==actual.keys(), ("NAME_MISMATCH",expected.keys()-actual.keys(),actual.keys()-expected.keys())
for name in expected:
    assert expected[name]==actual[name], ("SOURCE_CLASS_MISMATCH", name)
receipt = json.loads((project.parent / "GQ_COMBO28_SOURCE_RECEIPT.json").read_text())
assert receipt["mapped_sources"]==28 and receipt["original_count"]==26 and receipt["added_count"]==2
receipt["place_bytes"] = place.stat().st_size
receipt["place_sha256"] = hashlib.sha256(place.read_bytes()).hexdigest()
(project.parent / "GQ_COMBO28_SOURCE_RECEIPT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
print("GQ_28_ROJO_SOURCE_AND_CLASS_EXACT_PASS",place.stat().st_size)
