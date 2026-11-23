#!/usr/bin/env python3
"""GQ470 / #420: real REAL69 .rbxlx SOURCE art gate, never a beauty verdict.

The legacy S1/RC80 art checker expects different named Game/HUD scripts.
This explicit REAL69 profile inspects the actually generated 69-source Place
and emits a verifiable source-only report. No fake Roblox captures or FPS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

FORMAL = "rc/p0d-s1-kids-rc01"
PROFILE = "REAL69"
SCENES = ("lobby", "field_wide", "castle", "sea", "forest",
          "neutral", "beast", "combat")
CATEGORIES = ("terrain", "castle", "sea", "forest", "neutral",
              "beast", "roles", "combat", "lobby", "atmosphere")
FEATURES = {
    "bot_three_silhouettes": (
        "EGGRUMBLE_HeroSilhouetteArt",
        "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt",
        "gq470_bot_art_variants",
        "GQ470_ART_BOT_THREE_ARCHETYPES_REAL69_20261120",
        "1ef5bbfc3d73d82b74ad37eb4b34f64f83790ca352cf5825ebb6001ea6f20424",
        ("MAX_BOT_ARMOR_PIECES=7", "BulwarkChest", "ScoutHood", "EngineerBackpack"),
    ),
    "twin_reef_sculpt_and_signs": (
        "EGGRUMBLE_LegacyTwinBiomes",
        "ServerScriptService/EGGRUMBLE_LegacyTwinBiomes",
        "gq470_reef_sculpt_visual",
        "GQ470_ART_REEF_ORGANIC_SIGN_READABLE_REAL69_20261120",
        "c8a78277b74669caebfb7ac6e1dc18f065c537f2da00cf22d8fd7fbca0bf5a00",
        ("MATTE_FORK_CORAL", "gui.AlwaysOnTop = false", "gui.MaxDistance = 38"),
    ),
    "field_vs_released_egg_crest": (
        "EGGRUMBLE_EncounterReadabilityArt",
        "ServerScriptService/EGGRUMBLE_EncounterReadabilityArt",
        "gq470_objective_visual",
        "GQ470_P0_FIELD_RELEASED_EGG_CREST_REAL69_20261120",
        "9ec9982ed0d6e68457712e4e5dd10e7fb608c666adfe2e6904a209f5692a50c9",
        ("RaisedEggCrest", "ObjectiveBaseRing", 'egg.Name:match("^ReleasedEgg_")'),
    ),
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def demand(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("RED_REAL69_ART_SOURCE_GATE_" + code)

def check_text(text: str, expected_sha: str, marker: str, guards: tuple[str, ...]) -> None:
    demand(sha(text.encode("utf-8")) == expected_sha, "SOURCE_HASH_NOT_FIXED")
    demand(marker in text, "MARKER_NOT_IN_ACTUAL_PLACE")
    demand(all(guard in text for guard in guards), "BUDGET_OR_SCOPE_GUARD_MISSING")

def script_sources(place: pathlib.Path) -> dict:
    scripts: dict[str, dict] = {}
    root = ET.fromstring(place.read_bytes())
    for item in root.iter("Item"):
        cls = item.attrib.get("class")
        if cls not in ("ModuleScript", "LocalScript", "Script"):
            continue
        props = item.find("Properties")
        demand(props is not None, "SCRIPT_PROPERTIES_MISSING")
        name = props.find("string[@name='Name']")
        src = props.find("string[@name='Source']")
        demand(name is not None and name.text and src is not None,
               "SCRIPT_NAME_OR_SOURCE_MISSING")
        demand(name.text not in scripts, "DUPLICATE_SCRIPT_NAME")
        scripts[name.text] = {"class": cls, "source": src.text or ""}
    demand(len(scripts) == 69, "REAL69_SCRIPT_COUNT")
    return scripts

def selected_project(root: pathlib.Path) -> dict[str, pathlib.Path]:
    project = json.loads((root / "EGGRUMBLE_REAL69.project.json").read_text())
    selected: dict[str, pathlib.Path] = {}
    def walk(node, route=""):
        if not isinstance(node, dict):
            return
        if "$path" in node:
            file = (root / node["$path"]).resolve()
            demand(file.is_relative_to(root.resolve()) and file.is_file(),
                   "ESCAPED_SELECTED_SOURCE_PATH")
            demand(route not in selected, "DUPLICATE_SELECTED_ROUTE")
            selected[route] = file
        for key, child in node.items():
            if not key.startswith("$"):
                walk(child, route + "/" + key if route else key)
    walk(project["tree"])
    demand(len(selected) == 69, "REAL69_SELECTED_ROUTE_COUNT")
    return selected

def audit(root: pathlib.Path, head: str) -> dict:
    rp = root / "REAL69_LEGACY_INTAKE_RECEIPT.json"
    receipt = json.loads(rp.read_text())
    place = root / "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
    demand(place.is_file(), "PRIVATE_PLACE_MISSING")
    place_data = place.read_bytes()
    checksum = sha(place_data)
    demand(receipt.get("official_branch") == FORMAL and
           receipt.get("source_profile") == PROFILE and
           receipt.get("build_head") == head,
           "NOT_CURRENT_REAL69_RECEIPT")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        # This is a real authenticated CI context: prove whether the 69 scripts
        # belong to the official push or a nonformal synthetic PR merge.
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
        from quality_gameplay.gq470_art_pr_provenance_20261121.guard import verify_receipt
        live = subprocess.check_output([
            "gh", "api",
            f"repos/{os.environ['GITHUB_REPOSITORY']}/git/ref/heads/{FORMAL}",
            "--jq", ".object.sha"], text=True).strip()
        event_path = os.environ.get("GITHUB_EVENT_PATH", "")
        event = json.loads(pathlib.Path(event_path).read_text()) if event_path else {}
        provenance = verify_receipt(receipt, os.environ, event, live)
    else:
        # An offline read of an original formal-source snapshot is possible, but
        # never claim it has current live HEAD or verified CI provenance.
        demand(receipt.get("canonical_build") is True,
               "OFFLINE_SOURCE_ONLY_MUST_HAVE_ORIGINAL_FORMAL_RECEIPT")
        provenance = "OFFLINE_FORMAL_SOURCE_SNAPSHOT_NOT_LIVE"
    is_live_formal = provenance == "OFFICIAL"
    demand(receipt.get("private_place_sha256") == checksum and
           receipt.get("private_place_bytes") == len(place_data),
           "PLACE_RECEIPT_NOT_EXACT")
    scripts = script_sources(place)
    routes = selected_project(root)
    demand(len(receipt.get("source_hashes", {})) == 69 and
           len(receipt.get("source_classes", {})) == 69 and
           set(routes) == set(receipt["source_hashes"]),
           "SOURCE_RECEIPT_69")
    for route, file in routes.items():
        name = route.rsplit("/", 1)[-1]
        demand(name in scripts, "SELECTED_SOURCE_MISSING_IN_PLACE_" + name)
        raw = file.read_bytes()
        embedded = scripts[name]["source"].encode("utf-8")
        demand(raw == embedded and sha(raw) == receipt["source_hashes"][route],
               "REAL_PLACE_SOURCE_NOT_BYTE_EXACT_" + name)
        demand(scripts[name]["class"] == receipt["source_classes"][route],
               "REAL_PLACE_SCRIPT_CLASS_DRIFT_" + name)
    proofs = {}
    for key, (name, route, meta_key, marker, fixed_sha, guards) in FEATURES.items():
        demand(route in routes and name in scripts and
               scripts[name]["class"] == "Script", "ART_ROUTE_OR_CLASS_" + key)
        check_text(scripts[name]["source"], fixed_sha, marker, guards)
        metadata = receipt.get(meta_key)
        demand(isinstance(metadata, dict) and
               metadata.get("feature_id") == marker and
               metadata.get("native_rojo_off69") == "PASS_SOURCE_ONLY" and
               metadata.get("other_selected_routes_byte_exact") == 68 and
               metadata.get("owner_accepted") is False,
               "ART_FEATURE_SOURCE_RECEIPT_" + key)
        proofs[key] = {
            "selected_route": route, "real_place_embedded_source_sha256": fixed_sha,
            "source_gate": "PASS_SOURCE_ONLY", "studio_render": "NOT_TESTED",
            "android_render": "NOT_TESTED", "owner_accepted": False,
        }
    demand(receipt["gq470_objective_visual"].get(
           "decorative_egg_parts_per_egg_old_new") == [2, 2] and
           receipt["gq470_objective_visual"].get(
           "vault_deposit_source_untouched") is True,
           "EGG_OBJECTIVE_PART_BUDGET_OR_VAULT_OWNER")
    demand(receipt["gq470_bot_art_variants"].get("max_parts_per_bot") == 7,
           "BOT_MOBILE_PART_BUDGET")
    demand(receipt["gq470_reef_sculpt_visual"].get(
           "new_part_count_across_2_reefs") == 8,
           "REEF_MOBILE_PART_BUDGET")
    texts = [item["source"] for item in scripts.values()]
    return {
        "schema": "P0D_REAL69_GQ470_ART_CHECK_REPORT_V1",
        "only_formal_branch": FORMAL,
        "official_build_head": head if is_live_formal else None,
        "candidate_build_head": head,
        "receipt_provenance": provenance,
        "formal_rc_adoption_proven": is_live_formal,
        "selected_profile": "REAL69_PRIVATE_COMPANION",
        "active_s1_rich51_same_runtime": False,
        "private_place_sha256": checksum, "private_place_bytes": len(place_data),
        "source_gate": {
            "status": "PASS_SOURCE_ONLY", "actual_place_scripts": len(scripts),
            "PR_source_pass_does_not_certify_formal_RC": not is_live_formal,
            "selected_routes_source_class_hash_exact": 69,
            "verified_visual_feature_sources": len(FEATURES),
            "source_gate_is_not_roblox_engine_or_beauty_proof": True,
        },
        "features": proofs,
        "style_risk_indicators_not_beauty_scores": {
            "source_neon_mentions": sum(t.count("Enum.Material.Neon") for t in texts),
            "source_billboardgui_mentions": sum(t.count("BillboardGui") for t in texts),
            "source_part_constructor_mentions": sum(t.count('Instance.new("Part")') for t in texts),
            "warning": "Luau source mentions are NOT actual rendered drawcalls or visual ratings",
        },
        "visual_evidence_gate": {
            "status": "MISSING", "scenes": list(SCENES),
            "screenshots_required": 32, "screenshots_received": 0,
            "pc_android_before_after_same_camera": "NOT_TESTED",
        },
        "human_art": {
            "status": "NOT_TESTED", "visual_categories": list(CATEGORIES),
            "pc_target_score_out_of_5": 4.5,
            "android_target_score_out_of_5": 4.0,
            "recorded_human_scores": 0,
        },
        "mobile_runtime": {
            "status": "NOT_TESTED", "real_android_15_min": False,
            "low_end_median_fps_min": 30, "low_end_p10_fps_min": 25,
            "warm_fps_drop_max_fraction": 0.20,
            "device_model": None, "actual_fps": None,
        },
        "kid_first_3_minutes_fun": {
            "status": "NOT_TESTED", "first_move_15s": None,
            "first_attack_45s": None, "actual_damage_75s": None,
            "egg_castle_objective_180s": None, "fun_rating_out_of_5": None,
        },
        "studio_solo": "NOT_TESTED", "studio_two_client": "NOT_TESTED",
        "all_48_legacy_feature_semantic_parity": "NOT_PROVEN",
        "owner_accepted": False, "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
        "next_stage": "COLLECT_32_REAL_STUDIO_PNG_AND_ANDROID_15MIN_AND_OWNER_ACCEPTANCE",
    }

def selftest() -> None:
    marker = "FIXED_MARKER"
    raw = "prefix " + marker + " guard_a guard_b"
    check_text(raw, sha(raw.encode()), marker, ("guard_a", "guard_b"))
    for mutated, fixed, mark, guards in (
        (raw + "tamper", sha(raw.encode()), marker, ("guard_a",)),
        (raw, sha(raw.encode()), "WRONG_MARKER", ("guard_a",)),
        (raw, sha(raw.encode()), marker, ("guard_missing",)),
    ):
        try:
            check_text(mutated, fixed, mark, guards)
        except ValueError:
            continue
        raise AssertionError("RED_ART_NEGATIVE_MUTANT_ACCEPTED")
    assert len(SCENES) == 8 and len(CATEGORIES) == 10
    print("GQ470_REAL69_ART_GATE_3_NEGATIVES_PASS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path)
    parser.add_argument("--head", type=str, default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        selftest()
    else:
        demand(args.root is not None and args.out is not None and
               len(args.head) == 40, "ARGS")
        result = audit(args.root, args.head)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, sort_keys=True, indent=2,
                                       ensure_ascii=False) + "\n")
        print("GQ470_REAL69_ART_SOURCE_GATE_REAL_PLACE_69_PASS_ART_NO_GO",
              result["private_place_bytes"], result["private_place_sha256"])
