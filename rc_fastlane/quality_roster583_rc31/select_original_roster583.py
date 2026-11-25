#!/usr/bin/env python3
"""Source-select existing original #583 two roster guards into current RC31 Rules.

Reuses pinned original author patch_source() and native_harness(); does not create
another game, rules module, 32nd runtime script or second player-admission owner.
Must run after all earlier official selections (currently #508).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR_SHA = "60b67c8dade80ff7ccd1d97e03480ba333977084"
AUTHOR_SCRIPT_BLOB = "d7c1a8cbc86e32fc4f92617ba91a9245a598286e"
ORIGINAL_RULES_BLOB = "27da5ca1e9e6d9a7afe0674030e387f094ee7492"
AUTHOR = Path("_gq583_original/quality_gameplay/v3_roster_hardcap16_20261116/select_roster16.py")
ORIGINAL = Path("_v3_original/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_CastleMatchRules.luau")
RULES = "EGGRUMBLE_CastleMatchRules"
COUNT = 31
TYPES = {"Script", "ModuleScript", "LocalScript"}


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_author():
    if not AUTHOR.is_file() or git_blob(AUTHOR.read_bytes()) != AUTHOR_SCRIPT_BLOB:
        raise ValueError("RED #583 original source-author Python blob drift")
    if not ORIGINAL.is_file() or git_blob(ORIGINAL.read_bytes()) != ORIGINAL_RULES_BLOB:
        raise ValueError("RED #482 original Rules blob drift")
    author = importlib.machinery.SourceFileLoader("gq583_immutable_roster_author", str(AUTHOR)).load_module()
    original = ORIGINAL.read_text(encoding="utf-8")
    # Exact original two-hunk edit, never a replacement rules engine.
    patched = author.patch_source(original)
    if undo(patched, author) != original:
        raise ValueError("RED original #583 author patch isn't reversible")
    return author, original, patched


def undo(patched: str, author) -> str:
    result = patched
    for old, new in zip(author.OLD, author.NEW):
        if result.count(new) != 1:
            raise ValueError("RED missing/duplicate exact original #583 guard")
        result = result.replace(new, old, 1)
    return result


def map_sources(project: Path) -> tuple[dict, dict[tuple[str, ...], Path]]:
    data = json.loads(project.read_text(encoding="utf-8"))
    found = {}
    def visit(node: dict, route: tuple[str, ...]=()):
        for name, value in node.items():
            if not isinstance(value, dict):
                continue
            path = route + (name,)
            if "$path" in value:
                if set(value) != {"$path"}:
                    raise ValueError("RED unexpected Rojo mapped source node")
                file = (project.parent / value["$path"]).resolve()
                if not file.is_file() or path in found:
                    raise ValueError("RED nonexistent or duplicate source in 31")
                found[path] = file
            else:
                visit(value, path)
    visit(data["tree"])
    if len(found) != COUNT or len({route[-1] for route in found}) != COUNT:
        raise ValueError("RED selected project must have 31 unique scripts")
    if sum(route[-1] == RULES for route in found) != 1:
        raise ValueError("RED must select exactly one existing CastleMatchRules ModuleScript")
    return data, found


def patch_current(current: str, author, original: str, expected: str) -> str:
    # No "best effort" replacement on drift: source remains exact original #482.
    if git_blob(current.encode("utf-8")) != expected:
        raise ValueError("RED current Rules git blob source-lock drift")
    if current != original or expected != ORIGINAL_RULES_BLOB:
        raise ValueError("RED original #482 Rules changed since original #583 patch; reconcile first")
    selected = author.patch_source(current)
    if undo(selected, author) != current:
        raise ValueError("RED OFF rollback mismatch")
    if selected.count("M.MAX_HERO_SLOTS=16") != 1:
        raise ValueError("RED max roster invariant changed")
    return selected


def select(base: Path, out: Path, host_blob: str) -> dict:
    author, original, _ = load_author()
    project, before = map_sources(base)
    route = next(k for k in before if k[-1] == RULES)
    old_path = before[route]
    if not old_path.name.endswith(".luau") or old_path.name.endswith(".server.luau") or old_path.name.endswith(".client.luau"):
        raise ValueError("RED CastleMatchRules Script Class is not ModuleScript")
    old_raw = old_path.read_bytes()
    selected = patch_current(old_raw.decode("utf-8"), author, original, host_blob)
    if undo(selected, author).encode("utf-8") != old_raw:
        raise ValueError("RED rollback was not byte exact")
    out.mkdir(parents=True, exist_ok=True)
    destination = out / "GQ583_CastleMatchRules.luau"
    destination.write_bytes(selected.encode("utf-8"))
    new_project = copy.deepcopy(project)
    def modify(tree: dict, parents: tuple[str, ...] = ()):
        for name, node in tree.items():
            if not isinstance(node, dict):
                continue
            key = parents + (name,)
            if "$path" in node:
                p = destination if key == route else before[key]
                node["$path"] = os.path.relpath(p, out).replace(os.sep, "/")
            else:
                modify(node, key)
    modify(new_project["tree"])
    output = out / "GQ583_SELECTED31.project.json"
    output.write_text(json.dumps(new_project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, final = map_sources(output)
    changed = [key for key in before if before[key].read_bytes() != final[key].read_bytes()]
    if changed != [route]:
        raise ValueError("RED expected exactly one changed existing Rules module")
    if any(final[key].read_bytes() != before[key].read_bytes() for key in before if key != route):
        raise ValueError("RED other 30 original sources modified")
    receipt = {
        "status": "SOURCE_RC_CANDIDATE_NOT_ADOPTED",
        "script_count": COUNT,
        "changed_script_count": 1,
        "other_30_byte_exact": True,
        "rollback_byte_exact": True,
        "existing_module_only": "/".join(route),
        "original_author_sha": AUTHOR_SHA,
        "author_selector_blob": AUTHOR_SCRIPT_BLOB,
        "original_rules_blob": ORIGINAL_RULES_BLOB,
        "previous_current_rules_blob": git_blob(old_raw),
        "selected_rules_blob": git_blob(selected.encode("utf-8")),
        "previous_rules_sha256": sha256(old_raw),
        "selected_rules_sha256": sha256(selected.encode("utf-8")),
        "TEAM_BR_MAX_HERO_SLOTS": 16,
        "changed_guards": 2,
        "studio_android_owner": "NOT_TESTED",
    }
    (out / "GQ583_SELECTED_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def verify(base: Path, selected: Path, place: Path) -> dict:
    author, original, _ = load_author()
    _, previous = map_sources(base)
    _, current = map_sources(selected)
    if set(previous) != set(current):
        raise ValueError("RED Rojo script key drift")
    changed = [key for key in previous if previous[key].read_bytes() != current[key].read_bytes()]
    if len(changed) != 1 or changed[0][-1] != RULES:
        raise ValueError("RED selected other scripts")
    route = changed[0]
    if previous[route].read_text(encoding="utf-8") != original:
        raise ValueError("RED the original castle rules changed before apply")
    if undo(current[route].read_text(encoding="utf-8"), author) != original:
        raise ValueError("RED OFF did not restore exact CastleMatchRules")
    xml = ET.fromstring(place.read_bytes())
    actual = {}
    for item in xml.iter("Item"):
        kind = item.attrib.get("class")
        if kind not in TYPES:
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED Roblox Place script properties missing")
        name = props.findtext("string[@name='Name']")
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if not name or source is None or name in actual:
            raise ValueError("RED empty/duplicate Roblox script name or Source")
        actual[name] = (kind, source.replace("\r\n","\n"))
    if len(actual) != COUNT or set(actual) != {route[-1] for route in current}:
        raise ValueError("RED script keys not 31")
    for path, file in current.items():
        kind = ("Script" if file.name.endswith(".server.luau") else
                "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if actual[path[-1]] != (kind,file.read_text(encoding="utf-8").replace("\r\n","\n")):
            raise ValueError("RED real Rojo Source/Class exact failed for " + path[-1])
    return {
        "status": "RC_CANDIDATE_SELECTED_NOT_OFFICIALLY_ADOPTED",
        "source_exact": "31/31",
        "script_count": COUNT,
        "existing_only_one_rules_changed": True,
        "other_30_scripts_byte_exact": True,
        "off_rollback_byte_exact": True,
        "place_bytes": place.stat().st_size,
        "place_sha256": sha256(place.read_bytes()),
        "studio_android_owner": "NOT_TESTED",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("select","verify"))
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--host-blob",default="")
    p.add_argument("--place",type=Path)
    a=p.parse_args()
    if a.action=="select":
        if not a.host_blob:
            raise ValueError("RED select needs exact current CastleMatchRules blob")
        info=select(a.base,a.out,a.host_blob)
    else:
        if not a.place:
            raise ValueError("RED verify needs actual Place")
        info=verify(a.base,a.out,a.place)
    print(json.dumps(info,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
