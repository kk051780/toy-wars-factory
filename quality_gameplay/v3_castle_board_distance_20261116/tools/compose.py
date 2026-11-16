#!/usr/bin/env python3
"""Fail-closed, author-preserving PRIVATE EGGRUMBLE castle board distance fix.

ONLY generated Host is changed. Original V3 21-script project sources are untouched.
Never merges, publishes, or writes official RC.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
AUTHOR = REPO / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
SOURCE = AUTHOR / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
PROJECT = AUTHOR / "EGGRUMBLE_V3_STUDIO.project.json"
AUTHOR_HEAD = "fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9"
ORIGINAL_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
HOST_NODE = "EGGRUMBLE_LobbyCastleModesPreview"

def git_blob(source: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(source)).encode("ascii") + b"\0" + source).hexdigest()

def patch(original: str) -> str:
    if git_blob(original.encode("utf-8")) != ORIGINAL_BLOB:
        raise ValueError("SOURCE_LOCK: original #482 Host blob drift; STOP and reconcile")
    if original.count("b.AlwaysOnTop=true") != 1:
        raise ValueError("Unexpected original board definition")
    repairs = [
        ("core", 65, 160, 48),
        ("vault", 40, 115, 36),
    ]
    current = original
    for name, distance, width, height in repairs:
        pattern = rf"(?m)^[ \t]*board\({name},[^\n]+\)$"
        if len(re.findall(pattern, current)) != 1:
            raise ValueError(f"SOURCE_LOCK: {name} board anchor not unique")
        addition = (
            f"\n local {name}Board={name}:FindFirstChildOfClass(\"BillboardGui\")"
            f"\n if {name}Board then"
            f"\n  {name}Board.AlwaysOnTop=false"
            f"\n  {name}Board.MaxDistance={distance}"
            f"\n  {name}Board.Size=UDim2.fromOffset({width},{height})"
            f"\n end"
        )
        current, n = re.subn(pattern, lambda m: m.group(0) + addition, current)
        if n != 1:
            raise ValueError("Replacement not unique")
    return current

def walk_project(tree: dict, out: Path) -> tuple[dict, int]:
    copied = copy.deepcopy(tree)
    scripts = 0

    def visit(node: dict, path: tuple[str, ...] = ()) -> None:
        nonlocal scripts
        for key, value in node.items():
            if key == "$path":
                scripts += 1
                if path[-1] == HOST_NODE:
                    node[key] = "HostOverlay.server.luau"
                else:
                    target = (AUTHOR / value).resolve()
                    if not target.is_file() or not target.is_relative_to(AUTHOR.resolve()):
                        raise ValueError(f"Missing / escaped original source: {target}")
                    node[key] = os.path.relpath(target, out).replace("\\", "/")
            elif isinstance(value, dict):
                visit(value, path + (key,))
    visit(copied)
    if scripts != 21:
        raise ValueError(f"Unexpected original source count: {scripts} != 21")
    return copied, scripts

def compose(out: Path) -> dict:
    original_bytes = SOURCE.read_bytes()
    if git_blob(original_bytes) != ORIGINAL_BLOB:
        raise ValueError("Pinned original source SHA mismatch")
    original = original_bytes.decode("utf-8")
    patched = patch(original)
    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    mapped, count = walk_project(project, out)
    mapped["name"] = "EGGRUMBLE_V3_BOARD_DISTANCE_PRIVATE_NOT_RC"
    (out / "HostOverlay.server.luau").write_text(patched, encoding="utf-8", newline="")
    (out / "private.project.json").write_text(
        json.dumps(mapped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    receipt = {
        "feature": "GQ_V3_CASTLE_BOARD_DISTANCE_CULL_20261116",
        "author_head": AUTHOR_HEAD,
        "original_host_blob": ORIGINAL_BLOB,
        "patched_host_blob": git_blob(patched.encode("utf-8")),
        "source_count": count,
        "modified_original_script_count": 1,
        "mode": "PRIVATE_SOURCE_ONLY",
        "formal_rc": "NOT_INTEGRATED",
        "studio_android": "NOT_TESTED",
        "rollback": "Remove HostOverlay and use the exact original 21-script author project",
    }
    (out / "receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return receipt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compose(args.out.resolve()), ensure_ascii=False, indent=2))
