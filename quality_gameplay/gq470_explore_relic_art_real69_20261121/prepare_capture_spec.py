#!/usr/bin/env python3
"""Deterministic visual capture instructions for the existing #420 art gate.

This is NOT a screenshot generator, human rating, Roblox playtest or pass.
The existing #927/#420 evidence ingestion remains the only acceptance flow.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import export_b1 as handoff
import patch_explore_relic69 as gate

FIELD_SHOTS = (
    "before/pc/field_wide.png",
    "after/pc/field_wide.png",
    "before/android/field_wide.png",
    "after/android/field_wide.png",
)
SCENE = "field_wide"
REALM_SPEC = (
    ("REALM_SKY", -245, -310),
    ("REALM_SEA", 245, -310),
    ("REALM_EMBER", -245, 310),
    ("REALM_STAR", 245, 310),
)
SHARD_SPEC = (
    ("SHARD_1", -170, -240),
    ("SHARD_2", 170, -240),
    ("SHARD_3", -170, -75),
    ("SHARD_4", 170, 75),
    ("SHARD_5", -170, 240),
    ("SHARD_6", 170, 240),
)

def require(ok: bool, issue: str) -> None:
    if not ok:
        raise ValueError("RED_EXPLORE_CAPTURE_" + issue)

def make(template: dict, head: str, place_sha: str) -> dict:
    require(template.get("schema") == "P0D_ART_STUDIO_EVIDENCE_V1",
            "EXISTING_420_SCHEMA")
    require(isinstance(head, str) and re.fullmatch(r"[a-f0-9]{40}", head) is not None,
            "ACTUAL_HEAD_SHA")
    require(isinstance(place_sha, str) and re.fullmatch(r"[a-f0-9]{64}", place_sha) is not None,
            "ACTUAL_PLACE_SHA")
    shots = template.get("shots")
    require(isinstance(shots, list) and len(shots) == 32, "FULL_32_REQUIRED")
    files = [row.get("file") for row in shots]
    require(len(set(files)) == 32, "NO_DUPLICATE_IMAGE_PATHS")
    field = tuple(row.get("file") for row in shots if row.get("scene") == SCENE)
    require(field == FIELD_SHOTS, "FIXED_FOUR_IMAGE_SLOTS")
    require(len(REALM_SPEC) == 4 and len(SHARD_SPEC) == 6,
            "ORIGINAL_10_OBJECTIVES")
    return {
        "schema": "GQ470_EXPLORE_RELIC_REAL69_FIXED_CAMERA_PLAN_V1",
        "draft_instructions_only": True,
        "never_claim_as_actual_image_or_engine_pass": True,
        "candidate_branch": "quality/gq470-explore-relic-art-real69-20261121",
        "candidate_A_head": head,
        "base_formal_head_when_prepared": gate.BASE,
        "candidate_private_place_sha256": place_sha,
        "real_shots_accepted": 0,
        "real_shots_required": 32,
        "scene": SCENE,
        "scene_image_slots": list(field),
        "other_28_existing_art_gate_slots": "unchanged, required by #420",
        "world_path_TEAM": (
            "Workspace/EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW/"
            "TEAM_Arena/GQ8_LegacyExploration"
        ),
        "world_path_BR": (
            "Workspace/EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW/"
            "BATTLE_ROYALE_Arena/GQ8_LegacyExploration"
        ),
        "original_anchors_floor_local_XZ": {
            "realms": [{"id": k, "x": x, "z": z} for k,x,z in REALM_SPEC],
            "shards": [{"id": k, "x": x, "z": z} for k,x,z in SHARD_SPEC],
        },
        "camera_reference": {
            "note": "Studio capture operator must check real sightline and avatar position; coordinates below are a proposed identical BEFORE/AFTER starting point, not verified engine view",
            "floor_local_camera_xyz": [-273, 36, -358],
            "floor_local_focus_xyz": [-245, 3, -310],
            "fov_degrees": 70,
            "comparison_required": (
                "identical before/after world-camera CFrame, mode, avatar "
                "position, FOV, phase, graphics settings, weather, capture size"
            )
        },
        "additional_studio_inspection": [
            "all 4 realms and 6 shards show distinct silhouettes from normal play distance",
            "each of 10 artifacts remains discoverable, reachable, and prompted only once",
            "prompt requires real line of sight; remote spoof or off-team mode never grants exploration",
            "no objective markers block castle approaches or egg carrying line of sight",
            "no new collisions, touch, raycast or shadows; old 10*3 Part count stays unchanged",
            "after world destroy/next round, decorations do not persist or stack",
            "check both TEAM and BATTLE_ROYALE, PC and Android settings",
        ],
        "human_pc_art": "NOT_TESTED",
        "human_android_art": "NOT_TESTED",
        "solo_2client": "NOT_TESTED",
        "android_15min_fps_heat": "NOT_TESTED",
        "first_3min_fun": "NOT_TESTED",
        "owner_accepted": False,
        "art_gate": "ART_NO_GO",
        "product_gate": "PRODUCT_NO_GO",
    }

def self_test() -> None:
    sample=json.loads(Path("art_quality/EVIDENCE_TEMPLATE.json").read_text())
    plan=make(sample,gate.BASE,"a"*64)
    require(plan["real_shots_accepted"]==0 and plan["real_shots_required"]==32
            and len(plan["original_anchors_floor_local_XZ"]["realms"])==4
            and len(plan["original_anchors_floor_local_XZ"]["shards"])==6
            and plan["art_gate"]=="ART_NO_GO", "POSITIVE")
    malformed=json.loads(json.dumps(sample))
    malformed["shots"][4]["file"]="before/pc/unmatched.png"
    duplicated=json.loads(json.dumps(sample))
    duplicated["shots"][4]["file"]=duplicated["shots"][0]["file"]
    absent=json.loads(json.dumps(sample))
    absent["shots"].pop()
    for i,(t,h,p) in enumerate((
        (malformed,gate.BASE,"a"*64),
        (duplicated,gate.BASE,"a"*64),
        (absent,gate.BASE,"a"*64),
        (sample,"not-a-head","a"*64),
        (sample,gate.BASE,"wrong-place-sha"),
    )):
        try: make(t,h,p)
        except ValueError: pass
        else: raise AssertionError("RED_CAPTURE_MUTANT_ACCEPTED_"+str(i))
    print("GQ470_EXPLORE_RELIC_CAPTURE_5_MUTATION_NEGATIVES_PASS")

def main(candidate: Path, head: str, out: Path) -> None:
    before, after, cls=handoff.verified(candidate)
    require(cls=="Script" and before!=after, "SELECTED_ORIGINAL_SOURCE")
    require(after == gate.transform(before.decode("utf-8")).encode("utf-8"),
            "EXACT_SCULPT_SOURCE")
    receipt=json.loads((candidate/gate.RECEIPT).read_text())
    place_sha=receipt.get("private_place_sha256")
    require(isinstance(place_sha,str),"REAL_PRIVATE_PLACE_RECEIPT")
    template=json.loads(Path("art_quality/EVIDENCE_TEMPLATE.json").read_text())
    plan=make(template,head,place_sha)
    require(not out.exists(), "DO_NOT_OVERWRITE_ACTUAL_EVIDENCE")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(plan,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                   encoding="utf-8")
    print("GQ470_EXPLORE_RELIC_FIXED_CAMERA_INSTRUCTIONS_NO_REAL_PNG_PASS")

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--candidate",type=Path)
    a.add_argument("--candidate-head")
    a.add_argument("--out",type=Path)
    opts=a.parse_args()
    if opts.self_test: self_test()
    else:
        require(opts.candidate is not None and opts.out is not None and
                opts.candidate_head is not None, "MISSING_INPUTS")
        main(opts.candidate,opts.candidate_head,opts.out)
