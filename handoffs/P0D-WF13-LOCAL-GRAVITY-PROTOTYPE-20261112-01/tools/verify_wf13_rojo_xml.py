#!/usr/bin/env python3
"""WF13 true Rojo .rbxlx byte-for-byte source map audit. NOT Studio runtime."""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCRIPTS = {
    "ServerScriptService/WF13Demo": ("Script", "src/WF13Demo.server.luau"),
    "ServerScriptService/WF13Policy": ("ModuleScript", "src/WF13Policy.luau"),
    "ServerScriptService/WF13ZoneController": ("ModuleScript", "src/WF13ZoneController.luau"),
    "ServerScriptService/WF13Scene": ("ModuleScript", "src/WF13Scene.luau"),
}
SCRIPT_CLASSES = {"Script", "ModuleScript", "LocalScript"}

class IntegrityError(ValueError):
    pass

def require(value, reason):
    if not value:
        raise IntegrityError(reason)

def prop(item, name):
    p = item.find("Properties")
    if p is None:
        return None
    for ch in p:
        if ch.get("name") == name:
            return ch.text or ""
    return None

def item_paths(xml):
    try:
        doc = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise IntegrityError("XML_MALFORMED") from exc
    require(doc.tag == "roblox", "RBXLX_ROOT")
    items = []
    def walk(node, names):
        for ch in node:
            if ch.tag != "Item":
                continue
            cls = ch.get("class")
            name = prop(ch, "Name")
            require(cls and name, "NAME_OR_CLASS_MISSING")
            path = names if cls == "DataModel" else (*names, name)
            items.append(("/".join(path), cls, prop(ch, "Source")))
            walk(ch, path)
    walk(doc, ())
    return items

def verify(xml, root=ROOT):
    manifest = json.loads((root / "BUILD_MANIFEST.json").read_text("utf-8"))
    listed = {r["path"]: r for r in manifest["files"]}
    for _, source_path in EXPECTED_SCRIPTS.values():
        require(source_path in listed, "SOURCE_NOT_IN_LOCKED_MANIFEST")
        raw = (root / source_path).read_bytes()
        r = listed[source_path]
        require(hashlib.sha256(raw).hexdigest() == r["sha256"]
                and len(raw) == r["size"], "LOCKED_SOURCE_MISMATCH")
    scripts = [(p,c,s) for p,c,s in item_paths(xml) if c in SCRIPT_CLASSES]
    require(len(scripts) == 4, "EXPECTED_4_AND_ONLY_4_SCRIPTS")
    observed = set()
    for p,c,s in scripts:
        require(p not in observed, "DUPLICATE_SCRIPT_PATH")
        require(p in EXPECTED_SCRIPTS, "UNLISTED_SCRIPT_PATH: " + p)
        cls, path = EXPECTED_SCRIPTS[p]
        require(c == cls, "SCRIPT_CLASS_CHANGED")
        require(s is not None, "NO_SERIALIZED_SOURCE")
        require(s.encode("utf-8") == (root / path).read_bytes(),
                "SCRIPT_SOURCE_BYTES_CHANGED: " + p)
        observed.add(p)
    require(observed == set(EXPECTED_SCRIPTS), "SCRIPT_MISSING")
    require(sum(c == "Script" for _,c,_ in scripts) == 1, "DUPLICATE_EXECUTABLE_AUTHORITY")
    require(sum(c == "ModuleScript" for _,c,_ in scripts) == 3, "MISSING_MODULE")
    require("ENABLE_WF13_ISOLATED_DEMO = false" in scripts[
        next(i for i,x in enumerate(scripts) if x[0] == "ServerScriptService/WF13Demo")
    ][2], "DEMO_MUST_BE_DISABLED")
    require(not any(c == "LocalScript" for _,c,_ in scripts), "NO_CLIENT_AUTHORITY")
    return {"actual_place_sha256": hashlib.sha256(xml).hexdigest(),
            "actual_place_bytes": len(xml), "original_source_paths": sorted(observed),
            "script_count": 4, "executable_game_script_count": 1,
            "module_script_count": 3, "demo_enabled": False,
            "real_roblox_studio_tested": False, "mobile_tested": False,
            "two_clients_tested": False, "published": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--place", required=True)
    p.add_argument("--receipt", required=True)
    a = p.parse_args()
    raw = Path(a.place).read_bytes()
    require(len(raw) > 5000, "RBXLX_TOO_SMALL")
    receipt = verify(raw)
    Path(a.receipt).write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
    print("WF13_REAL_ROJO_4_OF_4_LUAU_BYTES_PASS")
    print("WF13_DEMO_DISABLED_SINGLE_SERVER_SCRIPT_PASS")
    print("WF13_RBXLX_SHA256=" + receipt["actual_place_sha256"])
    print("WF13_RBXLX_BYTES=" + str(receipt["actual_place_bytes"]))
    print("WF13_REAL_STUDIO_NOT_TESTED")

if __name__ == "__main__":
    main()
