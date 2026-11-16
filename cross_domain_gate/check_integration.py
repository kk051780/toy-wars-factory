#!/usr/bin/env python3
"""Independent 7-domain integration contract gate. No game-source mutation."""
import argparse
import json
from pathlib import Path

DOMAINS = {"character", "field", "battle", "castle", "neutral", "item", "lobby"}
CONTRACTS = {
    "GQ01": {"character", "field", "castle", "item"},
    "GQ02": {"character", "battle", "neutral"},
    "GQ03": {"character", "castle", "item"},
    "GQ04": {"character", "field", "battle", "neutral"},
    "GQ05": {"character", "battle", "lobby"},
    "GQ06": DOMAINS,
}
REQUIRED = {"rc_sha", "studio_place_sha256", "device", "observed_at", "evidence_url"}

def check(report):
    errors = []
    if not isinstance(report, dict):
        return ["report must be object"]
    for test_id, domains in CONTRACTS.items():
        row = report.get("cases", {}).get(test_id)
        if not isinstance(row, dict):
            errors.append(f"{test_id}: missing case")
            continue
        if set(row.get("domains", [])) != domains:
            errors.append(f"{test_id}: domain contract mismatch")
        if row.get("status") not in {"PASS", "FAIL", "NOT_RUN"}:
            errors.append(f"{test_id}: invalid status")
        if row.get("status") == "PASS":
            for key in REQUIRED:
                if not isinstance(row.get(key), str) or not row[key].strip():
                    errors.append(f"{test_id}: PASS without {key}")
            if row.get("device") not in {"Studio", "Android"}:
                errors.append(f"{test_id}: invalid device")
    if report.get("cases", {}).get("GQ06", {}).get("status") == "PASS" and report["cases"]["GQ06"].get("device") != "Android":
        errors.append("GQ06: Android evidence required")
    if any(report.get("cases", {}).get(k, {}).get("status") != "PASS" for k in CONTRACTS):
        errors.append("PRODUCT_NO_GO: incomplete or failing cross-domain evidence")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    issues = check(json.loads(args.report.read_text(encoding="utf-8")))
    print(json.dumps({"decision": "PASS" if not issues else "PRODUCT_NO_GO", "issues": issues}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(issues))

if __name__ == "__main__":
    main()
