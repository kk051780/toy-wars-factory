#!/usr/bin/env python3
"""GQ8 #839: source-loss-proof 55+4 HUD/Fog+2 Trade preview = candidate 61.

This is the sole cross-candidate composition gate, NOT a new gameplay owner.
It deliberately refuses to claim formal RC adoption or player-quality PASS.
"""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gq8_successor_real48_shop_20261119"))
from compose_real48 import flatten, klass  # reuse verified original source-route reader

PROFILE = "eggrumble_v3_real55"
BASE_COUNT = 55
COMBINED_COUNT = 61
REQUIRED = {
    ("ServerScriptService", "EGGRUMBLE_SevenRoleCombat"),
    ("ServerScriptService", "EGGRUMBLE_SwarmCombat"),
    ("ServerScriptService", "EGGRUMBLE_InvulRuntime"),
    ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview"),
    ("ServerScriptService", "EGGRUMBLE_MusouFeverPolicy"),
    ("ServerScriptService", "GQ8_LobbySocialPlaza"),
    ("ReplicatedStorage", "GQ8Trade", "GQ8_TradePolicy"),
}
SUFFIX = {"Script": ".server.luau", "LocalScript": ".client.luau",
          "ModuleScript": ".luau"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SAFE_PART = re.compile(r"^[A-Za-z0-9_]+$")


def red(name: str):
    raise ValueError("RED_" + name)


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_manifest(path: Path) -> dict:
    m = json.loads(path.read_text(encoding="utf8"))
    if (m.get("schema") != "GQ8_REAL61_HUD_TRADE_CROSS_LANE_SOURCE_CANDIDATE_V1"
        or m.get("parent_source_count") != BASE_COUNT
        or m.get("source_count") != COMBINED_COUNT
        or m.get("source_profile") != "eggrumble_v3_real61_candidate"
        or m.get("adoption_status") != "CANDIDATE_NOT_FORMALLY_ADOPTED"):
        red("MANIFEST_IDENTITY")
    src = m.get("new_sources")
    if not isinstance(src, list) or len(src) != COMBINED_COUNT - BASE_COUNT:
        red("NEW_SOURCE_COUNT")
    if {int(row["pr"]) for row in src} != {829, 838}:
        red("UNREVIEWED_SOURCE_OWNER")
    routes = []
    for row in src:
        route = tuple(row["route"].split("/"))
        if not route or not all(SAFE_PART.fullmatch(x) for x in route):
            red("INVALID_ROUTE")
        if row["class"] not in SUFFIX:
            red("UNSAFE_CLASS")
        if not HEX40.fullmatch(row["blob"]) or not HEX40.fullmatch(row["head"]):
            red("UNPINNED_SOURCE")
        if not isinstance(row["path"], str) or ".." in Path(row["path"]).parts:
            red("UNSAFE_AUTHOR_PATH")
        routes.append(route)
    if len(set(routes)) != len(routes):
        red("DUPLICATE_ADDITION")
    if {int(row["pr"]) for row in m.get("pending_intersection", [])} != {840, 841}:
        red("HIDDEN_PENDING_AUTHOR_WORK")
    if m["acceptance"]["shop_trade_live"] or m["acceptance"]["purchases"] or m["acceptance"]["roblox_published"]:
        red("UNSAFE_PUBLICATION_CLAIM")
    return m


def fetch_inputs(m: dict, out: Path, repository: str) -> dict:
    """Fetch exact immutable candidate source blobs and verify PR head path."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        red("BAD_GITHUB_REPO")
    if out.exists():
        red("REFUSE_INPUT_OVERWRITE")
    out.mkdir(parents=True)
    result = {}
    for i, row in enumerate(m["new_sources"]):
        url = "repos/" + repository + "/contents/" + row["path"] + "?ref=" + row["head"]
        metadata = json.loads(subprocess.check_output(["gh", "api", url], text=True))
        if metadata.get("sha") != row["blob"] or metadata.get("type") != "file":
            red("CANDIDATE_PR_PATH_BLOB_CHANGED_" + str(i))
        blobdoc = json.loads(subprocess.check_output(
            ["gh", "api", "repos/" + repository + "/git/blobs/" + row["blob"]], text=True))
        if blobdoc.get("encoding") != "base64":
            red("BLOB_NOT_BASE64")
        body = base64.b64decode(blobdoc["content"], validate=False)
        if git_blob(body) != row["blob"]:
            red("GIT_BLOB_CONTENT_MISMATCH")
        target = out / (f"{i:02d}" + SUFFIX[row["class"]])
        target.write_bytes(body)
        result[tuple(row["route"].split("/"))] = target
    return result


def compose(parent55: Path, receipt55: Path, manifest: dict, inputs: dict,
            out: Path) -> dict:
    if out.exists():
        red("REFUSE_OVERWRITE")
    old_doc, old = flatten(parent55)
    receipt = json.loads(receipt55.read_text(encoding="utf8"))
    if (len(old) != BASE_COUNT
        or receipt.get("source_profile") != PROFILE
        or receipt.get("selected_official_branch_sha") != manifest["baseline_official_head"]
        or receipt.get("official_rc_adopted") is not True
        or receipt.get("selected_real55_count") != BASE_COUNT):
        red("UNVERIFIED_OFFICIAL_REAL55")
    if not REQUIRED.issubset(old):
        red("MISSING_ORIGINAL_GAME_AUTHORITY")
    ledger = {}
    for row in receipt.get("sources", []):
        route = tuple(row["route"].split("/"))
        if route in ledger:
            red("DUPLICATE_PARENT_LEDGER")
        ledger[route] = row
    if set(ledger) != set(old):
        red("ORIGINAL55_RECEIPT_ROUTE_MISMATCH")
    for route, path in old.items():
        body = path.read_bytes()
        rec = ledger[route]
        if rec["sha256"] != sha(body) or rec["bytes"] != len(body) or rec["class"] != klass(path):
            red("ORIGINAL55_SOURCE_CLASS_OR_HASH_DRIFT_" + "/".join(route))
    incoming = {tuple(x["route"].split("/")): x for x in manifest["new_sources"]}
    if set(incoming) != set(inputs) or set(incoming) & set(old):
        red("SOURCE_ROUTE_LOSS_OR_COLLISION")
    for route, row in incoming.items():
        path = inputs[route]
        body = path.read_bytes()
        if git_blob(body) != row["blob"] or klass(path) != row["class"]:
            red("AUTHOR_GIT_BLOB_OR_CLASS_DRIFT_" + "/".join(route))
    # HUD may only read or send filtered map data; trade remains in preview-only mode.
    hud = [inputs[r].read_text(encoding="utf8") for r in incoming
           if incoming[r]["pr"] == 829]
    trade = [inputs[r].read_text(encoding="utf8") for r in incoming
             if incoming[r]["pr"] == 838]
    if any("OnServerEvent:Connect(" in s or "FireServer(" in s for s in hud):
        red("HUD_REMOTE_AUTHORITY")
    if any(bad in "".join(trade) for bad in
           ("DataStoreService", "UpdateAsync(", "SetAsync(", "ProcessReceipt",
            "MarketplaceService", "PromptProductPurchase", "FireServer(")):
        red("TRADE_PREVIEW_GRANT_OR_PAYMENT")
    selected = copy.deepcopy(old_doc)
    selected["name"] = "GQ8_REAL61_HUD_INTEL_TRADE_PREVIEW_PRIVATE_CANDIDATE"
    records = []

    def put(route: tuple, body: bytes, cls: str, origin: str):
        file = out.joinpath("sources", *route[:-1], route[-1] + SUFFIX[cls])
        if file.exists():
            red("FILE_PATH_COLLISION")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(body)
        node = selected["tree"]
        for depth, part in enumerate(route[:-1]):
            if part not in node:
                node[part] = {} if depth == 0 else {"$className": "Folder"}
            node = node[part]
        node[route[-1]] = {"$path": file.relative_to(out).as_posix()}
        records.append({"route": "/".join(route), "class": cls,
                        "bytes": len(body), "sha256": sha(body),
                        "git_blob": git_blob(body), "origin": origin})

    for route, path in sorted(old.items()):
        put(route, path.read_bytes(), klass(path), "IMMUTABLE_OFFICIAL_REAL55")
    for route, row in sorted(incoming.items()):
        put(route, inputs[route].read_bytes(), row["class"],
            "PR" + str(row["pr"]) + "_" + row["head"])
    project = out / "EGGRUMBLE_REAL61_CANDIDATE.project.json"
    project.write_text(json.dumps(selected, ensure_ascii=False, indent=2,
                                  sort_keys=True) + "\n", encoding="utf8")
    _, rebuilt = flatten(project)
    if len(rebuilt) != COMBINED_COUNT or set(rebuilt) != (set(old) | set(incoming)):
        red("REAL61_ACTUAL_SOURCE_COUNT")
    for route, path in old.items():
        if rebuilt[route].read_bytes() != path.read_bytes() or klass(rebuilt[route]) != klass(path):
            red("ORIGINAL55_LOST_OR_CHANGED")
    for route in incoming:
        if rebuilt[route].read_bytes() != inputs[route].read_bytes():
            red("NEW_FEATURE_DROPPED")
    report = {
        "schema": "GQ8_REAL61_CROSS_CANDIDATE_SOURCE_RECEIPT_V1",
        "source_count": 61, "official_baseline_source_count": 55,
        "original55_bytes_and_class_preserved": True,
        "new_hud_fog_sources": 4, "new_trade_preview_sources": 2,
        "feature_ids": ["GQ8_HUD_INTEL_FOG_20261119",
                        "GQ8_TRADE_UX_JOURNAL_20261119"],
        "pending_unmerged_prs": [840, 841],
        "official_rc_adopted": False,
        "studio_2client": "NOT_TESTED", "android_15min": "NOT_TESTED",
        "first3min_fun": "NOT_TESTED", "product_acceptance": "NO_GO",
        "paid_trade": False, "roblox_published": False,
        "rollback": "Select exact official Real55 source/project; current 61 is not formal",
        "scripts": records
    }
    (out / "B_REAL61_CANDIDATE_RECEIPT.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf8")
    print("GQ8_REAL61_PARENT55_PRESERVED_HUD4_TRADE2_NONOVERLAP_PASS")
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("fetch", "compose"))
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--inputs", required=True, type=Path)
    p.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    p.add_argument("--parent55", type=Path)
    p.add_argument("--receipt55", type=Path)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    m = checked_manifest(a.manifest)
    if a.command == "fetch":
        fetch_inputs(m, a.inputs, a.repository)
    else:
        if not a.parent55 or not a.receipt55 or not a.out:
            p.error("compose requires --parent55 --receipt55 --out")
        files = {tuple(r["route"].split("/")):
                 a.inputs / (f"{i:02d}" + SUFFIX[r["class"]])
                 for i, r in enumerate(m["new_sources"])}
        compose(a.parent55, a.receipt55, m, files, a.out)


if __name__ == "__main__":
    main()
