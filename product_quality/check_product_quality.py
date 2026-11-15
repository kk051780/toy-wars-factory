#!/usr/bin/env python3
"""Evidence coverage gate for P0D product quality. Does NOT judge subjective gameplay."""
import argparse
import json
import re
from datetime import date
from pathlib import Path

WEIGHTS = {"field_freedom":20,"combat_impact":20,"first_time_clarity":15,"roles_collectibles":15,"replay_growth":15,"ethical_monetization":10,"art_coherence":5}
REQUIRED_CORE = {"field_freedom", "combat_impact", "first_time_clarity"}
ALLOWED_SCHEMA = "P0D_PRODUCT_QUALITY_CANDIDATE_V1"

# Source compilation alone does not prove the actual owner-required gameplay loop.
REQUIRED_SCENARIOS = (
    "seven_jobs_select_and_dismiss", "warrior_multi_enemy_attack",
    "mage_heal_and_revive", "assassin_stealth_and_ambush",
    "trapper_trap_and_warp", "builder_wall_and_bridge",
    "beast_tamer_follow_and_mount", "necromancer_real_squad",
    "egg_steal_return_and_score", "neutral_mob_multikill",
    "solo_ally_and_enemy_objective_ai", "three_traversable_field_routes",
    "personal_egg_and_ko_results", "mobile_unobstructed_hud",
    "manual_ready_after_replay",
)

def valid_sha(v, n=40):
    return isinstance(v, str) and bool(re.fullmatch("[0-9a-f]{" + str(n) + "}", v.lower()))

def valid_url(v):
    return isinstance(v, str) and bool(re.fullmatch(r"https://[^\s/]+/[^\s]+", v))

def valid_date(v):
    try:
        if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return False
        date.fromisoformat(v)
        return True
    except ValueError:
        return False

def evaluate(doc):
    if not isinstance(doc, dict):
        doc = {}

    problems = []
    if doc.get("schema") != ALLOWED_SCHEMA:
        problems.append("WRONG_SCHEMA")
    dimensions = doc.get("measurements")
    if not isinstance(dimensions, dict):
        dimensions = {}
        problems.append("MISSING_MEASUREMENTS")
    scores = {}
    for key, weight in WEIGHTS.items():
        entry = dimensions.get(key)
        if not isinstance(entry, dict):
            problems.append(f"MISSING_DIMENSION:{key}")
            continue
        if entry.get("max_score") != weight:
            problems.append(f"WEIGHT_MISMATCH:{key}")
        s = entry.get("score")
        if isinstance(s, bool) or not isinstance(s, (int, float)) or not (0 <= s <= weight):
            problems.append(f"UNSCORED:{key}")
            continue
        if not isinstance(entry.get("reviewer"), str) or not entry["reviewer"].strip() or entry.get("benchmark_compared") is not True or not valid_date(entry.get("measured_on")):
            problems.append(f"NO_VERIFIABLE_REVIEW:{key}")
            continue
        if not isinstance(entry.get("evidence_urls"), list) or not entry["evidence_urls"] or any(not valid_url(u) for u in entry["evidence_urls"]):
            problems.append(f"BAD_EVIDENCE_URLS:{key}")
            continue
        scores[key] = s
    total = round(sum(scores.values()), 2) if len(scores) == len(WEIGHTS) else None
    if total is None:
        problems.append("PRODUCT_SCORE_UNKNOWN")
    elif total < 80:
        problems.append("SCORE_BELOW_80")
    for key in REQUIRED_CORE:
        if key in scores and scores[key] < WEIGHTS[key] * 0.7:
            problems.append(f"CORE_BELOW_70_PERCENT:{key}")
    if not isinstance(doc.get("major_blockers"), list) or doc["major_blockers"]:
        problems.append("P0_BLOCKERS_PRESENT")
    ops = doc.get("operational_gates")
    if not isinstance(ops, dict):
        ops = {}
    for key in ("studio_validated", "art_420_go", "android_420_go", "owner_accepted"):
        if ops.get(key) is not True:
            problems.append(f"MANDATORY_GATE_MISSING:{key}")
    readiness = doc.get("readiness")
    if not isinstance(readiness, dict):
        readiness = {}
    for key in ("research_reviewed", "product_comparison_reviewed", "implementation_ready", "sole_writer_ack"):
        if readiness.get(key) is not True:
            problems.append(f"READINESS_MISSING:{key}")
    candidate = doc.get("candidate")
    if not isinstance(candidate, dict):
        candidate = {}
    for key in ("official_rc_head", "source_head"):
        val = candidate.get(key)
        if not valid_sha(val):
            problems.append(f"UNPINNED_SHA:{key}")
    # Evidence MUST correspond to the exact official RC under review.
    ev = doc.get("source_evidence")
    if not isinstance(ev, dict):
        ev = {}
    if not valid_sha(ev.get("source_lock"), 64):
        problems.append("UNPINNED_SOURCE_LOCK_SHA256")
    for key in ("device_models", "studio_recordings", "competitor_timecodes"):
        values = ev.get(key)
        if not isinstance(values, list) or not values:
            problems.append("MISSING_SOURCE_EVIDENCE:" + key)
    scenarios = ev.get("core_scenarios")
    if not isinstance(scenarios, list):
        scenarios = []
    accepted = set()
    for row in scenarios:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            problems.append("MALFORMED_CORE_SCENARIO")
            continue
        name = row["id"]
        if name not in REQUIRED_SCENARIOS or name in accepted:
            problems.append("UNKNOWN_OR_DUPLICATE_CORE_SCENARIO:" + name)
            continue
        good = (
            row.get("result") == "PASS"
            and row.get("official_rc_head") == candidate.get("official_rc_head")
            and valid_sha(row.get("official_rc_head"))
            and valid_url(row.get("recording_url"))
            and isinstance(row.get("device"), str) and bool(row["device"].strip())
            and isinstance(row.get("reviewer"), str) and bool(row["reviewer"].strip())
            and valid_date(row.get("measured_on"))
            and isinstance(row.get("observed_effect"), str) and bool(row["observed_effect"].strip())
        )
        if name == "assassin_stealth_and_ambush":
            good = good and row.get("display_name") == "暗殺者" and row.get("internal_role") == "NINJA"
        if good:
            accepted.add(name)
        else:
            problems.append("INVALID_ENGINE_PROOF:" + name)
    for name in REQUIRED_SCENARIOS:
        if name not in accepted:
            problems.append("MISSING_ENGINE_PROOF:" + name)
    # Publication is independently prohibited; even an accepted review does not authorize publishing.
    if doc.get("publication_authorized") is True:
        problems.append("PUBLICATION_SCOPE_NOT_ALLOWED_BY_THIS_GATE")
    return {"schema": "P0D_PRODUCT_QUALITY_REPORT_V1",
            "issue": "https://github.com/kk051780/toy-wars-factory/issues/470",
            "total_score": total,
            "maximum_score": 100,
            "scored_dimensions": len(scores),
            "total_dimensions": len(WEIGHTS),
            "dimensions": scores,
            "core_scenarios_declared": len(accepted),
            "core_scenarios_required": len(REQUIRED_SCENARIOS),
            "problems": sorted(set(problems)),
            "decision": "PRODUCT_GO_REVIEWABLE" if not problems else "PRODUCT_NO_GO",
            "disclaimer": "This is evidence coverage and score arithmetic, not an AI evaluation of gameplay or media authenticity."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    doc = json.loads(Path(a.candidate).read_text(encoding="utf-8"))
    result = evaluate(doc)
    Path(a.report).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result["decision"], result["total_score"], len(result["problems"]), "problems")
    return 0 if result["decision"] == "PRODUCT_GO_REVIEWABLE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
