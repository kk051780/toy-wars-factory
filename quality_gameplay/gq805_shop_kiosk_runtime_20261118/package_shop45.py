#!/usr/bin/env python3
"""Package 41 original source-locked scripts plus 4 additive GQ805 shop scripts.

Strictly offline. Cannot write official RC, main, Store, Roblox or purchased inventory.
Authenticates upstream #796 41-source receipt and immutable original #808 Git blobs.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

CANDIDATE_NEW = {
    ("ServerScriptService", "GQ805_LobbyGuildShop"): ("GQ805_LobbyGuildShop.server.luau", ".server.luau", "Script"),
    ("StarterPlayer", "StarterPlayerScripts", "GQ805_ShopKioskClient"): ("GQ805_ShopKioskClient.client.luau", ".client.luau", "LocalScript"),
    ("ReplicatedStorage", "GQ805Shop", "EGGRUMBLE_LobbyShopCatalog"): ("_catalog_", ".luau", "ModuleScript"),
    ("ReplicatedStorage", "GQ805Shop", "EGGRUMBLE_LobbyShopView"): ("_view_", ".luau", "ModuleScript"),
}
UPSTREAM_CATALOG_BLOB = "f71eb575aacd61dd8ccb7719f7dae4caec5fedcd"
UPSTREAM_VIEW_BLOB = "f3cf10c8b0256896e9d194844deda91039429ddc"
PARENT_SOURCE_COUNT = 41
OUTPUT_SOURCE_COUNT = 45
REQUIRED_ORIGINAL_ROUTES = {
    ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview"),
    ("ServerScriptService", "EGGRUMBLE_SwarmCombat"),
    ("ServerScriptService", "EGGRUMBLE_CastleMatchRules"),
}
SAFE_ROUTE = re.compile(r"[A-Za-z0-9_]+")
SHA40 = re.compile(r"[0-9a-f]{40}")


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def class_of(file: Path) -> tuple[str, str]:
    for suffix, klass in ((".server.luau", "Script"), (".client.luau", "LocalScript"), (".luau", "ModuleScript")):
        if file.name.endswith(suffix):
            return suffix, klass
    raise ValueError("RED_UNSUPPORTED_SCRIPT_SUFFIX")


def flatten(project: Path) -> tuple[dict, dict[tuple[str, ...], Path]]:
    project = project.resolve(strict=True)
    doc = json.loads(project.read_text(encoding="utf8"))
    if not isinstance(doc.get("tree"), dict):
        raise ValueError("RED_PROJECT_TREE_NOT_DICT")
    out: dict[tuple[str, ...], Path] = {}

    def walk(node: dict, route: tuple[str, ...] = ()) -> None:
        for name, child in node.items():
            if name.startswith("$"):
                continue
            if not SAFE_ROUTE.fullmatch(name) or not isinstance(child, dict):
                raise ValueError("RED_UNSAFE_ROUTE")
            key = route + (name,)
            if "$path" in child:
                if key in out or not isinstance(child["$path"], str):
                    raise ValueError("RED_DUPLICATE_SOURCE_PATH")
                out[key] = (project.parent / child["$path"]).resolve(strict=True)
            else:
                walk(child, key)

    walk(doc["tree"])
    return doc, out


def package(parent41: Path, receipt41: Path, catalog: Path, view: Path,
            kiosk: Path, out: Path, expected_parent_head: str) -> dict:
    if not SHA40.fullmatch(expected_parent_head):
        raise ValueError("RED_PARENT_HEAD_REQUIRED")
    if out.exists():
        raise ValueError("RED_DO_NOT_REUSE_PORTABLE_FOLDER")
    parent_doc, parent_sources = flatten(parent41)
    receipt = json.loads(receipt41.read_text(encoding="utf8"))
    if receipt.get("candidate_sha") != expected_parent_head:
        raise ValueError("RED_WRONG_UPSTREAM_DRI_HEAD")
    if receipt.get("source_count") != PARENT_SOURCE_COUNT or len(parent_sources) != PARENT_SOURCE_COUNT:
        raise ValueError("RED_REAL41_COUNT_MISMATCH")
    if not REQUIRED_ORIGINAL_ROUTES.issubset(parent_sources):
        raise ValueError("RED_MISSING_ORIGINAL_SINGLETONS")
    old_ledger = receipt.get("sources", [])
    if len(old_ledger) != PARENT_SOURCE_COUNT:
        raise ValueError("RED_REAL41_SOURCE_RECEIPT_INCOMPLETE")
    locked = {}
    for entry in old_ledger:
        route = tuple(entry["route"].split("/"))
        if route in locked or not SHA40.fullmatch(entry["git_blob"]):
            raise ValueError("RED_DUPLICATED_OR_BAD_41_RECEIPT")
        locked[route] = entry
    if set(locked) != set(parent_sources):
        raise ValueError("RED_PARENT_41_ROUTE_DRIFT")
    for route, src in parent_sources.items():
        payload = src.read_bytes()
        ext, klass = class_of(src)
        data = locked[route]
        if (git_blob(payload) != data["git_blob"] or
            hashlib.sha256(payload).hexdigest() != data["sha256"] or
            klass != data["class"] or len(payload) != data["bytes"]):
            raise ValueError("RED_REAL41_SOURCE_CLASS_OR_SHA_DRIFT_" + "/".join(route))
    if git_blob(catalog.read_bytes()) != UPSTREAM_CATALOG_BLOB:
        raise ValueError("RED_CATALOG_808_AUTHOR_DRIFT")
    if git_blob(view.read_bytes()) != UPSTREAM_VIEW_BLOB:
        raise ValueError("RED_SHOPVIEW_808_AUTHOR_DRIFT")
    if set(parent_sources).intersection(CANDIDATE_NEW):
        raise ValueError("RED_DUPLICATED_EXISTING_SHOP_ROUTE")
    provided = {
        "_catalog_": catalog.resolve(strict=True),
        "_view_": view.resolve(strict=True),
    }
    new_paths = {}
    for route, (name, extension, klass) in CANDIDATE_NEW.items():
        src = provided.get(name, kiosk / name)
        src = src.resolve(strict=True)
        if not src.is_file():
            raise ValueError("RED_MISSING_ADDITIVE_SOURCE")
        new_paths[route] = (src, extension, klass)
    client = new_paths[("StarterPlayer", "StarterPlayerScripts", "GQ805_ShopKioskClient")][0].read_text(encoding="utf8")
    if not all(x in client for x in ("View.mount(", "Catalog.list()", "robuxEnabled=false", "nil)")):
        raise ValueError("RED_KIOSK_CANNOT_BE_READONLY")
    out.mkdir(parents=True)
    result = copy.deepcopy(parent_doc)
    result["name"] = "EGGRUMBLE_REAL45_KIOSK_PRIVATE_NOT_OFFICIAL_RC"
    ledger = []

    def install(route: tuple[str, ...], payload: bytes, suffix: str, klass: str, origin: str) -> None:
        for key in route:
            if not SAFE_ROUTE.fullmatch(key):
                raise ValueError("RED_OUTPUT_ROUTE_TRAVERSAL")
        dest = Path("sources").joinpath(*route[:-1], route[-1] + suffix)
        target = out / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise ValueError("RED_OUTPUT_PATH_COLLISION")
        target.write_bytes(payload)
        node = result["tree"]
        for depth, name in enumerate(route[:-1]):
            if name not in node:
                # Rojo knows top-level services but custom intermediate containers
                # MUST explicitly declare a Roblox class (not an untyped JSON node).
                node[name] = {} if depth == 0 else {"$className": "Folder"}
            node = node[name]
        node[route[-1]] = {"$path": dest.as_posix()}
        ledger.append({
            "route": "/".join(route),
            "path": dest.as_posix(),
            "class": klass,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "git_blob": git_blob(payload),
            "origin": origin,
        })

    for route, path in sorted(parent_sources.items()):
        suffix, klass = class_of(path)
        install(route, path.read_bytes(), suffix, klass, "original_796_source_locked")
    for route, (src, suffix, klass) in sorted(new_paths.items()):
        origin = "original_808_byte_exact_module_source" if route[-1].startswith("EGGRUMBLE_") else "new_816_private_runtime_source"
        install(route, src.read_bytes(), suffix, klass, origin)
    project = out / "EGGRUMBLE_REAL45_KIOSK.project.json"
    project.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf8")
    _, checked = flatten(project)
    if len(checked) != OUTPUT_SOURCE_COUNT or set(checked) != set(parent_sources) | set(CANDIDATE_NEW):
        raise ValueError("RED_READBACK_45_COUNT_OR_ROUTE")
    for route, path in parent_sources.items():
        if path.read_bytes() != checked[route].read_bytes():
            raise ValueError("RED_PARENT_41_MUTATED")
        if class_of(path)[1] != class_of(checked[route])[1]:
            raise ValueError("RED_PARENT_41_CLASS_MUTATED")
    for route, (path, suffix, klass) in new_paths.items():
        if path.read_bytes() != checked[route].read_bytes() or class_of(checked[route])[1] != klass:
            raise ValueError("RED_ADDITIVE_SOURCE_OR_CLASS_MUTATED")
    report = {
        "feature_id": "GQ805_3D_SHOP_KIOSK_RUNTIME_20261118",
        "source_count": OUTPUT_SOURCE_COUNT,
        "base_source_count": PARENT_SOURCE_COUNT,
        "unchanged_original_count": PARENT_SOURCE_COUNT,
        "original_parent_pr": 796,
        "original_parent_sha": expected_parent_head,
        "existing_shop_policy_pr": 808,
        "module_class_override_without_source_edit": "EGGRUMBLE_LobbyShopView",
        "new_script_count": 2,
        "reused_script_count": 2,
        "official_rc_cas": False,
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "shop_purchase": "OFF_NOT_INTEGRATED",
        "rollback": "Remove four GQ805 routes -> original 41 Source+Class exact",
        "original41_readback_pass": True,
        "sources": ledger,
    }
    (out / "B_PRIVATE45_SOURCE_RECEIPT.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf8")
    print("GQ805_PRIVATE_REAL45_SOURCE_CLASS_AND_OFF41_EXACT", sum(e["bytes"] for e in ledger))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--real41", type=Path, required=True)
    ap.add_argument("--receipt41", type=Path, required=True)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--view", type=Path, required=True)
    ap.add_argument("--kiosk", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--expected-parent-head", required=True)
    a = ap.parse_args()
    package(a.real41, a.receipt41, a.catalog, a.view, a.kiosk, a.out, a.expected_parent_head)
