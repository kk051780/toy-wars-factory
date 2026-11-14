#!/usr/bin/env python3
"""#420 P0: check EVERY Luau source at its exact Rojo instance path/class/name.

An aggregate Counter(source texts) does NOT detect two real scripts swapping bodies.
This verifier rejects that regression, plus silent/Source-less extra scripts,
missing scripts, duplicate path, class drift, alias-to-HUD drift, unsafe XML,
unmatched project references, and incompatible SOURCE_LOCK files.

SOURCE_GATE only. Never infer Roblox Studio runtime, visual, FPS or OWNER GO.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from defusedxml import ElementTree as ET


CLASSES = frozenset(("Script", "LocalScript", "ModuleScript"))

# Python -O strips assert statements: NEVER permit a falsely successful receipt.
if not __debug__:
    raise RuntimeError("P0D_IDENTITY_GATE_PYTHON_OPTIMIZATION_FORBIDDEN")


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _project_path(raw: str) -> str:
    assert isinstance(raw, str) and raw.startswith("src/"), ("INVALID_PROJECT_PATH", raw)
    p = Path(raw)
    assert not p.is_absolute() and ".." not in p.parts, ("PROJECT_PATH_ESCAPE", raw)
    return p.as_posix()


def _class_name(relative: str) -> tuple[str, str]:
    name = Path(relative).name
    if name.endswith(".server.luau"):
        return "Script", name[:-len(".server.luau")]
    if name.endswith(".client.luau"):
        return "LocalScript", name[:-len(".client.luau")]
    assert name.endswith(".luau"), ("NOT_LUAU_SOURCE", relative)
    return "ModuleScript", name[:-len(".luau")]


def expected_bindings(dist: Path) -> dict[tuple[str, str], bytes]:
    """Map Rojo (full Instance path, class) to exact SOURCE bytes for all scripts."""
    dist = dist.resolve()
    assert dist.is_dir(), "SOURCE_ROOT_MISSING"
    src = dist / "src"
    assert src.is_dir(), "SOURCE_FOLDER_MISSING"
    assert not any(p.is_symlink() for p in dist.rglob("*")), "SYMLINK_FORBIDDEN"
    scripts = {
        p.relative_to(dist).as_posix(): p.read_bytes()
        for p in sorted(src.rglob("*.luau"))
    }
    assert scripts, "NO_SOURCES"
    for path, content in scripts.items():
        assert path.startswith("src/") and content, ("BAD_SCRIPT", path)
    sl = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
    fl = json.loads((dist / "RC_FEATURE_LOCK.json").read_text("utf8"))
    pins = {
        k.removeprefix("src/"): blob(v) for k, v in sorted(scripts.items())
    }
    assert sl["total_scripts"] == fl["total_sources"] == len(scripts), "SOURCE_COUNT_LOCK_DRIFT"
    assert sl["blobs"] == fl["source_gitblobs"] == pins, "SOURCE_BLOB_LOCK_DRIFT"
    project = json.loads((dist / "default.project.json").read_text("utf8"))
    assert isinstance(project["tree"], dict), "NO_PROJECT_TREE"

    explicit: dict[str, tuple[str, ...]] = {}
    folders: dict[str, tuple[str, ...]] = {}

    def walk(node: dict, path: tuple[str, ...]) -> None:
        assert isinstance(node, dict), ("BAD_PROJECT_NODE", path)
        if "$path" in node:
            uri = _project_path(node["$path"])
            if uri.endswith(".luau"):
                assert uri not in explicit, ("DUPLICATE_EXPLICIT_PROJECT_MAPPING", uri)
                explicit[uri] = path
            else:
                assert uri not in folders, ("DUPLICATE_PROJECT_FOLDER", uri)
                folders[uri] = path
        for name, child in node.items():
            if name.startswith("$"):
                continue
            assert "/" not in name and name not in (".", ".."), ("INVALID_NODE_NAME", name)
            walk(child, path + (name,))

    walk(project["tree"], ())
    expected: dict[tuple[str, str], bytes] = {}
    for source, raw in scripts.items():
        kind, name = _class_name(source)
        if source in explicit:
            prefix = explicit[source]
            # Explicit Rojo script alias (HUD.client.luau -> TrapRaidersHUD)
            assert prefix, ("EMPTY_EXPLICIT_PATH", source)
            path = prefix
        else:
            candidates = [
                (len(folder), path, folder)
                for folder, path in folders.items()
                if source.startswith(folder.rstrip("/") + "/")
            ]
            assert candidates, ("SOURCE_NOT_MAPPED_BY_PROJECT", source)
            _, basepath, basefolder = max(candidates, key=lambda item: item[0])
            remainder = source[len(basefolder.rstrip("/") + "/"):]
            dirs = tuple(part for part in remainder.split("/")[:-1] if part)
            path = basepath + dirs + (name,)
        item = ("/".join(path), kind)
        assert item not in expected, ("PROJECT_DUPLICATE_RUNTIME_SCRIPT", item)
        expected[item] = raw
    unknown = set(explicit) - set(scripts)
    assert not unknown, ("PROJECT_REFERENCES_MISSING_LUAU_SOURCE", sorted(unknown))
    assert len(expected) == len(scripts)
    return expected


def expected_ancestor_classes(
    dist: Path, expected: dict[tuple[str, str], bytes]
) -> dict[tuple[str, ...], str]:
    """Check the *container* classes too, not just leaf Game/HUD classes."""
    project = json.loads((dist / "default.project.json").read_text("utf8"))
    classes: dict[tuple[str, ...], str] = {}

    def walk(node: dict, path: tuple[str, ...]) -> None:
        if path and not str(node.get("$path", "")).endswith(".luau"):
            classes[path] = node.get("$className", "Folder")
        for name, child in node.items():
            if not name.startswith("$"):
                assert "/" not in name and "\\" not in name
                walk(child, path + (name,))

    walk(project["tree"], ())
    for (runtime_path, _), _source in expected.items():
        names = runtime_path.split("/")
        for i in range(1, len(names)):
            classes.setdefault(tuple(names[:i]), "Folder")
    assert classes, "PROJECT_HAS_NO_ANCESTOR_CLASSES"
    return classes


def actual_bindings(
    place: Path, observed_ancestors: dict[tuple[str, ...], str] | None = None
) -> dict[tuple[str, str], bytes]:
    raw = place.read_bytes()
    assert 0 < len(raw) <= 10_000_000, "BAD_PLACE_SIZE"
    assert b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "XML_ENTITY_REJECTED"
    xml = ET.fromstring(raw)
    out: dict[tuple[str, str], bytes] = {}
    count = 0

    def walk(node, ancestors: tuple[str, ...]) -> None:
        nonlocal count
        for item in node.findall("Item"):
            kind = item.get("class")
            properties = item.find("Properties")
            assert properties is not None, ("ITEM_WITHOUT_PROPERTIES", kind)
            name_node = properties.find("string[@name='Name']")
            assert name_node is not None and name_node.text, ("ITEM_WITHOUT_NAME", kind)
            name = name_node.text
            assert ("/" not in name and "\\" not in name and name not in (".", "..")), (
                "INVALID_INSTANCE_NAME", name)
            instance_path = ancestors + (name,)
            if kind != "DataModel" and kind not in CLASSES and observed_ancestors is not None:
                prior = observed_ancestors.get(instance_path)
                assert prior is None or prior == kind, ("DUPLICATE_ANCESTOR_CLASS", instance_path)
                observed_ancestors[instance_path] = kind
            if kind in CLASSES:
                count += 1
                source_nodes = [
                    child for child in properties
                    if child.get("name") == "Source"
                    and child.tag in ("string", "ProtectedString")
                ]
                assert len(source_nodes) == 1, ("SCRIPT_WITHOUT_SOURCE_OR_DUPLICATE", instance_path)
                source_node = source_nodes[0]
                key = ("/".join(instance_path), kind)
                assert key not in out, ("DUPLICATE_SCRIPT_INSTANCE", key)
                out[key] = (source_node.text or "").encode("utf8")
            # Rojo XML normally has service Items directly under <roblox>.
            # Some serializers add a DataModel root Item named Game; that root
            # does not participate in runtime paths, so exclude it strictly.
            walk(item, ancestors if kind == "DataModel" else instance_path)

    walk(xml, ())
    assert count == len(out), "UNACCOUNTED_SCRIPT_ITEM"
    return out


def verify(dist: Path, place: Path, receipt: Path, expected_count: int | None = None) -> dict:
    expected = expected_bindings(dist)
    expected_parents = expected_ancestor_classes(dist, expected)
    observed_parents: dict[tuple[str, ...], str] = {}
    actual = actual_bindings(place, observed_parents)
    for path, required_class in expected_parents.items():
        assert observed_parents.get(path) == required_class, (
            "ROJO_ANCESTOR_CLASS_DRIFT", path, required_class, observed_parents.get(path))
    if expected_count is not None:
        assert len(expected) == expected_count, ("EXPECTED_COUNT_CHANGED", len(expected))
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    assert not missing and not extra, (
        "ROJO_INSTANCE_PATH_OR_CLASS_DRIFT",
        sorted(missing), sorted(extra))
    changed = [
        identity for identity in sorted(expected)
        if expected[identity] != actual[identity]
    ]
    assert not changed, ("ROJO_SCRIPT_SOURCE_WRONG_INSTANCE", changed)
    games = [key for key in actual if key[0].endswith("/Game") and key[1] == "Script"]
    assert len(games) == 1, ("NOT_SINGLE_GAME", games)
    data = {
        "schema": "P0D_RC_ROJO_FULL_IDENTITY_SOURCE_GATE_V1",
        "source_gate": "PASS",
        "embedded_count": len(actual),
        "source_count": len(expected),
        "all_instance_class_name_path_source_exact": True,
        "all_ancestor_container_class_exact": True,
        "source_less_script_rejected": True,
        "swapped_source_rejected": True,
        "one_Game": True,
        "place_sha256": hashlib.sha256(place.read_bytes()).hexdigest(),
        "place_bytes": place.stat().st_size,
        "studio_engine": "NOT_TESTED",
        "android15min": "NOT_TESTED",
        "art_decision": "ART_NO_GO",
        "mobile_decision": "MOBILE_NO_GO",
        "fun_decision": "FUN_NO_GO",
        "owner_accepted": False,
    }
    assert not receipt.exists(), "DO_NOT_OVERWRITE_RECEIPT"
    receipt.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf8")
    print("P0D_ALL_ROJO_INSTANCE_PATH_CLASS_NAME_SOURCE_EXACT_PASS", len(actual), data["place_bytes"])
    return data


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dist", required=True, type=Path)
    p.add_argument("--place", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    p.add_argument("--count", required=False, type=int)
    a = p.parse_args()
    verify(a.dist, a.place, a.receipt, a.count)
