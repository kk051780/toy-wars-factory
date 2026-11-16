#!/usr/bin/env python3
"""Assemble/verify a true Rojo V3 private Place with 20 unmodified author scripts.

This does NOT merge/publish or write the canonical RC.  Both ON and OFF builds
use the exact same 21-source original author project and only overlay its
single Combat ModuleScript in a generated temporary project.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

from compose import AUTHOR_REL, AUTHOR_BLOB, git_blob_sha, compose

ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = ROOT / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
ORIGINAL_PROJECT = SOURCE_ROOT / "EGGRUMBLE_V3_STUDIO.project.json"
ORIGINAL_PROJECT_BLOB = "1d3e5bdc9ac2ac3fb6e70110ff3c6636d70fc714"
SCRIPTS = {"Script", "ModuleScript", "LocalScript"}

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def entries(node: dict, prefix: tuple[str, ...] = ()):
    for name, value in node.items():
        if not isinstance(value, dict):
            continue
        if "$path" in value:
            yield prefix + (name,), value
        else:
            yield from entries(value, prefix + (name,))

def get_parent(tree: dict, parts: tuple[str, ...]) -> dict:
    cur = tree
    for p in parts[:-1]:
        cur = cur[p]
    return cur

def make(output: Path, enabled: bool) -> tuple[Path, Path]:
    data = ORIGINAL_PROJECT.read_bytes()
    if git_blob_sha(data) != ORIGINAL_PROJECT_BLOB:
        raise ValueError("RED_SOURCE_LOCK: original 21 source project changed")
    root_project = json.loads(data)
    original_scripts = list(entries(root_project["tree"]))
    if len(original_scripts) != 21:
        raise ValueError("RED_SOURCE_LOCK: original 21 script slots changed")
    original = (ROOT / AUTHOR_REL).read_bytes()
    if git_blob_sha(original) != AUTHOR_BLOB:
        raise ValueError("RED_SOURCE_LOCK: original Combat changed")
    output.mkdir(parents=True, exist_ok=True)
    mode = "ON" if enabled else "OFF"
    patched = compose(original, enabled=enabled)
    overlay = output / ("GQ_Caster_" + mode + "_Combat.luau")
    overlay.write_bytes(patched)
    trial = copy.deepcopy(root_project)
    trial["name"] = "GQ_DEAD_CASTER_PRIVATE_" + mode + "_NOT_OFFICIAL_RC"
    manifest = {"mode": mode, "original_project_blob": ORIGINAL_PROJECT_BLOB,
                "original_combat_blob": AUTHOR_BLOB, "original21": 21,
                "source_exact": {}, "no_main_or_rc_write": True,
                "engine_studio": "NOT_TESTED", "official_rc": False}
    seen_names = set()
    for parts, node in entries(trial["tree"]):
        name = parts[-1]
        if name in seen_names:
            raise ValueError("RED_DUPLICATE_SCRIPT: " + name)
        seen_names.add(name)
        input_file = SOURCE_ROOT / node["$path"]
        if not input_file.is_file():
            raise ValueError("RED_SOURCE_MISSING: " + str(input_file))
        expected_bytes = input_file.read_bytes()
        if name == "EGGRUMBLE_SevenRoleCombat":
            expected_bytes = patched
            input_file = overlay
        node["$path"] = os.path.relpath(input_file, output).replace(os.sep, "/")
        manifest["source_exact"][name] = {
            "class": ("LocalScript" if ".client." in input_file.name else
                      "Script" if ".server." in input_file.name else "ModuleScript"),
            "sha256": sha256(expected_bytes),
            "bytes": len(expected_bytes)
        }
    if len(manifest["source_exact"]) != 21:
        raise ValueError("RED_SOURCE_COUNT")
    project = output / ("GQ_CASTER_PRIVATE_" + mode + "21.project.json")
    project.write_text(json.dumps(trial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = output / ("GQ_CASTER_PRIVATE_" + mode + "21_receipt.json")
    receipt.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return project, receipt

def verify_place(place: Path, receipt: Path) -> None:
    proof = json.loads(receipt.read_text(encoding="utf-8"))
    actual: dict[str, dict] = {}
    tree = ET.parse(place)
    for item in tree.getroot().iter("Item"):
        if item.get("class") not in SCRIPTS:
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_NO_PROPS")
        name_node = props.find("./string[@name='Name']")
        source_node = next((s for s in props if s.get("name") == "Source"), None)
        if name_node is None or source_node is None:
            raise ValueError("RED_NO_SCRIPT_SOURCE")
        name = name_node.text or ""
        if name in actual:
            raise ValueError("RED_DUPLICATE_IN_PLACE: " + name)
        content = (source_node.text or "").encode("utf-8")
        actual[name] = {"class": item.get("class"), "sha256": sha256(content),
                        "bytes": len(content)}
    expect = proof["source_exact"]
    if actual != expect:
        absent = sorted(set(expect) - set(actual))
        extra = sorted(set(actual) - set(expect))
        changed = sorted(k for k in set(expect)&set(actual) if expect[k] != actual[k])
        raise ValueError(f"RED_PLACE_SOURCE_EXACT: absent={absent} extra={extra} changed={changed}")
    print(f"PRIVATE_PLACE_{proof['mode']}21_SOURCE_CLASS_EXACT_PASS",
          "source_count",len(actual),"place_bytes",place.stat().st_size,
          "place_sha256",sha256(place.read_bytes()))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--verify-on", type=Path)
    parser.add_argument("--verify-off", type=Path)
    opts = parser.parse_args()
    output = opts.out_dir.resolve()
    on, onreceipt = make(output, True)
    off, offreceipt = make(output, False)
    print("PRIVATE21_ON_OFF_PROJECT_COMPOSED", on, off)
    if opts.verify_on:
        verify_place(opts.verify_on, onreceipt)
    if opts.verify_off:
        verify_place(opts.verify_off, offreceipt)

if __name__ == "__main__":
    main()
