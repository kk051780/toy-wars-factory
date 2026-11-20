#!/usr/bin/env python3
"""Reproducible camera instructions for true Studio comparison, not screenshots.

Reads the existing #420 32-image template and the actual REAL69 selected
source. Does not invent pictures, FPS, human ratings or owner acceptance.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import export_b1 as handoff
import patch_canyon_facets69 as gate

FIELD_SHOTS = (
    "before/pc/field_wide.png",
    "after/pc/field_wide.png",
    "before/android/field_wide.png",
    "after/android/field_wide.png",
)
ORIGIN = "floor.CFrame*CFrame.new(0,floor.Size.Y/2+12,-175)"
SCENE_NAME = "GQ8_RC85_WCS_Canyon"

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("RED_CANYON_CAPTURE_SPEC_" + reason)

def build(data: dict, actual_before: bytes, actual_after: bytes,
          candidate_head: str, candidate_place_sha: str) -> dict:
    require(len(candidate_head) == 40 and
            all(c in "0123456789abcdef" for c in candidate_head),
            "CANDIDATE_HEAD_REQUIRED")
    require(len(candidate_place_sha) == 64 and
            all(c in "0123456789abcdef" for c in candidate_place_sha),
            "REAL_PLACE_SHA_REQUIRED")
    require(data.get("schema") == "P0D_ART_STUDIO_EVIDENCE_V1",
            "EXISTING_ART_SCHEMA")
    shots = data.get("shots")
    require(isinstance(shots, list) and len(shots) == 32,
            "COMPLETE_ORIGINAL_TEMPLATE_32")
    fields = [x.get("file") for x in shots if x.get("scene") == "field_wide"]
    require(tuple(fields) == FIELD_SHOTS, "FOUR_GENUINE_FIELDMAP_SLOTS")
    require(len({x.get("file") for x in shots}) == 32, "GLOBAL_NO_DUPLICATE")
    for raw in (actual_before, actual_after):
        source = raw.decode("utf-8")
        require(ORIGIN in source and
                f'stage.Name="{SCENE_NAME}"' in source and
                'local safe=block("AlwaysOpenSafeRoute"' in source and
                'local shortcut=block("ShortcutBridge"' in source,
                "ACTUAL_CANYON_SOURCE_GEOMETRY_ANCHOR")
    require(actual_after == gate.transform(actual_before.decode()).encode(),
            "EXACT_MATCHED_PATCH")
    gate.verify_visual_contract(gate.NEW)
    return {
        "schema": "GQ470_CANYON_REAL69_FIELD_WIDE_CAPTURE_GUIDE_V1",
        "candidate_only": True,
        "never_use_as_evidence_or_owner_acceptance": True,
        "formal_original_head": gate.BASE,
        "candidate_A_head": candidate_head,
        "actual_candidate_place_sha256": candidate_place_sha,
        "before_selected_source_sha256": gate.sha(actual_before),
        "after_selected_source_sha256": gate.sha(actual_after),
        "scene": "field_wide",
        "project_required_32_shots": 32,
        "this_feature_screenshot_slots": list(FIELD_SHOTS),
        "this_feature_shots_received": 0,
        "studio_only": True,
        "in_game_instance_path": (
            "Workspace/EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW/"
            "TEAM_Arena/GQ8_RC85_WCS_Canyon"),
        "also_recheck_in_mode": "BATTLE_ROYALE_Arena",
        "origin_formula_relative_to_existing_arena_floor": ORIGIN,
        "camera_local_offset_studs": [0, 24, -52],
        "focus_local_offset_studs": [0, 3, -15],
        "camera_fov_degrees": 70,
        "before_after_must_match": (
            "camera_world_CFrame, zoom/FOV, mode, character position, "
            "weather, render graphics quality and image dimensions"),
        "visible_design_expected_not_proven": (
            "seven crystals are matte bank-side geometry; central bridge "
            "and safe route visible, no new overhead HUD"),
        "negative_engine_checks": [
            "no canyon respawn duplicate decorations per arena",
            "both modes have 7 dynamic decorations after scene startup",
            "collisions/touch/query/shadow remain false",
            "player can traverse central safe route and optional gate",
            "egg objective is not obstructed by silhouettes",
        ],
        "pc_capture": "NOT_TESTED",
        "android_capture": "NOT_TESTED",
        "human_art_rating": "NOT_TESTED",
        "android_15min_fps_and_heat": "NOT_TESTED",
        "first_3_min_fun": "NOT_TESTED",
        "owner_accepted": False,
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
    }

def main(root: Path, template: Path, head: str, out: Path) -> None:
    before, after, _ = handoff.verified(root)
    receipt = json.loads((root/gate.RECEIPT).read_text())
    place_sha = receipt.get("private_place_sha256")
    require(isinstance(place_sha, str), "REAL_PLACE_RECEIPT")
    report = build(json.loads(template.read_text()), before, after,
                   head, place_sha)
    require(not out.exists(), "OUTPUT_CANNOT_OVERWRITE_REAL_EVIDENCE")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                              sort_keys=True)+"\n", encoding="utf-8")
    print("GQ470_CANYON_FIELDMAP_FIXED_CAMERA_SPEC_NOT_EVIDENCE_PASS")

def self_test() -> None:
    template = json.loads(Path("art_quality/EVIDENCE_TEMPLATE.json").read_text())
    sample = (
        "-- " + gate.AUTHOR_MARK + "\n" +
        'if not RunService:IsStudio() then return end\n' +
        'local function setGate(open:boolean)\nend\n' +
        'local function authorized(p:Player,target:BasePart):boolean\nend\n' +
        'stage:SetAttribute("SafeRouteAlwaysAvailable",true)\n' +
        'local safe=block("AlwaysOpenSafeRoute"\n' +
        'local shortcut=block("ShortcutBridge"\n' +
        f'local origin={ORIGIN}\n' +
        f'stage.Name="{SCENE_NAME}"\n' +
        gate.OLD)
    newer = gate.transform(sample).encode()
    report = build(template, sample.encode(), newer,
                   gate.BASE, "a"*64)
    require(report["this_feature_shots_received"] == 0
            and report["owner_accepted"] is False
            and report["project_required_32_shots"] == 32,
            "NO_FAKE_EVIDENCE")
    broken = json.loads(json.dumps(template))
    broken["shots"][4]["file"] = "before/pc/not_field_wide.png"
    for t,b,a,sha in (
        (broken,sample.encode(),newer,"a"*64),
        (template,sample.encode(),newer,"abc"),
        (template,sample.encode(),b"fake Lua","a"*64),
    ):
        try:
            build(t,b,a,gate.BASE,sha)
        except (ValueError, UnicodeDecodeError):
            pass
        else:
            raise AssertionError("RED_FAKE_CAPTURE_PLAN_MUTANT_ACCEPTED")
    print("GQ470_CANYON_CAPTURE_GUIDE_3_NEGATIVE_MUTATIONS_PASS")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--candidate", type=Path)
    p.add_argument("--template", type=Path,
                   default=Path("art_quality/EVIDENCE_TEMPLATE.json"))
    p.add_argument("--candidate-head", type=str)
    p.add_argument("--out", type=Path)
    args=p.parse_args()
    if args.self_test:
        self_test()
    else:
        require(args.candidate is not None and args.out is not None and
                args.candidate_head is not None, "NEED_CAPTURE_INPUTS")
        main(args.candidate,args.template,args.candidate_head,args.out)
