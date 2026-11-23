#!/usr/bin/env python3
"""Add original #778's two presentation sources to one pinned official artifact.

This is a SOURCE preparation builder, not a canonical or Studio acceptance gate.
All existing sources, instance routes, classes and non-Source properties survive.
The disabled profile reproduces the input project, sources and Place exactly.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOCK = HERE / "source_lock.json"
FEATURE = "BATTLE_ATTR_VFX_20261118"
ADDITIONS = {
    "ReplicatedStorage/EGGRUMBLE_ElementVisuals": {
        "class_name": "ModuleScript",
        "path": "sources/ReplicatedStorage/EGGRUMBLE_ElementVisuals.luau",
        "source": "handoffs/EGGRUMBLE-ATTR-VFX-20261118/ElementVisuals.luau",
    },
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AttributeCue": {
        "class_name": "LocalScript",
        "path": "sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_AttributeCue.client.luau",
        "source": "handoffs/EGGRUMBLE-ATTR-VFX-20261118/EGGRUMBLE_AttributeCue.client.luau",
    },
}
SOURCE_CLASSES = {"ModuleScript", "Script", "LocalScript"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(reason: str):
    raise ValueError("GQ778_RED_" + reason)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(data: bytes):
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)


def safe_member(path: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
        fail("UNSAFE_ARTIFACT_PATH")
    pieces = path.split("/")
    if path.startswith("/") or any(p in ("", ".", "..") for p in pieces):
        fail("UNSAFE_ARTIFACT_PATH")
    if ":" in pieces[0] or str(PurePosixPath(path)) != path:
        fail("UNSAFE_ARTIFACT_PATH")
    return path


def project_inventory(project: dict) -> dict:
    if not isinstance(project, dict) or not isinstance(project.get("tree"), dict):
        fail("PROJECT_TREE")
    result = {}

    def visit(node, route):
        if not isinstance(node, dict):
            fail("PROJECT_NODE")
        if "$path" in node:
            path = safe_member(node["$path"])
            if not path.startswith("sources/") or not path.endswith(".luau"):
                fail("SOURCE_PATH")
            if any(not k.startswith("$") for k in node):
                fail("SOURCE_WITH_CHILDREN")
            if not route or route in result:
                fail("DUPLICATE_SOURCE_ROUTE")
            result[route] = path
            return
        for name, child in node.items():
            if name.startswith("$"):
                continue
            if not name or "/" in name or "\\" in name:
                fail("PROJECT_ROUTE")
            visit(child, route + "/" + name if route else name)

    visit(project["tree"], "")
    if len(set(result.values())) != len(result):
        fail("DUPLICATE_SOURCE_PATH")
    return result


def place_inventory(data: bytes):
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        fail("XML_ENTITY")
    root = ET.fromstring(data)
    if root.tag != "roblox" or root.attrib != {"version": "4"}:
        fail("PLACE_FORMAT")
    items = {}
    referents = {}

    def visit(item, parent):
        if set(item.attrib) != {"class", "referent"}:
            fail("PLACE_ITEM_ATTRIBUTES")
        props = item.findall("Properties")
        if len(props) != 1:
            fail("PLACE_PROPERTIES")
        names = [p.text or "" for p in props[0] if p.attrib.get("name") == "Name"]
        if len(names) != 1 or not names[0] or "/" in names[0]:
            fail("PLACE_NAME")
        route = parent + "/" + names[0] if parent else names[0]
        if route in items:
            fail("DUPLICATE_INSTANCE_ROUTE")
        ref = item.attrib.get("referent")
        if ref is None or ref in referents:
            fail("PLACE_REFERENT")
        referents[ref] = route
        source_props = [p for p in props[0] if p.attrib.get("name") == "Source"]
        class_name = item.attrib.get("class")
        if len(source_props) != (1 if class_name in SOURCE_CLASSES else 0):
            fail("PLACE_SOURCE_PROPERTY")
        if any(p.tag != "string" or p.attrib != {"name": "Source"} or len(p) for p in source_props):
            fail("PLACE_SOURCE_PROPERTY_SHAPE")
        if any(c.tag not in ("Properties", "Item") for c in item):
            fail("UNSUPPORTED_INSTANCE_CHILD")
        items[route] = {
            "class_name": class_name,
            "source": (source_props[0].text or "").encode("utf-8") if source_props else None,
            "properties_element": props[0],
        }
        for child in item.findall("Item"):
            visit(child, route)

    for item in root.findall("Item"):
        visit(item, "")

    def canonical(element):
        text = element.text or ""
        if len(element) and not text.strip():
            text = ""
        if element.tag == "Ref" and text in referents:
            text = "route:" + referents[text]
        return [element.tag, sorted(element.attrib.items()), text,
                [canonical(child) for child in element]]

    for value in items.values():
        props = value.pop("properties_element")
        value["properties"] = [canonical(p) for p in props if p.attrib.get("name") != "Source"]
    envelope = [canonical(c) for c in root if c.tag != "Item"]
    return items, envelope


def validate_official(project_bytes: bytes, place_bytes: bytes, sources: dict, lock: dict):
    if digest(project_bytes) != lock["project"]["sha256"]:
        fail("OFFICIAL_PROJECT_HASH")
    if digest(place_bytes) != lock["place"]["sha256"]:
        fail("OFFICIAL_PLACE_HASH")
    project = read_json(project_bytes)
    routes = project_inventory(project)
    expected = {entry["route"]: entry for entry in lock["sources"]}
    if len(expected) != 69 or len(lock["sources"]) != 69 or set(routes) != set(expected):
        fail("OFFICIAL_SOURCE_ROUTES")
    if set(sources) != {entry["path"] for entry in expected.values()}:
        fail("OFFICIAL_SOURCE_PATH_SET")
    items, envelope = place_inventory(place_bytes)
    if len(items) != lock["instance_count"] or len(items) != 75:
        fail("OFFICIAL_INSTANCE_COUNT")
    actual_source_routes = {route for route, item in items.items() if item["source"] is not None}
    if actual_source_routes != set(expected):
        fail("OFFICIAL_PLACE_SOURCE_ROUTES")
    for route, entry in expected.items():
        body = sources[entry["path"]]
        if routes[route] != entry["path"] or digest(body) != entry["sha256"] or len(body) != entry["bytes"]:
            fail("OFFICIAL_SOURCE_HASH_OR_ROUTE")
        if items[route]["class_name"] != entry["class_name"] or items[route]["source"] != body:
            fail("OFFICIAL_PLACE_SOURCE_OR_CLASS")
    counts = dict(collections.Counter(item["class_name"] for item in items.values()))
    if counts != lock["class_counts"]:
        fail("OFFICIAL_CLASS_COUNTS")
    if set(ADDITIONS) & set(items):
        fail("ADDITIVE_ROUTE_ALREADY_PRESENT")
    return project, items, envelope


def read_official_artifact(artifact: Path, lock=None):
    lock = read_json(LOCK.read_bytes()) if lock is None else lock
    if lock.get("schema") != "GQ778_CURRENT69_INPUT_V1" or lock.get("feature_id") != FEATURE:
        fail("INPUT_LOCK_SCHEMA")
    if artifact.is_symlink() or not artifact.is_file():
        fail("ARTIFACT_FILE")
    raw = artifact.read_bytes()
    if len(raw) != lock["artifact"]["bytes"] or digest(raw) != lock["artifact"]["sha256"]:
        fail("OFFICIAL_ZIP_HASH")
    required = {lock["project"]["path"], lock["place"]["path"]} | {x["path"] for x in lock["sources"]}
    with zipfile.ZipFile(artifact) as archive:
        names = set()
        for info in archive.infolist():
            name = safe_member(info.filename.rstrip("/") if info.is_dir() else info.filename)
            if name in names or stat.S_ISLNK(info.external_attr >> 16):
                fail("DUPLICATE_OR_SYMLINK_ZIP_MEMBER")
            names.add(name)
        if not required <= names:
            fail("ARTIFACT_MISSING_MEMBER")
        data = {name: archive.read(name) for name in required}
    sources = {name: data[name] for name in required if name.startswith("sources/")}
    project_bytes = data[lock["project"]["path"]]
    place_bytes = data[lock["place"]["path"]]
    project, items, envelope = validate_official(project_bytes, place_bytes, sources, lock)
    return lock, project_bytes, place_bytes, sources, project, items, envelope


def validate_output(place_bytes, base_items, base_envelope, source_bodies, enabled):
    items, envelope = place_inventory(place_bytes)
    additions = set(ADDITIONS) if enabled else set()
    if set(items) != set(base_items) | additions or envelope != base_envelope:
        fail("OUTPUT_INSTANCE_OR_ENVELOPE_DRIFT")
    for route, original in base_items.items():
        if items[route] != original:
            fail("OUTPUT_EXISTING_SOURCE_CLASS_OR_PROPERTY_DRIFT")
    for route in additions:
        item = items[route]
        if item["class_name"] != ADDITIONS[route]["class_name"] or item["source"] != source_bodies[route]:
            fail("OUTPUT_ADDITION_SOURCE_OR_CLASS")
        if item["properties"] != [["string", [("name", "Name")], route.rsplit("/", 1)[-1], []]]:
            fail("OUTPUT_ADDITION_PROPERTIES")
    return items


def compose(artifact: Path, destination: Path, rojo: Path, *, enabled=True):
    lock_bytes = LOCK.read_bytes()
    lock, project_bytes, original_place, sources, project, base_items, envelope = read_official_artifact(artifact)
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        fail("OUTPUT_ALREADY_EXISTS")
    # A new self-contained directory prevents rebase references to arbitrary host files.
    addition_bodies = {}
    if enabled:
        for route, specification in ADDITIONS.items():
            source = ROOT / specification["source"]
            if source.is_symlink() or not source.is_file() or source.resolve() != source.absolute():
                fail("CANDIDATE_SOURCE_PATH")
            addition_bodies[route] = source.read_bytes()
            if not addition_bodies[route]:
                fail("EMPTY_CANDIDATE_SOURCE")
    version = subprocess.run([str(rojo), "--version"], check=True, text=True, capture_output=True)
    if version.stdout.strip() != lock["rojo_version"]:
        fail("ROJO_VERSION")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".gq778-build-", dir=destination.parent) as temporary:
        stage = Path(temporary) / "payload"
        stage.mkdir()
        for path, body in sources.items():
            target = stage / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        output_project = copy.deepcopy(project)
        if enabled:
            for route, specification in ADDITIONS.items():
                names = route.split("/")
                node = output_project["tree"]
                for name in names[:-1]:
                    node = node[name]
                if names[-1] in node:
                    fail("ADDITION_PROJECT_COLLISION")
                node[names[-1]] = {"$path": specification["path"]}
                target = stage / specification["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(addition_bodies[route])
            output_project_bytes = (json.dumps(output_project, ensure_ascii=False, indent=2) + "\n").encode()
        else:
            output_project_bytes = project_bytes
        project_name = "EGGRUMBLE_ATTR_CURRENT71.project.json" if enabled else lock["project"]["path"]
        (stage / project_name).write_bytes(output_project_bytes)
        output_routes = project_inventory(output_project)
        expected_routes = project_inventory(project) | {r: ADDITIONS[r]["path"] for r in addition_bodies}
        if output_routes != expected_routes:
            fail("OUTPUT_PROJECT_ROUTE_DRIFT")
        for path, body in sources.items():
            if (stage / path).read_bytes() != body:
                fail("OUTPUT_SOURCE_BYTES")
        place_name = "EGGRUMBLE_ATTR_CURRENT71_PRIVATE.rbxlx" if enabled else lock["place"]["path"]
        command = [str(rojo), "build", str(stage / project_name), "-o", str(stage / place_name)]
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        built = (stage / place_name).read_bytes()
        items = validate_output(built, base_items, envelope, addition_bodies, enabled)
        if not enabled and (built != original_place or output_project_bytes != project_bytes):
            fail("OFF69_NOT_BYTE_EXACT")
        # Recheck after the external build: a passing Place must describe the
        # actual delivered source files and the same inputs we started with.
        if LOCK.read_bytes() != lock_bytes or digest(artifact.read_bytes()) != lock["artifact"]["sha256"]:
            fail("INPUT_CHANGED_DURING_BUILD")
        for path, body in sources.items():
            if (stage / path).read_bytes() != body:
                fail("OUTPUT_SOURCE_CHANGED_DURING_BUILD")
        for route, body in addition_bodies.items():
            specification = ADDITIONS[route]
            if (stage / specification["path"]).read_bytes() != body or (ROOT / specification["source"]).read_bytes() != body:
                fail("CANDIDATE_CHANGED_DURING_BUILD")
        if (stage / project_name).read_bytes() != output_project_bytes:
            fail("OUTPUT_PROJECT_CHANGED_DURING_BUILD")
        receipt = {
            "schema": "GQ778_CURRENT71_SOURCE_COMPOSITION_V1", "feature_id": FEATURE,
            "profile": "ON71" if enabled else "OFF69", "official_rc_sha": lock["official_rc_sha"],
            "official_artifact": lock["artifact"], "source_count": len(output_routes),
            "instance_count": len(items), "class_counts": dict(collections.Counter(i["class_name"] for i in items.values())),
            "all_original69_source_bytes_routes_classes_preserved": True,
            "all_original75_instance_properties_preserved": True,
            "off69_project_sources_place_byte_exact": not enabled,
            "additions": {r: {"sha256": digest(body), "bytes": len(body)} for r, body in addition_bodies.items()},
            "project": {"path": project_name, "sha256": digest(output_project_bytes)},
            "place": {"path": place_name, "sha256": digest(built), "bytes": len(built)},
            "rojo": {"version": version.stdout.strip(), "returncode": result.returncode,
                     "stdout": result.stdout, "stderr": result.stderr},
            "studio": "NOT_TESTED", "android": "NOT_TESTED", "art": "NOT_TESTED", "fun": "NOT_TESTED",
            "source_acceptance": False, "official_rc_adoption": False,
        }
        # Exclusively own the delivery directory at publication time. rename/
        # replace can overwrite an empty directory created by another producer.
        # A partial write has no receipt; the receipt is published last.
        destination.mkdir(exist_ok=False)
        for path in sorted(stage.rglob("*")):
            target = destination / path.relative_to(stage)
            if path.is_dir():
                target.mkdir(exist_ok=False)
            elif path.is_file() and not path.is_symlink():
                with target.open("xb") as handle:
                    handle.write(path.read_bytes())
            else:
                fail("UNSUPPORTED_DELIVERY_MEMBER")
        with (destination / "COMPOSITION_RECEIPT.json").open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--rojo", type=Path, required=True)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    result = compose(args.artifact, args.out_dir, args.rojo, enabled=not args.off)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
