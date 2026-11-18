#!/usr/bin/env python3
"""Select #792's ONE original-author Realm station authorization fix in genuine Core36.

This composes an actual 36-source Rojo project from genuine official31 -> original
#764 Realm -> original #775 Regen -> original #780 Core36. It is strictly PREP:
only the authenticated #220 B writer may CAS the canonical RC selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from patch_realm_station_los import (
    FEATURE_ID, UPSTREAM_BLOB, UPSTREAM_HEAD, apply, git_blob_sha, rollback,
)

TARGET = ("ServerScriptService", "EGGRUMBLE_RealmBattleCore")
SCRIPT_COUNT = 36
OFF_COUNT = 31


def flatten(project: Path) -> dict[tuple[str, ...], Path]:
    project = project.resolve(strict=True)
    model = json.loads(project.read_text(encoding="utf8"))
    tree = model["tree"]
    files: dict[tuple[str, ...], Path] = {}

    def walk(node: dict, route: tuple[str, ...] = ()):
        for name, value in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(value, dict):
                raise ValueError("RED_BAD_ROJO_PROJECT_CHILD")
            here = route + (name,)
            if "$path" in value:
                if here in files:
                    raise ValueError("RED_DUPLICATE_ROUTE")
                source = (project.parent / value["$path"]).resolve(strict=True)
                if source.suffix != ".luau":
                    raise ValueError("RED_NON_LUAU_SCRIPT")
                files[here] = source
            else:
                walk(value, here)

    walk(tree)
    return files


def compose(real36: Path, baseline31: Path, out: Path):
    real36 = real36.resolve(strict=True)
    baseline31 = baseline31.resolve(strict=True)
    out = out.resolve()
    if out.exists() or out == real36 or out.parent != real36.parent:
        raise ValueError("RED_OVERWRITE_OR_MISMATCHED_OUTPUT")
    original = flatten(real36)
    old = flatten(baseline31)
    if len(original) != SCRIPT_COUNT or len(old) != OFF_COUNT:
        raise ValueError("RED_NOT_TRUE_CORE36_PLUS_31")
    if TARGET not in original or TARGET in old:
        raise ValueError("RED_REALM_ROUTE_ORIGINAL_BASE_DRIFT")
    selected_source = original[TARGET].read_bytes()
    if git_blob_sha(selected_source) != UPSTREAM_BLOB:
        raise ValueError("RED_REALM_AUTHOR_SOURCE_DOES_NOT_MATCH_SELECTED_CORE36")
    modified_source = apply(selected_source)
    if rollback(modified_source) != selected_source:
        raise ValueError("RED_REALM_STATION_LOS_OFF_INVERSE")
    patched_file = out.parent / "GQ8_RealmBattleCore_StationLOS.server.luau"
    if patched_file.exists():
        raise ValueError("RED_SELECTED_SOURCE_FILE_EXISTS")
    patched_file.write_bytes(modified_source)
    model = json.loads(real36.read_text(encoding="utf8"))
    child = model["tree"]
    for part in TARGET:
        child = child[part]
    child["$path"] = os.path.relpath(patched_file, out.parent).replace(os.sep, "/")
    model["name"] = "EGGRUMBLE_REALM_STATION_LOS_CORE36_PREP"
    out.write_text(json.dumps(model, indent=2, ensure_ascii=False)+"\n", encoding="utf8")
    actual = flatten(out)
    if set(actual) != set(original) or len(actual) != 36:
        raise ValueError("RED_NOT_THE_EXACT_SAME_36_SCRIPT_ROUTES")
    changed = [route for route in original if original[route].read_bytes() != actual[route].read_bytes()]
    if changed != [TARGET]:
        raise ValueError("RED_NOT_ONLY_REALM_SERVER_PATCH")
    if any(x.read_bytes() != old[r].read_bytes() for r, x in flatten(baseline31).items()):
        raise ValueError("RED_OFF31_SOURCE_MUTATION")
    receipt = {
        "feature_id": FEATURE_ID,
        "mode": "SOURCE_PREP_ONLY_NOT_OFFICIAL_RC",
        "source_count": 36,
        "baseline_off31_source_count": 31,
        "author_head": UPSTREAM_HEAD,
        "original_realm_git_blob": UPSTREAM_BLOB,
        "replacement_realm_git_blob": git_blob_sha(modified_source),
        "real36_routes_preserved": True,
        "only_one_modified_existing_author_script": "/".join(TARGET),
        "non_target_35_byte_exact": True,
        "off31_original_unchanged": True,
        "new_gameplay_scripts": 0,
        "new_game_damage_or_score_authority": 0,
        "source_sha256": hashlib.sha256(modified_source).hexdigest(),
        "official_rc_adopted": False,
        "main_changed": False,
        "published": False,
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "fun_first3min": "NO_GO",
    }
    out.with_suffix(".receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False)+"\n", encoding="utf8"
    )
    return receipt


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--project", type=Path, required=True)
    a.add_argument("--off31", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    args = a.parse_args()
    print(json.dumps(compose(args.project, args.off31, args.out), ensure_ascii=False))


if __name__ == "__main__":
    main()
