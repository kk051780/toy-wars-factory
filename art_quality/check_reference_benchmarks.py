#!/usr/bin/env python3
"""Compare P0D against documented high-end Roblox visual references.

Honest about what cannot be verified: no source-only script or metadata search
proves a video was watched, a screenshot is authentic, or visuals are top tier.
Fast CI validates contracts; strict review requires human-submitted real media.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

SCHEMA = "P0D_ART_TOP_CLASS_REFERENCE_V2"
REVIEW_SCHEMA = "P0D_ART_TOP_CLASS_HUMAN_REVIEW_V1"
DEVICES = ("pc", "android")
EXPECTED_CLIPS = {"ref01", "ref02", "ref03", "ref04"}

def load(path: Path) -> dict:
    obj = json.loads(path.read_text("utf8"))
    if not isinstance(obj, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return obj

def audit_registry(data: dict) -> dict:
    errors = []
    if data.get("schema") != SCHEMA:
        errors.append("REGISTRY_SCHEMA_MISMATCH")
    if data.get("target") != "TOP_CLASS_ROBLOX_BATTLE_VISUALS":
        errors.append("WEAKENED_TARGET")
    if data.get("no_auto_beauty_signoff") is not True:
        errors.append("AUTO_BEAUTY_PASS_PROHIBITED")
    if data.get("owner_accepted") is not False:
        errors.append("FALSE_OWNER_ACCEPTANCE")
    if data.get("overall_grade_goal", 0) < 4.5:
        errors.append("ART_TARGET_BELOW_4_5")
    refs = data.get("user_referenced_clips", [])
    ids = [r.get("id") for r in refs if isinstance(r, dict)]
    if len(refs) != 4 or set(ids) != EXPECTED_CLIPS or len(ids) != len(set(ids)):
        errors.append("OWNER_REFERENCED_FOUR_VIDEO_INVENTORY_INCOMPLETE")
    unreviewed = []
    for ref in refs:
        if not isinstance(ref, dict):
            errors.append("INVALID_REFERENCE_RECORD")
            continue
        label = ref.get("id", "unknown")
        watched = ref.get("full_video_watched")
        status = ref.get("source_verification", "")
        url = ref.get("link")
        if watched is True:
            # The registry is metadata only. A claim of watching must be
            # accompanied by timestamped frame evidence in the review form.
            errors.append("UNSUPPORTED_PLAYBACK_CLAIM_IN_REGISTRY:" + label)
        if watched is not False:
            errors.append("REFERENCE_VIDEO_REVIEW_STATUS_UNKNOWN:" + label)
        if not status:
            errors.append("MISSING_SOURCE_VERIFICATION:" + label)
        if url is not None and not (isinstance(url, str) and url.startswith("https://")):
            errors.append("INVALID_VERIFIED_URL:" + label)
        unreviewed.append(label)
    additional = data.get("additional_grounded_references", [])
    if not isinstance(additional, list) or len(additional) < 2:
        errors.append("WORLD_COMBAT_COMPARATORS_MISSING")
    by_id = {r.get("id"): r for r in additional if isinstance(r, dict)}
    for name in ("fushimi_castle", "the_strongest_battlegrounds"):
        if name not in by_id or not by_id[name].get("evidence_status"):
            errors.append("MISSING_COMPARATOR:" + name)
    dims = data.get("grade_dimensions", [])
    if not isinstance(dims, list) or len(dims) != 8 or len({r.get("id") for r in dims if isinstance(r, dict)}) != 8:
        errors.append("TOP_CLASS_EIGHT_DIMENSIONS_REQUIRED")
    weights = []
    for dim in dims:
        if not isinstance(dim, dict) or dim.get("reference") not in by_id:
            errors.append("INVALID_DIMENSION_REFERENCE")
            continue
        weights.append(dim.get("weight", 0))
        if not isinstance(dim.get("criterion"), str) or not dim["criterion"].strip():
            errors.append("DIMENSION_WITHOUT_CRITERION:" + str(dim.get("id")))
    if abs(sum(weights) - 1.0) > 1e-6:
        errors.append("DIMENSION_WEIGHTS_NOT_NORMALIZED")
    return {"registry_valid": not errors, "errors": errors,
            "owner_video_count": len(refs), "full_video_reviewed": 0,
            "confirmed_still_comparators": sum(
                "STILL" in str(r.get("evidence_status", "")) for r in additional if isinstance(r, dict)),
            "target": data.get("target"), "score_goal": 4.5,
            "note": "User supplied search screenshot, not video media. Full playback not verified."}

def audit_human_review(registry: dict, review_file: Path | None) -> dict:
    if review_file is None:
        return {"review_status": "MISSING", "violations": ["NO_HUMAN_VIDEO_AND_STUDIO_REVIEW"],
                "owner_accepted": False}
    try:
        record = load(review_file)
    except (OSError, ValueError) as exc:
        return {"review_status": "INVALID", "violations": ["INVALID_REVIEW_JSON:" + str(exc)],
                "owner_accepted": False}
    errors = []
    if record.get("schema") != REVIEW_SCHEMA:
        errors.append("REVIEW_SCHEMA_MISMATCH")
    reviewer = record.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        errors.append("MISSING_NAMED_REVIEWER")
    clips = record.get("user_clip_reviews", [])
    by_clip = {c.get("id"): c for c in clips if isinstance(c, dict)}
    for ref in registry.get("user_referenced_clips", []):
        ident = ref["id"]
        claim = by_clip.get(ident, {})
        if claim.get("full_video_watched") is not True:
            errors.append("VIDEO_NOT_FULLY_REVIEWED:" + ident)
            continue
        # This only validates submitted evidence, not actual video authenticity.
        if not ref.get("link") and not claim.get("verified_source_url"):
            errors.append("UNRESOLVED_VIDEO_SOURCE:" + ident)
        if not claim.get("reviewer") or not claim.get("frames_by_timestamp"):
            errors.append("UNSUPPORTED_VIDEO_REVIEW_CLAIM:" + ident)
        else:
            frames = claim["frames_by_timestamp"]
            if not isinstance(frames, list) or len(frames) < 3 or not all(
                isinstance(f, dict) and isinstance(f.get("timestamp_seconds"), (int,float))
                and isinstance(f.get("observation"), str) and f.get("observation").strip()
                and isinstance(f.get("frame_file"), str) and f.get("frame_file").strip()
                for f in frames):
                errors.append("REFERENCE_FRAME_TIMESTAMPS_INCOMPLETE:" + ident)
    scores = record.get("comparisons", {})
    if not isinstance(scores, dict):
        scores = {}
    good = 0
    for dim in registry.get("grade_dimensions", []):
        name = dim.get("id")
        entry = scores.get(name, {})
        for device in DEVICES:
            cell = entry.get(device, {}) if isinstance(entry, dict) else {}
            p0d = cell.get("p0d_score")
            ref = cell.get("reference_score")
            name_pair = str(name) + "/" + device
            if type(p0d) not in (int, float) or type(ref) not in (int, float):
                errors.append("SCORE_NOT_YET_MEASURED:" + name_pair)
                continue
            if not (1 <= p0d <= 5 and 1 <= ref <= 5):
                errors.append("OUT_OF_RANGE_SCORE:" + name_pair)
                continue
            if abs(round(p0d*2) - p0d*2) > 1e-8 or abs(round(ref*2) - ref*2) > 1e-8:
                errors.append("HALF_POINT_INCREMENTS_REQUIRED:" + name_pair)
            minimum = 4.5 if device == "pc" else 4.0
            # A low-end phone needs a clear, attractive scene, not desktop-only photorealism.
            # PC comparisons retain the benchmark delta; mobile FPS is gated separately.
            below = p0d < minimum or (device == "pc" and p0d < ref - 0.25)
            if below:
                errors.append("BELOW_TOP_CLASS_PLAYABLE_TARGET:" + name_pair)
            elif not (cell.get("p0d_studio_evidence") and cell.get("reference_frame_evidence")
                      and cell.get("reason")):
                errors.append("MISSING_SIDE_BY_SIDE_EVIDENCE:" + name_pair)
            else:
                good += 1
    if record.get("critical_visual_blockers") != []:
        errors.append("CRITICAL_VISUAL_BLOCKERS_PRESENT_OR_UNKNOWN")
    if record.get("android_pc_gameplay_tested") is not True:
        errors.append("MISSING_REAL_STUDIO_PC_ANDROID_TEST")
    for category in ("running","sword_hit","beast_boss","forest_camera"):
        video = record.get("p0d_live_videos", {}).get(category, {})
        if not video.get("file") or not video.get("review_notes"):
            errors.append("MISSING_P0D_MOTION_CLIP:" + category)
    # Real OWNER acceptance must remain external to this automated tool.
    return {"review_status": "REVIEW_READY_OWNER_PENDING" if not errors else "EVIDENCE_INCOMPLETE",
            "violations": errors, "passed_dimension_device_pairs": good,
            "required_dimension_device_pairs": 16, "owner_accepted": False}

def report(registry_file: Path, review_file: Path | None) -> dict:
    reg = load(registry_file)
    source = audit_registry(reg)
    review = audit_human_review(reg, review_file)
    decision = "ART_NO_GO"
    return {"schema": "P0D_ART_REFERENCE_AUDIT_V2",
            "objective": "top-class showcase world AND top-class battle visuals",
            "reference_catalog": source, "real_video_review": review,
            "art_decision": decision, "owner_accepted": False,
            "integration_policy": "FAST_SOURCE_LINT_EVERY_PR_FULL_ART_REVIEW_AT_RC_MILESTONES",
            "limitation": "No automation validates full-video watching, Studio screenshot authenticity, or artistic quality without human review."}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--strict-review", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = report(args.references, args.review)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {"schema": "P0D_ART_REFERENCE_AUDIT_V2", "art_decision": "ART_NO_GO",
                  "owner_accepted": False,
                  "reference_catalog": {"registry_valid": False, "errors": [str(exc)]},
                  "real_video_review": {"review_status": "INVALID"}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
    valid = result["reference_catalog"].get("registry_valid") is True
    ready = result["real_video_review"].get("review_status") == "REVIEW_READY_OWNER_PENDING"
    print("P0D_TOP_CLASS_VISUAL_BENCHMARK", "REGISTERED" if valid else "INVALID",
          result["real_video_review"].get("review_status"), "ART_NO_GO")
    return 2 if not valid or (args.strict_review and not ready) else 0

if __name__ == "__main__":
    sys.exit(main())
