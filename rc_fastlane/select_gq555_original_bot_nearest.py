#!/usr/bin/env python3
"""Integrate existing original author #555 into the ONE canonical V3 BotActors.

Only source-selects the original author's immutable patch into the already
source-selected official31 (including #541/#537/#540/#539/#489). This script
contains no new gameplay decision/AI logic and fails closed on source drift.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.machinery
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

AUTHOR_HEAD = "cd7d2cd6b39c7d5531a2b2d2437a523a6d09e32d"
AUTHOR_GIT_BLOB = "b176a76833d88b8ac4231965e47e8950d38776e4"
PARENT_BOT_SHA256 = "9e2246f3bed6747d8b61a60a289111b5290a6f4ea79d18b4d15ad81bae5218a7"
BOT = ("ServerScriptService", "EGGRUMBLE_BotActors")
REQUIRED = {
    "EGGRUMBLE_LobbyCastleModesPreview",
    "EGGRUMBLE_BotActors",
    "EGGRUMBLE_SevenRoleCombat",
    "EGGRUMBLE_SwarmCombat",
    "EGGRUMBLE_MatchResultService",
    "EGGRUMBLE_FieldItemPickups",
}
CLASSES = {"Script", "LocalScript", "ModuleScript"}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def author(path: Path):
    if blob(path.resolve(strict=True).read_bytes()) != AUTHOR_GIT_BLOB:
        raise ValueError("RED_GQ555_AUTHOR_PATCH_BLOB_CHANGED")
    return importlib.machinery.SourceFileLoader("original_author_555_nearest", str(path)).load_module()

def flatten(path: Path):
    path = path.resolve(strict=True)
    tree = json.loads(path.read_text(encoding="utf-8"))
    found = {}
    def walk(part, prefix=()):
        for name, value in part.items():
            if name.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("RED_ROJO_INVALID_NODE")
            here = prefix + (name,)
            if "$path" in value:
                if set(value) != {"$path"} or here in found:
                    raise ValueError("RED_ROJO_ALIAS_OR_DUPLICATE")
                found[here] = (path.parent / value["$path"]).resolve(strict=True)
            else:
                walk(value, here)
    walk(tree["tree"])
    names = [key[-1] for key in found]
    if len(names) != 31 or len(set(names)) != 31 or not REQUIRED.issubset(names) or BOT not in found:
        raise ValueError("RED_NOT_ONE_CANONICAL_EIGHT_DOMAIN_31")
    return tree, found

def prepare(base: Path, original_author: Path, out: Path):
    base_doc, sources = flatten(base)
    source = sources[BOT].read_bytes()
    if sha(source) != PARENT_BOT_SHA256:
        raise ValueError("RED_OFFICIAL_BOT_AUTHOR_PARENT_DRIFT")
    patch = author(original_author)
    on, off = patch.apply(source)
    if off != source or on == source or on.count(b"nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)") != 1:
        raise ValueError("RED_NOT_ORIGINAL_555_SINGLE_TARGET_REPLACEMENT")
    if out.exists():
        raise ValueError("RED_NO_PROJECT_OVERWRITE")
    out.parent.mkdir(parents=True, exist_ok=True)
    patched_file = out.parent / "EGGRUMBLE_BotActors_555.luau"
    if patched_file.exists():
        raise ValueError("RED_NO_BOT_FILE_OVERWRITE")
    patched_file.write_bytes(on)
    updated = copy.deepcopy(base_doc)
    updated["name"] = "EGGRUMBLE_V3_RC31_ORIGINAL_GQ555_ONE_BOT_AFTER_ITEM489"
    def remap(part, prefix=()):
        for name, val in part.items():
            if name.startswith("$"):
                continue
            here = prefix + (name,)
            if "$path" in val:
                dst = patched_file if here == BOT else sources[here]
                val["$path"] = os.path.relpath(dst, out.parent).replace(os.sep, "/")
            else:
                remap(val, here)
    remap(updated["tree"])
    out.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, result = flatten(out)
    if set(result) != set(sources):
        raise ValueError("RED_CHANGED_SCRIPT_SET")
    for key in sources:
        expected = on if key == BOT else sources[key].read_bytes()
        if result[key].read_bytes() != expected:
            raise ValueError("RED_CHANGED_OTHER_AUTHOR_" + "/".join(key))
    receipt = {
        "original_author_555_head": AUTHOR_HEAD,
        "original_author_patch_git_blob": AUTHOR_GIT_BLOB,
        "source_count": 31,
        "only_changed_script": "/".join(BOT),
        "other_current_official_sources_byte_identical": 30,
        "original_parent_bot_sha256": sha(source),
        "selected_bot_sha256": sha(on),
        "off_rollback_byte_exact": off == source,
        "preserves_541_537_540_539_489": True,
        "official_rc_changed_during_candidate": False,
        "studio_android_owner": "NOT_TESTED",
        "source_sha256": {"/".join(key): sha(src.read_bytes()) for key, src in sorted(result.items())},
    }
    (out.parent / "GQ555_SOURCE_SELECTION_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ555_ORIGINAL_BOT_ONLY_SELECTED_PRESERVING_30_OF_31_PASS")
    return receipt

def verify(base: Path, selected: Path, original_author: Path, place: Path):
    _, previous = flatten(base)
    _, current = flatten(selected)
    if set(current) != set(previous):
        raise ValueError("RED_SOURCE_ROUTES_CHANGED")
    patched, off = author(original_author).apply(previous[BOT].read_bytes())
    if off != previous[BOT].read_bytes() or current[BOT].read_bytes() != patched:
        raise ValueError("RED_AUTHOR_PATCH_OR_ROLLBACK_MISMATCH")
    for key in current:
        if key != BOT and current[key].read_bytes() != previous[key].read_bytes():
            raise ValueError("RED_OTHER_AUTHOR_CHANGED_" + "/".join(key))
    found = {}
    for node in ET.parse(place).getroot().iter("Item"):
        cls = node.get("class")
        if cls not in CLASSES:
            continue
        properties = node.find("Properties")
        if properties is None:
            raise ValueError("RED_MISSING_ROJO_PROPERTIES")
        name = properties.findtext("string[@name='Name']")
        source = properties.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = properties.findtext("string[@name='Source']")
        if not name or name in found or source is None:
            raise ValueError("RED_BAD_OR_DUPLICATE_ROJO_SCRIPT")
        found[name] = (cls, source.replace("\r\n", "\n"))
    if len(found) != 31 or set(found) != {key[-1] for key in current}:
        raise ValueError("RED_ROJO_REAL_SCRIPT_COUNT")
    for key, script in current.items():
        cls = "Script" if script.name.endswith(".server.luau") else (
              "LocalScript" if script.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]] != (cls, script.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_ROJO_SCRIPT_CLASS_OR_SOURCE_" + key[-1])
    receipt = {
        "native_expected_script_count": 31,
        "rojo_source_class_exact": "31/31",
        "other_30_sources_byte_identical": True,
        "only_original_bot_555_changed": True,
        "rollback_original_bot_exact": True,
        "place_bytes": place.stat().st_size,
        "place_sha256": sha(place.read_bytes()),
        "rc_branch_integrated_by_this_check": False,
        "studio_android_fun_owner": "NOT_TESTED",
    }
    (selected.parent / "GQ555_ROJO_EXACT_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ555_ORIGINAL_ONE_BOT_FINAL_NATIVE_ROJO_31_SOURCE_EXACT_PASS",receipt["place_bytes"],receipt["place_sha256"])
    return receipt

def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("prepare", "verify"))
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--author", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--place", type=Path)
    args = p.parse_args()
    if args.action == "prepare":
        prepare(args.base, args.author, args.out)
    else:
        if not args.place:
            p.error("verify requires --place")
        verify(args.base, args.out, args.author, args.place)

if __name__ == "__main__":
    main()
