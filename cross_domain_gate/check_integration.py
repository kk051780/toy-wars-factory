#!/usr/bin/env python3
"""P0D independent cross-domain *evidence* gate; never claims engine verification.

All PASS data comes from externally recorded Studio/Android observations. No game
source writes, scoring implementation, visual implementation or official RC writes.
"""
import argparse
import datetime as dt
import json
import re
from pathlib import Path
from urllib.parse import urlparse

DOMAINS = frozenset({"character", "field", "battle", "castle", "neutral", "item", "lobby"})
CONTRACTS = {
    "GQ01": {"domains": {"character", "field", "castle", "item"}, "checks": ("assassin_castle_entry", "egg_pickup_authorized", "egg_deposit_server_scored", "wall_pickup_blocked")},
    "GQ02": {"domains": {"character", "battle", "neutral"}, "checks": ("role_weapon_equipped", "multi_target_real_damage", "neutral_ko_server_counted")},
    "GQ03": {"domains": {"character", "castle", "item"}, "checks": ("siege_item_consumed", "castle_hp_server_changed", "defender_response_possible")},
    "GQ04": {"domains": {"character", "field", "battle", "neutral"}, "checks": ("beast_summoned", "beast_follows_across_field", "beast_attacks_real_neutral")},
    "GQ05": {"domains": {"character", "battle", "lobby"}, "checks": ("seven_roles_selectable", "server_role_ack", "role_specific_weapon_works", "selection_overlay_clears")},
    "GQ06": {"domains": set(DOMAINS), "checks": ("android_touch_role_selection", "android_touch_combat", "android_egg_and_castle_loop", "neutral_and_items_visible", "hud_not_obstructive")},
}
REQUIRED = ("rc_sha", "studio_place_sha256", "device", "observed_at", "evidence_url")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")

def _valid_time(value):
    if not isinstance(value, str):
        return False
    try:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.tzinfo is not None and t.utcoffset() is not None
    except ValueError:
        return False

def _valid_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname)

def check(report, expected_rc_sha=None):
    issues = []
    if not isinstance(report, dict):
        return ["report must be object"]
    cases = report.get("cases")
    if not isinstance(cases, dict):
        return ["cases must be object"]
    if expected_rc_sha is not None and not SHA40.fullmatch(expected_rc_sha):
        return ["invalid expected RC SHA"]

    rc_shas, place_shas = set(), set()
    for case_id, contract in CONTRACTS.items():
        row = cases.get(case_id)
        if not isinstance(row, dict):
            issues.append(f"{case_id}: missing case")
            continue
        domains = row.get("domains")
        if not isinstance(domains, list) or not all(isinstance(x, str) for x in domains) or len(domains) != len(set(domains)) or set(domains) != contract["domains"]:
            issues.append(f"{case_id}: domain contract mismatch")
        status = row.get("status")
        if status not in ("PASS", "FAIL", "NOT_RUN"):
            issues.append(f"{case_id}: invalid status")
        if status != "PASS":
            continue

        for field in REQUIRED:
            if not isinstance(row.get(field), str) or not row[field].strip():
                issues.append(f"{case_id}: PASS without {field}")
        rc = row.get("rc_sha")
        place = row.get("studio_place_sha256")
        if not isinstance(rc, str) or not SHA40.fullmatch(rc):
            issues.append(f"{case_id}: invalid rc_sha")
        else:
            rc_shas.add(rc)
            if expected_rc_sha is not None and rc != expected_rc_sha:
                issues.append(f"{case_id}: RC HEAD differs from expected")
        if not isinstance(place, str) or not SHA64.fullmatch(place):
            issues.append(f"{case_id}: invalid studio_place_sha256")
        else:
            place_shas.add(place)
        if row.get("device") not in ("Studio", "Android"):
            issues.append(f"{case_id}: invalid device")
        if not _valid_time(row.get("observed_at")):
            issues.append(f"{case_id}: observed_at needs timezone ISO8601")
        if not _valid_url(row.get("evidence_url")):
            issues.append(f"{case_id}: evidence_url must be https")
        assertions = row.get("assertions")
        if not isinstance(assertions, dict) or set(assertions) != set(contract["checks"]):
            issues.append(f"{case_id}: missing or extra behavior assertions")
        elif any(assertions[name] is not True for name in contract["checks"]):
            issues.append(f"{case_id}: behavior not verified")
        if case_id == "GQ06" and row.get("device") != "Android":
            issues.append("GQ06: Android evidence required")

    if len(rc_shas) > 1:
        issues.append("cross-case RC SHA mismatch")
    if len(place_shas) > 1:
        issues.append("cross-case Place SHA mismatch")
    if any(cases.get(k, {}).get("status") != "PASS" for k in CONTRACTS if isinstance(cases.get(k), dict)) or any(not isinstance(cases.get(k), dict) for k in CONTRACTS):
        issues.append("PRODUCT_NO_GO: incomplete or failing cross-domain evidence")
    return issues

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Externally observed Studio/Android evidence JSON")
    parser.add_argument("--expected-rc-sha", help="Official writer #220's pinned 40-char RC HEAD")
    args = parser.parse_args()
    issues = check(json.loads(args.report.read_text(encoding="utf-8")), args.expected_rc_sha)
    print(json.dumps({
        "decision": "EVIDENCE_READY_FOR_HUMAN_REVIEW" if not issues else "PRODUCT_NO_GO",
        "note": "Schema PASS is not engine verification, ART/FUN approval, RC integration or OWNER acceptance.",
        "issues": issues,
    }, ensure_ascii=False, indent=2))
    raise SystemExit(bool(issues))

if __name__ == "__main__":
    main()
