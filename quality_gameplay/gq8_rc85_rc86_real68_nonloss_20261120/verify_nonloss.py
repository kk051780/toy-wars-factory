#!/usr/bin/env python3
"""Fail-closed RC85/RC86/REAL65->REAL68 selected-source conservation gate.

This is a source-level gate, NOT a claim of complete semantic parity of the
48 legacy flags, Roblox Studio runtime success, or public release readiness.
It requires the exact existing 67 routes, one intentional Combat modification,
one TwinBiomes addition, and source-marker proof of already-integrated features.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import tempfile

FORMAL = "rc/p0d-s1-kids-rc01"
COMBAT = "ServerScriptService/EGGRUMBLE_SevenRoleCombat"
TWIN = "ServerScriptService/EGGRUMBLE_LegacyTwinBiomes"
OLD_S1_PREFIX = "ServerScriptService/TrapRaidersS1/"
EVIDENCE = (
    ("rc86_ninja_wind", COMBAT, "RC86_FB029_WIND_SINGLE_COMBAT_PORT"),
    ("rc86_stage_weapons", "ServerScriptService/EGGRUMBLE_FieldItemPickups",
     "GQ8_RC86_STAGE_WEAPONS_TO_REAL65_20261119"),
    ("rc86_undead_48s", COMBAT, "GQ8_RC86_UNDEAD_SQUAD_COMMAND_RECONCILE_20261119"),
    ("rc86_trapper_pair", COMBAT, "GQ8_RC86_TRAPPER_PAIR_PORT_20261119"),
    ("rc85_lobby_dojo", COMBAT, "GQ8_RC85_DOJO_RECONCILE_20261119"),
    ("rc86_starfall_10", "ServerScriptService/EGGRUMBLE_RealmBattleCore",
     "GQ8_RC86_STARRY_PATH_SINGLE_REALM_REAL66_20261119"),
    ("rc86_meteor", "ServerScriptService/EGGRUMBLE_RealmBattleCore",
     "GQ8_RC86_METEOR_SHORTCUT_SINGLE_REALM_REAL66_20261119"),
    ("rc86_egg_relay", "ServerScriptService/EGGRUMBLE_CastleMatchRules",
     "GQ8_RC86_EGG_RELAY_CLASSIC_SINGLE_CASTLE_AUTHORITY_REAL67_20261119"),
    ("rc86_gorogan_visual", "ServerScriptService/EGGRUMBLE_EncounterReadabilityArt",
     "GQ8_RC86_FB015_GOROGAN_RUNESTONE_ART_SINGLE_EXISTING_OWNER_20261119"),
    ("rc85_crystal_canyon", "ServerScriptService/EGGRUMBLE_LegacyCanyonRoutes",
     "GQ8_RC85_WCS_CANYON_ONLY_REAL67_20261119"),
    ("rc85_twin_training_bond", TWIN,
     "GQ8_RC85_TWIN_BIOMES_TRAINING_BOND_REAL68_20261119"),
)

def demand(predicate: bool, msg: str) -> None:
    if not predicate:
        raise ValueError("RED_RC85_86_REAL68_NONLOSS_" + msg)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def project_scan(directory: pathlib.Path, project_name: str) -> dict:
    project = json.loads((directory / project_name).read_text(encoding="utf-8"))
    mapping: dict[str, dict] = {}
    root = directory.resolve()
    def walk(node: dict, prefix: tuple[str, ...] = ()) -> None:
        for name, child in node.items():
            if name.startswith("$") or not isinstance(child, dict):
                continue
            route = "/".join(prefix + (name,))
            if "$path" in child:
                demand(route not in mapping, "DUPLICATE_ROUTE_" + route)
                rel = child["$path"]
                demand(isinstance(rel, str), "INVALID_PATH_" + route)
                filename = (directory / rel).resolve()
                demand(filename.is_relative_to(root) and filename.is_file(),
                       "UNSAFE_OR_MISSING_SOURCE_" + route)
                raw = filename.read_bytes()
                suffix = filename.name
                inferred = ("Script" if suffix.endswith(".server.luau")
                            else "LocalScript" if suffix.endswith(".client.luau")
                            else "ModuleScript" if suffix.endswith(".luau")
                            else "UNKNOWN")
                cls = child.get("$className", inferred)
                demand(cls == inferred and cls in ("Script", "LocalScript", "ModuleScript"),
                       "BAD_CLASS_" + route)
                mapping[route] = {"sha256": digest(raw), "class": cls,
                                  "path": rel, "source": raw}
            else:
                walk(child, prefix + (name,))
    walk(project["tree"])
    return mapping

def verify(parent: pathlib.Path, current: pathlib.Path) -> dict:
    before = project_scan(parent, "EGGRUMBLE_REAL67.project.json")
    after = project_scan(current, "EGGRUMBLE_REAL68.project.json")
    off = project_scan(current / "off67", "EGGRUMBLE_REAL67.project.json")
    receipt = json.loads((current / "REAL68_LEGACY_INTAKE_RECEIPT.json").read_text())
    demand(len(before) == 67 and len(after) == 68 and len(off) == 67,
           "EXPECTED_COUNTS_67_68_OFF67")
    demand(set(after) - set(before) == {TWIN}, "ONLY_TWIN_ROUTE_ADDED")
    demand(set(before) <= set(after) and set(before) == set(off),
           "PARENT_ROUTE_LOST")
    changed = [r for r in before if before[r]["sha256"] != after[r]["sha256"]]
    demand(changed == [COMBAT], "ONLY_COMBAT_MAY_CHANGE_" + repr(changed))
    for route, old in before.items():
        demand(off[route]["sha256"] == old["sha256"] and
               off[route]["class"] == old["class"],
               "OFF67_MUST_BE_BYTE_EXACT_" + route)
        demand(after[route]["class"] == old["class"] and
               after[route]["path"] == old["path"],
               "EXISTING_CLASS_OR_PATH_CHANGED_" + route)
    demand(not any(route.startswith(OLD_S1_PREFIX) for route in after),
           "DUPLICATE_OLD_S1_GAME")
    demand(receipt.get("formal_branch") == FORMAL and
           receipt.get("selected_source_count") == 68 and
           receipt.get("previous_selected_source_count") == 67 and
           receipt.get("unchanged_existing_source_bodies") == 66 and
           receipt.get("one_existing_combat_modified") is True and
           receipt.get("added_game_or_store_or_remote_owners") == 0,
           "RECEIPT_PROFILE_OR_AUTHORITY")
    claimed_hashes = receipt.get("source_hashes", {})
    demand(set(claimed_hashes) == set(after), "RECEIPT_ROUTE_SET")
    for route, info in after.items():
        demand(claimed_hashes[route] == info["sha256"],
               "HASH_MISMATCH_" + route)
    demand(receipt.get("source_adopted_flags") == [
        "TWIN_BIOMES_4NPC_V1", "TWIN_CREATURE_TRAINING_V1",
        "TWIN_BOND_PVE_COMPANION_V1"], "TWIN_ORIGINAL_FLAGS")
    for route in (COMBAT, "ServerScriptService/EGGRUMBLE_LobbyCastleModesPreview",
                  "ServerScriptService/EGGRUMBLE_RealmBattleCore",
                  "ServerScriptService/EGGRUMBLE_CastleMatchRules",
                  "ServerScriptService/EGGRUMBLE_FieldItemPickups"):
        demand(route in after, "UNIFIED_V3_AUTHORITY_ABSENT_" + route)
    marker_result = {}
    for feature, route, marker in EVIDENCE:
        demand(route in after and marker.encode() in after[route]["source"],
               "PREVIOUSLY_PORTED_MARKER_MISSING_" + feature)
        marker_result[feature] = "SOURCE_PRESENT_ENGINE_NOT_TESTED"
    return {
        "schema": "GQ8_RC85_RC86_REAL65_ONE_RC_CUMULATIVE_NONLOSS_V1",
        "official_branch": FORMAL,
        "source_profile": "REAL68",
        "selected_sources": 68,
        "preserved_original_67_routes": 67,
        "untouched_original_script_bodies": 66,
        "intentional_changed_existing_route": COMBAT,
        "added_route": TWIN,
        "off67_source_exact": True,
        "original_rc85_artifact": 14158848286,
        "original_rc86_artifact": 14161823401,
        "source_marker_checks": marker_result,
        "historical_legacy_feature_flag_count": 48,
        "historical_48_full_semantic_parity": "NOT_PROVEN",
        "primary_active_s1": "rich51_SEPARATE_RUNTIME",
        "v3_private_companion": "REAL68",
        "studio_solo": "NOT_TESTED",
        "studio_two_client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "child_fun": "NO_GO",
        "roblox_published": False,
        "paid_trades_enabled": False,
    }

def selftest() -> None:
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        (root / "sources").mkdir()
        p = root / "sources" / "ServerScriptService"
        p.mkdir()
        (p / "Sample.server.luau").write_text("--!strict\n")
        project = {"tree": {"ServerScriptService": {
            "Sample": {"$path": "sources/ServerScriptService/Sample.server.luau"}
        }}}
        (root / "t.project.json").write_text(json.dumps(project))
        assert list(project_scan(root, "t.project.json")) == ["ServerScriptService/Sample"]
        project["tree"]["ServerScriptService"]["Malicious"] = {"$path": "../../etc/passwd"}
        (root / "t.project.json").write_text(json.dumps(project))
        try:
            project_scan(root, "t.project.json")
        except ValueError as err:
            assert "UNSAFE_OR_MISSING_SOURCE" in str(err)
        else:
            raise AssertionError("RED_SOURCE_PATH_ESCAPE_UNDETECTED")
    print("GQ8_REAL68_NONLOSS_NEGATIVE_PATH_TEST_PASS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=pathlib.Path)
    parser.add_argument("--current", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        selftest()
    else:
        demand(args.parent is not None and args.current is not None and
               args.out is not None, "REQUIRED_DIRECTORIES")
        result = verify(args.parent, args.current)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                       sort_keys=True) + "\n", encoding="utf-8")
        print("GQ8_RC85_RC86_REAL65_TO_SINGLE_FORMAL_REAL68_CUMULATIVE_SOURCE_GUARD_PASS",
              result["selected_sources"], len(result["source_marker_checks"]))
