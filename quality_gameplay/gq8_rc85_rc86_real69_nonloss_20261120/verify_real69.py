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
BOT_ART = "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt"
REEF_ART = "ServerScriptService/EGGRUMBLE_LegacyTwinBiomes"
EGG_ART = "ServerScriptService/EGGRUMBLE_EncounterReadabilityArt"
EGG_ART_BASE_SHA = "899cc3a1fddcf53b31a163f7e406f3758e1b607b185fc1d1f27ce10952d1be97"
EGG_ART_ADOPT_SHA = "9ec9982ed0d6e68457712e4e5dd10e7fb608c666adfe2e6904a209f5692a50c9"
EGG_ART_MARKER = "GQ470_P0_FIELD_RELEASED_EGG_CREST_REAL69_20261120"
EGG_ART_ORIGINAL_HEAD = "c8f59a3d5815276ed71f9f62edd7e568e61911e3"
REEF_ART_BASE_SHA = "686b39af03bd8df1e1c81da449fd2b1415c8093c4a14c650853b64be8047537e"
REEF_ART_ADOPT_SHA = "c8a78277b74669caebfb7ac6e1dc18f065c537f2da00cf22d8fd7fbca0bf5a00"
REEF_ART_MARKER = "GQ470_ART_REEF_ORGANIC_SIGN_READABLE_REAL69_20261120"
REEF_ART_ORIGINAL_HEAD = "c226c63eeb235503f9292503b61f2173550337ec"
BOT_ART_BASE_SHA = "7ca5be97c2c76cb0b7d4c228168a6f14fa6ecf213de31eb4222086d358462da4"
BOT_ART_ADOPT_SHA = "1ef5bbfc3d73d82b74ad37eb4b34f64f83790ca352cf5825ebb6001ea6f20424"
BOT_ART_MARKER = "GQ470_ART_BOT_THREE_ARCHETYPES_REAL69_20261120"
BOT_ART_ORIGINAL_HEAD = "c226c63eeb235503f9292503b61f2173550337ec"
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

def verify_bot_art(now: dict, previous: dict, receipt: dict,
                   root: pathlib.Path) -> dict:
    """Bounded #920 source adoption; one visual Script, exact A verified bytes.

    Unlike a general exemption, every other route remains byte-locked.
    All Studio/Android/owner visual judgments still require real-world proof.
    """
    meta = receipt.get("gq470_bot_art_variants")
    require(isinstance(meta, dict), "BOT_ART_ADOPTION_RECEIPT_MISSING")
    require(BOT_ART in now and BOT_ART in previous, "BOT_ART_ROUTE_MISSING")
    require(meta.get("route") == BOT_ART and
            meta.get("feature_id") == BOT_ART_MARKER and
            meta.get("formal_parent") == BOT_ART_ORIGINAL_HEAD,
            "BOT_ART_IDENTITY_MISMATCH")
    require(previous[BOT_ART]["sha256"] == BOT_ART_BASE_SHA and
            now[BOT_ART]["sha256"] == BOT_ART_ADOPT_SHA and
            meta.get("original_source_sha256") == BOT_ART_BASE_SHA and
            meta.get("changed_source_sha256") == BOT_ART_ADOPT_SHA,
            "BOT_ART_DIGEST_NOT_CERTIFIED")
    require(BOT_ART_MARKER.encode("utf-8") in now[BOT_ART]["source"] and
            BOT_ART_MARKER.encode("utf-8") not in previous[BOT_ART]["source"],
            "BOT_ART_MARKER_NOT_REAL")
    require(meta.get("other_selected_routes_byte_exact") == 68 and
            meta.get("source_count") == 69 and
            meta.get("max_parts_per_bot") == 7 and
            meta.get("new_scripts") == 0 and
            meta.get("new_combat_authority") is False and
            meta.get("collision_changed") is False and
            meta.get("owner_accepted") is False and
            meta.get("native_rojo_off69") == "PASS_SOURCE_ONLY",
            "BOT_ART_BUDGET_OR_AUTHORITY_DRIFT")
    # Validate the BOT stage at its own immutable boundary. A later REEF
    # stage is allowed to change its disjoint source, not retroactively count
    # as an extra bot-stage modification.
    off = project_scan(root / "off69_bot_art", "EGGRUMBLE_REAL69.project.json")
    after_bot = project_scan(root / "off69_reef", "EGGRUMBLE_REAL69.project.json")
    require(len(off) == len(after_bot) == len(now) == 69 and
            set(off) == set(after_bot) == set(now), "BOT_ART_OFF69_ROUTE_SET")
    require(off[BOT_ART]["sha256"] == BOT_ART_BASE_SHA and
            after_bot[BOT_ART]["sha256"] == BOT_ART_ADOPT_SHA and
            {key for key in now
             if off[key]["sha256"] != after_bot[key]["sha256"]} == {BOT_ART},
            "BOT_ART_OFF69_INVERSE_NOT_EXACT")
    require(all(off[key]["class"] == after_bot[key]["class"] and
                off[key]["path"] == after_bot[key]["path"] for key in now),
            "BOT_ART_OFF69_CLASS_PATH_DRIFT")
    require(after_bot[REEF_ART]["sha256"] == REEF_ART_BASE_SHA and
            after_bot[BOT_ART]["sha256"] == now[BOT_ART]["sha256"],
            "BOT_ART_REEF_STAGE_SEPARATION")
    return {
        "feature_id": BOT_ART_MARKER,
        "selected_route": BOT_ART,
        "source_original_sha256": BOT_ART_BASE_SHA,
        "source_adopted_sha256": BOT_ART_ADOPT_SHA,
        "unchanged_vs_pre_bot_selected_sources": 68,
        "native_rojo_off69": "PASS_SOURCE_ONLY",
        "studio_android_human_art": "NOT_TESTED",
        "owner_accepted": False,
    }


def verify_reef_art(now: dict, previous: dict, receipt: dict,
                    root: pathlib.Path) -> dict:
    """ART-FB015: fail-closed one-source coral and visual sign readability."""
    meta = receipt.get("gq470_reef_sculpt_visual")
    require(isinstance(meta, dict), "REEF_ART_RECEIPT_MISSING")
    require(REEF_ART in now and REEF_ART in previous, "REEF_ROUTE_MISSING")
    require(meta.get("selected_source") == REEF_ART and
            meta.get("feature_id") == REEF_ART_MARKER and
            meta.get("formal_parent") == REEF_ART_ORIGINAL_HEAD,
            "REEF_IDENTITY_MISMATCH")
    require(previous[REEF_ART]["sha256"] == REEF_ART_BASE_SHA and
            now[REEF_ART]["sha256"] == REEF_ART_ADOPT_SHA and
            meta.get("original_source_sha256") == REEF_ART_BASE_SHA and
            meta.get("new_source_sha256") == REEF_ART_ADOPT_SHA,
            "REEF_DIGEST_NOT_CERTIFIED")
    require(REEF_ART_MARKER.encode() in now[REEF_ART]["source"] and
            REEF_ART_MARKER.encode() not in previous[REEF_ART]["source"],
            "REEF_MARKER_INVALID")
    require(meta.get("other_selected_routes_byte_exact") == 68 and
            meta.get("new_part_count_across_2_reefs") == 8 and
            meta.get("old_sign_range_studs") == 100 and
            meta.get("new_sign_range_studs") == 38 and
            meta.get("collision_changed") is False and
            meta.get("new_game_authority") is False and
            meta.get("owner_accepted") is False and
            meta.get("native_rojo_off69") == "PASS_SOURCE_ONLY",
            "REEF_BUDGET_OR_AUTHORITY_DRIFT")
    off = project_scan(root / "off69_reef", "EGGRUMBLE_REAL69.project.json")
    after_reef = project_scan(root / "off69_objective", "EGGRUMBLE_REAL69.project.json")
    require(len(off) == len(after_reef) == len(now) == 69 and
            set(off) == set(after_reef) == set(now), "REEF_OFF69_ROUTE_SET")
    require(off[REEF_ART]["sha256"] == REEF_ART_BASE_SHA and
            after_reef[REEF_ART]["sha256"] == REEF_ART_ADOPT_SHA and
            {key for key in now
             if off[key]["sha256"] != after_reef[key]["sha256"]} == {REEF_ART},
            "REEF_OFF69_INVERSE_NOT_EXACT")
    require(all(off[key]["class"] == after_reef[key]["class"] and
                off[key]["path"] == after_reef[key]["path"] for key in now),
            "REEF_OFF69_CLASS_PATH_DRIFT")
    require(after_reef[EGG_ART]["sha256"] == EGG_ART_BASE_SHA and
            after_reef[REEF_ART]["sha256"] == now[REEF_ART]["sha256"],
            "REEF_EGG_STAGE_SEPARATION")
    return {
        "feature_id": REEF_ART_MARKER,
        "selected_route": REEF_ART,
        "source_adopted_sha256": REEF_ART_ADOPT_SHA,
        "unchanged_vs_pre_reef_selected_sources": 68,
        "native_rojo_off69": "PASS_SOURCE_ONLY",
        "studio_android_human_art": "NOT_TESTED",
        "owner_accepted": False,
    }


def verify_egg_art(now: dict, previous: dict, receipt: dict,
                   root: pathlib.Path) -> dict:
    """Source-only two-ornament egg silhouette, without vault/deposit changes."""
    meta = receipt.get("gq470_objective_visual")
    require(isinstance(meta, dict), "EGG_ART_RECEIPT_MISSING")
    require(EGG_ART in now and EGG_ART in previous, "EGG_ROUTE_MISSING")
    require(meta.get("only_changed_selected_route") == EGG_ART and
            meta.get("feature_id") == EGG_ART_MARKER and
            meta.get("official_base") == EGG_ART_ORIGINAL_HEAD,
            "EGG_IDENTITY_MISMATCH")
    require(previous[EGG_ART]["sha256"] == EGG_ART_BASE_SHA and
            now[EGG_ART]["sha256"] == EGG_ART_ADOPT_SHA and
            meta.get("changed_source_sha256") == EGG_ART_ADOPT_SHA,
            "EGG_SHA_MISMATCH")
    require(EGG_ART_MARKER.encode() in now[EGG_ART]["source"] and
            EGG_ART_MARKER.encode() not in previous[EGG_ART]["source"],
            "EGG_MARKER_MISSING")
    require(meta.get("decorative_egg_parts_per_egg_old_new") == [2, 2] and
            meta.get("vault_deposit_source_untouched") is True and
            meta.get("scope_nonoverlap_with_pr_922") == "decorateEgg_only" and
            meta.get("additional_vault_parts_per_station") == 0 and
            meta.get("other_selected_routes_byte_exact") == 68 and
            meta.get("collision_changed") is False and
            meta.get("authority_changed") is False and
            meta.get("native_rojo_off69") == "PASS_SOURCE_ONLY" and
            meta.get("owner_accepted") is False,
            "EGG_BUDGET_OR_AUTHORITY_DRIFT")
    off = project_scan(root / "off69_objective", "EGGRUMBLE_REAL69.project.json")
    require(len(off) == 69 and set(off) == set(now), "EGG_OFF69_ROUTE_SET")
    require(off[EGG_ART]["sha256"] == EGG_ART_BASE_SHA and
            {key for key in now if off[key]["sha256"] != now[key]["sha256"]} ==
                {EGG_ART}, "EGG_OFF69_INVERSE_NOT_EXACT")
    require(all(off[key]["class"] == now[key]["class"] and
                off[key]["path"] == now[key]["path"] for key in now),
            "EGG_OFF69_CLASS_PATH_DRIFT")
    source_anchor = b"local function decorateVault(part:BasePart)"
    require(source_anchor in off[EGG_ART]["source"] and
            source_anchor in now[EGG_ART]["source"] and
            off[EGG_ART]["source"].split(source_anchor, 1)[1] ==
                now[EGG_ART]["source"].split(source_anchor, 1)[1],
            "EGG_STATION_OWNER_CHANGED")
    return {
        "feature_id": EGG_ART_MARKER,
        "selected_route": EGG_ART,
        "source_adopted_sha256": EGG_ART_ADOPT_SHA,
        "decorative_parts_per_egg": 2,
        "vault_deposit_untouched": True,
        "unchanged_vs_pre_egg_selected_sources": 68,
        "studio_android_human_art": "NOT_TESTED",
        "owner_accepted": False,
    }


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
        if route not in (HUD, P0_COMBAT, P0_SWARM, BOT_ART, REEF_ART, EGG_ART):
            require(previous[route]["sha256"] == info["sha256"],
                    "UNRELATED_SCRIPT_CHANGED_" + route)
    bot_art_receipt = verify_bot_art(now, previous, receipt, root)
    reef_art_receipt = verify_reef_art(now, previous, receipt, root)
    egg_art_receipt = verify_egg_art(now, previous, receipt, root)
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
        "unrelated_pre_discovery_scripts_byte_exact": 63,
        "gq470_fb015_egg_crest_source_adoption": egg_art_receipt,
        "gq470_fb015_reef_sculpt_source_adoption": reef_art_receipt,
        "gq470_fb015_bot_silhouette_source_adoption": bot_art_receipt,
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
    # Guard the fixed source adoption against identifier, digest and acceptance lies.
    fixed = (BOT_ART, BOT_ART_MARKER, BOT_ART_ORIGINAL_HEAD,
             BOT_ART_BASE_SHA, BOT_ART_ADOPT_SHA)
    assert len(set(fixed)) == 5
    for bad in ("UNKNOWN", "", "SOURCE_UNVERIFIED"):
        assert bad not in fixed
    assert len(BOT_ART_BASE_SHA) == len(BOT_ART_ADOPT_SHA) == 64
    assert len(REEF_ART_BASE_SHA) == len(REEF_ART_ADOPT_SHA) == 64
    assert REEF_ART != BOT_ART and REEF_ART != HUD
    assert EGG_ART not in (BOT_ART, REEF_ART, HUD, P0_COMBAT, P0_SWARM)
    assert len(EGG_ART_BASE_SHA) == len(EGG_ART_ADOPT_SHA) == 64
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
