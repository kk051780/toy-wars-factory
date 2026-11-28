#!/usr/bin/env python3
"""Conservative #420 art and mobile acceptance receipt for a REAL70 A candidate.

This tool reports evidence gaps. It NEVER fabricates screenshot, Studio,
Android FPS, initial-3-minute FUN, or OWNER observations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SCENES=(
    "lobby_character_spawn",
    "lobby_ready_and_class",
    "red_castle_far",
    "red_castle_gate",
    "blue_castle_far",
    "blue_castle_gate",
    "egg_escape_lane",
    "forest_coast_route",
)
DEVICES=("PC","ANDROID")
VERSIONS=("BEFORE","AFTER")
OFFICIAL="e80973c354f14a0d0088577f3cc1a875454f0f8f"
PLACE_OFF_BYTES=798390

def fail(code:str):
    raise ValueError("RED_GQ470_BANNER_ART420_"+code)

def make(candidate:Path, place:Path)->dict:
    from compose_official70 import REPORT
    info=json.loads((candidate/REPORT).read_text(encoding="utf-8"))
    if info.get("formal_base_sha")!=OFFICIAL or info.get("formal_rc_modified") is not False:
        fail("FALSE_FORMAL_RC")
    if info.get("original_script_count_exact")!=69 or info.get("candidate_script_count")!=70:
        fail("WRONG_SOURCE_COUNT")
    raw=place.read_bytes()
    image=[
        dict(scene=scene,device=device,version=version,image_file=None,
             captured_at=None,image_exists=False,human_art_rating=None,
             real_device=None,authoritative_game_head=None)
        for scene in SCENES for device in DEVICES for version in VERSIONS
    ]
    return dict(
        schema="GQ470_BANNER_ART420_ACTUAL_EVIDENCE_GAP_V1",
        feature_id=info["feature_id"],
        formal_rc_head=OFFICIAL,
        official_original_place_bytes=PLACE_OFF_BYTES,
        candidate_real70_place_bytes=len(raw),
        candidate_real70_place_sha256=hashlib.sha256(raw).hexdigest(),
        formal_rc_integrated=False,
        source_native69_70="PASSED_IN_SAME_HEAD_CI",
        source_rojo_off69_on70="PASSED_IN_SAME_HEAD_CI",
        real_comparison_image_count=0,
        expected_comparison_image_count=32,
        comparison_images=image,
        owner_p0_player_not_visible="UNRESOLVED_NEEDS_STUDIO_RETEST",
        studio_solo="NOT_TESTED",
        studio_2client="NOT_TESTED",
        android15="NOT_TESTED",
        mobile_low_end_target=dict(
            median_fps=30,p10_fps=25,max_thermal_fps_degradation_pct=20,
            max_crashes=0),
        mobile_low_end_measurements=dict(
            device_model=None,ram_gb=None,median_fps=None,p10_fps=None,
            thermal_fps_degradation_pct=None,crashes=None),
        android_human_art_target=4.0,
        pc_human_art_target=4.5,
        android_human_art_measured=None,
        pc_human_art_measured=None,
        first3min_kid_fun_target=4.0,
        first3min_fun_measured=None,
        first_action_seconds_measured=None,
        castle_banner_visible_in_real_frame=None,
        player_avatar_visible_in_real_frame=None,
        art_gate="ART_NO_GO",
        mobile_gate="MOBILE_NO_GO",
        fun_gate="FUN_NO_GO",
        product_gate="PRODUCT_NO_GO",
        owner_accepted=False,
        reason="No Studio 2client images, Android 15min or human feedback; P0 player absent unresolved",
        rollback="omit optional new LocalScript, original 69 sources and Place remain byte identical",
    )

def verify(report:dict):
    expected={(s,d,v) for s in SCENES for d in DEVICES for v in VERSIONS}
    frames=report.get("comparison_images",[])
    actual={(e["scene"],e["device"],e["version"]) for e in frames}
    if len(frames)!=32 or len(actual)!=32 or actual!=expected:fail("32_SCENE_MATRIX")
    if report.get("real_comparison_image_count")!=0:fail("FAKE_SCREENSHOTS")
    if any(e.get("image_exists") is not False or e.get("image_file") is not None
           or e.get("human_art_rating") is not None for e in frames):fail("FAKE_PHOTOS")
    for key in ("studio_solo","studio_2client","android15"):
        if report.get(key)!="NOT_TESTED":fail("FAKE_ENGINE")
    if report.get("art_gate")!="ART_NO_GO" or report.get("fun_gate")!="FUN_NO_GO" or report.get("mobile_gate")!="MOBILE_NO_GO":fail("FAKE_PASS")
    if report.get("owner_accepted") is not False or report.get("formal_rc_integrated") is not False:fail("FAKE_ADOPTION")
    if report.get("mobile_low_end_measurements",{}).get("median_fps") is not None:fail("FAKE_FPS")
    if report.get("owner_p0_player_not_visible")!="UNRESOLVED_NEEDS_STUDIO_RETEST":fail("P0_UNJUSTIFIED_CLEAR")
    if report.get("first3min_fun_measured") is not None:fail("FAKE_FUN")
    return True

def negatives(report:dict):
    import copy
    for key,val in (
        ("real_comparison_image_count",32),
        ("studio_solo","PASS"),
        ("android15","PASS"),
        ("art_gate","ART_GO"),
        ("fun_gate","FUN_GO"),
        ("owner_accepted",True),
        ("formal_rc_integrated",True),
        ("owner_p0_player_not_visible","FIXED"),
        ("first3min_fun_measured",5.0),
    ):
        altered=copy.deepcopy(report)
        altered[key]=val
        try:verify(altered)
        except ValueError:pass
        else:raise AssertionError("RED_ART420_FAKE_"+key)
    fake=copy.deepcopy(report)
    fake["comparison_images"][0]["image_exists"]=True
    try:verify(fake)
    except ValueError:pass
    else:raise AssertionError("RED_ART420_FAKE_SCREENSHOT")
    print("GQ470_BANNER_ART420_TEN_FAKE_EVIDENCE_NEGATIVES_REJECTED")

def main(args):
    r=make(args.candidate,args.place)
    verify(r)
    negatives(r)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ470_BANNER_ART420_32_REAL_IMAGE_GAPS_0_OF_32_HONEST_NO_GO")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate",type=Path,required=True)
    parser.add_argument("--place",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    main(parser.parse_args())
