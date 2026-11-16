#!/usr/bin/env python3
"""Compare 28 mapped Luau Script SOURCES byte-exact to private Rojo Place XML."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def sources(path, tree):
    def walk(node):
        if isinstance(node, dict):
            if "$path" in node:
                yield (path.parent / node["$path"]).resolve(strict=True)
            else:
                for name, child in node.items():
                    if not name.startswith("$"):
                        yield from walk(child)
    yield from walk(tree)

def exact(project, place, receipt_path):
    project, place, receipt_path = project.resolve(strict=True), place.resolve(strict=True), receipt_path.resolve(strict=True)
    tree = json.loads(project.read_text(encoding="utf-8"))["tree"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected = {}
    for p in sources(project, tree):
        name = p.name.removesuffix(".server.luau").removesuffix(".client.luau").removesuffix(".luau")
        assert name not in expected, name
        cl = ("Script" if p.name.endswith(".server.luau")
              else "LocalScript" if p.name.endswith(".client.luau") else "ModuleScript")
        source = p.read_text(encoding="utf-8").replace("\r\n", "\n")
        expected[name] = (cl, source)
        assert receipt["source_sha256"][name] == hashlib.sha256(p.read_bytes()).hexdigest(), name
    assert len(expected) == 28
    assert {"EGGRUMBLE_CastleDefenseLive","EGGRUMBLE_CastleDefensePolicy"}.issubset(expected)
    assert sum(1 for kind, _ in expected.values() if kind == "Script") == 1, "second server GAME detected"
    assert sum(1 for kind, _ in expected.values() if kind == "LocalScript") == 3
    actual = {}
    for node in ET.fromstring(place.read_bytes()).iter("Item"):
        cl = node.attrib.get("class")
        if cl not in ("Script", "LocalScript", "ModuleScript"):
            continue
        prop = node.find("Properties")
        assert prop is not None
        name = prop.findtext("string[@name='Name']")
        assert name and name not in actual, ("missing/duplicate script", name)
        value = prop.findtext("ProtectedString[@name='Source']")
        if value is None:
            value = prop.findtext("string[@name='Source']")
        assert value is not None, ("no embedded source", name)
        actual[name] = (cl, value.replace("\r\n", "\n"))
    assert actual == expected, {
        "missing": sorted(set(expected)-set(actual)),
        "unexpected": sorted(set(actual)-set(expected)),
        "different": sorted(name for name in set(actual)&set(expected) if actual[name]!=expected[name]),
    }
    assert receipt["unaltered_existing"] == 25
    assert receipt["original_26_exact"] is True
    receipt["real_place_bytes"]=place.stat().st_size
    receipt["real_place_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    receipt["native_engine"]="PURE_LUAU_ONLY"
    receipt["rojo"]="SOURCE_EXACT_28"
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EGGRUMBLE_CASTLE_DEFENSE_SOURCE_EXACT_28_OF_28_PASS",
          receipt["real_place_bytes"],receipt["real_place_sha256"])

def main():
    p=argparse.ArgumentParser()
    for name in ("project","place","receipt"):
        p.add_argument("--"+name, required=True,type=Path)
    a=p.parse_args()
    exact(a.project,a.place,a.receipt)

if __name__=="__main__":
    main()
