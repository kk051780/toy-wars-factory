#!/usr/bin/env python3
"""Read-only P0D 67-feature catalog audit; metadata is NOT actual engine proof."""
import argparse
import json
from collections import Counter
from pathlib import Path

REQUIRED_ROLES = {f"P0D-{n:03d}" for n in range(8, 16)}
ACCEPTED_STAGES = {"IDEA", "SOURCE", "RC", "STUDIO", "FUN"}

def audit(catalog):
    issues = []
    rows = catalog.get("rows") if isinstance(catalog, dict) else None
    if not isinstance(rows, list):
        rows = []
        issues.append("NO_CATALOG_ROWS")
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    counts = Counter(r.get("stage") for r in rows if isinstance(r, dict))
    if len(rows) != 67:
        issues.append("CATALOG_COUNT_CHANGED_REVIEW_REQUIRED")
    if len(ids) != len(rows) or len(set(ids)) != len(ids):
        issues.append("INVALID_OR_DUPLICATE_FEATURE_ID")
    if any(x not in ACCEPTED_STAGES for x in counts):
        issues.append("UNRECOGNIZED_FEATURE_STAGE")
    by_id = {r["id"]: r for r in rows if isinstance(r, dict) and isinstance(r.get("id"), str)}
    missing = sorted(REQUIRED_ROLES - set(by_id))
    if missing:
        issues.append("MISSING_ROLE_FEATURES:" + ",".join(missing))
    assassin = by_id.get("P0D-011", {})
    if "暗殺者" not in str(assassin.get("name", "")) or "忍者" in str(assassin.get("name", "")):
        issues.append("STALE_ASSASSIN_DISPLAY_NAME:P0D-011")
    # 'RC' is source adoption ONLY. Never silently promote source to playtested.
    runtime_proof_count = counts.get("STUDIO", 0) + counts.get("FUN", 0)
    if runtime_proof_count < len(rows):
        issues.append("CATALOG_RUNTIME_BEHAVIOR_NOT_FULLY_VERIFIED")
    return {
        "schema": "P0D_FEATURE_CATALOG_READ_ONLY_AUDIT_V1",
        "row_count": len(rows),
        "ids_examined": len(ids),
        "stage_counts": dict(sorted(counts.items())),
        "required_seven_job_ids_present": len(REQUIRED_ROLES) - len(missing),
        "required_seven_job_ids": len(REQUIRED_ROLES),
        "studio_or_fun_metadata_count": runtime_proof_count,
        "gameplay_engine_pass_count": None,
        "issues": sorted(issues),
        "decision": "CATALOG_REVIEW_REQUIRED" if issues else "CATALOG_METADATA_CONSISTENT_ONLY",
        "note": "67/67 metadata inspection does NOT mean 67/67 gameplay tested. Cross-check same-HEAD Studio/Android/OWNER separately.",
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()
    try:
        result = audit(json.loads(Path(args.catalog).read_text(encoding="utf-8")))
    except (ValueError, OSError, TypeError) as exc:
        result = audit({})
        result["issues"].append("CATALOG_UNREADABLE:" + type(exc).__name__)
        result["decision"] = "CATALOG_REVIEW_REQUIRED"
    Path(args.report).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(result["decision"], result["row_count"], result["stage_counts"], result["issues"])
    # Evidence audit is advisory until the official B writer wires it as a gate.
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
