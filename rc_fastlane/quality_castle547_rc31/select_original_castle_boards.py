#!/usr/bin/env python3
"""Original #547 source-selective castle/vault board LOD on existing V3 RC31 Host.

This is not a second castle implementation. The *two exact insertions* are
extracted from the original #547 immutable author composer applied to the exact
#482 source blob. Every other existing script is kept byte-identical.
Native/Rojo verification belongs to the pinned official workflow.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

AUTHOR_SHA = "b8c6774a3b9b886dd46c60dd9e8722c0cb6a4125"
AUTHOR_COMPOSER_BLOB = "e8b38e0cbb4f9ae330bc958ffb8f5dc00b66002c"
ORIGINAL_HOST_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
HOST = "EGGRUMBLE_LobbyCastleModesPreview"
SRC_COUNT = 31
TARGETS = ("core", "vault")
AUTHOR_FILE = Path("_gq547_original/quality_gameplay/v3_castle_board_distance_20261116/tools/compose.py")
SOURCE_FILE = Path("_gq547_original/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_LobbyCastleModesPreview.server.luau")
TYPES = {"Script", "ModuleScript", "LocalScript"}


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_mapping(project: Path) -> tuple[dict, dict[tuple[str, ...], Path]]:
    data = json.loads(project.read_text(encoding="utf-8"))
    found = {}
    def walk(node: dict, route: tuple[str, ...] = ()):
        for key, value in node.items():
            if not isinstance(value, dict):
                continue
            path = route + (key,)
            if "$path" in value:
                if set(value) != {"$path"}:
                    raise ValueError("RED competing source map: " + "/".join(path))
                file = (project.parent / value["$path"]).resolve()
                if not file.is_file() or path in found:
                    raise ValueError("RED missing/duplicate source: " + "/".join(path))
                found[path] = file
            else:
                walk(value, path)
    walk(data["tree"])
    if len(found) != SRC_COUNT or len({r[-1] for r in found}) != SRC_COUNT:
        raise ValueError("RED not a unique real 31-script project")
    if len([r for r in found if r[-1] == HOST]) != 1:
        raise ValueError("RED existing Host not unique")
    return data, found


def author_insertions(original: str, original_patched: str) -> dict[str, tuple[str, str]]:
    """Derive only two original-author inserted blocks; fail on any other author diff."""
    changes = {}
    recovered = original_patched
    for name in TARGETS:
        matches = list(re.finditer(rf"(?m)^[ \t]*board\({name},[^\n]+\)$", original))
        if len(matches) != 1:
            raise ValueError("RED original #547 source call anchor changed: " + name)
        old_line = matches[0].group(0)
        if original_patched.count(old_line) != 1:
            raise ValueError("RED original #547 composer changed call: " + name)
        pos = original_patched.index(old_line) + len(old_line)
        end = original_patched.find("\n end", pos)
        if end < 0:
            raise ValueError("RED original insertion terminator missing")
        insertion = original_patched[pos:end + len("\n end")]
        if not (insertion.startswith(f'\n local {name}Board={name}:FindFirstChildOfClass("BillboardGui")')
                and f"{name}Board.AlwaysOnTop=false" in insertion
                and f"{name}Board.MaxDistance=" in insertion
                and f"{name}Board.Size=UDim2.fromOffset(" in insertion):
            raise ValueError("RED original #547 author insertion drift")
        if recovered.count(old_line + insertion) != 1:
            raise ValueError("RED author insertion not unique")
        recovered = recovered.replace(old_line + insertion, old_line, 1)
        changes[name] = (old_line, insertion)
    if recovered != original:
        raise ValueError("RED original #547 author changed game logic besides 2 existing boards")
    return changes


def original_author_changes() -> dict[str, tuple[str, str]]:
    if not AUTHOR_FILE.is_file() or blob(AUTHOR_FILE.read_bytes()) != AUTHOR_COMPOSER_BLOB:
        raise ValueError("RED original #547 composer blob mismatched")
    if not SOURCE_FILE.is_file() or blob(SOURCE_FILE.read_bytes()) != ORIGINAL_HOST_BLOB:
        raise ValueError("RED original #482 Host blob mismatched")
    module = importlib.machinery.SourceFileLoader("gq547_original_pinned", str(AUTHOR_FILE)).load_module()
    original = SOURCE_FILE.read_text(encoding="utf-8")
    patched = module.patch(original)
    return author_insertions(original, patched)


def patch(current: str, changes: dict[str, tuple[str, str]]) -> str:
    if "local function nearbyBoard(" not in current or "gui.MaxDistance=math.clamp(maxDistance,16,52)" not in current:
        raise ValueError("RED prior official #539 role/mode lobby patch missing")
    if "session.refresh=function()" not in current or "c.vaultEggs" not in current:
        raise ValueError("RED prior official castle HP/egg authority missing")
    for name in TARGETS:
        old_line, chunk = changes[name]
        if current.count(old_line) != 1 or chunk in current or f"{name}Board.MaxDistance=" in current:
            raise ValueError("RED existing " + name + " board call drift / duplicate GQ547")
        current = current.replace(old_line, old_line + chunk, 1)
    return current


def undo(current: str, changes: dict[str, tuple[str, str]]) -> str:
    for name in TARGETS:
        old_line, chunk = changes[name]
        if current.count(old_line + chunk) != 1:
            raise ValueError("RED cannot roll back exact GQ547 " + name + " insertion")
        current = current.replace(old_line + chunk, old_line, 1)
    return current


def select(base: Path, out: Path, host_blob: str) -> dict:
    project, old = source_mapping(base)
    route = next(r for r in old if r[-1] == HOST)
    host_path = old[route]
    raw = host_path.read_bytes()
    if blob(raw) != host_blob:
        raise ValueError("RED official input Host git blob source-lock drift")
    previous = raw.decode("utf-8")
    changes = original_author_changes()
    selected = patch(previous, changes)
    if undo(selected, changes) != previous:
        raise ValueError("RED GQ547 OFF rollback is not byte exact")
    if selected.count('Instance.new("BillboardGui")') != previous.count('Instance.new("BillboardGui")'):
        raise ValueError("RED new UI authority")
    out.mkdir(parents=True, exist_ok=True)
    new_host = out / "GQ547_CastleBoards.server.luau"
    new_host.write_bytes(selected.encode("utf-8"))
    tree = copy.deepcopy(project)
    def rewrite(node: dict, parents: tuple[str, ...] = ()) -> None:
        for name, value in node.items():
            if not isinstance(value, dict):
                continue
            key = parents + (name,)
            if "$path" in value:
                desired = new_host if key == route else old[key]
                value["$path"] = os.path.relpath(desired, out).replace(os.sep, "/")
            else:
                rewrite(value, key)
    rewrite(tree["tree"])
    final = out / "GQ547_SELECTED31.project.json"
    final.write_text(json.dumps(tree, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, resolved = source_mapping(final)
    if resolved.keys() != old.keys():
        raise ValueError("RED script routes changed")
    if sum(resolved[key].read_bytes() != old[key].read_bytes() for key in old) != 1:
        raise ValueError("RED unexpected count of changed sources")
    for key in old:
        if key != route and resolved[key].read_bytes() != old[key].read_bytes():
            raise ValueError("RED non-Host source changed: " + "/".join(key))
    receipt = {
        "status": "RC_CANDIDATE_NOT_OFFICIAL_UNTIL_CAS",
        "source_count": SRC_COUNT,
        "modified_existing_scripts": 1,
        "unchanged_existing_scripts": 30,
        "author547_fixed_head": AUTHOR_SHA,
        "author547_composer_blob": AUTHOR_COMPOSER_BLOB,
        "original482_host_blob": ORIGINAL_HOST_BLOB,
        "input_host_blob": host_blob,
        "output_host_blob": blob(selected.encode("utf-8")),
        "roll_back_to_previous_canonical_host_exact": True,
        "distance_core": 65,
        "distance_vault": 40,
        "original_lobby_and_prior_role_logic_preserved": True,
        "original_castle_hp_and_egg_authority_preserved": True,
        "studio_android_owner": "NOT_TESTED",
    }
    (out / "GQ547_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def verify(base: Path, selected: Path, place: Path) -> dict:
    _, before = source_mapping(base)
    _, after = source_mapping(selected)
    if set(before) != set(after):
        raise ValueError("RED selected script routes changed")
    changes = original_author_changes()
    changed = [route for route in after if before[route].read_bytes() != after[route].read_bytes()]
    if len(changed) != 1 or changed[0][-1] != HOST:
        raise ValueError("RED selected extra scripts")
    route = changed[0]
    if undo(after[route].read_text(encoding="utf-8"), changes) != before[route].read_text(encoding="utf-8"):
        raise ValueError("RED rollback differs from immediate official Host")
    xml = ET.fromstring(place.read_bytes())
    actual = {}
    for item in xml.iter("Item"):
        kind = item.attrib.get("class")
        if kind not in TYPES:
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED missing Roblox Script Props")
        name = props.findtext("string[@name='Name']")
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if not name or source is None or name in actual:
            raise ValueError("RED duplicate or empty Script in Place")
        actual[name] = (kind, source.replace("\r\n", "\n"))
    if len(actual) != SRC_COUNT or {key[-1] for key in after} != set(actual):
        raise ValueError("RED Rojo 31-script name mismatch")
    for route, file in after.items():
        kind = ("Script" if file.name.endswith(".server.luau") else
                "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if actual[route[-1]] != (kind, file.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED Rojo Source/Class mismatch: " + route[-1])
    return {
        "status": "PRIVATE_RC_PR_NATIVE_ROJO_PASS_PENDING_OFFICIAL_CAS",
        "script_count": SRC_COUNT,
        "rojo_exact": "31/31",
        "unchanged_other_scripts": 30,
        "modified_existing_host_only": True,
        "rollback_byte_exact": True,
        "place_bytes": place.stat().st_size,
        "place_sha256": digest(place.read_bytes()),
        "studio_android_owner": "NOT_TESTED",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("select", "verify"))
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--host-blob")
    p.add_argument("--place", type=Path)
    args = p.parse_args()
    if args.action == "select":
        if not args.host_blob:
            p.error("select requires pinned --host-blob")
        print(json.dumps(select(args.base, args.out, args.host_blob), ensure_ascii=False, indent=2))
    else:
        if not args.place:
            p.error("verify requires --place")
        print(json.dumps(verify(args.base, args.out, args.place), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
