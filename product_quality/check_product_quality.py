#!/usr/bin/env python3
"""Evidence coverage gate for P0D product quality. Does NOT judge subjective gameplay."""
import argparse
import json
from pathlib import Path

WEIGHTS = {"field_freedom":20,"combat_impact":20,"first_time_clarity":15,"roles_collectibles":15,"replay_growth":15,"ethical_monetization":10,"art_coherence":5}
REQUIRED_CORE = {"field_freedom", "combat_impact", "first_time_clarity"}
ALLOWED_SCHEMA = "P0D_PRODUCT_QUALITY_CANDIDATE_V1"

def evaluate(doc):
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
        if not entry.get("reviewer") or not entry.get("evidence_urls") or not entry.get("benchmark_compared") or not entry.get("measured_on"):
            problems.append(f"NO_VERIFIABLE_REVIEW:{key}")
            continue
        if not isinstance(entry["evidence_urls"], list) or any(not isinstance(u, str) or not u.startswith(("https://", "http://")) for u in entry["evidence_urls"]):
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
    if doc.get("major_blockers"):
        problems.append("P0_BLOCKERS_PRESENT")
    ops = doc.get("operational_gates") or {}
    for key in ("studio_validated", "art_420_go", "android_420_go", "owner_accepted"):
        if ops.get(key) is not True:
            problems.append(f"MANDATORY_GATE_MISSING:{key}")
    readiness = doc.get("readiness") or {}
    for key in ("research_reviewed", "product_comparison_reviewed", "implementation_ready", "sole_writer_ack"):
        if readiness.get(key) is not True:
            problems.append(f"READINESS_MISSING:{key}")
    candidate = doc.get("candidate") or {}
    for key in ("official_rc_head", "source_head"):
        val = candidate.get(key)
        if not isinstance(val, str) or len(val) != 40 or any(ch not in "0123456789abcdef" for ch in val.lower()):
            problems.append(f"UNPINNED_SHA:{key}")
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
