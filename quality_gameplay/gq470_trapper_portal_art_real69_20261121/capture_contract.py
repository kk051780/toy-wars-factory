#!/usr/bin/env python3
"""32-slot matched-camera Studio art evidence request, NOT fabricated renders.

Supports #420 ART / #470 FB015. A slot is a capture task, never a screenshot.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

FEATURE = "GQ470_FB015_TRAPPER_WARP_FACET_REAL69_20261121"
SCENES = {
    "A_NEAR": "First trapper warp pad A at 4-7 studs, prompt in sight",
    "B_NEAR": "Second warp pad B at 4-7 studs, prompt in sight",
    "PAIR_WIDE": "Both linked pads visible with the same world landmarks",
    "TWOCLIENT_USE": "Two Studio clients after an authorized real warp, both pads in session",
}
DEVICES = ("PC", "ANDROID")
VERSIONS = ("OFFICIAL_BEFORE", "CANDIDATE_AFTER")
VIEWS = ("SAME_NEAR", "SAME_WIDE")

def need(ok: bool, code: str):
    if not ok:
        raise ValueError("RED_GQ470_TRAPPER_CAPTURE_" + code)

def build() -> dict:
    slots = []
    for scene, instruction in SCENES.items():
        for device in DEVICES:
            for view in VIEWS:
                for version in VERSIONS:
                    slots.append({
                        "id": f"{scene}_{device}_{view}_{version}",
                        "scene": scene,
                        "device": device,
                        "camera_pose": view,
                        "version": version,
                        "instruction": instruction,
                        "camera_contract": "exact same CFrame, FOV, GUI scale, quality preset and time of day in BEFORE and AFTER",
                        "file_expected": f"{scene}_{device}_{view}_{version}.png",
                        "file_received": None,
                        "image_sha256": None,
                        "device_model": None,
                        "measured_fps": None,
                        "human_score_1_to_5": None,
                    })
    return {
        "schema": "GQ470_TRAPPER_PORTAL_ART_CAPTURE_SPEC_32_V1",
        "feature_id": FEATURE,
        "source_gate": "SOURCE_ONLY",
        "formal_rc_integrated": False,
        "studio_tested": False,
        "android_15min_tested": False,
        "art_gate": "ART_NO_GO",
        "human_art_evaluation": "NOT_TESTED",
        "required_png": 32,
        "received_png": 0,
        "scenes": SCENES,
        "capture_slots": slots,
        "comparison_notes": [
            "A/B differentiability: visual form and color must be readable without relying only on the prompt",
            "At 4-7 studs prompt text remains legible; at wide view 3D facet remains recognizable",
            "Check paired warp in both directions and after 3 uses / 40s cleanup",
            "Check 2client TEAM / BR negatives and egg-carry veto without mistaking visual signals for travel authorization",
            "PC vs Android: check glare, overdraw, touch occlusion, and FPS after 15 minutes",
            "Do not invent screenshot files, scores, FPS or a Roblox Studio PASS",
        ],
    }

def validate(report: dict) -> None:
    slots = report.get("capture_slots")
    need(isinstance(slots, list) and len(slots) == 32, "COUNT32")
    need(report.get("required_png") == 32 and
         report.get("received_png") == 0, "EVIDENCE_NOT_FAKED")
    need(report.get("formal_rc_integrated") is False and
         report.get("studio_tested") is False and
         report.get("android_15min_tested") is False and
         report.get("art_gate") == "ART_NO_GO" and
         report.get("human_art_evaluation") == "NOT_TESTED",
         "ART_MUST_REMAIN_NO_GO")
    found = set()
    pairs = {}
    for s in slots:
        key = (s["scene"], s["device"], s["camera_pose"], s["version"])
        need(key not in found, "DUP_SLOT")
        found.add(key)
        need(s["scene"] in SCENES and s["device"] in DEVICES and
             s["camera_pose"] in VIEWS and s["version"] in VERSIONS,
             "INVALID_AXIS")
        need(s["file_expected"] == "_".join(key) + ".png", "FILENAME_DRIFT")
        need(s["file_received"] is None and s["image_sha256"] is None and
             s["human_score_1_to_5"] is None and s["measured_fps"] is None,
             "FABRICATED_ART")
        base = key[:3]
        pairs.setdefault(base, set()).add(s["version"])
        need("exact same CFrame" in s["camera_contract"], "NOT_MATCHED_CAMERA")
    need(len(found) == 32 and len(pairs) == 16 and
         all(versions == set(VERSIONS) for versions in pairs.values()),
         "ALL_SAME_CAMERA_PAIRS")

def selftest():
    report=build()
    validate(report)
    import copy
    for mutate in (
        lambda x:x["capture_slots"].pop(),
        lambda x:x["capture_slots"].append(copy.deepcopy(x["capture_slots"][0])),
        lambda x:x["capture_slots"][0].update(file_received="not_really.png"),
        lambda x:x["capture_slots"][0].update(human_score_1_to_5=5.0),
        lambda x:x["capture_slots"][0].update(camera_contract="different cameras"),
        lambda x:x["capture_slots"][0].update(device="VIRTUAL_ANDROID"),
        lambda x:x["capture_slots"][0].update(file_expected="wrong.png"),
        lambda x:x.update(received_png=32),
        lambda x:x.update(art_gate="ART_GO"),
        lambda x:x.update(studio_tested=True),
    ):
        t=copy.deepcopy(report)
        mutate(t)
        try:
            validate(t)
        except (ValueError, KeyError):
            pass
        else:
            raise AssertionError("RED_CAPTURE_EVIDENCE_FORGERY_ACCEPTED")
    print("GQ470_TRAPPER_32_SLOTS_16_MATCHED_PAIRS_10_NEGATIVES_PASS_NO_FAKE_PNG")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--out", type=Path)
    args=p.parse_args()
    if args.self_test:
        selftest()
    else:
        need(args.out is not None and not args.out.exists(), "OUTPUT_PATH_REQUIRED")
        report=build()
        validate(report)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        print("GQ470_TRAPPER_ART_CAPTURE_SPEC_ONLY_REAL_PNG_0_OF_32")
if __name__=="__main__":
    main()
