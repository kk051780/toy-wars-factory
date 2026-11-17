#!/usr/bin/env python3
"""Append exactly one pure policy ModuleScript to the *real* selected V3 31-source project.

No Combat/HP/Host code is replaced; ON32 is source-only and NOT game-connected.
OFF31 must preserve every old script byte, route and Roblox class.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

NAME = "ElementalAffinityPolicy"
MODULE = Path(__file__).resolve().parents[2] / "handoffs/EGGRUMBLE-ELEMENTAL-20261118/ElementalAffinityPolicy.luau"
FEATURE = "BATTLE-ELEMENT-RULES-OFFICIAL31-BRIDGE"


def inventory(p: Path):
    model = json.loads(p.read_text("utf-8"))
    tree = model.get("tree")
    if not isinstance(tree, dict):
        raise ValueError("RED_NO_ROJO_TREE")
    entries = {}

    def scan(node, key=()):
        for name, val in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(val, dict):
                raise ValueError("RED_BAD_ROJO_NODE")
            route = key + (name,)
            if "$path" in val:
                path = (p.parent / val["$path"]).resolve(strict=True)
                if route in entries:
                    raise ValueError("RED_DUPLICATE_SCRIPT")
                entries[route] = (path, copy.deepcopy(val))
            else:
                scan(val, route)

    scan(tree)
    return model, entries


def compose(source_project: Path, dest: Path, enabled: bool) -> dict:
    source_project = source_project.resolve(strict=True)
    dest = dest.resolve()
    if dest == source_project or dest.exists():
        raise ValueError("RED_REFUSE_OVERWRITE")
    if not MODULE.is_file():
        raise ValueError("RED_MISSING_POLICY_SOURCE")
    original, before = inventory(source_project)
    if len(before) != 31:
        raise ValueError("RED_SOURCE_IS_NOT_CANONICAL31")
    names = {route[-1] for route in before}
    if not {"EGGRUMBLE_LobbyCastleModesPreview", "EGGRUMBLE_SwarmCombat"}.issubset(names):
        raise ValueError("RED_MISSING_GAME_OR_SWARM")
    if NAME in names:
        raise ValueError("RED_DUPLICATE_POLICY_MODULE")

    result = copy.deepcopy(original)
    result["name"] = "EGGRUMBLE_V3_ELEMENT_RULES32_SOURCE_ONLY" if enabled else original.get("name", "OFF31")
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Move only the project-file-relative references; never copy or alter actual 31 source.
    def rebase(node, key=()):
        for name, val in node.items():
            if name.startswith("$"):
                continue
            here = key + (name,)
            if "$path" in val:
                val["$path"] = os.path.relpath(before[here][0], dest.parent).replace(os.sep, "/")
            else:
                rebase(val, here)

    rebase(result["tree"])
    if enabled:
        r = result["tree"].setdefault("ReplicatedStorage", {"$className": "ReplicatedStorage"})
        if not isinstance(r, dict) or NAME in r:
            raise ValueError("RED_REPLICATED_STORAGE_COLLISION")
        r[NAME] = {"$path": os.path.relpath(MODULE, dest.parent).replace(os.sep, "/")}
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf-8")
    _, after = inventory(dest)
    if len(after) != 31 + int(enabled):
        raise ValueError("RED_WRONG_SOURCE_COUNT")
    for route, (old_path, old_node) in before.items():
        if route not in after or old_path.read_bytes() != after[route][0].read_bytes():
            raise ValueError("RED_NOT_BYTE_EXACT_ORIGINAL31: " + "/".join(route))
        if old_node.get("$className") != after[route][1].get("$className"):
            raise ValueError("RED_OLD_CLASS_CHANGED: " + "/".join(route))
    if enabled:
        diff = set(after) - set(before)
        expected = ("ReplicatedStorage", NAME)
        if diff != {expected} or after[expected][0] != MODULE:
            raise ValueError("RED_NOT_ONE_MODULE")
    else:
        if set(before) != set(after):
            raise ValueError("RED_OFF_CHANGED_ROUTES")
    receipt = {
        "feature_id": FEATURE, "source_only_not_gameplay": True,
        "enabled": enabled, "source_count": len(after),
        "module_blob_sha256": hashlib.sha256(MODULE.read_bytes()).hexdigest() if enabled else None,
        "original31_exact": True, "original31_source_routes": ["/".join(x) for x in sorted(before)],
        "old_31_sha256": {"/".join(k): hashlib.sha256(p.read_bytes()).hexdigest() for k, (p, _) in before.items()},
        "studio": "NOT_TESTED", "android": "NOT_TESTED", "owner_fun": "NO_GO",
        "rc": "NOT_OFFICIALLY_ADOPTED", "no_second_damage_authority": True,
    }
    dest.with_suffix(".receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print("BATTLE_ELEMENT_REAL31_TO32_SOURCE_EXACT_PASS" if enabled else "BATTLE_ELEMENT_OFF31_EXACT_PASS")
    return receipt


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--current31", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--off", action="store_true")
    args=parser.parse_args()
    compose(args.current31, args.out, not args.off)


if __name__=="__main__":
    main()
