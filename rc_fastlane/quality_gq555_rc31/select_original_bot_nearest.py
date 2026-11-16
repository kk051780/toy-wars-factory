#!/usr/bin/env python3
"""Select exact original #555 AI nearest-human behavior into existing RC31 BotActors.

Single-existing-source overlay only. Author patch is checked out at an immutable
commit by the workflow; its apply() fails closed on #484/#531 source drift.
No new authority, no change to canonical branch, no publication.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from importlib.machinery import SourceFileLoader
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0] / ".." / "quality_item489_rc31"))
from select_original_item489 import flatten

BOT_KEY = ("ServerScriptService", "EGGRUMBLE_BotActors")
N = 31

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def author_module(path: Path):
    return SourceFileLoader("gq555_immutable_original_patch", str(path.resolve(strict=True))).load_module()

def changed_sources(base: dict, selected: dict):
    if set(base) != set(selected):
        raise ValueError("RED RC31 script map changed")
    return [key for key in base if base[key].read_bytes() != selected[key].read_bytes()]

def prepare(base_path: Path, out_path: Path, author_path: Path) -> None:
    base_path = base_path.resolve(strict=True)
    out_path = out_path.resolve()
    if base_path.parent != out_path.parent or base_path == out_path:
        raise ValueError("RED expected adjacent isolated project, not RC overwrite")
    base_json, source = flatten(base_path)
    if BOT_KEY not in source:
        raise ValueError("RED original singleton BotActors missing")
    author = author_module(author_path)
    old = source[BOT_KEY].read_bytes()
    new, rollback = author.apply(old)  # immutable #555 author source-locks #484 and #531
    if old != rollback or new == old:
        raise ValueError("RED byte-exact rollback not possible")
    if b"nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)" not in new:
        raise ValueError("RED missing original #555 gameplay behavior")
    bot_path = out_path.parent / "GQ555_ORIGINAL_NEAREST_BOTACTORS.luau"
    if bot_path.exists() and bot_path.read_bytes() != new:
        raise ValueError("RED previous selector output drift")
    bot_path.write_bytes(new)
    selected_json = copy.deepcopy(base_json)
    selected_json["tree"]["ServerScriptService"]["EGGRUMBLE_BotActors"]["$path"] = bot_path.name
    out_path.write_text(json.dumps(selected_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, after = flatten(out_path)
    if changed_sources(source, after) != [BOT_KEY]:
        raise ValueError("RED changed a script other than existing BotActors")
    if after[BOT_KEY].read_bytes() != new:
        raise ValueError("RED selected original-author AI differs")
    receipt = {
        "source_count": N, "changed": ["ServerScriptService/EGGRUMBLE_BotActors"],
        "unchanged_other_scripts": N - 1,
        "original_gq555_head": "cd7d2cd6b39c7d5531a2b2d2437a523a6d09e32d",
        "base_project_sha256": sha(base_path.read_bytes()),
        "selected_project_sha256": sha(out_path.read_bytes()),
        "base_bot_sha256": sha(old), "on_bot_sha256": sha(new),
        "off_bot_sha256": sha(rollback), "on_off_exact": True,
        "rollback": "Select previous original #489 RC31 project, removing only #555 BotActors",
        "studio_android_art_fun_owner": "NOT_TESTED",
        "official_rc_commit_verified": False,
    }
    (out_path.parent / "GQ555_RC31_SELECTION_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ555_SINGLE_ORIGINAL_BOTACTORS_ONLY_OTHER30_BYTE_EXACT_PREP_PASS")

def embedded_scripts(place_path: Path):
    found = {}
    for element in ET.parse(place_path).iter("Item"):
        klass = element.attrib.get("class")
        if klass not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = element.find("Properties")
        if props is None:
            raise ValueError("RED missing real Rojo script properties")
        name = props.findtext("string[@name='Name']")
        content = props.findtext("ProtectedString[@name='Source']")
        if content is None:
            content = props.findtext("string[@name='Source']")
        if not name or content is None or name in found:
            raise ValueError("RED missing or duplicated real source")
        found[name] = (klass, content.replace("\r\n","\n"))
    if len(found) != N:
        raise ValueError("RED Rojo does not contain exactly 31 scripts")
    return found

def verify(base_path: Path, out_path: Path, place_path: Path, author_path: Path) -> None:
    _, base = flatten(base_path)
    _, selected = flatten(out_path)
    if changed_sources(base, selected) != [BOT_KEY]:
        raise ValueError("RED modified more than one original script")
    author = author_module(author_path)
    expected, off = author.apply(base[BOT_KEY].read_bytes())
    if off != base[BOT_KEY].read_bytes() or selected[BOT_KEY].read_bytes() != expected:
        raise ValueError("RED author patch/rollback drift")
    found = embedded_scripts(place_path)
    if set(found) != {k[-1] for k in selected}:
        raise ValueError("RED real Rojo changed canonical script names")
    for key, source_file in selected.items():
        expected_class = ("Script" if source_file.name.endswith(".server.luau") else
                          "LocalScript" if source_file.name.endswith(".client.luau") else "ModuleScript")
        expected_source = source_file.read_text(encoding="utf-8").replace("\r\n","\n")
        if found[key[-1]] != (expected_class, expected_source):
            raise ValueError("RED real Place Source/Class mismatched "+key[-1])
    receipt_path = out_path.parent / "GQ555_RC31_SELECTION_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt["on_bot_sha256"] != sha(selected[BOT_KEY].read_bytes()):
        raise ValueError("RED manifest selected AI SHA drift")
    receipt["true_rojo_scripts_source_class_exact"] = "31/31"
    receipt["place_bytes"] = place_path.stat().st_size
    receipt["place_sha256"] = sha(place_path.read_bytes())
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)+"\n", encoding="utf-8")
    print("GQ555_REAL_ROJO_CLASS_SOURCE_31_OF_31_PASS", place_path.stat().st_size, receipt["place_sha256"])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("prepare","verify"))
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--author", required=True, type=Path)
    p.add_argument("--place", type=Path)
    args = p.parse_args()
    if args.mode == "prepare":
        prepare(args.base, args.out, args.author)
    else:
        if args.place is None: p.error("--place required")
        verify(args.base, args.out, args.place, args.author)

if __name__ == "__main__":
    main()
