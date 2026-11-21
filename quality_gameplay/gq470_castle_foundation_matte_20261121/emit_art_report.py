#!/usr/bin/env python3
"""Strict #420 source-vs-actual human ART evidence separation for #470 FB015 foundation.

An offline/native/Rojo pass does not fill any Studio screenshots or FPS data.
This report is for the private A candidate only; it cannot approve formal RC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS))
from compose_official70 import BASE, FEATURE, ROUTE, verify_b

SCENES = [
    "lobby_spawn",
    "role_selection",
    "castle_foundation_silhouette",
    "coastal_land_sea",
    "neutral_swarm",
    "enemy_egg_pickup",
    "egg_return_path",
    "match_result",
]
DEVICES = ["PC", "ANDROID_LOW_2_TO_4_GB_RAM"]
PHASES = ["BEFORE", "AFTER"]
# User-visible fade starts at 150 and reaches invisible at 190 studs.
# At >190 the foundation is removed by the ordinary camera LOD.
LOD_TRIAL_DISTANCES = [130, 150, 160, 175, 189, 195]


def planned_fade_alpha(distance: int) -> float | None:
    if distance > 190:
        return None  # decor absent; not a rendered object with transparency=1
    return round(min(1.0, max(0.0, (distance - 150) / 40)), 3)


def foundation_lod_evidence() -> dict:
    """Describe real tests still owed; never turn source math into art proof."""
    return {
        "same_camera_distance_trials": [
            {
                "camera_to_core_studs": distance,
                "expected_present": distance <= 190,
                "source_expected_transparency": planned_fade_alpha(distance),
                "actual_studio_capture": None,
                "actual_rendered_visibility": None,
                "actual_device_fps": None,
                "status": "NOT_TESTED",
            }
            for distance in LOD_TRIAL_DISTANCES
        ],
        "streaming_cases": {
            "one_stone_removed_then_rebuilt": "NOT_TESTED",
            "stone_reparented_and_old_orphan_destroyed": "NOT_TESTED",
            "whole_folder_removed_then_rebuilt": "NOT_TESTED",
            "round_exit_all_stones_removed": "NOT_TESTED",
        },
        # Source-only upper bounds from TWO independent optional proposals,
        # not a combined Studio measurement or blanket authorization.
        "source_budget_parts": {
            "foundation_982_touch": 16,
            "foundation_982_pc": 24,
            "approach_988_touch": 16,
            "approach_988_pc": 24,
            "both_optional_touch": 32,
            "both_optional_pc": 48,
        },
        "approve_dual_adoption_without_mobile_runtime_evidence": False,
        "studio_2client_verified": False,
        "gate": "ART_NO_GO_NOT_TESTED",
    }


def require(ok: bool, failure: str):
    if not ok:
        raise ValueError("RED_GQ470_FOUNDATION_ART_REPORT_" + failure)


def digest(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def emit(candidate: Path, place: Path, out: Path) -> dict:
    candidate, place, out = candidate.resolve(), place.resolve(), out.resolve()
    verify_b(candidate, place)
    source_receipt = json.loads(
        (candidate / "GQ470_CASTLE_FOUNDATION_SOURCE_RECEIPT.json").read_text(encoding="utf-8")
    )
    require(source_receipt["base_head"] == BASE and
            source_receipt["feature_id"] == FEATURE and
            source_receipt["added_selected_script"] == ROUTE and
            source_receipt["original_sources_preserved"] == 69 and
            source_receipt["candidate_source_count"] == 70 and
            source_receipt["formal_integrated"] is False and
            source_receipt["owner_accepted"] is False and
            source_receipt["art_gate"] == "ART_NO_GO",
            "CANDIDATE_SOURCE_RECEIPT")
    shots = [
        {"scene": scene, "device": device, "comparison": phase,
         "exists": False, "file": None, "human_score": None}
        for scene in SCENES for device in DEVICES for phase in PHASES
    ]
    require(len(shots) == 32 and all(not s["exists"] for s in shots),
            "NO_REAL_CAMERA_EVIDENCE")
    report = {
        "schema": "GQ470_FB015_CASTLE_FOUNDATION_ART_GATE_20261121_V1",
        "feature_id": FEATURE,
        "status": "SOURCE_QA_ONLY_NOT_FORMAL_NOT_ART_GO",
        "official_branch": "rc/p0d-s1-kids-rc01",
        "base_head": BASE,
        "candidate_place_bytes": place.stat().st_size,
        "candidate_place_sha256": digest(place.read_bytes()),
        "original_place_bytes": source_receipt["original_place_bytes"],
        "script_count_change": "PRIVATE_ONLY_69_TO_70",
        "source_nonloss": "69_ORIGINAL_EXACT",
        "native_compile": "PASS_SOURCE_ONLY_AFTER_ACTIONS",
        "rojo": "PASS_SOURCE_ONLY_AFTER_ACTIONS",
        "rendering_score": "NOT_TESTED",
        "pc_art_45of50": "NOT_TESTED_TARGET_4_5_OUT_OF_5",
        "android_art_40of50": "NOT_TESTED_TARGET_4_0_OUT_OF_5",
        "android_15min_low_end": {
            "hardware_model": None,
            "duration_minutes": None,
            "median_fps": None,
            "p10_fps": None,
            "thermal_drop_fraction": None,
            "crash_or_oom_count": None,
            "targets": {"median_fps_at_least": 30,
                        "p10_fps_at_least": 25,
                        "thermal_drop_fraction_at_most": 0.20,
                        "crash_or_oom_count": 0},
            "gate": "MOBILE_NO_GO_NOT_TESTED",
        },
        "kid_first_3min": {
            "time_to_move_seconds": None,
            "time_to_attack_seconds": None,
            "time_to_hit_enemy_seconds": None,
            "time_to_understand_egg_castle_seconds": None,
            "fun_score": None,
            "targets": {"move": 15, "attack": 45,
                        "hit_enemy": 75, "understand_egg_castle": 180,
                        "fun_score_at_least": 4},
            "gate": "FUN_NO_GO_NOT_TESTED",
        },
        "comparison_images": shots,
        "foundation_lod_evidence": foundation_lod_evidence(),
        "comparison_image_count": 0,
        "expected_comparison_image_count": 32,
        "pc_android_comparison_images": "0/32",
        "studio_solo": "NOT_TESTED",
        "studio_2client": "NOT_TESTED",
        "owner_accepted": False,
        "formal_rc_integrated": False,
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
        "b_admission": "DEFER_P0_910_FIRST_PENDING_CLAIM_AND_250",
    }
    require(len(report["foundation_lod_evidence"]["same_camera_distance_trials"]) == 6
            and not report["foundation_lod_evidence"]["approve_dual_adoption_without_mobile_runtime_evidence"]
            and all(x["status"] == "NOT_TESTED"
                    and x["actual_studio_capture"] is None
                    for x in report["foundation_lod_evidence"]["same_camera_distance_trials"]),
            "FAKE_DISTANCE_OR_STREAMING_PROOF")
    require(report["comparison_image_count"] == 0 and
            report["art_gate"] == "ART_NO_GO" and
            report["product_gate"] == "PRODUCT_NO_GO",
            "CANNOT_MARK_HUMAN_ART_GO")
    require(not out.exists(), "NO_REPORT_OVERWRITE")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--place", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    opt = ap.parse_args()
    result = emit(opt.candidate, opt.place, opt.out)
    print("GQ470_FOUNDATION_ART_REPORT_0_OF_32_HONEST_SOURCE_ONLY_PASS",
          result["candidate_place_bytes"], result["candidate_place_sha256"])
