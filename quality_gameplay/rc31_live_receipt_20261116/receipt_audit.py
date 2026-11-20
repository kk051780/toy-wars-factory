#!/usr/bin/env python3
"""Read-only RC31 evidence audit: never equate old receipt with live HEAD CI.

This script does not fetch GitHub or alter game source. The caller supplies the
independently read official branch SHA. No release, Studio or OWNER approval is inferred.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
LANES = {
    "character": ("original_game482", "fused_gameplay_quality530"),
    "field": ("art485", "original_route536"),
    "battle": ("mage510", "four_combat529", "current_human535"),
    "castle_egg": ("castle_refresh537", "castle_board547", "carrier_stale_avatar551"),
    "neutral": ("pacing494", "fairness501", "neutral_fallback541"),
    "item": ("original_item489",),
    "lobby": ("lobby_world_539",),
    "balance": ("neutral_budget528", "bot_nearest555"),
}
FLAGS = {
    "DEAD_CASTER_FENCE_530",
    "HUMAN_MATCH_MEMBERSHIP_535",
    "NEUTRAL_NEAREST_ELIGIBLE_FALLBACK_541",
    "ORIGINAL_ITEM_AUTHOR_489",
    "LOBBY_NEARBY_BOARDS_539",
    "BOT_ROUTE_FULLSTEP_536",
    "CASTLE_EGG_BOARD_DISTANCE_547",
    "CARRIER_STALE_AVATAR_DIED_FENCE_551",
}


def require_sha(value: object, name: str) -> str:
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise ValueError(f"{name}: expected immutable lowercase 40-character SHA")
    return value


def audit(manifest: dict, active: dict, catalog: dict, official_head: str) -> dict:
    head = require_sha(official_head, "official_head")
    if manifest.get("source_count") != 31 or not manifest.get("enabled"):
        raise ValueError("canonical companion must be enabled with 31 sources")
    if manifest.get("canonical_branch") != "rc/p0d-s1-kids-rc01":
        raise ValueError("wrong canonical branch")
    profile = active.get("source_profiles", {}).get("eggrumble_v3_31", {})
    if profile.get("source_count") != 31 or profile.get("source_manifest") != "rc_fastlane/EGGRUMBLE_V3_ACTIVE.json":
        raise ValueError("ACTIVE companion profile and manifest disagree")
    sources = manifest.get("source_heads", {})
    if not isinstance(sources, dict):
        raise ValueError("missing source_heads")
    for lane, owners in LANES.items():
        for owner in owners:
            require_sha(sources.get(owner), f"{lane}.{owner}")
    flags = manifest.get("feature_flags", {})
    if not isinstance(flags, dict) or any(flags.get(key) is not True for key in FLAGS):
        raise ValueError("mandatory integrated feature flag missing/disabled")
    if manifest.get("publication_authorized") is not False:
        raise ValueError("this audit assumes publication is not authorized")
    rows = catalog.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("catalogue has no feature rows")
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or len(set(ids)) != len(ids):
        raise ValueError("catalogue has invalid/duplicate feature IDs")
    if any(not isinstance(i, str) or not re.fullmatch(r"P0D-[0-9]{3}", i) for i in ids):
        raise ValueError("catalogue contains malformed feature ID")
    stages = Counter(row.get("stage") for row in rows)
    if any(stage not in {"IDEA", "SOURCE", "RC", "STUDIO", "FUN"} for stage in stages):
        raise ValueError("catalogue contains unknown stage")
    stored_v3 = require_sha(manifest.get("last_verified_rc_run", {}).get("rc_head_sha"), "V3.last_verified_rc_run")
    stored_active = require_sha(profile.get("last_verified_rc_run", {}).get("rc_head_sha"), "ACTIVE.last_verified_rc_run")
    run = manifest["last_verified_rc_run"]
    recorded_run_id = run.get("run_id")
    if not isinstance(recorded_run_id, int) or recorded_run_id <= 0:
        raise ValueError("invalid stored verification run ID")
    freshness = stored_v3 == head and stored_active == head
    return {
        "schema": "P0D_GQ_RC31_LIVE_RECEIPT_AUDIT_V1",
        "official_branch_head": head,
        "source_count": 31,
        "eight_lane_author_pins_present": {key: list(vals) for key, vals in LANES.items()},
        "recorded_v3_receipt_head": stored_v3,
        "recorded_active_receipt_head": stored_active,
        "recorded_v3_run_id": recorded_run_id,
        "recorded_receipts_match_live_head": freshness,
        "receipt_status": "CURRENT_RECORDED_HEAD_ONLY" if freshness else "HISTORICAL_RECEIPT_ONLY",
        "same_head_actual_ci": "NOT_VERIFIED_BY_THIS_AUDIT",
        "zip_bytes": None,
        "place_bytes": None,
        "source_primary_profile": active.get("active_profile"),
        "v3_is_primary": active.get("active_profile") == "eggrumble_v3_31",
        "catalog_count": len(rows),
        "catalog_stage_counts": dict(sorted(stages.items())),
        "catalog_snapshot_head": catalog.get("verified_rc_head"),
        "studio": manifest.get("studio_2client", "UNKNOWN"),
        "android": manifest.get("android_15min", "UNKNOWN"),
        "owner_fun": manifest.get("art_fun_owner", "UNKNOWN"),
        "release_accepted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--official-head", required=True, help="Live HEAD SHA from independent official branch read")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-current-recorded-receipt", action="store_true")
    args = parser.parse_args()
    root = args.repo_root
    try:
        manifest = json.loads((root / "rc_fastlane/EGGRUMBLE_V3_ACTIVE.json").read_text(encoding="utf-8"))
        active = json.loads((root / "rc_fastlane/ACTIVE.json").read_text(encoding="utf-8"))
        catalog = json.loads((root / "rc_fastlane/FEATURE_CATALOG.json").read_text(encoding="utf-8"))
        report = audit(manifest, active, catalog, args.official_head)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"audit_error": str(exc)}, ensure_ascii=False))
        return 1
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    return 2 if args.require_current_recorded_receipt and not report["recorded_receipts_match_live_head"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
