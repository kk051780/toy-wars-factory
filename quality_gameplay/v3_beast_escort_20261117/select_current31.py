#!/usr/bin/env python3
"""GQ618: source-select one BEAST skill inside the existing real 31-script V3 project.

Selection is an isolated candidate: NEVER update official ref or modify author files.
Fail-closed on previous Combat sha256, one specified route, 31 unique scripts,
other30 identical sources, exact inverse OFF, actual Rojo Source/Class.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from compose_single_combat import compose, rollback

COUNT = 31
COMBAT = ("ServerScriptService", "EGGRUMBLE_SevenRoleCombat")
FEATURE_ID = "GQ_BEAST_ESCORT_REAL_UNIT_20261117"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def inspect(project: Path) -> tuple[dict, dict]:
    project = project.resolve(strict=True)
    p = json.loads(project.read_text(encoding="utf-8"))
    result: dict[tuple[str, ...], Path] = {}

    def walk(node, route=()):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("RED_INVALID_PROJECT_NODE")
            k = (*route, key)
            if "$path" in value:
                if set(value) != {"$path"} or k in result:
                    raise ValueError("RED_DUPLICATE_PROJECT_ROUTE")
                result[k] = (project.parent / value["$path"]).resolve(strict=True)
            else:
                walk(value, k)
    if "tree" not in p:
        raise ValueError("RED_MISSING_PROJECT_TREE")
    walk(p["tree"])
    if len(result) != COUNT or len({route[-1] for route in result}) != COUNT:
        raise ValueError("RED_NOT_31_SINGLE_AUTHOR_NAMES")
    if COMBAT not in result:
        raise ValueError("RED_NO_SINGLE_COMBAT")
    for k, source in result.items():
        if source.suffix != ".luau" or not source.is_file():
            raise ValueError("RED_MISSING_SOURCE_" + "/".join(k))
    return p, result


def prepare(base: Path, out: Path, runtime: Path, expected_sha256: str) -> None:
    base, out = base.resolve(strict=True), out.resolve()
    if out.parent != base.parent or out == base or out.exists():
        raise ValueError("RED_NO_OVERWRITE_OR_FOREIGN_PROJECT")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("RED_SOURCE_SHA_FORMAT")
    project, original = inspect(base)
    combat_raw = original[COMBAT].read_bytes()
    if sha(combat_raw) != expected_sha256:
        raise ValueError("RED_CURRENT_COMBAT_SOURCE_LOCK_SHA")
    runtime_text = runtime.resolve(strict=True).read_text(encoding="utf-8")
    selected, inline = compose(combat_raw.decode("utf-8"), runtime_text)
    if rollback(selected, inline).encode("utf-8") != combat_raw:
        raise ValueError("RED_EXACT_OFF_INVERSE")
    out_combat = out.parent / "GQ618_BEAST_EXISTING_COMBAT_SELECTED.luau"
    if out_combat.exists():
        raise ValueError("RED_REFUSE_OVERWRITE_SELECTED_COMBAT")
    out_combat.write_text(selected, encoding="utf-8")
    chosen = copy.deepcopy(project)
    chosen["tree"][COMBAT[0]][COMBAT[1]]["$path"] = out_combat.name
    out.write_text(json.dumps(chosen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, final = inspect(out)
    if set(original) != set(final):
        raise ValueError("RED_SOURCE_ROUTES_CHANGED")
    diffs = [route for route in original if original[route].read_bytes() != final[route].read_bytes()]
    if diffs != [COMBAT]:
        raise ValueError("RED_NOT_EXACTLY_ONE_COMBAT_SELECTED")
    receipt = dict(
        feature_id=FEATURE_ID,
        exact_original_combat_sha256=sha(combat_raw),
        exact_selected_combat_sha256=sha(selected.encode()),
        source_count=31,
        original_30_scripts_byte_identical=True,
        off_previous_combat_exact=True,
        no_second_game_combat_remote_store_score_authority=True,
        source_gate="SOURCE_CANDIDATE_ONLY",
        formal_rc_adopted=False,
        studio_android_art_fun_owner="NOT_TESTED",
    )
    (out.parent / "GQ618_CURRENT31_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ618_CURRENT31_SINGLE_COMBAT_SELECT_OTHER30_EXACT_OFF_PASS")


def verify(base: Path, out: Path, runtime: Path, place: Path, expected_sha256: str) -> None:
    _, first = inspect(base)
    _, final = inspect(out)
    if set(first) != set(final):
        raise ValueError("RED_SCRIPT_SET_MISMATCH")
    current_raw = first[COMBAT].read_bytes()
    if sha(current_raw) != expected_sha256:
        raise ValueError("RED_EXPECTED_COMBAT_CHANGED_BEFORE_VERIFY")
    selected, inline = compose(current_raw.decode("utf-8"), runtime.read_text(encoding="utf-8"))
    if final[COMBAT].read_text(encoding="utf-8") != selected:
        raise ValueError("RED_SELECTED_COMBAT_DRIFT")
    if rollback(selected, inline).encode() != current_raw:
        raise ValueError("RED_OFF_NOT_EXACT")
    for route in first:
        if route != COMBAT and first[route].read_bytes() != final[route].read_bytes():
            raise ValueError("RED_OTHER_30_SCRIPT_DRIFT")
    entries = {}
    for item in ET.parse(place).iter("Item"):
        kind = item.attrib.get("class")
        if kind not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        if props is None:
            raise ValueError("RED_MISSING_SOURCE_PROPERTIES")
        name = props.findtext("string[@name='Name']")
        source = props.findtext("ProtectedString[@name='Source']")
        if source is None:
            source = props.findtext("string[@name='Source']")
        if not name or source is None or name in entries:
            raise ValueError("RED_SOURCE_DUPLICATE_OR_ABSENT")
        entries[name] = kind, source.replace("\r\n", "\n")
    expected_names = {route[-1] for route in final}
    if len(entries) != COUNT or set(entries) != expected_names:
        raise ValueError("RED_ROJO_NOT_EXACT_CURRENT31")
    for route, source in final.items():
        name = route[-1]
        kind = ("Script" if source.name.endswith(".server.luau") else
                "LocalScript" if source.name.endswith(".client.luau") else "ModuleScript")
        expected = (kind, source.read_text(encoding="utf-8").replace("\r\n", "\n"))
        if entries[name] != expected:
            raise ValueError("RED_ROJO_SOURCE_CLASS_NOT_EXACT_" + name)
    receipt_path = out.parent / "GQ618_CURRENT31_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt.update(
        actual_native31="MUST_BE_RUN_SEPARATELY_BY_CI",
        actual_rojo31_source_class="31/31",
        private_place_bytes=place.stat().st_size,
        private_place_sha256=sha(place.read_bytes()),
        formal_rc_adopted=False,
    )
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("GQ618_CURRENT31_TRUE_ROJO_SOURCE_CLASS_EXACT_31_PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["prepare", "verify"])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--place", type=Path)
    args = ap.parse_args()
    if args.action == "prepare":
        prepare(args.base, args.out, args.runtime, args.expected_sha256)
    else:
        if args.place is None:
            ap.error("verify requires --place")
        verify(args.base, args.out, args.runtime, args.place, args.expected_sha256)


if __name__ == "__main__":
    main()
