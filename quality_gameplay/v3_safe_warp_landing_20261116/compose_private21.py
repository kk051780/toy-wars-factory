#!/usr/bin/env python3
"""Compose and verify ORIGINAL #482 21-source unpublished Place (one generated Combat overlay)."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from patch_safe_warp import git_blob_sha, patch, EXPECTED_GIT_BLOB, ORIGINAL

BASE = ORIGINAL.parent
PROJECT = "EGGRUMBLE_V3_STUDIO.project.json"
TARGET = ORIGINAL.name


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mapped_sources() -> list[str]:
    project = json.loads((BASE / PROJECT).read_text(encoding="utf-8"))
    names: list[str] = []

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            if "$path" in obj:
                names.append(obj["$path"])
            else:
                for value in obj.values():
                    walk(value)
    walk(project["tree"])
    assert len(names) == len(set(names)) == 21, "expected original mapped 21 unique source paths"
    return sorted(names)


def prepare(out: Path) -> None:
    if out.exists() and any(out.iterdir()):
        raise ValueError("REFUSE_REUSE_NONEMPTY_PACKAGE")
    out.mkdir(parents=True, exist_ok=True)
    original = ORIGINAL.read_bytes()
    assert git_blob_sha(original) == EXPECTED_GIT_BLOB
    selected = patch(original)
    mapping = []
    for name in mapped_sources():
        src = BASE / name
        content = selected if name == TARGET else src.read_bytes()
        (out / name).write_bytes(content)
        mapping.append(dict(name=name, original_sha256=sha256(src.read_bytes()),
                            selected_sha256=sha256(content), changed=name == TARGET,
                            clazz="LocalScript" if name.endswith(".client.luau") else
                                  "Script" if name.endswith(".server.luau") else "ModuleScript"))
    shutil.copyfile(BASE / PROJECT, out / PROJECT)
    assert sum(x["changed"] for x in mapping) == 1
    receipt = dict(kind="PRIVATE_21_SOURCE_NOT_RC", source_author_head="fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9",
                   original_combat_gitblob=EXPECTED_GIT_BLOB, script_count=21,
                   unchanged_originals=20, mapping=mapping, studio="NOT_TESTED",
                   android="NOT_TESTED", fun="NO_GO", official_rc_adopted=False)
    (out / "SOURCE_LOCK.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GQ_SAFE_WARP_PRIVATE21_SOURCE_LOCK_PASS", len(mapping))


def verify(place: Path, directory: Path) -> None:
    project = json.loads((directory / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
    assert project["script_count"] == 21 and project["unchanged_originals"] == 20
    expected = {row["name"].removesuffix(".luau").removesuffix(".server").removesuffix(".client"): row
                for row in project["mapping"]}
    actual = {}
    for item in ET.parse(place).iter("Item"):
        if item.attrib.get("class") not in ("Script", "ModuleScript", "LocalScript"):
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = props.find("./string[@name='Name']")
        if name is None or name.text not in expected:
            continue
        source = props.find("./ProtectedString[@name='Source']")
        if source is None:
            source = props.find("./string[@name='Source']")
        assert source is not None, f"missing source {name.text}"
        assert name.text not in actual, f"duplicate script instance {name.text}"
        actual[name.text] = (item.attrib.get("class"), source.text or "")
    assert set(expected) == set(actual), f"place mapped scripts differ: {sorted(set(expected)^set(actual))}"
    for name, row in expected.items():
        clazz, source = actual[name]
        assert clazz == row["clazz"], (name, "class mismatch", clazz, row["clazz"])
        assert sha256(source.encode("utf-8")) == row["selected_sha256"], (name, "SOURCE_CONTENT_DRIFT")
    print("GQ_SAFE_WARP_PRIVATE21_ACTUAL_ROJO_SOURCE_CLASS_EXACT_PASS", len(expected),
          "PLACE_BYTES", place.stat().st_size, "PLACE_SHA256", sha256(place.read_bytes()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["prepare", "verify"])
    ap.add_argument("--out", type=Path, required=True, help="Private package directory")
    ap.add_argument("--place", type=Path, help="Actual unpublished .rbxlx required for verification")
    args = ap.parse_args()
    if args.action == "prepare":
        prepare(args.out)
    else:
        if args.place is None:
            ap.error("--place is required for verify")
        verify(args.place, args.out)


if __name__ == "__main__":
    main()
