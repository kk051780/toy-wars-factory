#!/usr/bin/env python3
"""GQ8 successor DRI: preserve Real42 weather, Real43 neutral and add #812 existing Item silhouettes.

This is SOURCE selection for a private Studio candidate, never a second gameplay authority.
Official RC write is reserved to the authenticated #220 B writer with non-force CAS.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ITEM = ("ServerScriptService", "EGGRUMBLE_FieldItemPickups")
SWARM = ("ServerScriptService", "EGGRUMBLE_SwarmCombat")
NEUTRAL_POLICY = ("ServerScriptService", "EGGRUMBLE_NeutralFinisherPolicy")
FEATURE = "GQ8_REAL42_WEATHER_NEUTRAL43_ITEM_SCULPTURE_SOURCE_INTAKE_20261119"
FORMAL_PIN = "f77b4d4393d9e9b19b65566413432a7a9f13962b"


def load_python(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise ValueError("RED_MISSING_SOURCE_MODULE_" + name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flatten(project: Path):
    project = Path(project).resolve(strict=True)
    doc = json.loads(project.read_text(encoding="utf-8"))
    found = {}

    def walk(node, route=()):
        for name, item in node.items():
            if name.startswith("$"):
                continue
            child = route + (name,)
            if "$path" in item:
                if child in found:
                    raise ValueError("RED_DUPLICATE_AUTHORITY_" + "/".join(child))
                src = (project.parent / item["$path"]).resolve(strict=True)
                if not src.is_file():
                    raise ValueError("RED_MISSING_LUAU_SOURCE")
                found[child] = src
            else:
                walk(item, child)
    walk(doc["tree"])
    return doc, found


def relink(doc, sources, project_path):
    """Keep exact class suffix and source routes; relink all old paths to output project."""
    next_doc = copy.deepcopy(doc)

    def walk(node, route=()):
        for name, item in node.items():
            if name.startswith("$"):
                continue
            child = route + (name,)
            if "$path" in item:
                item["$path"] = os.path.relpath(sources[child], project_path.parent).replace(os.sep, "/")
            else:
                walk(item, child)
    walk(next_doc["tree"])
    return next_doc


def compose_item(original43: Path, patcher: Path, out: Path, portable: Path):
    original43 = Path(original43).resolve(strict=True)
    patcher = Path(patcher).resolve(strict=True)
    out = Path(out).resolve()
    portable = Path(portable).resolve()
    if out.exists() or portable.exists() or portable.parent.exists():
        raise ValueError("RED_REFUSE_OVERWRITE_SELECTED_SOURCE")
    doc, before = flatten(original43)
    if len(before) != 43 or set((ITEM, SWARM, NEUTRAL_POLICY)) - set(before):
        raise ValueError("RED_NOT_REAL43_SINGLETON_SOURCE")
    if "GQ800" not in doc.get("name", ""):
        raise ValueError("RED_MISSING_REAL43_NEUTRAL_ANCESTRY")
    for token in ("NeutralFinisherPolicy.select(", "KoFence.mayCredit", "neutralBudget:acquire"):
        if token not in before[SWARM].read_text(encoding="utf-8"):
            raise ValueError("RED_LOST_ACTUAL_NEUTRAL_SINGLE_OWNER_" + token)
    patch = load_python(patcher, "pinned_gq802_item_sculpture")
    original_item = before[ITEM].read_bytes()
    candidate = patch.apply(original_item)
    if patch.inverse(candidate) != original_item:
        raise ValueError("RED_GQ802_ITEM_REVERSE_MISMATCH")
    if original_item == candidate or patch.MARKER.encode() not in candidate:
        raise ValueError("RED_NO_REAL_ITEM_EDIT")
    for disallowed in ("RemoteEvent", "DataStoreService", "MarketplaceService"):
        if disallowed in candidate.decode() and disallowed not in original_item.decode():
            raise ValueError("RED_NEW_REMOTE_STORE_OR_CURRENCY_AUTHORITY")

    out.parent.mkdir(parents=True, exist_ok=True)
    suffix = (".server.luau" if before[ITEM].name.endswith(".server.luau") else
              ".client.luau" if before[ITEM].name.endswith(".client.luau") else ".luau")
    item_file = out.parent / ("GQ802_SelectedItemSculpture" + suffix)
    if item_file.exists():
        raise ValueError("RED_ITEM_SOURCE_EXISTS")
    item_file.write_bytes(candidate)
    selected_sources = dict(before)
    selected_sources[ITEM] = item_file
    selected_doc = relink(doc, selected_sources, out)
    selected_doc["name"] = "GQ8_REAL42_WEATHER_NEUTRAL8_ITEM3D_REAL43_PRIVATE_NOT_RC"
    out.write_text(json.dumps(selected_doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _, selected = flatten(out)
    if len(selected) != 43 or set(selected) != set(before):
        raise ValueError("RED_REAL43_SOURCE_ROUTE_NOT_PRESERVED")
    changed = [route for route in before if before[route].read_bytes() != selected[route].read_bytes()]
    if changed != [ITEM]:
        raise ValueError("RED_OTHER_REAL43_SOURCE_MUTATED_" + repr(changed))
    if selected[SWARM].read_bytes() != before[SWARM].read_bytes():
        raise ValueError("RED_SINGLE_SWARM_CHANGED")
    if selected[NEUTRAL_POLICY].read_bytes() != before[NEUTRAL_POLICY].read_bytes():
        raise ValueError("RED_NEUTRAL_FINISHER_POLICY_CHANGED")

    # Portable complete source; no fragile path reference back to other branches/artifacts.
    portable.parent.mkdir(parents=True, exist_ok=False)
    portable_doc = copy.deepcopy(selected_doc)
    portable_sources = {}
    for route, src in selected.items():
        name = src.name
        suffix = (".server.luau" if name.endswith(".server.luau") else
                  ".client.luau" if name.endswith(".client.luau") else
                  ".luau" if name.endswith(".luau") else None)
        if not suffix:
            raise ValueError("RED_NON_LUAU_SCRIPT_CLASS")
        relative = Path("sources").joinpath(*route[:-1], route[-1] + suffix)
        dest = portable.parent / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        portable_sources[route] = dest
    portable_doc = relink(portable_doc, portable_sources, portable)
    portable_doc["name"] = "GQ8_PORTABLE_REAL43_WEATHER_NEUTRAL_ITEM_NO_RC"
    portable.write_text(json.dumps(portable_doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _, packed = flatten(portable)
    if len(packed) != 43 or any(packed[k].read_bytes() != selected[k].read_bytes() for k in selected):
        raise ValueError("RED_PORTABLE_REAL43_CONTENT_OR_CLASS_DRIFT")

    receipt = {
        "feature_id": FEATURE,
        "base_formal_rc_sha": FORMAL_PIN,
        "source_start": "latest #796 weather42 portable, not formal RC",
        "second_stage": "original #815 Neutral8 single-Swarm / #801 Finisher into 43",
        "this_stage": "original #812 existing FieldItemPickups visual overlay",
        "existing_source_count": 43,
        "selected_source_count": 43,
        "changed_existing": ["/".join(ITEM)],
        "unchanged_existing": 42,
        "additional_remote_store_hp_score_authority": 0,
        "original_item_blob": patch.git_blob_sha(original_item),
        "selected_item_blob": patch.git_blob_sha(candidate),
        "neutral_swarm_sha256": hashlib.sha256(before[SWARM].read_bytes()).hexdigest(),
        "rollback": "Select exact incoming neutral43 Source: existing FieldItemPickups source only; weather42 and neutral43 remain byte exact",
        "official_rc_adopted": False,
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "kid_fun": "NO_GO",
    }
    (out.parent / "INTEGRATED_ITEM43_RECEIPT.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("GQ8_LATEST_WEATHER_NEUTRAL_ITEM43_ONE_AUTHORITY_SOURCE_SELECTION_PASS")
    return receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--weather42", type=Path, required=True)
    p.add_argument("--composer815", type=Path, required=True)
    p.add_argument("--swarm815", type=Path, required=True)
    p.add_argument("--policy801", type=Path, required=True)
    p.add_argument("--patch812", type=Path, required=True)
    p.add_argument("--neutral43", type=Path, required=True)
    p.add_argument("--selected43", type=Path, required=True)
    p.add_argument("--portable43", type=Path, required=True)
    a = p.parse_args()
    composer = load_python(a.composer815, "pinned_real43_single_swarm")
    if a.neutral43.exists():
        raise ValueError("RED_REFUSE_REAL43_OVERWRITE")
    composer.compose(a.weather42, a.swarm815, a.policy801, a.neutral43)
    compose_item(a.neutral43, a.patch812, a.selected43, a.portable43)


if __name__ == "__main__":
    main()
