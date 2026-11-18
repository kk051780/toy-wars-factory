#!/usr/bin/env python3
"""Evidence-only nine-domain receipt for the immutable Real53 source selection.

This does NOT certify playable behavior, native execution, Roblox Studio, Android,
or official RC adoption. It refuses stale/incomplete/unverified source receipts.
Distinct from author composers: no source authorship, no Host/Remote modifications.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

N = 55
ROUTES = {
    "characters": [
        "ServerScriptService/EGGRUMBLE_SevenRoleCombat",
        "ServerScriptService/EGGRUMBLE_CurseConversionPolicy",
    ],
    "field": [
        "ServerScriptService/EGGRUMBLE_RealmBattleCore",
        "ServerScriptService/GQ802_StageTileVisualRenderer",
    ],
    "combat": [
        "ServerScriptService/EGGRUMBLE_MusouFeverPolicy",
        "ServerScriptService/EGGRUMBLE_InvulRuntime",
        "ServerScriptService/EGGRUMBLE_SevenRoleCombat",
    ],
    "castles": [
        "ServerScriptService/EGGRUMBLE_CastleGuardianRuntime",
        "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview",
    ],
    "neutrals": [
        "ServerScriptService/EGGRUMBLE_SwarmCombat",
        "ServerScriptService/EGGRUMBLE_CurseConversionPolicy",
    ],
    "items": [
        "ServerScriptService/EGGRUMBLE_FieldItemPickups",
        "ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopCatalog",
        "ReplicatedStorage/GQ8Trade/GQ8_TradePolicy",
    ],
    "lobby": [
        "ServerScriptService/GQ805_LobbyGuildShop",
        "ServerScriptService/GQ8_LobbySocialPlaza",
        "StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient",
    ],
    "ui": [
        "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraController",
        "ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopView",
    ],
    "balance": [
        "ServerScriptService/EGGRUMBLE_MusouFeverPolicy",
        "ServerScriptService/EGGRUMBLE_InvulnerabilityPolicy",
    ],
}
SINGLE = (
    "ServerScriptService/EGGRUMBLE_SevenRoleCombat",
    "ServerScriptService/EGGRUMBLE_SwarmCombat",
    "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview",
)
CLIENT = {
    "StarterPlayer/StarterPlayerScripts/GQ805_ShopKioskClient",
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_MusouAuraController",
}
MODULE = {
    "ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopCatalog",
    "ReplicatedStorage/GQ805Shop/EGGRUMBLE_LobbyShopView",
}
EXPECTED = {
    **{k: "LocalScript" for k in CLIENT},
    **{k: "ModuleScript" for k in MODULE},
}


def fail(code: str):
    raise ValueError("RED_" + code)


def flatten(project: Path):
    project = project.resolve(strict=True)
    data = json.loads(project.read_text(encoding="utf-8"))
    if not isinstance(data.get("tree"), dict):
        fail("NO_PROJECT_TREE")
    result = {}
    def descend(node, parts=()):
        for name, child in node.items():
            if name.startswith("$"):
                continue
            if not name or "/" in name or not isinstance(child, dict):
                fail("INVALID_TREE_ROUTE")
            route = parts + (name,)
            if "$path" in child:
                key = "/".join(route)
                if key in result:
                    fail("DUPLICATE_TREE_ROUTE")
                source = (project.parent / child["$path"]).resolve(strict=True)
                if not source.is_file() or not source.is_relative_to(project.parent):
                    fail("UNSAFE_SOURCE_PATH")
                result[key] = source
            else:
                descend(child, route)
    descend(data["tree"])
    return result


def source_class(file: Path):
    n = file.name
    if n.endswith(".server.luau"):
        return "Script"
    if n.endswith(".client.luau"):
        return "LocalScript"
    if n.endswith(".luau"):
        return "ModuleScript"
    fail("UNKNOWN_SOURCE_CLASS")


def verify(project: Path, receipt: Path):
    files = flatten(project)
    data = json.loads(receipt.read_text(encoding="utf-8"))
    if len(files) != N or data.get("selected_real55_count") != N:
        fail("REAL53_COUNT_DRIFT")
    if data.get("actual_trade_settlement_enabled") is not False or data.get("formal_rc_adopted") is not False:
        fail("FALSE_COMMERCE_OR_RC_CLAIM")
    ledger = data.get("sources", [])
    if not isinstance(ledger, list) or len(ledger) != N:
        fail("RECEIPT_LENGTH")
    indexed = {}
    for item in ledger:
        key = item.get("route")
        if not isinstance(key, str) or key in indexed:
            fail("DUPLICATE_LEDGER_ROUTE")
        indexed[key] = item
    if set(files) != set(indexed):
        fail("LEDGER_ROUTE_DRIFT")
    total_bytes = 0
    for route, src in files.items():
        b = src.read_bytes()
        row = indexed[route]
        cls = source_class(src)
        if len(b) != row.get("bytes") or hashlib.sha256(b).hexdigest() != row.get("sha256"):
            fail("SOURCE_HASH_" + route.replace("/", "_"))
        if cls != row.get("class"):
            fail("SOURCE_CLASS_" + route.replace("/", "_"))
        total_bytes += len(b)
    present = {}
    for lane, required in ROUTES.items():
        missing = [r for r in required if r not in files]
        if missing:
            fail("MISSING_" + lane.upper() + "_" + "_".join(missing))
        present[lane] = {"source_selected": True, "source_routes": required,
                         "studio_play_verified": False, "android15_verified": False,
                         "fun_verified": False}
    for route in SINGLE:
        if sum(1 for name in files if name == route) != 1:
            fail("DUPLICATE_GAME_AUTHORITY")
    for route, cls in EXPECTED.items():
        if source_class(files[route]) != cls:
            fail("WRONG_CLIENT_MODULE_CLASS_" + route.replace("/", "_"))
    return {
        "schema": "GQ8_NINE_LANE_FORMAL_REAL55_SOURCE_EVIDENCE_V2",
        "parent_feature_ids": ["GQ8_MUSOU_INVUL_REAL49_COMPOSITE_20261119",
                               "GQ8_REAL55_CANONICAL_PRIVATE_RC_PROMOTION_20261119"],
        "source_count": N,
        "source_bytes_sum_not_place_size": total_bytes,
        "evidenced_lanes_source_only": len(present),
        "evidenced_lanes_actual_studio": 0,
        "evidenced_lanes_android": 0,
        "evidenced_lanes_fun": 0,
        "author_private_artifact_claims_formal_rc": False,
        "same_head_formal_rc_status": "REQUIRES_EXTERNAL_CI_VERIFICATION",
        "source_areas_verified_against_formal_manifest": len(present),
        "shop_purchases": "OFF",
        "single_authority_routes": list(SINGLE),
        "lanes": present,
        "blockers": [
            "Formal #220 RC CAS occurred; verify current official SHA and same-HEAD run externally",
            "Same official RC HEAD Native, Rojo, source-lock, OFF and artifact",
            "Roblox Studio 2-client, Android 15min and owner FUN evidence",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    result = verify(a.project, a.receipt)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("GQ8_NINE_LANE_REAL55_RECEIPT_HASH_CLASS_NO_FALSE_RC_PASS", result["source_count"], result["evidenced_lanes_source_only"])


if __name__ == "__main__":
    main()
