#!/usr/bin/env python3
"""P0D V6 nonblocking issue triage. Read-only; never authorizes a merge/ref update.

Candidate assertions are advisory; GitHub actor, grant, CI and source proofs must
be verified independently by #220 before any official RC write.
"""
from __future__ import annotations
import argparse
import json
import re

RED_DOMAINS = frozenset({
    "syntax", "native_luau", "rojo", "source_lock", "same_head_ci",
    "security", "permissions", "remote_authority", "save_data", "data_corruption",
    "double_rewards", "server_authority", "game_crash", "core_round", "egg_score",
    "rollback", "writer_grant", "cas", "source_conflict", "unverified_severity"
})
VALID_LEVELS = {"RED", "YELLOW", "GREEN"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
FEATURE = re.compile(r"^P0D-[0-9]{3}$")
ISSUE = re.compile(r"^FB-[0-9]{3}$")


def evaluate(packet: dict) -> dict:
    """Return advisory lane; unknown/malformed/safety defects fail closed."""
    out = {"schema": "P0D_V6_TRIAGE_V1", "lane": "HOLD_RED",
           "official_rc_write_allowed": False, "product_pass": False,
           "reason": "MALFORMED_PACKET", "debt": []}
    if not isinstance(packet, dict) or packet.get("schema") != "P0D_V6_TRIAGE_V1":
        return out
    if not HEX40.fullmatch(str(packet.get("base_rc_sha", ""))):
        out["reason"] = "BASE_RC_UNVERIFIED"
        return out
    if not FEATURE.fullmatch(str(packet.get("feature_id", ""))):
        out["reason"] = "INVALID_FEATURE_ID"
        return out
    checks = packet.get("mandatory_checks")
    required = ("source_exact", "native_luau", "rojo", "same_head_ci",
                "no_authority_duplication", "rollback_verified", "original_claim_verified")
    if not isinstance(checks, dict) or not all(checks.get(k) is True for k in required):
        out["reason"] = "HARD_GATE_MISSING"
        return out
    findings = packet.get("findings")
    if not isinstance(findings, list) or len(findings) > 100:
        out["reason"] = "INVALID_FINDINGS"
        return out
    seen = set()
    for f in findings:
        if not isinstance(f, dict):
            out["reason"] = "INVALID_FINDING"
            return out
        key = f.get("id")
        level, domain = f.get("severity"), f.get("domain")
        if not isinstance(key, str) or not key or key in seen:
            out["reason"] = "INVALID_OR_DUPLICATE_FINDING_ID"
            return out
        seen.add(key)
        if level not in VALID_LEVELS or not isinstance(domain, str) or not domain:
            out["reason"] = "UNKNOWN_SEVERITY_OR_DOMAIN"
            return out
        if level == "RED" or domain in RED_DOMAINS:
            out["reason"] = "BLOCKING_FINDING_" + key
            return out
        if level == "YELLOW":
            if not ISSUE.fullmatch(str(f.get("fb_id", ""))):
                out["reason"] = "YELLOW_REQUIRES_FB_ID_" + key
                return out
            fields = ("owner", "reproduction", "impact", "fix_trigger", "rollback")
            if not all(isinstance(f.get(k), str) and len(f[k].strip()) >= 8 for k in fields):
                out["reason"] = "YELLOW_DEBT_INCOMPLETE_" + key
                return out
            if not isinstance(f.get("feature_flag_off"), bool):
                out["reason"] = "YELLOW_FLAG_STATE_UNKNOWN_" + key
                return out
            if f["feature_flag_off"] is False and f.get("affects_core_gameplay") is not False:
                out["reason"] = "YELLOW_CORE_IMPACT_NOT_ISOLATED_" + key
                return out
            out["debt"].append({"id": key, "fb_id": f["fb_id"], "owner": f["owner"],
                                "fix_trigger": f["fix_trigger"]})
    if out["debt"]:
        out["lane"] = "YELLOW_TRACK_AND_REVIEW"
        out["reason"] = "KNOWN_DEBT_NONBLOCKING_FOR_PRIVATE_SOURCE_REVIEW"
    else:
        out["lane"] = "GREEN_REVIEW"
        out["reason"] = "NO_DECLARED_FINDINGS"
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("packet")
    args = p.parse_args()
    try:
        with open(args.packet, encoding="utf-8") as f:
            result = evaluate(json.load(f))
    except (OSError, ValueError):
        result = {"schema": "P0D_V6_TRIAGE_V1", "lane": "HOLD_RED",
                  "official_rc_write_allowed": False, "product_pass": False,
                  "reason": "UNREADABLE_PACKET", "debt": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["lane"] in ("YELLOW_TRACK_AND_REVIEW", "GREEN_REVIEW") else 2


if __name__ == "__main__":
    raise SystemExit(main())
