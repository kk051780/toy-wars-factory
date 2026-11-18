#!/usr/bin/env python3
"""Independent GQ8 gate: distinguish V3 source CI from a playable default experience.

This tool is read-only. GREEN means its *classification* is correct, not that
Roblox Studio, Android, multiplayer or the owner accepted gameplay.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

DOMAINS = {
    "character": "GQ8_ROLE_SELECTION_ACK_20261117",
    "field": "TEAM_FIELD_ITEM_RIDGE_FOREST_CLEARANCE_520",
    "battle": "GQ81_CONFIRMED_HIT_042_V3_PORT_20261117",
    "castle": "GQ500_ORIGINAL_LIVE_CASTLE_DEFENSE_INLINE_20261117",
    "neutral": "NEUTRAL_MELEE_533",
    "item": "ORIGINAL_ITEM_AUTHOR_489",
    "lobby": "LOBBY_NEARBY_BOARDS_539",
    "balance": "MATCH_DEADLINE_DRAW_499",
}
STUDIO_GUARD = re.compile(
    r"(?m)^\s*if\s+not\s+RunService:IsStudio\(\)\s+then\s+return\s+end\b"
)
ENGINE_KEYS = ("studio_2client", "android_15min", "art_fun_owner")
EXPECTED_PROFILE = "eggrumble_v3_31"
EXPECTED_SOURCE_COUNT = 31


def assess(active: dict, companion: dict, original_host: str) -> dict:
    """Source and metadata checks do not simulate Roblox Engine."""
    errors = []
    profiles = active.get("source_profiles") or {}
    listed = profiles.get(EXPECTED_PROFILE) or {}
    flags = companion.get("feature_flags") or {}
    source_count = companion.get("source_count")

    if companion.get("profile") != EXPECTED_PROFILE or companion.get("enabled") is not True:
        errors.append("V3 companion manifest profile missing/disabled")
    if source_count != EXPECTED_SOURCE_COUNT or listed.get("source_count") != EXPECTED_SOURCE_COUNT:
        errors.append("V3 expected 31-source contract drift")
    if companion.get("canonical_game_host_count") != 1:
        errors.append("duplicate/missing game Host")
    if companion.get("canonical_combat_count") != 1:
        errors.append("duplicate/missing Combat owner")
    if companion.get("canonical_bot_actor_count") != 1:
        errors.append("duplicate/missing AI owner")
    if companion.get("canonical_neutral_swarm_count") != 1:
        errors.append("duplicate/missing Swarm owner")
    if not original_host.strip() or "RunService" not in original_host:
        errors.append("original pinned Host not loaded")
    missing = [name for name, flag in DOMAINS.items() if flags.get(flag) is not True]
    if missing:
        errors.append("source domain flag missing: " + ",".join(missing))

    default_profile = active.get("active_profile")
    preview_only = bool(STUDIO_GUARD.search(original_host))
    engine = {key: companion.get(key, "UNKNOWN") for key in ENGINE_KEYS}

    # These are metadata labels, NEVER proof of a real Studio/Android session.
    if errors:
        verdict = "RED_SOURCE_CONTRACT"
    elif default_profile != EXPECTED_PROFILE:
        verdict = "NO_GO_NOT_PRIMARY_EXPERIENCE"
    elif preview_only:
        verdict = "NO_GO_STUDIO_ONLY_ORIGINAL_HOST"
    elif any(value != "PASS" for value in engine.values()):
        verdict = "NO_GO_ENGINE_AND_FUN_UNVERIFIED"
    else:
        verdict = "RECEIPTS_REQUIRE_INDEPENDENT_REVIEW"

    return {
        "gate": "GQ8_FIRSTPLAY_REALITY_20261118",
        "verdict": verdict,
        "source_contract_errors": errors,
        "default_profile": default_profile,
        "v3_companion_enabled": companion.get("enabled") is True,
        "v3_scripts_reported": source_count,
        "original_host_studio_only_guard": preview_only,
        "eight_domains_source_flags": {
            domain: bool(flags.get(flag)) for domain, flag in DOMAINS.items()
        },
        "engine_evidence_declared": engine,
        "roblox_engine_executed_by_this_gate": False,
        "formal_rc_mutated": False,
        "release_go_claim": False,
        "note": (
            "A green CI here only validates the source/profile classification. "
            "It cannot establish live gameplay, FPS, visual quality, or OWNER acceptance."
        ),
    }


def self_test(active: dict, companion: dict, original_host: str) -> int:
    checks = 0

    def expect(a: dict, c: dict, host: str, target: str) -> None:
        nonlocal checks
        got = assess(a, c, host)["verdict"]
        assert got == target, (target, got)
        checks += 1

    # The real pinned source/manifest is the primary positive contract.
    baseline = assess(active, companion, original_host)
    assert baseline["verdict"] == "NO_GO_NOT_PRIMARY_EXPERIENCE", baseline
    checks += 1

    changed_active = copy.deepcopy(active)
    changed_active["active_profile"] = EXPECTED_PROFILE
    expect(changed_active, companion, original_host, "NO_GO_STUDIO_ONLY_ORIGINAL_HOST")

    no_guard_host = STUDIO_GUARD.sub("-- removed preview-only guard", original_host)
    assert no_guard_host != original_host, "pinned original Host guard vanished"
    expect(changed_active, companion, no_guard_host, "NO_GO_ENGINE_AND_FUN_UNVERIFIED")

    evidence_claim = copy.deepcopy(companion)
    for key in ENGINE_KEYS:
        evidence_claim[key] = "PASS"
    expect(
        changed_active, evidence_claim, no_guard_host,
        "RECEIPTS_REQUIRE_INDEPENDENT_REVIEW"
    )
    # Even spoofed PASS labels may not defeat the primary/default or Studio guards.
    expect(active, evidence_claim, no_guard_host, "NO_GO_NOT_PRIMARY_EXPERIENCE")
    expect(changed_active, evidence_claim, original_host, "NO_GO_STUDIO_ONLY_ORIGINAL_HOST")

    bad = copy.deepcopy(companion)
    bad["source_count"] = 32
    expect(active, bad, original_host, "RED_SOURCE_CONTRACT")
    bad = copy.deepcopy(companion)
    bad["feature_flags"]["NEUTRAL_MELEE_533"] = False
    expect(active, bad, original_host, "RED_SOURCE_CONTRACT")
    bad = copy.deepcopy(companion)
    bad["canonical_game_host_count"] = 2
    expect(active, bad, original_host, "RED_SOURCE_CONTRACT")
    # A commented-out guard is not executable: no false positive.
    comment_only = STUDIO_GUARD.sub(
        "-- if not RunService:IsStudio() then return end", original_host
    )
    expect(changed_active, companion, comment_only, "NO_GO_ENGINE_AND_FUN_UNVERIFIED")
    print(f"GQ8_FIRSTPLAY_CLASSIFICATION_{checks}_CASES_PASS")
    return checks


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--active", required=True, type=Path)
    p.add_argument("--companion", required=True, type=Path)
    p.add_argument("--pinned-host", required=True, type=Path)
    p.add_argument("--report", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    active = json.loads(args.active.read_text(encoding="utf-8"))
    companion = json.loads(args.companion.read_text(encoding="utf-8"))
    original_host = args.pinned_host.read_text(encoding="utf-8")
    result = assess(active, companion, original_host)
    if args.self_test:
        self_test(active, companion, original_host)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(payload)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(payload, encoding="utf-8")
    # NO_GO is expected for a private RC preview and MUST NOT block source-only prep.
    return 1 if result["verdict"] == "RED_SOURCE_CONTRACT" else 0


if __name__ == "__main__":
    raise SystemExit(main())
