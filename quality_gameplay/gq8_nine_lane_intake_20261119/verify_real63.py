#!/usr/bin/env python3
"""Independent Real63 source/class preservation audit; gameplay/Studio remain untested."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from verify_real59_host import inspect
from verify_real59 import require, sha
from verify_real62 import AREAS

HOST = "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview"
COMBAT = "ServerScriptService/EGGRUMBLE_SevenRoleCombat"
HUD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"
DODGE = "ServerScriptService/EGGRUMBLE_BasicMobilityPolicy"
PARENT = "b15db4b9ad1f1f4c1f02fb0976eb3c2f6db8a6ff"
CHANGED = {COMBAT, HUD}

def verify(real62: Path, real63: Path, off62: Path, receipt: Path, expected_head: str):
    parent = inspect(real62)
    current = inspect(real63)
    reverted = inspect(off62)
    info = json.loads(receipt.read_text(encoding="utf8"))
    require(len(expected_head) == 40, "INVALID_HEAD")
    require(len(parent) == 62 and len(current) == 63 and len(reverted) == 62, "SOURCE_COUNT")
    require(parent == reverted, "OFF62_CLASS_OR_SOURCE_DRIFT")
    require(set(current) == set(parent) | {DODGE}, "CURRENT_ROUTES_OR_DUPLICATES")
    require(current[DODGE][0] == "ModuleScript", "DODGE_NOT_MODULE")
    require(parent[HOST][0] == current[HOST][0] == "Script", "HOST_NOT_AUTOSTART")
    actual_changes = {route for route in parent if parent[route] != current[route]}
    require(actual_changes == CHANGED, "ORIGINAL_MODIFIED_ROUTES")
    require(all(parent[route][0] == current[route][0] for route in parent), "ORIGINAL_CLASSES_CHANGED")
    require(sum(route == COMBAT for route in current) == 1, "SECOND_COMBAT_OWNER")
    require(sum(route.endswith("/EGGRUMBLE_SwarmCombat") for route in current) == 1, "SECOND_SWARM_OWNER")
    require(
        info.get("feature_id") == "GQ828_BASIC_DODGE_REAL63_20261119"
        and info.get("official_parent_sha") == PARENT
        and info.get("candidate_git_head") == expected_head
        and info.get("parent_original_sources") == 62
        and info.get("candidate_sources") == 63
        and info.get("original_unchanged") == 60
        and set(info.get("original_modified", [])) == CHANGED
        and info.get("added_module") == DODGE
        and info.get("official_rc_adopted") is True,
        "FORMAL_RECEIPT_PROVENANCE",
    )
    require(
        info.get("native") == "PASS"
        and info.get("rojo") == "PASS"
        and info.get("off62") == "PASS"
        and info.get("host_original_class") == "Script"
        and info.get("trade_original_three_sources_retained") is True
        and info.get("parent_host_fix_retained") is True
        and info.get("combat_owner_count") == 1
        and info.get("remote_added") == 0
        and info.get("direct_damage_site_added") == 0,
        "OWNER_NATIVE_ROJO_PROOF",
    )
    require(
        info.get("robuxtx_enabled") is False
        and info.get("roblox_published") is False
        and info.get("studio2client") == "NOT_TESTED"
        and info.get("android15min") == "NOT_TESTED"
        and info.get("art_fun") == "NO_GO",
        "FALSE_PAID_OR_PRODUCT_CLAIM",
    )
    for name, expected in (("on_sources", current), ("off_sources", parent)):
        rows = info.get(name, [])
        require(len(rows) == len(expected), "RECEIPT_LENGTH_" + name)
        index = {}
        for row in rows:
            route = row.get("route")
            require(isinstance(route, str) and route not in index, "DUPLICATE_ROUTE_" + name)
            index[route] = row
        require(set(index) == set(expected), "LEDGER_ROUTES_" + name)
        for route, (klass, body) in expected.items():
            row = index[route]
            require(row.get("class") == klass and row.get("bytes") == len(body)
                    and row.get("sha256") == sha(body), "HASH_CLASS_" + name + "_" + route.replace("/", "_"))
    areas = {}
    for area, routes in AREAS.items():
        require(all(route in current for route in routes), "NINE_DOMAIN_MISSING_" + area)
        areas[area] = "SOURCE_PRESENT_NOT_STUDIO_VERIFIED"
    require(len(areas) == 9, "NINE_DOMAIN_COUNT")
    return {
        "schema": "GQ8_INDEPENDENT_REAL63_9DOMAIN_DODGE_FENCE_V1",
        "official_head": expected_head,
        "source_count": 63,
        "original_unchanged": 60,
        "modified_routes": sorted(CHANGED),
        "added_route": DODGE,
        "host_class": "Script",
        "off62_source_class_exact": True,
        "nine_source_domains": len(areas),
        "nine_studio_domains": 0,
        "paid_inventory_transfer": False,
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "fun": "NOT_TESTED",
        "product_go": False,
        "areas": areas,
    }

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for key in ("real62", "real63", "off62", "receipt", "output"):
        p.add_argument("--" + key, type=Path, required=True)
    p.add_argument("--expected-head", required=True)
    a = p.parse_args()
    report = verify(a.real62, a.real63, a.off62, a.receipt, a.expected_head)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf8")
    print("GQ8_INDEPENDENT_REAL63_NINE_DOMAIN_60_UNCHANGED_2_MODIFIED_1_ADDED_PASS")
