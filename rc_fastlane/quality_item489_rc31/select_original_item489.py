#!/usr/bin/env python3
"""Select existing original #489 ITEM in exactly one canonical V3 31-source map.
Source-only preview for #220 authenticated writer; no alternate Game/ITEM/Remote.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

ORIGINAL_ITEM_BLOB = "24a35a2e6004c635456cc6f2288cf13f8365ba27"
AUTHOR489_ITEM_BLOB = "107046cb0bf81fed9e3cba1699ada31571e44a22"
AUTHOR489_COMMIT = "03c51bf5c8d12484bd8dc4667b0d3d3841cb4ddd"
ITEM_NAME = "EGGRUMBLE_FieldItemPickups"
ITEM_KEY = ("ServerScriptService", ITEM_NAME)
N = 31


def git_blob(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def flatten(path: Path):
    project = json.loads(path.read_text(encoding="utf-8"))
    scripts = {}
    def scan(node, prefix=()):
        for name, value in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("Invalid project node")
            key = prefix + (name,)
            if "$path" in value:
                if set(value) != {"$path"}:
                    raise ValueError("Project path has unexpected metadata")
                f = (path.parent / value["$path"]).resolve(strict=True)
                if key in scripts:
                    raise ValueError("Repeated Script key")
                scripts[key] = f
            else:
                scan(value, key)
    scan(project["tree"])
    if len(scripts) != N or len({k[-1] for k in scripts}) != N:
        raise ValueError("Expected exactly one unique 31-script map")
    if ITEM_KEY not in scripts:
        raise ValueError("Missing original ITEM source")
    for single in ("EGGRUMBLE_LobbyCastleModesPreview",
                   "EGGRUMBLE_SevenRoleCombat", "EGGRUMBLE_SwarmCombat"):
        if sum(k[-1] == single for k in scripts) != 1:
            raise ValueError("Duplicate authority " + single)
    return project, scripts


def author_guard(item: bytes) -> None:
    if git_blob(item) != AUTHOR489_ITEM_BLOB:
        raise ValueError("Original #489 ITEM source blob drift")
    source = item.decode("utf-8")
    for anchor in ("local function restoreSpeed()",
                   "if not matchActive() or player.Character~=buffCharacter then return end",
                   "if kind~=\"HEAL\" and carryingEnemyEggs(player,session) then return end",
                   'interactionGuard.allow(player,part,"拾う",part.Name)'):
        if source.count(anchor) != 1:
            raise ValueError("Expected #489 original gameplay safety missing: " + anchor)


def prepare(base_project: Path, original489: Path, out_project: Path):
    base_project = base_project.resolve(strict=True)
    original489 = original489.resolve(strict=True)
    if out_project.resolve() == base_project:
        raise ValueError("Refuse modifying the authoritative base map")
    if base_project.parent.resolve() != out_project.parent.resolve():
        raise ValueError("Output must be beside original project to preserve all other 30 paths")
    base, scripts = flatten(base_project)
    old = scripts[ITEM_KEY].read_bytes()
    if git_blob(old) != ORIGINAL_ITEM_BLOB:
        raise ValueError("Original ITEM not #482; do not duplicate an existing author adoption")
    item_bytes = original489.read_bytes()
    author_guard(item_bytes)
    parent = out_project.parent
    author_path = parent / "GQ_ITEM489_ORIGINAL_AUTHOR_SINGLE.luau"
    if author_path.exists() and author_path.read_bytes() != item_bytes:
        raise ValueError("Existing selected Item source drift")
    author_path.write_bytes(item_bytes)
    selected = copy.deepcopy(base)
    selected["tree"]["ServerScriptService"][ITEM_NAME]["$path"] = author_path.name
    out_project.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, rebuilt = flatten(out_project)
    if set(rebuilt) != set(scripts):
        raise ValueError("Script key/class layout changed")
    changed = [key for key in scripts if scripts[key].read_bytes() != rebuilt[key].read_bytes()]
    if changed != [ITEM_KEY]:
        raise ValueError("Expected one original Item source replacement only: " + repr(changed))
    if rebuilt[ITEM_KEY].read_bytes() != item_bytes:
        raise ValueError("New Item bytes not source-author exact")
    receipt = {
        "canonical_source_count": N,
        "changed_sources": ["/".join(ITEM_KEY)],
        "unchanged_source_count": N - 1,
        "original_author489_commit": AUTHOR489_COMMIT,
        "original489_item_git_blob": AUTHOR489_ITEM_BLOB,
        "replaced_original482_git_blob": ORIGINAL_ITEM_BLOB,
        "base_project_sha256": sha(base_project.read_bytes()),
        "selected_project_sha256": sha(out_project.read_bytes()),
        "selected_item_sha256": sha(item_bytes),
        "base_item_sha256": sha(old),
        "off_project": base_project.name,
        "on_project": out_project.name,
        "rollback": "Do not select ON project; keep original 31-source base project",
        "formal_rc_adopted": False,
        "studio_android_owner": "NOT_TESTED",
    }
    (parent / "GQ_ITEM489_RC31_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("GQ_ITEM489_ORIGINAL_AUTHOR_ONLY_CHANGED_ONE_OF_31", len(changed), "ALL_30_OTHER_AUTHORS_BYTE_EXACT=PASS")


def verify(base_project: Path, selected_project: Path, place: Path):
    _, old = flatten(base_project)
    _, current = flatten(selected_project)
    if set(old) != set(current):
        raise ValueError("Source count or names changed")
    changed = [key for key in old if old[key].read_bytes() != current[key].read_bytes()]
    if changed != [ITEM_KEY]:
        raise ValueError("Not a single Item change")
    author_guard(current[ITEM_KEY].read_bytes())
    found = {}
    for item in ET.parse(place).iter("Item"):
        class_name = item.attrib.get("class")
        if class_name not in ("Script", "ModuleScript", "LocalScript"):
            continue
        props = item.find("Properties")
        if props is None:
            continue
        name = props.findtext("string[@name='Name']")
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if not name or source is None or name in found:
            raise ValueError("Missing or duplicate Place source")
        found[name] = (class_name, source.replace("\r\n", "\n"))
    if set(found) != {k[-1] for k in current}:
        raise ValueError("Real Place doesn't embed exact 31 source names")
    for key, file in current.items():
        expected_class = ("Script" if file.name.endswith(".server.luau") else
                          "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if found[key[-1]] != (expected_class, file.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("Real Rojo class/Source mismatch: " + key[-1])
    data = json.loads((selected_project.parent / "GQ_ITEM489_RC31_SOURCE_RECEIPT.json").read_text())
    data["private_place_bytes"] = place.stat().st_size
    data["private_place_sha256"] = sha(place.read_bytes())
    data["real_rojo_source_and_class_exact"] = "31/31"
    (selected_project.parent / "GQ_ITEM489_RC31_SOURCE_RECEIPT.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("GQ_ITEM489_RC31_PRIVATE_REAL_ROJO_SOURCE_CLASS_EXACT_PASS", N,
          "PLACE_BYTES", place.stat().st_size, "SHA256", sha(place.read_bytes()))
    print("SOURCE_CANDIDATE_ONLY_NOT_OFFICIAL_RC_STUDIO_ANDROID_OWNER_NOT_TESTED")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["prepare", "verify"])
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--item", type=Path)
    p.add_argument("--place", type=Path)
    a = p.parse_args()
    if a.action == "prepare":
        if a.item is None:
            p.error("--item required")
        prepare(a.base, a.item, a.out)
    else:
        if a.place is None:
            p.error("--place required")
        verify(a.base, a.out, a.place)


if __name__ == "__main__":
    main()
