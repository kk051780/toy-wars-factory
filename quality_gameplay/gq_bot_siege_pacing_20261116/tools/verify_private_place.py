#!/usr/bin/env python3
"""Verify actual Rojo .rbxlx Source + script class 22/22 against staged files."""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET


def flatten(node, out):
    if isinstance(node, dict):
        if "$path" in node:
            out[Path(node["$path"]).name] = node["$path"]
        for value in node.values():
            flatten(value, out)


def verify(folder: Path, place: Path):
    project = json.loads((folder / "private_v3.project.json").read_text())
    expected = {}
    paths = {}
    flatten(project["tree"], paths)
    for basename, rel in paths.items():
        stem = basename.replace(".server.luau", "").replace(".client.luau", "").replace(".luau", "")
        cls = ("Script" if ".server." in basename else
               "LocalScript" if ".client." in basename else "ModuleScript")
        expected[stem] = (cls, (folder / rel).read_text(encoding="utf-8"))
    assert len(expected) == 22, "expected exactly 22 scripts"

    xml = ET.parse(place)
    actual = {}
    for item in xml.iter("Item"):
        cls = item.attrib.get("class")
        if cls not in {"ModuleScript", "Script", "LocalScript"}:
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = next((e.text for e in props if e.attrib.get("name") == "Name"), None)
        source = next((e.text or "" for e in props if e.attrib.get("name") == "Source"), None)
        if name is not None and source is not None:
            assert name not in actual, f"duplicate script {name}"
            actual[name] = (cls, source)
    assert set(actual) == set(expected), f"script names drift: missing={set(expected)-set(actual)} extra={set(actual)-set(expected)}"
    for name, pair in expected.items():
        assert actual[name] == pair, f"Source/class drift {name}"
    print("GQ_BOT_SIEGE_PRIVATE_ROJO_SOURCE_EXACT_22_PASS", place.stat().st_size, "bytes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", type=Path, required=True)
    ap.add_argument("--place", type=Path, required=True)
    a = ap.parse_args()
    verify(a.folder, a.place)
