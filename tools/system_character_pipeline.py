"""Character catalog and benefit/effort checks. No release or execution authority.

Scores are design hypotheses, not measured acquisition, revenue or retention.
The source parser checks the project's literal balance table; Lua regressions
remain responsible for executing model, selection, production and combat code.
"""
import argparse
import json
from pathlib import Path
import re

BASELINE_IDS = {"pon", "guardon", "tankuru"}
EFFORT_KEYS = {"model", "animation", "combat", "ui", "qa"}
APPEAL_KEYS = {"acquisition", "retention", "strategy"}


def registered_ids(source):
    block = re.search(r"B\.UNITS\s*=\s*\{(.*?)\n\}", source, re.S)
    if not block:
        raise ValueError("literal B.UNITS table missing")
    ids = re.findall(r"^\s{4}([a-z][a-z0-9_]*)\s*=\s*\{", block[1], re.M)
    if len(ids) != len(set(ids)) or "junk" not in ids:
        raise ValueError("duplicate unit or missing NPC boundary")
    return set(ids) - {"junk"}


def catalog_errors(catalog, balance_source, required):
    errors = []
    active = catalog.get("characters")
    planned = catalog.get("candidates", [])
    if not isinstance(active, list) or not active or not isinstance(planned, list):
        return ["invalid character lists"]
    entries = active + planned
    if any(not isinstance(c, dict) for c in entries):
        return ["invalid character record"]
    ids = [c.get("id") for c in entries]
    if any(not isinstance(i, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", i) for i in ids):
        return ["invalid character id"]
    if len(ids) != len(set(ids)) or "junk" in ids:
        errors.append("duplicate/player-NPC identity")
    active_ids = {c["id"] for c in active}
    if not BASELINE_IDS <= active_ids:
        errors.append("baseline characters removed")
    try:
        if active_ids != registered_ids(balance_source):
            errors.append("catalog and executable balance roster disagree")
    except ValueError as exc:
        errors.append(str(exc))
    for c in entries:
        if any(c.get(k) in (None, "", []) for k in required):
            errors.append("required identity/role missing: " + c["id"])
    for key in ("shape", "color"):
        values = [c.get(key) for c in entries]
        if any(not isinstance(v, str) for v in values) or len(values) != len(set(values)):
            errors.append("indistinct " + key)
    if any(c.get("status") != "prototype" for c in active):
        errors.append("active roster must report prototype status")
    if any(c.get("status") != "design_proposal_not_implemented" for c in planned):
        errors.append("planned characters presented as implemented")
    for c in entries:
        if c["id"] in BASELINE_IDS:
            continue
        business = c.get("business_case", {})
        effort = business.get("effort_points", {})
        appeal = business.get("appeal_scores", {})
        if (not business.get("acquisition_hook") or not business.get("retention_hypothesis") or
                business.get("evidence_status") != "HYPOTHESIS_NOT_MEASURED"):
            errors.append("unmeasured benefit must remain a hypothesis: " + c["id"])
        if (not isinstance(effort, dict) or set(effort) != EFFORT_KEYS or
                any(type(v) is not int or not 1 <= v <= 20 for v in effort.values())):
            errors.append("invalid effort estimate: " + c["id"])
        if (not isinstance(appeal, dict) or set(appeal) != APPEAL_KEYS or
                any(type(v) is not int or not 1 <= v <= 5 for v in appeal.values())):
            errors.append("invalid benefit estimate: " + c["id"])
        visual = c.get("visual_contract", {})
        budget = visual.get("primitive_part_budget")
        if (not visual.get("signature") or type(budget) is not int or not 1 <= budget <= 24 or
                visual.get("silhouette_pixels") != [32, 64]):
            errors.append("missing simple-shape visual budget: " + c["id"])
        if visual.get("native_render_verified") is not False:
            errors.append("native visual proof not supplied by this pipeline: " + c["id"])
        refs = c.get("source_review")
        if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x.startswith("https://") for x in refs):
            errors.append("primary reference review missing: " + c["id"])
    return errors


def assess(catalog):
    result = []
    for c in catalog.get("candidates", []):
        b = c["business_case"]
        a = b["appeal_scores"]
        effort = sum(b["effort_points"].values())
        benefit = 2*a["acquisition"] + 2*a["retention"] + a["strategy"]
        result.append({"id": c["id"], "name_ja": c["name_ja"],
                       "estimated_benefit_points": benefit, "estimated_effort_points": effort,
                       "estimated_priority": round(benefit/effort, 4),
                       "market_effect": "NOT_MEASURED", "native_visuals": "NOT_RUN"})
    return sorted(result, key=lambda c: (-c["estimated_priority"], c["id"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    catalog = json.loads((args.root/"config/characters.json").read_text())
    policy = json.loads((args.root/"config/quality_policy.json").read_text())
    errors = catalog_errors(catalog, (args.root/"src/ToyWarsBalance.lua").read_text(), policy["character_required"])
    report = {"status": "FAIL" if errors else "PASS_CATALOG_ONLY", "errors": errors,
              "runtime_characters": len(catalog["characters"]), "planned_characters": len(catalog.get("candidates", [])),
              "candidate_priority_hypotheses": [] if errors else assess(catalog),
              "scope": "No acquisition, retention, Roblox rendering or release certification"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
