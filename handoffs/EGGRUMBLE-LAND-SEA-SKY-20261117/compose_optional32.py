#!/usr/bin/env python3
"""Non-destructive original31 -> optional Studio32 land/sea/sky composer.

Input must be the *current exact* official V3 selected 31-source .project.json
from the RC builder. This tool never touches the existing 31 source bytes or
the official branch. OFF selects the unchanged 31-source input.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

FEATURE = "GQ8_LAND_SEA_SKY_ROLE_TRAVERSAL_20261117"
NAME = "EGGRUMBLE_LandSeaSkyTraversal"
SCRIPT = Path(__file__).resolve().with_name(NAME + ".server.luau")


def flat(project: Path):
    model = json.loads(project.read_text(encoding="utf-8"))
    if "tree" not in model or not isinstance(model["tree"], dict):
        raise ValueError("RED_NO_ROJO_TREE")
    sources = {}

    def walk(node, keys):
        for key, val in node.items():
            if key.startswith("$"):
                continue
            if not isinstance(val, dict):
                raise ValueError("RED_MALFORMED_ROJO_ROUTE")
            here = keys + (key,)
            if "$path" in val:
                if any(v in val for v in ("$className", "$properties")) and not isinstance(val.get("$path"), str):
                    raise ValueError("RED_INVALID_SCRIPT_PATH")
                source = (project.parent / val["$path"]).resolve(strict=True)
                if not source.is_file() or here in sources:
                    raise ValueError("RED_DUPLICATE_OR_MISSING_SOURCE")
                sources[here] = source
            else:
                walk(val, here)
    walk(model["tree"], ())
    return model, sources


def overlay(canonical: Path, output: Path, enabled: bool = True):
    canonical = canonical.resolve(strict=True)
    output = output.resolve()
    if canonical == output or output.exists():
        raise ValueError("RED_OVERWRITE_EXISTING_PROJECT")
    if not SCRIPT.exists():
        raise ValueError("RED_MISSING_TRAVERSAL_AUTHOR_SCRIPT")
    model, before = flat(canonical)
    if len(before) != 31 or len(set(k[-1] for k in before)) != 31:
        raise ValueError("RED_NOT_CURRENT_31_SOURCE_BASE")
    if any(k[-1] == NAME for k in before):
        raise ValueError("RED_ALREADY_PRESENT")
    if not any(k[-1] == "EGGRUMBLE_LobbyCastleModesPreview" for k in before):
        raise ValueError("RED_NOT_V3_HOST")
    if not any(k[-1] == "EGGRUMBLE_SwarmCombat" for k in before):
        raise ValueError("RED_NOT_CANONICAL_SWARM")
    candidate = copy.deepcopy(model)
    candidate["name"] = "EGGRUMBLE_V3_STUDIO_LAND_SEA_SKY_OPTIONAL32" if enabled else model.get("name", "V3")
    server = candidate["tree"].get("ServerScriptService")
    if not isinstance(server, dict):
        raise ValueError("RED_NO_SERVER_SCRIPT_SERVICE")
    output.parent.mkdir(parents=True, exist_ok=True)

    def rebase(node, keys=()):
        for key, val in node.items():
            if key.startswith("$"):
                continue
            here = keys + (key,)
            if "$path" in val:
                val["$path"] = os.path.relpath(before[here], output.parent).replace(os.sep, "/")
            else:
                rebase(val, here)
    rebase(candidate["tree"])
    if enabled:
        if NAME in server:
            raise ValueError("RED_DUPLICATE_TRAVERSAL")
        server[NAME] = {"$path": os.path.relpath(SCRIPT, output.parent).replace(os.sep, "/")}

    output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    after_model, after = flat(output)
    expected = len(before) + (1 if enabled else 0)
    if len(after) != expected:
        raise ValueError("RED_WRONG_SOURCE_COUNT")
    for key, path in before.items():
        if key not in after or path.read_bytes() != after[key].read_bytes():
            raise ValueError("RED_CHANGED_ORIGINAL_SOURCE_" + "/".join(key))
    if enabled:
        new = [key for key in after if key not in before]
        if len(new) != 1 or new[0][-1] != NAME or after[new[0]] != SCRIPT:
            raise ValueError("RED_NOT_SINGLE_TRAVERSAL_ADDITION")
    receipt = {
        "feature_id": FEATURE,
        "input_31": str(canonical),
        "output": str(output),
        "enabled": enabled,
        "source_count": expected,
        "old_31_source_sha256": {
            "/".join(keys): hashlib.sha256(source.read_bytes()).hexdigest()
            for keys, source in before.items()
        },
        "new_source_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest() if enabled else None,
        "existing_31_byte_exact": True,
        "new_game_combat_swarm_remote_store": False,
        "production_rc_adopted": False,
        "studio_2_client": "NOT_TESTED",
        "android_15_min": "NOT_TESTED",
        "art_and_fun": "NO_GO",
    }
    receipt_path = output.with_suffix(".receipt.json")
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print("LSS_CURRENT31_32_SOURCE_EXACT" if enabled else "LSS_OFF_ORIGINAL31_UNCHANGED")
    return receipt


def verify_place(project: Path, place: Path):
    _, files = flat(project)
    expected = {key[-1]: path.read_text(encoding="utf-8").replace("\r\n", "\n")
                for key, path in files.items()}
    actual = {}
    for item in ET.parse(place).getroot().iter("Item"):
        if item.get("class") not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_NO_LUA_SOURCE")
        name = props.findtext("string[@name='Name']")
        src = props.findtext("ProtectedString[@name='Source']")
        if src is None:
            src = props.findtext("string[@name='Source']")
        if not name or src is None or name in actual:
            raise ValueError("RED_MISSING_OR_DUPLICATE_ROJO_SCRIPT")
        actual[name] = src.replace("\r\n", "\n")
    if expected != actual:
        raise ValueError("RED_SELECTED_ROJO_SOURCE_MISMATCH")
    print("LSS_REAL_ROJO_SOURCE_EXACT", len(actual), hashlib.sha256(place.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current31", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--off", action="store_true")
    parser.add_argument("--place", type=Path)
    args = parser.parse_args()
    overlay(args.current31, args.out, not args.off)
    if args.place:
        verify_place(args.out, args.place)


if __name__ == "__main__":
    main()
