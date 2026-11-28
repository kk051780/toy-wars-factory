"""Evidence-honest #420 art report. Source proof never means Studio/ART GO."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

SCENES=("lobby","field_wide","castle","sea","forest","neutral","beast","combat")
DEVICES=("pc","android")
VERSIONS=("before","after")

def build(place:Path,receipt:Path,geometry:Path)->dict:
    raw=place.read_bytes()
    source=json.loads(receipt.read_text(encoding="utf-8"))
    geom=json.loads(geometry.read_text(encoding="utf-8"))
    if source.get("candidate_source_count")!=70 or not source.get("original_69_routes_sha_and_class_identical"):
        raise ValueError("RED_GQ470_ART_SOURCE_COMPOSITION_MISSING")
    if geom.get("source_gate")!="GEOMETRY_MODEL_PASS_NOT_STUDIO":
        raise ValueError("RED_GQ470_ART_GEOMETRY_NOT_CHECKED")
    if len(raw)<798390:
        raise ValueError("RED_GQ470_ART_CANDIDATE_PLACE_TOO_SMALL")
    shots=[f"{v}/{d}/{s}.png" for s in SCENES for d in DEVICES for v in VERSIONS]
    assert len(shots)==32 and len(set(shots))==32
    return {
        "schema":"GQ470_FB015_SKY_ART_CHECK_REPORT_V1",
        "source_head":os.environ.get("GITHUB_SHA","UNKNOWN"),
        "source_workflow_run":os.environ.get("GITHUB_RUN_ID","UNKNOWN"),
        "feature_id":source["feature_id"],
        "baseline_formal_rc_sha":source["formal_rc_head"],
        "stage":"A_REAL70_PRIVATE_SOURCE_ONLY_NOT_FORMAL",
        "formal_rc_integrated":False,
        "place_sha256":hashlib.sha256(raw).hexdigest(),
        "place_bytes":len(raw),
        "original_place_bytes":source["original_place_bytes"],
        "original_69_sources_exact":True,
        "candidate_sources":70,
        "new_local_scripts":1,
        "native_off69_on70":"PASS_CI_SOURCE_COMPILATION_ONLY",
        "rojo_off69_exact_and_on70":"PASS_CI_SOURCE_CONSTRUCTION_ONLY",
        "geometry_source_model":geom,
        "visual_evidence_gate":{
            "required":32,
            "provided":0,
            "missing_images":shots,
            "identical_camera_reproduction":"NOT_TESTED",
        },
        "pc_human_art_rating":None,
        "android_human_art_rating":None,
        "reference_benchmark_video_frames":"NOT_TESTED",
        "studio_solo":"NOT_TESTED",
        "studio_2client":"NOT_TESTED",
        "android_15min_fps_thermal":"NOT_TESTED",
        "first_three_minute_kid_fun":"NOT_TESTED",
        "actual_collision_and_camera_occlusion":"NOT_TESTED",
        "owner_accepted":False,
        "art_verdict":"ART_NO_GO",
        "mobile_verdict":"MOBILE_NO_GO",
        "fun_verdict":"FUN_NO_GO",
        "product_verdict":"PRODUCT_NO_GO",
        "adoption_priority":"DEFER_910_PLAYABLE_CORE_FIRST",
        "next_required":"#220 authenticated fresh-HASH and #420 same camera PC/Android screenshots + human/OWNER gate",
    }

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--place",required=True,type=Path)
    a.add_argument("--receipt",required=True,type=Path)
    a.add_argument("--geometry",required=True,type=Path)
    a.add_argument("--out",required=True,type=Path)
    x=a.parse_args()
    report=build(x.place,x.receipt,x.geometry)
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ART_CHECK_REPORT",report["place_sha256"],report["place_bytes"],
          report["visual_evidence_gate"]["provided"],"/",
          report["visual_evidence_gate"]["required"],report["art_verdict"])
