#!/usr/bin/env python3
"""Fail-closed design-to-game trace audit. No source metadata can prove engine play."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

SCHEMA = "P0D_DESIGN_TO_GAME_TRACE_V1"
ROLE_CAPABILITIES = {
    "P0D-009": ("durability", "heavy_attack", "multi_target", "castle_gate_damage"),
    "P0D-010": ("elemental_attack", "ally_heal", "ally_revive"),
    "P0D-011": ("speed", "timed_invisibility", "infiltration_escape", "ambush"),
    "P0D-012": ("place_trap", "two_point_warp"),
    "P0D-013": ("wall", "bridge", "gate_repair"),
    "P0D-014": ("one_real_summon", "follow", "guard", "attack", "mount"),
    "P0D-015": ("multi_spawn", "control", "ai_command"),
}
RELEASE_ROLE_IDS = set(ROLE_CAPABILITIES) | {"P0D-008"}

def sha(v, n=40):
    return isinstance(v, str) and re.fullmatch(r"[0-9a-f]{" + str(n) + "}", v) is not None

def url(v):
    return isinstance(v, str) and v.startswith("https://") and len(v) > 12

def engine_evidence_ok(proof, head):
    """Only a structurally reviewable claim. Reviewer must verify footage+artifact."""
    return (isinstance(proof, dict)
            and proof.get("result") == "PASS"
            and proof.get("official_rc_head") == head
            and sha(head)
            and url(proof.get("recording_url"))
            and isinstance(proof.get("device"), str) and bool(proof["device"].strip())
            and isinstance(proof.get("reviewer"), str) and bool(proof["reviewer"].strip())
            and isinstance(proof.get("observed_effect"), str) and bool(proof["observed_effect"].strip())
            and url(proof.get("same_head_build_url")))

def evaluate(catalog, trace):
    problems = []
    if not isinstance(catalog, dict):
        catalog = {}
    if not isinstance(trace, dict):
        trace = {}
    rows = catalog.get("rows", [])
    traced = trace.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    if not isinstance(traced, list):
        traced = []
    official_head = trace.get("official_rc_head")
    if trace.get("schema") != SCHEMA:
        problems.append("WRONG_TRACE_SCHEMA")
    if not sha(official_head):
        problems.append("OFFICIAL_HEAD_NOT_PINNED")
    if len(rows) != 67:
        problems.append("CATALOG_67_NOT_VERIFIED")
    catalog_ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if len(catalog_ids) != len(rows) or len(set(catalog_ids)) != len(rows):
        problems.append("CATALOG_INVALID_OR_DUPLICATE_IDS")
    traced_ids = [r.get("feature_id") for r in traced if isinstance(r, dict)]
    if len(traced_ids) != len(traced) or len(set(traced_ids)) != len(traced_ids):
        problems.append("TRACE_INVALID_OR_DUPLICATE_IDS")
    missing = sorted(set(catalog_ids) - set(traced_ids))
    extra = sorted(set(traced_ids) - set(catalog_ids))
    if missing:
        problems.append("UNMAPPED_FEATURE_IDS:" + ",".join(missing))
    if extra:
        problems.append("UNKNOWN_TRACE_IDS:" + ",".join(extra))
    catalog_by_id = {r["id"]: r for r in rows if isinstance(r, dict) and isinstance(r.get("id"), str)}
    covered = 0
    mapped_count = 0
    engine_count = 0
    verified_roles = 0
    release_total = 0
    release_unresolved = 0
    gap_counts = Counter()
    for row in traced:
        if not isinstance(row, dict):
            problems.append("MALFORMED_TRACE_ROW")
            continue
        fid = row.get("feature_id")
        src = catalog_by_id.get(fid)
        if src is None:
            continue
        required = src.get("release") == "S1" or fid in RELEASE_ROLE_IDS
        if required:
            release_total += 1
        if row.get("concept_id") != fid or not url(row.get("design_source_url")):
            problems.append("DESIGN_SOURCE_MISSING:" + fid)
        else:
            mapped_count += 1
        if row.get("release_required") is not required:
            problems.append("RELEASE_REQUIREMENT_MISMATCH:" + fid)
        if fid in RELEASE_ROLE_IDS and row.get("catalog_release") == "S2+":
            # OWNER overrides old S2+ release label; flag the unresolved planning drift.
            gap_counts["OWNER_RELEASE_OVERRIDE_NEEDS_CATALOG_SYNC"] += 1
        if row.get("catalog_release") != src.get("release"):
            problems.append("CATALOG_RELEASE_DRIFT:" + fid)
        if fid == "P0D-011" and (row.get("display_name") != "暗殺者" or row.get("internal_role") != "NINJA"):
            problems.append("ASSASSIN_ALIAS_INVALID")
        if fid == "P0D-011" and "忍者" in str(src.get("name", "")):
            problems.append("CATALOG_ASSASSIN_NAME_STALE")
        gap = row.get("gap_type")
        if gap not in ("ABSENT", "STUB", "WRONG_BEHAVIOR", "PARTIAL", "REGRESSION", "EVIDENCE_MISSING", "NONE"):
            problems.append("GAP_TYPE_INVALID:" + fid)
        gap_counts[str(gap)] += 1
        must = row.get("must_behave")
        has_contract = (isinstance(must, str) and bool(must.strip())
                        and row.get("design_contract_status") == "VERIFIED"
                        and url(row.get("design_revision_url")))
        if has_contract:
            covered += 1
        elif required:
            problems.append("DESIGN_CONTRACT_UNVERIFIED:" + fid)
        else:
            gap_counts["DEFERRED_FUTURE_DESIGN_PENDING"] += 1
        paths = row.get("real_source_paths")
        hashes = row.get("real_source_sha256")
        has_source = (isinstance(paths, list) and bool(paths)
                      and isinstance(hashes, list) and len(paths) == len(hashes)
                      and all(isinstance(p, str) and p.strip() for p in paths)
                      and all(sha(h, 64) for h in hashes))
        proof_ok = has_contract and has_source and engine_evidence_ok(row.get("engine_proof"), official_head)
        if proof_ok:
            engine_count += 1
        elif required:
            problems.append(("ENGINE_UNKNOWN:" if has_source else "SOURCE_OR_ENGINE_UNKNOWN:") + fid)
        else:
            gap_counts["DEFERRED_FUTURE_ENGINE_UNTESTED"] += 1
        if fid in ROLE_CAPABILITIES:
            caps = row.get("capability_proofs")
            if not isinstance(caps, dict):
                caps = {}
            all_caps_ok = True
            for cap in ROLE_CAPABILITIES[fid]:
                if not engine_evidence_ok(caps.get(cap), official_head):
                    problems.append("ROLE_CAPABILITY_ENGINE_UNKNOWN:" + fid + ":" + cap)
                    all_caps_ok = False
            if all_caps_ok and proof_ok:
                verified_roles += 1
        if required and (not proof_ok or fid in ROLE_CAPABILITIES and not all_caps_ok):
            release_unresolved += 1
    if release_total == 0:
        problems.append("NO_RELEASE_SCOPE")
    if verified_roles != 7:
        problems.append("SEVEN_JOBS_FULL_ENGINE_NO_GO")
    if mapped_count != 67:
        problems.append("DESIGN_MAPPING_NOT_67")
    if release_unresolved:
        problems.append("RELEASE_GAMEPLAY_ENGINE_NO_GO")
    if trace.get("art_gate") != "ART_GO" or trace.get("mobile_gate") != "MOBILE_GO" or trace.get("kid_fun_gate") != "FUN_GO":
        problems.append("ART_MOBILE_KID_GATES_UNVERIFIED")
    if trace.get("owner_accepted") is not True:
        problems.append("OWNER_NOT_ACCEPTED")
    return {
        "schema": "P0D_DESIGN_TO_GAME_TRACE_AUDIT_V1",
        "official_rc_head": official_head if sha(official_head) else None,
        "catalog_entries": len(rows),
        "trace_rows": len(traced),
        "inventory_covered": len(set(catalog_ids) & set(traced_ids)),
        "design_coverage": f"{mapped_count}/67",
        "verified_design_contracts": f"{covered}/67",
        "real_engine_pass": engine_count,
        "seven_jobs_full_engine_pass": f"{verified_roles}/7",
        "release_must_pass": release_total,
        "release_unresolved": release_unresolved,
        "gap_counts": dict(sorted(gap_counts.items())),
        "issues": sorted(set(problems)),
        "decision": "DESIGN_CONFORMITY_REVIEWABLE" if not problems else "DESIGN_NO_GO",
        "disclaimer": "Self-reported proofs are NOT authenticated Studio/Android measurements; independently inspect recording and same-HEAD official build."
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--trace", required=True)
    p.add_argument("--report", required=True)
    a = p.parse_args()
    try:
        c = json.loads(Path(a.catalog).read_text(encoding="utf-8"))
        t = json.loads(Path(a.trace).read_text(encoding="utf-8"))
        report = evaluate(c, t)
    except (OSError, ValueError, TypeError) as exc:
        report = {"decision": "DESIGN_NO_GO", "issues": ["INPUT_INVALID:" + type(exc).__name__]}
    Path(a.report).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(report["decision"], report.get("design_coverage", "0/67"), report.get("seven_jobs_full_engine_pass", "0/7"))
    return 0 if report["decision"] == "DESIGN_CONFORMITY_REVIEWABLE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
