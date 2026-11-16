#!/usr/bin/env python3
"""Select original GQ583 roster cap inside ONE current canonical 31 CastleRules.

This is an RC intake adapter for the existing author PR #583, not another
implementation of the roster policy. It never alters the original author's
branch or a server authority other than the one existing CastleRules module.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

from importlib.machinery import SourceFileLoader

mapping = SourceFileLoader(
    "gq508_pinned_project_mapper",
    "rc_fastlane/quality_ko508_rc31/select_original508_neutral_ko.py"
).load_module().mapping

SLOT = ("ServerScriptService", "EGGRUMBLE_CastleMatchRules")
AUTHOR_HEAD = "60b67c8dade80ff7ccd1d97e03480ba333977084"
ORIGINAL_AUTHOR_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_BLOB = "27da5ca1e9e6d9a7afe0674030e387f094ee7492"
RECEIPT = "GQ583_ROSTER16_RC31_RECEIPT.json"
NEW_SOURCE = "GQ583_ORIGINAL_CASTLE_RULES_16.luau"
MAX_SCRIPTS = 31


def git_blob(src: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(src)).encode() + b"\0" + src).hexdigest()


def sha256(src: bytes) -> str:
    return hashlib.sha256(src).hexdigest()


def source_author(script: Path):
    """Reuse the exact code from original #583 without copying its logic."""
    script = script.resolve(strict=True)
    spec = importlib.util.spec_from_file_location("gq583_original_logic", script)
    if spec is None or spec.loader is None:
        raise ValueError("RED_AUTHOR_MODULE_LOAD")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.AUTHOR_HEAD != ORIGINAL_AUTHOR_HEAD or module.ORIGINAL_BLOB != ORIGINAL_BLOB:
        raise ValueError("RED_GQ583_AUTHOR_PROVENANCE")
    return module


def get_script_map(project: Path):
    data, source = mapping(project)
    if len(source) != MAX_SCRIPTS or SLOT not in source:
        raise ValueError("RED_MISSING_SINGLE_CASTLERULES_31")
    return data, source


def select(base: Path, author_py: Path, original_author_luau: Path, out: Path):
    base = base.resolve(strict=True)
    original_author_luau = original_author_luau.resolve(strict=True)
    if out.resolve() == base or out.parent.resolve() != base.parent:
        raise ValueError("RED_PROJECT_SIBLING_ONLY_NO_INPLACE")
    oldbytes = original_author_luau.read_bytes()
    if git_blob(oldbytes) != ORIGINAL_BLOB:
        raise ValueError("RED_ORIGINAL482_BLOB_DRIFT")
    logic = source_author(author_py)
    data, old = get_script_map(base)
    previous = old[SLOT].read_bytes()
    if git_blob(previous) != ORIGINAL_BLOB or previous != oldbytes:
        raise ValueError("RED_CURRENT_RC31_CASTLERULES_NOT_ORIGINAL482")
    patched = logic.patch_source(previous.decode("utf-8"))
    if patched.replace(logic.NEW[0], logic.OLD[0], 1).replace(
            logic.NEW[1], logic.OLD[1], 1) != previous.decode("utf-8"):
        raise ValueError("RED_OFF_NOT_BYTE_EXACT")
    new_luau = out.parent / NEW_SOURCE
    new_luau.write_text(patched, encoding="utf-8")
    fresh = copy.deepcopy(data)
    fresh["tree"]["ServerScriptService"]["EGGRUMBLE_CastleMatchRules"]["$path"] = NEW_SOURCE
    out.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, files = get_script_map(out)
    if set(old) != set(files) or [k for k in old if old[k].read_bytes() != files[k].read_bytes()] != [SLOT]:
        raise ValueError("RED_30_OTHER_SOURCES_MODIFIED")
    # Real differential native executable uses the frozen #583 author's original test logic.
    (out.parent / "GQ583_ORIGINAL_NATIVE.spec.luau").write_text(
        logic.native_harness(previous.decode("utf-8"), True), encoding="utf-8")
    (out.parent / "GQ583_PATCHED_NATIVE.spec.luau").write_text(
        logic.native_harness(patched, False), encoding="utf-8")
    receipt = {
        "feature_id": "GQ_V3_ROSTER16_HARDCAP_583",
        "original_author_pr": 583,
        "original_author_head": AUTHOR_HEAD,
        "original_482_head": ORIGINAL_AUTHOR_HEAD,
        "original_482_module_blob": ORIGINAL_BLOB,
        "script_count": MAX_SCRIPTS,
        "source_changed": "/".join(SLOT),
        "other_30_byte_exact": True,
        "gameplay_ownership_count_new": 0,
        "off_rollback_byte_exact": True,
        "old_sha256": sha256(previous),
        "new_sha256": sha256(patched.encode("utf-8")),
        "original_can_exceed_16": True,
        "patched_17_32_rejected": True,
        "studio_android_owner": "NOT_TESTED",
        "official_rc_adopted": False,
    }
    (out.parent / RECEIPT).write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ583_ROSTER_16_ONE_EXISTING_CASTLERULES_30_OTHER_SOURCES_EXACT")


def verify(base: Path, author_py: Path, original_author_luau: Path, selected: Path, place: Path):
    base = base.resolve(strict=True)
    selected = selected.resolve(strict=True)
    original_author_luau = original_author_luau.resolve(strict=True)
    place = place.resolve(strict=True)
    logic = source_author(author_py)
    _, before = get_script_map(base)
    _, after = get_script_map(selected)
    if set(before) != set(after) or [k for k in before if before[k].read_bytes() != after[k].read_bytes()] != [SLOT]:
        raise ValueError("RED_OTHER_SOURCE_CHANGE_OR_NOT_SELECTED")
    original = before[SLOT].read_bytes()
    if git_blob(original) != ORIGINAL_BLOB or original != original_author_luau.read_bytes():
        raise ValueError("RED_CURRENT_SOURCE_ORIGINAL_MISMATCH")
    expected = logic.patch_source(original.decode("utf-8"))
    if after[SLOT].read_text(encoding="utf-8") != expected:
        raise ValueError("RED_WRONG_SELECTED_SOURCE")
    embedded = {}
    for item in ET.parse(place).iter("Item"):
        kind = item.attrib.get("class")
        if kind not in {"Script", "ModuleScript", "LocalScript"}:
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_MISSING_SCRIPT_PROPERTIES")
        name = props.findtext("string[@name='Name']")
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if not name or source is None or name in embedded:
            raise ValueError("RED_SCRIPT_DUPLICATE_OR_MISSING_SOURCE")
        embedded[name] = (kind, source.replace("\r\n", "\n"))
    if set(embedded) != {k[-1] for k in after}:
        raise ValueError("RED_ROJO_SCRIPT_NAMES_NOT_EXACT_31")
    for key, path in after.items():
        expected_class = ("Script" if path.name.endswith(".server.luau") else
                          "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded[key[-1]] != (expected_class, path.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_ROJO_SOURCE_CLASS_MISMATCH " + key[-1])
    receipt = selected.parent / RECEIPT
    info = json.loads(receipt.read_text(encoding="utf-8"))
    if not info.get("off_rollback_byte_exact") or not info.get("other_30_byte_exact"):
        raise ValueError("RED_ROLLBACK_RECEIPT_FALSE")
    info.update({
        "true_rojo_source_class_exact": "31/31",
        "place_bytes": place.stat().st_size,
        "place_sha256": sha256(place.read_bytes()),
        "verified": True,
    })
    receipt.write_text(json.dumps(info, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ583_ORIGINAL_MODULE_ROSTER16_TRUE_ROJO_31_SOURCE_CLASS_EXACT",
          info["place_bytes"], info["place_sha256"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "verify"))
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--original-luau", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--place", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        select(args.base, args.author, args.original_luau, args.out)
    elif args.place:
        verify(args.base, args.author, args.original_luau, args.out, args.place)
    else:
        parser.error("verify requires --place")


if __name__ == "__main__":
    main()
