#!/usr/bin/env python3
"""Private #482 V3 21-source Rojo source-select. Never edits official RC.

This script copies pinned original author files and replaces exactly ONE Item
source using our byte-reversible DASH callback guard. A genuine private Place
build is then checked against the 21 expected author source bytes/classes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from patch_dash import ORIGINAL_BLOB, ORIGINAL_PATH, git_blob_sha, patch_source

PROJECT = "EGGRUMBLE_V3_STUDIO.project.json"
EXPECTED_COUNT = 21
SCRIPT_CLASSES = {"ModuleScript", "Script", "LocalScript"}


def listed_scripts(project: dict) -> dict[str, str]:
    selected: dict[str, str] = {}

    def scan(tree: dict):
        for name, child in tree.items():
            if name.startswith("$"):
                continue
            if not isinstance(child, dict):
                raise ValueError("Invalid Rojo project node")
            if "$path" in child:
                path = child["$path"]
                if not isinstance(path, str) or Path(path).name != path or not path.endswith(".luau"):
                    raise ValueError("Refuse unsafe or duplicate Rojo path")
                if name in selected or path in selected.values():
                    raise ValueError("Duplicate script or source authority")
                selected[name] = path
            else:
                scan(child)
    scan(project["tree"])
    if len(selected) != EXPECTED_COUNT or set(selected) != set(selected.keys()):
        raise ValueError(f"Expected {EXPECTED_COUNT} single-owner sources, got {len(selected)}")
    if selected.get("EGGRUMBLE_FieldItemPickups") != "EGGRUMBLE_FieldItemPickups.luau":
        raise ValueError("Original author ITEM must be the only selected ITEM")
    if sum("LobbyCastleModesPreview" in n for n in selected) != 1:
        raise ValueError("Single original server host required")
    return selected


def prepare(author_root: Path, out: Path) -> None:
    if out.resolve() == author_root.resolve() or author_root.resolve() in out.resolve().parents:
        raise ValueError("Refuse writing inside author's original checkout")
    project = json.loads((author_root / PROJECT).read_text(encoding="utf-8"))
    sources = listed_scripts(project)
    out.mkdir(parents=True, exist_ok=False)
    (out / PROJECT).write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, filename in sources.items():
        content = (author_root / filename).read_text(encoding="utf-8")
        if name == "EGGRUMBLE_FieldItemPickups":
            if git_blob_sha(content) != ORIGINAL_BLOB:
                raise ValueError("Pinned original ITEM Git blob drift")
            content = patch_source(content)
        (out / filename).write_text(content, encoding="utf-8")
    _exact_sources(author_root, out, sources)
    print(f"GQ543_PRIVATE_PREPARED={len(sources)} SELECTED=ONE_ITEM_DASH PATCHED=1 OTHER20_ORIGINAL_EXACT=PASS")


def _exact_sources(author_root: Path, out: Path, sources: dict[str, str]) -> None:
    modified = 0
    for name, filename in sources.items():
        original = (author_root / filename).read_text(encoding="utf-8")
        actual = (out / filename).read_text(encoding="utf-8")
        if name == "EGGRUMBLE_FieldItemPickups":
            if actual != patch_source(original):
                raise ValueError("DASH patch mismatch")
            modified += 1
        elif original != actual:
            raise ValueError(f"Unrelated author source changed: {filename}")
    if modified != 1:
        raise ValueError("Expected exactly one Item patch")


def verify(author_root: Path, out: Path, place: Path) -> None:
    project = json.loads((out / PROJECT).read_text(encoding="utf-8"))
    sources = listed_scripts(project)
    _exact_sources(author_root, out, sources)
    tree = ET.parse(place)
    embedded: dict[str, str] = {}
    for item in tree.iter("Item"):
        if item.attrib.get("class") not in SCRIPT_CLASSES:
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = props.find("string[@name='Name']")
        source = props.find("ProtectedString[@name='Source']")
        if source is None:
            source = props.find("string[@name='Source']")
        if name is None or name.text not in sources:
            continue
        if name.text in embedded:
            raise ValueError(f"Duplicate embedded {name.text}")
        if source is None:
            raise ValueError(f"Missing source in Place: {name.text}")
        embedded[name.text] = source.text or ""
        expected = (out / sources[name.text]).read_text(encoding="utf-8")
        if embedded[name.text] != expected:
            raise ValueError(f"Real Place source mismatch: {name.text}")
    if len(embedded) != EXPECTED_COUNT:
        raise ValueError(f"Place had {len(embedded)} selected source objects, not {EXPECTED_COUNT}")
    size = place.stat().st_size
    digest = hashlib.sha256(place.read_bytes()).hexdigest()
    print(f"GQ543_REAL_PRIVATE_PLACE_SOURCE_EXACT={len(embedded)}/{EXPECTED_COUNT} BYTE_SIZE={size} SHA256={digest}")
    print("FORMAL_RC_INTEGRATED=0 STUDIO_ANDROID_OWNER_NOT_TESTED")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("prepare", "verify"))
    p.add_argument("--author-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--place", type=Path)
    a = p.parse_args()
    if a.action == "prepare":
        prepare(a.author_root, a.out)
    else:
        if not a.place:
            p.error("--place is required for verify")
        verify(a.author_root, a.out, a.place)


if __name__ == "__main__":
    main()
