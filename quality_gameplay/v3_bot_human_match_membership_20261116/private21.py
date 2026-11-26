#!/usr/bin/env python3
"""Recompose original #482 21-script PRIVATE Place with only the two exact overlays.

No original author file or protected RC branch is modified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from compose import BOT, HOST, OWNER_BLOBS, OWNER_HEAD, SOURCE_ROOT, AI_AUTHOR_HEAD, AI_BOT_BLOB, git_blob_sha

PROJECT_NAME = "EGGRUMBLE_V3_STUDIO.project.json"
OVERLAY_NAMES = {HOST, BOT}


def original_blob(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{OWNER_HEAD}:{SOURCE_ROOT}/{path}"])


def mapped_sources(node: dict):
    found = {}
    def scan(current, key=()):
        for name, child in current.items():
            if name.startswith("$") or not isinstance(child, dict):
                continue
            next_key = key + (name,)
            if "$path" in child:
                rel = child["$path"]
                if "/" in rel or "\\" in rel or not rel.endswith(".luau"):
                    raise ValueError("RED: unexpected project source path " + repr(rel))
                if next_key in found:
                    raise ValueError("duplicate Roblox service name")
                kind = ("Script" if rel.endswith(".server.luau") else
                        "LocalScript" if rel.endswith(".client.luau") else "ModuleScript")
                found[next_key] = (rel, kind)
            else:
                scan(child, next_key)
    scan(node)
    return found


def assemble(out: Path, require_ai: bool = False):
    if not all((out / x).exists() for x in OVERLAY_NAMES):
        raise RuntimeError("overlay two-file pair missing")
    project_bytes = original_blob(PROJECT_NAME)
    project = json.loads(project_bytes.decode("utf-8"))
    paths = mapped_sources(project["tree"])
    assert len(paths) == 21, ("original author project source count changed", len(paths))
    assert len({name for name, _ in paths.values()}) == 21, "duplicate source filenames"
    assert {name for name, _ in paths.values()} >= OVERLAY_NAMES
    assert sum(kind == "Script" for _, kind in paths.values()) == 1, "multiple game hosts"
    assert sum(kind == "LocalScript" for _, kind in paths.values()) == 2, "unexpected mobile HUD client count"
    assert sum(kind == "ModuleScript" for _, kind in paths.values()) == 18
    for path, _ in paths.values():
        if path in OVERLAY_NAMES:
            assert git_blob_sha((out / path).read_bytes()) != OWNER_BLOBS[path]
            continue
        raw = original_blob(path)
        (out / path).write_bytes(raw)
    (out / PROJECT_NAME).write_bytes(project_bytes)
    lock = json.loads((out / "overlay_source_lock.json").read_text(encoding="utf-8"))
    assert lock["owner_head"] == OWNER_HEAD
    assert set(lock["source_files"]) == OVERLAY_NAMES
    assert lock["source_files"][HOST]["owner_blob"] == OWNER_BLOBS[HOST]
    if require_ai:
        assert lock["selected_ai_author_head"] == AI_AUTHOR_HEAD
        assert lock["source_files"][BOT]["owner_blob"] == AI_BOT_BLOB
        assert lock["ai_duel_preserved"] is True
        code = (out / BOT).read_text(encoding="utf-8")
        assert code.count("for targetId,targetActor in pairs(bots)") == 1
        assert code.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)") == 1
        print("GQ_ORIGINAL_484_BOT_DUEL_PRESERVED 1/1")
    else:
        assert lock["selected_ai_author_head"] is None
        assert lock["source_files"][BOT]["owner_blob"] == OWNER_BLOBS[BOT]
    for name in OVERLAY_NAMES:
        assert git_blob_sha((out / name).read_bytes()) == lock["source_files"][name]["overlay_blob"]
    print("GQ_PRIVATE21_PREPARED exact original19+patched2", len(paths))
    return paths


def verify(out: Path, place: Path):
    paths = mapped_sources(json.loads((out / PROJECT_NAME).read_text(encoding="utf-8"))["tree"])
    assert len(paths) == 21, len(paths)
    actual = {}
    for item in ET.parse(place).iter("Item"):
        cls = item.attrib.get("class")
        if cls not in {"Script", "LocalScript", "ModuleScript"}:
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = props.findtext("string[@name='Name']")
        if name in actual:
            raise AssertionError(("duplicate Script in true Place", name))
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if source is None:
            raise AssertionError(("missing embedded script source", name))
        actual[name] = (cls, source.replace("\r\n", "\n"))
    if len(actual) != len(paths):
        raise AssertionError(("Place source count mismatch", len(actual), len(paths)))
    for key, (filename, kind) in paths.items():
        name = key[-1]
        if name not in actual:
            raise AssertionError(("Place missing source", name))
        actual_class, source = actual[name]
        if actual_class != kind:
            raise AssertionError(("wrong Roblox class", name, kind, actual_class))
        expected = (out / filename).read_text(encoding="utf-8").replace("\r\n", "\n")
        if source != expected:
            raise AssertionError(("byte source mismatch after LF canonicalization", name))
    receipt = {
        "candidate_head_sha": os.environ.get("GITHUB_SHA", "LOCAL_ONLY"),
        "owner_head_sha": OWNER_HEAD,
        "selected_ai_author_head": json.loads((out / "overlay_source_lock.json").read_text(encoding="utf-8")).get("selected_ai_author_head"),
        "rc_integrated": False,
        "original_author_scripts_unchanged": 19,
        "patched_author_scripts": [HOST, BOT],
        "single_game_host": True,
        "source_count": len(actual),
        "source_exact": True,
        "private_place_bytes": place.stat().st_size,
        "private_place_sha256": hashlib.sha256(place.read_bytes()).hexdigest(),
        "real_studio": "NOT_TESTED",
        "android": "NOT_TESTED",
        "owner_accept": False,
        "published": False,
    }
    (out / "PRIVATE21_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("GQ_PRIVATE21_ROJO_SOURCE_EXACT_PASS", len(actual))
    print("PRIVATE21_PLACE_BYTES", receipt["private_place_bytes"], "SHA256", receipt["private_place_sha256"])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("operation", choices=["assemble", "verify"])
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--place", type=Path)
    p.add_argument("--require-ai", action="store_true")
    a = p.parse_args()
    if a.operation == "assemble":
        assemble(a.out, a.require_ai)
    else:
        if not a.place:
            p.error("--place required for verify")
        verify(a.out, a.place)
