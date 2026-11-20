#!/usr/bin/env python3
"""Final source-level nonloss gate for the ONE formal REAL65-descendant REAL69.

Verifies selected Luau routes/classes/hashes, all 11 historic source-family
anchors already proven at REAL68, plus six later source adaptations, the
pre-HUD byte-exact rollback, and the single delivered Studio Place.

NOT proof of full 48 legacy feature semantic parity or Studio/Android testing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] /
                       "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import EVIDENCE, FORMAL, OLD_S1_PREFIX, project_scan

HUD = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"
P0_COMBAT = "ServerScriptService/EGGRUMBLE_SevenRoleCombat"
P0_SWARM = "ServerScriptService/EGGRUMBLE_SwarmCombat"
P0_MARKERS = ((P0_COMBAT, "GQ8_P0_COMBAT_BOT_USERID_SCOPE_20261120"),
              (P0_SWARM, "GQ8_P0_NEUTRAL_BILLBOARD_DISTANCE_20261120"))
EXTRA = (
    ("rc85_rc86_4realms_6shards",
     "ServerScriptService/EGGRUMBLE_LegacyExplorationBridge",
     "GQ8_LEGACY_RC85_86_EXPLORATION_INTAKE_20261119"),
    ("rc86_fb016_foliage_sightline",
     "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD",
     "GQ8_RC86_FB016_FOLIAGE_SIGHTLINE_V3_20261119"),
    ("rc86_gorogan_mobile_lod",
     "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ArtDistanceLOD",
     "GQ8_RC86_GOROGAN_MOBILE_LOD_REAL68_20261120"),
    ("rc85_first90_studio_guide",
     "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_LegacyFirst90",
     "GQ8_RC85_FIRST90_REAL69_STUDIO_GUIDE_20261120"),
    ("rc86_fortress_partial_visual",
     "ServerScriptService/EGGRUMBLE_FlagshipFieldArt",
     "GQ8_RC86_FB015_FORTRESS_DETAIL_VISUAL_PORT_REAL69_20261120"),
    ("rc85_rc86_exploration_progress_toast",
     HUD, "GQ8_RC85_RC86_LEGACY_EXPLORE_DISCOVERY_TOAST_REAL69_20261120"),
)
FAMILIES = tuple(EVIDENCE) + EXTRA

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("RED_REAL69_LEGACY_NONLOSS_" + reason)

def marker_check(sources: dict) -> dict[str, str]:
    result = {}
    require(len(FAMILIES) == 17 and len({f for f, _, _ in FAMILIES}) == 17,
            "FAMILY_INVENTORY_NOT_17_UNIQUE")
    for feature, route, marker in FAMILIES:
        require(route in sources, "ROUTE_MISSING_" + feature)
        require(marker.encode("utf-8") in sources[route]["source"],
                "PORT_MARKER_MISSING_" + feature)
        result[feature] = "SOURCE_PRESENT_ENGINE_NOT_TESTED"
    return result

def verify(root: pathlib.Path, expected_head: str = "") -> dict:
    now = project_scan(root, "EGGRUMBLE_REAL69.project.json")
    previous = project_scan(root / "off69_discovery", "EGGRUMBLE_REAL69.project.json")
    receipt_path = root / "REAL69_LEGACY_INTAKE_RECEIPT.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(len(now) == len(previous) == 69, "SOURCE_COUNT_69")
    require(set(now) == set(previous), "ROUTE_NONLOSS")
    require(not any(route.startswith(OLD_S1_PREFIX) for route in now),
            "DUPLICATE_OLD_S1_GAME")
    require(receipt.get("official_branch") == FORMAL, "FORMAL_BRANCH")
    require(receipt.get("selected_source_count") == 69, "RECEIPT_SOURCE_COUNT")
    require(set(receipt.get("source_hashes", {})) == set(now), "RECEIPT_ROUTE_SET")
    for route, info in now.items():
        require(receipt["source_hashes"][route] == info["sha256"],
                "RECEIPT_SHA_" + route)
        require(previous[route]["class"] == info["class"] and
                previous[route]["path"] == info["path"], "CLASS_PATH_CHANGED_" + route)
        if route not in (HUD, P0_COMBAT, P0_SWARM):
            require(previous[route]["sha256"] == info["sha256"],
                    "UNRELATED_SCRIPT_CHANGED_" + route)
    require(previous[HUD]["sha256"] != now[HUD]["sha256"],
            "HUD_PORT_NOT_SELECTED")
    for route, marker in P0_MARKERS:
        require(route in now and route in previous, "P0_ROUTE_MISSING_" + route)
        require(previous[route]["sha256"] != now[route]["sha256"],
                "P0_REPAIR_NOT_SELECTED_" + route)
        require(marker.encode("utf-8") in now[route]["source"],
                "P0_REPAIR_MARKER_MISSING_" + route)
    if expected_head:
        require(receipt.get("build_head") == expected_head, "WRONG_BUILD_HEAD")
    require(receipt.get("rc85_realm_hunt_discovery_toast", {})
            .get("all_prior_real69_routes_preserved") is True,
            "HUD_RECEIPT_NONLOSS")
    family_results = marker_check(now)

    delivery = root / "delivery"
    places = list(delivery.glob("*.rbxlx"))
    require(len(places) == 1, "ONE_PLACE_ONLY")
    canonical_place = root / "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
    require(canonical_place.is_file() and places[0].read_bytes() == canonical_place.read_bytes(),
            "DELIVERY_PLACE_MISMATCH")
    place = canonical_place.read_bytes()
    place_sha = hashlib.sha256(place).hexdigest()
    require(receipt.get("private_place_bytes") == len(place) and
            receipt.get("private_place_sha256") == place_sha,
            "PLACE_RECEIPT_MISMATCH")
    return {
        "schema": "GQ8_REAL65_RC85_RC86_TO_SINGLE_REAL69_NONLOSS_V1",
        "only_formal_rc_branch": FORMAL,
        "selected_profile": "REAL69_PRIVATE_COMPANION",
        "selected_luau_sources": 69,
        "source_route_class_hash_receipt": "PASS_69_OF_69",
        "hud_selected_delta": "EXACT_ONE_SCRIPT",
        "unrelated_pre_discovery_scripts_byte_exact": 66,
        "gq470_p0_combat_swarm_repaired_source_routes": 2,
        "historic_source_family_evidence": family_results,
        "source_family_marker_count": len(family_results),
        "old_legacy_enabled_flags": 48,
        "all_48_semantic_parity": "NOT_PROVEN",
        "primary_s1_rich51_same_runtime_as_v3": False,
        "studio_solo": "NOT_TESTED",
        "studio_two_client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "roblox_publish": False,
        "paid_trades": False,
        "build_head": receipt.get("build_head"),
        "private_place_bytes": len(place),
        "private_place_sha256": place_sha,
    }

def selftest() -> None:
    assert len(FAMILIES) == 17
    data = {route: {"source": marker.encode("utf-8"), "class": "Script", "path": route}
            for _, route, marker in FAMILIES}
    # Routes reused by multiple features must accumulate all source markers.
    for _, route, marker in FAMILIES:
        data[route]["source"] += b"\n" + marker.encode("utf-8")
    assert len(marker_check(data)) == 17
    data[HUD]["source"] = b"-- missing adaptation"
    try:
        marker_check(data)
    except ValueError as exc:
        assert "PORT_MARKER_MISSING_" in str(exc)
    else:
        raise AssertionError("RED_MISSING_MARKER_DID_NOT_FAIL")
    print("GQ8_REAL69_SOURCE_FAMILY_17_NEGATIVE_MARKER_TEST_PASS")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=pathlib.Path)
    p.add_argument("--out", type=pathlib.Path)
    p.add_argument("--head", default=os.environ.get("GITHUB_SHA", ""))
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        selftest()
    else:
        require(args.root is not None and args.out is not None,
                "MISSING_ROOT_OR_OUTPUT")
        result = verify(args.root, args.head)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                       indent=2) + "\n", encoding="utf-8")
        print("GQ8_REAL69_SINGLE_FORMAL_CUMULATIVE_69_OF_69_17_FAMILIES_SOURCE_PASS")
