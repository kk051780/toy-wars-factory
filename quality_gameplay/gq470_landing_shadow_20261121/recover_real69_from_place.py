#!/usr/bin/env python3
"""Reconstruct source-exact REAL69 selected tree from ART17 GitHub packet .rbxlx.

Only reads data; does not execute Luau or trust a stale PR body. Rebuilds source
files from actual Rojo XML, verifies all 69 source routes and 17 ART17 selected
patch files byte-for-byte, and checks pinned Place SHA256.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import xml.etree.ElementTree as ET

EXPECTED_ART17_PLACE_SHA256 = "443914a672f4f535fe4c6313b0dec524892a0afeb4684a8d935e4eebb1458305"
PLACE_NAME = "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
PROJECT_NAME = "EGGRUMBLE_REAL69.project.json"
SELECTED17 = "B220_ART16_P0_SELECTED17_NOT_FORMAL/selected_sources"


def ensure(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("GQ470_REHYDRATE_RED_" + reason)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def paths_from_project(tree: dict) -> dict[str, str]:
    found: dict[str, str] = {}

    def descend(node: dict, path: tuple[str, ...]) -> None:
        ensure(isinstance(node, dict), "BAD_PROJECT_NODE")
        if "$path" in node:
            key = "/".join(path)
            ensure(key not in found, "DUPLICATE_PROJECT_ROUTE")
            found[key] = node["$path"]
        for key, val in node.items():
            if not key.startswith("$"):
                descend(val, (*path, key))

    descend(tree, ())
    ensure(len(found) == 69, "PROJECT_NOT_REAL69")
    return found


def source_from_place(xml: bytes, expected_count: int = 69) -> dict[str, tuple[str, bytes]]:
    root = ET.fromstring(xml)
    result: dict[str, tuple[str, bytes]] = {}

    def visit(item: ET.Element, parents: tuple[str, ...]) -> None:
        if item.tag != "Item":
            for child in item:
                visit(child, parents)
            return
        props = item.find("Properties")
        ensure(props is not None, "ITEM_PROPERTIES_MISSING")
        name_el = props.find("string[@name='Name']")
        ensure(name_el is not None and bool(name_el.text), "ITEM_NAME_MISSING")
        name = name_el.text
        route = (*parents, name)
        if item.attrib.get("class") in ("Script", "LocalScript", "ModuleScript"):
            text = props.find("ProtectedString[@name='Source']")
            if text is None:
                text = props.find("string[@name='Source']")
            ensure(text is not None, "SCRIPT_SOURCE_MISSING")
            full = "/".join(route)
            ensure(full not in result, "DUPLICATE_PLACE_SCRIPT")
            result[full] = (item.attrib["class"], (text.text or "").encode("utf-8"))
        for child in item:
            if child.tag == "Item":
                visit(child, route)

    visit(root, ())
    ensure(len(result) == expected_count, "PLACE_SCRIPT_COUNT_MISMATCH")
    return result


def recover(root: pathlib.Path) -> dict:
    place = root / PLACE_NAME
    ensure(place.is_file(), "PLACE_MISSING")
    raw_place = place.read_bytes()
    ensure(digest(raw_place) == EXPECTED_ART17_PLACE_SHA256, "PLACE_SHA256_MISMATCH")
    obj = json.loads((root / PROJECT_NAME).read_text(encoding="utf-8"))
    paths = paths_from_project(obj["tree"])
    sources = source_from_place(raw_place)
    ensure(set(paths) == set(sources), "PROJECT_PLACE_ROUTE_MISMATCH")

    checked = 0
    for route, path in sorted(paths.items()):
        destination = (root / path).resolve()
        ensure(destination.is_relative_to(root.resolve()), "SOURCE_PATH_TRAVERSAL")
        ensure(not destination.exists(), "ALREADY_REHYDRATED_OR_COLLISION")
        cls, content = sources[route]
        ensure(cls in ("LocalScript", "ModuleScript", "Script"), "SCRIPT_CLASS_INVALID")
        selection_file = (root / SELECTED17 / (route + ".luau"))
        if selection_file.exists():
            ensure(selection_file.read_bytes() == content, "AUTHOR17_SOURCE_MISMATCH")
            checked += 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    ensure(checked == 17, "ART17_SELECTED_COUNT")
    proof = {
        "schema": "GQ470_REAL69_ART17_TRUE_SOURCE_REHYDRATED_20261121",
        "place_sha256": digest(raw_place),
        "place_bytes": len(raw_place),
        "source_count": len(paths),
        "place_route_count": len(sources),
        "author_selected17_byte_exact": checked,
        "artifact_origin": "PR983 Actions 44864701798 / artifact 14691232367",
        "formal_rc": False,
        "studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "source_digest_by_route": {r: digest(sources[r][1]) for r in sorted(sources)},
    }
    (root / "GQ470_REHYDRATED_ART17_SOURCE_PROOF.json").write_text(
        json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return proof


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=pathlib.Path, required=True)
    a = ap.parse_args()
    p = recover(a.root)
    print("GQ470_ART17_REAL_SOURCE_69_EXACT_17_SELECTED_AUTHOR_EXACT_NOT_FORMAL", p["place_sha256"])

if __name__ == "__main__":
    main()
