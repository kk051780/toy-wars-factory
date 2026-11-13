#!/usr/bin/env python3
"""Fail-closed human trial report completeness check. Not Roblox Studio verification."""
import argparse
import json
import re
from pathlib import Path

EXPECTED = {
    "B42_FIRST90": "837853e66278e38bb79f6399c3e8bfc9a2403be6",
    "A40_V6": "4b09de3eb70abb2e79268ce41bdecc4b614d39df",
}
GATES = (
    "server_2clients", "egg_and_score_consistency",
    "server_security_and_duplicates", "terrain_traversal",
    "android_actual", "no_severe_defects",
)
SCORES = (
    "clarity_first15", "action_first35", "distinctive_play_60",
    "egg_payoff_90", "fairness_readability", "rematch_desire",
)
SHA256 = re.compile(r"^[a-f0-9]{64}$")


def evaluate(report):
    """Return a conservative decision about the *completeness* of supplied evidence."""
    errors = []
    missing = []
    failed = []
    if not isinstance(report, dict):
        return {"status": "INVALID_INPUT", "errors": ["report_not_object"]}
    candidate = report.get("candidate") or {}
    if not isinstance(candidate, dict):
        return {"status": "INVALID_INPUT", "errors": ["candidate_not_object"]}
    name = candidate.get("id")
    if name not in EXPECTED:
        errors.append("candidate_not_whitelisted")
    elif candidate.get("source_sha") != EXPECTED[name]:
        errors.append("candidate_source_sha_mismatch")
    expected_selection = {"B42_FIRST90": "PRIVATE_TRIAL_SELECTED",
                          "A40_V6": "COMPARISON_ONLY"}
    if name in expected_selection and candidate.get("selection") != expected_selection[name]:
        errors.append("candidate_selection_changed")
    if report.get("official_rc_integrated") is not False:
        errors.append("unexpected_official_rc_integrated_claim")
    if report.get("official_rc_adoption") != "NO":
        errors.append("unexpected_official_rc_adoption_claim")
    digest = candidate.get("place_sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        missing.append("valid_real_place_sha256")
    obs = report.get("observed") or {}
    gates = report.get("hard_gates") or {}
    scores = report.get("scores_out_of_5") or {}
    if not isinstance(obs, dict) or not isinstance(gates, dict) or not isinstance(scores, dict):
        errors.append("report_sections_not_objects")
    if errors:
        return {"status": "INVALID_INPUT", "errors": errors, "missing": missing}
    for g in GATES:
        v = gates.get(g)
        if v == "FAIL":
            failed.append(g)
        elif v != "PASS":
            missing.append("gate_" + g)
    for s in SCORES:
        v = scores.get(s)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 5:
            missing.append("human_score_" + s)
    if obs.get("owner_tested") != "PASS":
        missing.append("owner_real_studio_session")
    if not obs.get("tested_at_jst"):
        missing.append("test_timestamp")
    if not isinstance(obs.get("actual_clients"), int) or obs.get("actual_clients") < 2:
        missing.append("observed_two_clients")
    if not obs.get("logs_or_screenshots"):
        missing.append("actual_engine_log_or_capture")
    for step in ("first15", "first35", "first60", "first90"):
        if obs.get(step) not in ("PASS", "OBSERVED"):
            missing.append("observed_" + step)
    if report.get("owner_fun_decision") != "FUN_GO":
        missing.append("explicit_human_fun_go")
    if failed:
        return {"status": "REVISE_BLOCKED", "failed_gates": failed,
                "missing": sorted(set(missing)), "errors": [],
                "official_rc_adopted": False, "studio_verified_by_tool": False}
    if missing:
        return {"status": "WAITING_EVIDENCE", "missing": sorted(set(missing)),
                "failed_gates": [], "errors": [],
                "official_rc_adopted": False, "studio_verified_by_tool": False}
    average = sum(scores[k] for k in SCORES) / len(SCORES)
    if average < 4 or scores["rematch_desire"] < 4:
        return {"status": "REVISE_FUN", "average_fun": round(average, 2),
                "failed_gates": [], "missing": [], "errors": [],
                "official_rc_adopted": False, "studio_verified_by_tool": False}
    return {"status": "PRODUCT_DRI_REVIEW_CANDIDATE",
            "average_fun": round(average, 2), "failed_gates": [],
            "missing": [], "errors": [], "official_rc_adopted": False,
            "studio_verified_by_tool": False,
            "warning": "Self-reported evidence only. #250 selection, #220 independent RC review, and real Studio evidence authenticity remain required."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", type=Path, nargs="+", help="copied and filled trial-result JSON files")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = {}
    for path in args.reports:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            results[str(path)] = evaluate(report)
        except (OSError, ValueError) as exc:
            results[str(path)] = {"status": "INVALID_INPUT", "errors": [type(exc).__name__]}
    output = {"schema": "P0D_FIRST90_TRIAL_EVIDENCE_GATE_V2",
              "real_studio_execution_by_this_tool": False,
              "product_adoption_automatic": False,
              "official_rc_mutation": False, "results": results}
    serialized = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 0 if all(v["status"] == "PRODUCT_DRI_REVIEW_CANDIDATE"
                    for v in results.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
