#!/usr/bin/env python3
"""Verify exact 23 Luau sources in a *private* Rojo rbxlx. No Studio claim."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

project = Path(sys.argv[1]).resolve(strict=True)
place = Path(sys.argv[2]).resolve(strict=True)
data = json.loads(project.read_text(encoding="utf-8"))
wanted = {}

def visit(node):
    for name, child in node.items():
        if name.startswith("$") or not isinstance(child, dict):
            continue
        if "$path" in child:
            src = (project.parent / child["$path"]).resolve(strict=True)
            assert name not in wanted, ("DUPLICATE_MAP", name)
            wanted[name] = src.read_text(encoding="utf-8").replace("\r\n", "\n")
        else:
            visit(child)
visit(data["tree"])
assert len(wanted) == 23, ("SOURCE_COUNT", len(wanted))
actual = {}
for item in ET.fromstring(place.read_bytes()).iter("Item"):
    if item.attrib.get("class") not in ("Script", "LocalScript", "ModuleScript"):
        continue
    props = item.find("Properties")
    if props is None:
        continue
    name = props.findtext("string[@name='Name']")
    source = props.findtext("ProtectedString[@name='Source']")
    if source is None:
        source = props.findtext("string[@name='Source']")
    if name:
        assert name not in actual, ("DUPLICATE_GAME_SOURCE", name)
        actual[name] = (source or "").replace("\r\n", "\n")
assert wanted.keys() == actual.keys(), (set(wanted)-set(actual), set(actual)-set(wanted))
for name, source in wanted.items():
    assert actual[name] == source, ("SOURCE_BYTES_MISMATCH", name)
receipt = {
    "scope": "PRIVATE_STUDIO_SOURCE_ONLY",
    "original_v3_git_head": "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
    "scripts": 23,
    "original_scripts": 21,
    "addon_scripts": 2,
    "place_bytes": place.stat().st_size,
    "place_sha256": hashlib.sha256(place.read_bytes()).hexdigest(),
    "source_sha256": {k:hashlib.sha256(v.encode()).hexdigest() for k,v in wanted.items()},
    "official_rc_integrated": False,
    "studio_play": "NOT_TESTED",
    "android": "NOT_TESTED",
    "art_fun": "NO_GO",
    "owner_accepted": False,
}
out = place.with_suffix(".receipt.json")
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print("GQ_ROUND_FENCE_PRIVATE23_SOURCE_EXACT_PASS", place.stat().st_size, "bytes")
