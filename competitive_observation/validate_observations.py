#!/usr/bin/env python3
"""Validate real competitive observations; cannot certify gameplay or footage authenticity."""
import argparse
import json
from pathlib import Path

SCENARIOS = {
    "FIELD_ROUTE": ("base_to_base_seconds", "usable_distinct_routes", "traversal_blockers", "egg_escape_branches"),
    "MOB_CLEAR_30S": ("kills_30s", "max_valid_targets_one_attack", "input_to_first_hit_ms"),
    "ONBOARD_180S": ("seconds_to_role_select", "seconds_to_first_hit", "seconds_to_objective_understood", "persistent_hud_coverage_percent"),
    "REPLAY_3MATCH": ("eggs_scored", "neutral_kills_scored", "distinct_tactical_choices", "voluntary_next_match"),
}
GAMES = {"steal_an_egg", "blox_fruits", "strongest_battlegrounds", "bedwars", "nights_99", "p0d_official_rc"}
META = ("source_url", "video_timecode", "device", "capture_date", "observer", "game_version_or_sha")
COUNTS = {"usable_distinct_routes", "traversal_blockers", "egg_escape_branches", "kills_30s", "max_valid_targets_one_attack", "eggs_scored", "neutral_kills_scored", "distinct_tactical_choices"}

def check(doc):
    problems = []
    if doc.get("schema") != "P0D_PQ470_OBSERVATION_PROTOCOL_V1":
        problems.append("SCHEMA")
    observations = doc.get("observations", [])
    if not isinstance(observations, list):
        return {"decision": "NOT_MEASURED", "problems": ["OBSERVATIONS_NOT_ARRAY"], "valid_observations": 0, "coverage": {}}
    unique = set()
    coverage = {}
    for i, o in enumerate(observations):
        if not isinstance(o, dict):
            problems.append(f"{i}:NOT_OBJECT")
            continue
        g, s, trial = o.get("game_id"), o.get("scenario_id"), o.get("trial")
        if g not in GAMES or s not in SCENARIOS or type(trial) is not int or trial not in (1, 2, 3):
            problems.append(f"{i}:INVALID_GAME_SCENARIO_TRIAL")
            continue
        key = (g, s, trial)
        if key in unique:
            problems.append(f"{i}:DUPLICATE_TRIAL")
            continue
        unique.add(key)
        if any(not isinstance(o.get(k), str) or not o[k].strip() for k in META):
            problems.append(f"{i}:MISSING_PROVENANCE")
            continue
        if not o["source_url"].startswith(("https://", "http://")):
            problems.append(f"{i}:INVALID_SOURCE_URL")
            continue
        if g == "p0d_official_rc":
            sha = o.get("official_rc_sha")
            if not isinstance(sha, str) or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha.lower()):
                problems.append(f"{i}:UNPINNED_OFFICIAL_RC")
                continue
        values = o.get("metrics")
        if not isinstance(values, dict):
            problems.append(f"{i}:METRICS_NOT_OBJECT")
            continue
        invalid = False
        for m in SCENARIOS[s]:
            v = values.get(m)
            if m == "voluntary_next_match":
                ok = type(v) is bool
            else:
                ok = type(v) in (int, float) and v >= 0 and (m not in COUNTS or int(v) == v)
                if m == "persistent_hud_coverage_percent" and ok:
                    ok = v <= 100
            if not ok:
                problems.append(f"{i}:INVALID_METRIC:{m}")
                invalid = True
        if invalid:
            continue
        coverage.setdefault(g, {}).setdefault(s, []).append(trial)
    completed = [f"{g}/{s}" for g, scenarios in coverage.items() for s, trials in scenarios.items() if len(trials) == 3]
    return {"decision": "EVIDENCE_FORMAT_READY" if not problems and len(completed) == len(GAMES) * len(SCENARIOS) else "NOT_MEASURED",
            "problems": sorted(set(problems)), "valid_observations": sum(len(v) for ss in coverage.values() for v in ss.values()),
            "completed_scenarios": completed, "required_scenarios": len(GAMES) * len(SCENARIOS),
            "disclaimer": "No gameplay authenticity, art score, performance, commercial value, or owner acceptance is certified."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    result = check(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.report).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result["decision"], result["valid_observations"], "/", 72)
    return 0 if result["decision"] == "EVIDENCE_FORMAT_READY" else 1

if __name__ == "__main__":
    raise SystemExit(main())
