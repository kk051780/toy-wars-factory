#!/usr/bin/env python3
"""Fail-closed one-source storm phase repair for the genuine #764 RealmCore.
No RC/main writer. Compose only the explicitly selected Core36 Script.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

SOURCE_BLOB = "1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1"
ROUTE = ("ServerScriptService", "EGGRUMBLE_RealmBattleCore")
ORIGINAL_TRANSITION = (
    '  if state.weather~=weather then\n'
    '   state.weather=weather;core:SetAttribute("RealmWeather",weather)\n'
    '  end\n'
)
PATCHED_TRANSITION = (
    '  if state.weather~=weather then\n'
    '   state.weather=weather;core:SetAttribute("RealmWeather",weather)\n'
    '   -- A storm warning is a promise only while THUNDER remains active.\n'
    '   -- Cancel a late warning at phase expiry; do not strike in CLEAR.\n'
    '   if weather~="THUNDER" then\n'
    '    state.pendingLightning=nil\n'
    '    core:SetAttribute("LightningWarning",false)\n'
    '   end\n'
    '  end\n'
)
ORIGINAL_STRIKE = '  if state.pendingLightning and now>=state.pendingLightning then\n'
PATCHED_STRIKE = '  if weather=="THUNDER" and state.pendingLightning and now>=state.pendingLightning then\n'


def blob_sha(source: bytes) -> str:
    payload = b"blob " + str(len(source)).encode("ascii") + b"\x00" + source
    return hashlib.sha1(payload).hexdigest()


def patch_source(source: bytes, *, verify_blob: bool = True) -> bytes:
    if verify_blob and blob_sha(source) != SOURCE_BLOB:
        raise ValueError("RED_REALM_AUTHOR_SOURCE_BLOB_CHANGED")
    body = source.decode("utf-8")
    if body.count(ORIGINAL_TRANSITION) != 1 or body.count(ORIGINAL_STRIKE) != 1:
        raise ValueError("RED_REALM_STORM_ANCHOR_CHANGED")
    fixed = body.replace(ORIGINAL_TRANSITION, PATCHED_TRANSITION, 1).replace(
        ORIGINAL_STRIKE, PATCHED_STRIKE, 1
    )
    # Inverse proves no unrelated Realm, combat, vehicle or environment edit.
    original = fixed.replace(PATCHED_TRANSITION, ORIGINAL_TRANSITION, 1).replace(
        PATCHED_STRIKE, ORIGINAL_STRIKE, 1
    )
    if original != body or fixed.count('state.pendingLightning=nil') != 2:
        raise ValueError("RED_UNREVIEWED_REALM_EDIT")
    return fixed.encode("utf-8")


def flatten(project: Path):
    project = project.resolve(strict=True)
    model = json.loads(project.read_text(encoding="utf-8"))
    if not isinstance(model.get("tree"), dict):
        raise ValueError("RED_NOT_ROJO_PROJECT")
    files = {}
    def walk(node, route=()):
        for name, child in node.items():
            if name.startswith("$"):
                continue
            if not isinstance(child, dict):
                raise ValueError("RED_BAD_ROJO_NODE")
            current = route + (name,)
            if "$path" in child:
                if current in files:
                    raise ValueError("RED_DUPLICATE_ROUTE")
                files[current] = (project.parent / child["$path"]).resolve(strict=True)
            else:
                walk(child, current)
    walk(model["tree"])
    return model, files


def compose36(project: Path, output: Path):
    project = project.resolve(strict=True)
    output = output.resolve()
    if output == project or output.exists():
        raise ValueError("RED_REFUSE_OVERWRITE")
    model, sources = flatten(project)
    if len(sources) != 36 or ROUTE not in sources or not {
        ("ServerScriptService", "EGGRUMBLE_SevenRoleCombat"),
        ("ServerScriptService", "EGGRUMBLE_SwarmCombat"),
        ("ServerScriptService", "EGGRUMBLE_NaturalRegen"),
    }.issubset(sources):
        raise ValueError("RED_NOT_REAL_CORE36")
    changed = patch_source(sources[ROUTE].read_bytes())
    out_dir = output.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    new_source = out_dir / "EGGRUMBLE_RealmBattleCore.StormPhaseFence.server.luau"
    if new_source.exists() or new_source.resolve() in sources.values():
        raise ValueError("RED_EXISTING_OUTPUT_SOURCE")
    selected = copy.deepcopy(model)
    selected["name"] = "EGGRUMBLE_V3_CORE36_REALM_STORM_PHASE_FENCE_PREP"
    def walk(node, route=()):
        for name, child in node.items():
            if name.startswith("$"):
                continue
            key = route + (name,)
            if "$path" in child:
                target = new_source if key == ROUTE else sources[key]
                child["$path"] = os.path.relpath(target, out_dir).replace(os.sep, "/")
            else:
                walk(child, key)
    walk(selected["tree"])
    new_source.write_bytes(changed)
    output.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, after = flatten(output)
    if len(after) != 36 or set(after) != set(sources):
        raise ValueError("RED_SOURCE_SET_CHANGED")
    for route, origin in sources.items():
        if route != ROUTE and after[route].read_bytes() != origin.read_bytes():
            raise ValueError("RED_UNRELATED_SCRIPT_DRIFT")
    if after[ROUTE].read_bytes() != changed:
        raise ValueError("RED_PATCHED_SOURCE_MISMATCH")
    receipt = {
        "feature_id": "GQ8_REALM_STORM_PHASE_FENCE_20261118",
        "baseline_count": 36, "output_count": 36,
        "only_changed": "/".join(ROUTE),
        "original_author_pr": 764, "original_author_head": "c51de1ed4feb7a7500ada95d21282402053ef988",
        "original_author_blob": SOURCE_BLOB,
        "preserved_other_sources": 35, "formal_rc_written": False,
        "studio_2client": "NOT_TESTED", "android_15min": "NOT_TESTED",
        "owner_fun": "NO_GO", "published": False,
        "rollback": "Select official unpatched CORE36 project (36 original sources)",
    }
    output.with_suffix(".receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--origin", type=Path)
    p.add_argument("--project36", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if (a.origin is None) == (a.project36 is None):
        p.error("exactly one of --origin or --project36 is required")
    if a.origin is not None:
        if a.out.exists():
            raise ValueError("RED_REFUSE_OVERWRITE")
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_bytes(patch_source(a.origin.read_bytes()))
    else:
        compose36(a.project36, a.out)
    print("GQ8_REALM_STORM_FENCE_PREP_SOURCE_EXACT_PASS")
