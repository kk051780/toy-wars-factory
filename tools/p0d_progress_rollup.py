#!/usr/bin/env python3
"""Deterministic P0-D progress rollup from a pinned registry.

No Studio/Codex/GitHub writes. Does not decrypt, execute, or extract sealed work.
Issue comments are untrusted discovery hints, never a quality attestation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

# Reuse the shipped v1 strict registry validator when this runs inside the GitHub handoff.
# Its contract refuses to assert a PC/Studio pass for public metadata.

ID = re.compile(r"[A-Za-z0-9_.-]{1,96}\Z")
FEATURE = re.compile(r"D\d\d\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
PC_SOURCE = re.compile(r"https://github[.]com/kk051780/toy-wars-factory/issues/213#issuecomment-[0-9]+\Z")
PC_COORD = re.compile(r"https://github[.]com/kk051780/toy-wars-factory/issues/218#issuecomment-[0-9]+\Z")
MAX_INPUT = 1_000_000

class ProgressError(ValueError):
    pass


def strict_loads(raw: bytes | str):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ProgressError("DUPLICATE_JSON_KEY")
            result[k] = v
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ProgressError("INVALID_JSON") from exc


def load_file(path: Path):
    if path.is_symlink():
        raise ProgressError("SYMLINK_INPUT_REJECTED")
    with path.open("rb") as f:
        raw = f.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ProgressError("INPUT_TOO_LARGE")
    return strict_loads(raw)


def parse_issue_comments(doc):
    """Discover additional handoff CLAIMS only. Never infer PC/STUDIO quality."""
    if not isinstance(doc, list) or len(doc) > 1000:
        raise ProgressError("BAD_COMMENTS_FEED")
    rows = {}
    for item in doc:
        body = item.get("body", "") if isinstance(item, dict) else ""
        if not isinstance(body, str) or len(body) > 30000:
            continue
        if not ("[P0D_DELIVERY]" in body or "[P0D_PROGRESS_EVENT v1]" in body):
            continue
        packet_match = re.search(r"(?m)^packet_id=([^\r\n]+)$", body)
        commit_match = re.search(r"(?m)^commit_sha=([^\r\n]+)$", body)
        if not packet_match or not commit_match:
            continue
        pid, commit = packet_match[1].strip(), commit_match[1].strip()
        if not ID.fullmatch(pid) or not SHA.fullmatch(commit):
            continue
        rows[(pid, commit)] = {
            "packet_id": pid, "commit": commit,
            "status": "DISCOVERED_UNVERIFIED_UNINDEXED", "pc_qa": "NOT_TESTED",
        }
    return sorted(rows.values(), key=lambda x: (x["packet_id"], x["commit"]))


def validate_pc_evidence(evidence, registry):
    """Accept *recorded PC reports* only with source references and pinned hashes.

    This does not run Windows/Studio or cryptographically authenticate a GitHub
    comment. The result must always be presented as SOURCE-REPORTED evidence.
    """
    if not isinstance(evidence, dict) or evidence.get("schema") != "P0D_PC_EVIDENCE_V1":
        raise ProgressError("BAD_PC_EVIDENCE_SCHEMA")
    if (evidence.get("game_id"), evidence.get("work_id")) != (registry.get("game_id"), registry.get("work_id")):
        raise ProgressError("PC_EVIDENCE_WRONG_PROJECT")
    if evidence.get("evidence_level") != "WINDOWS_CODEX_REPORT_RECORDED_NOT_INDEPENDENTLY_RERUN":
        raise ProgressError("PC_EVIDENCE_NOT_AUTHORITATIVE")
    if not PC_SOURCE.fullmatch(str(evidence.get("source_issue_comment", ""))):
        raise ProgressError("PC_EVIDENCE_BAD_SOURCE")
    if not PC_COORD.fullmatch(str(evidence.get("coordination_comment", ""))):
        raise ProgressError("PC_EVIDENCE_BAD_COORDINATION_SOURCE")
    if evidence.get("global_release_status") != "PARTIAL_NOT_READY" or registry.get("pc_status") != "PARTIAL_NOT_READY":
        raise ProgressError("PC_EVIDENCE_GLOBAL_PASS_UNSUPPORTED")
    if evidence.get("pc_studio_exit") != "STUDIO_CLOSED_VERIFIED_REPORTED":
        raise ProgressError("PC_STUDIO_EXIT_NOT_CONFIRMED")
    if not SHA.fullmatch(str(evidence.get("pc_local_head_sha1", ""))):
        raise ProgressError("PC_LOCAL_HEAD_INVALID")
    for field in ("pc_place_sha256", "pc_cumulative_zip_sha256", "pc_source_set_sha256", "pc_manifest_sha256", "prior_v37_place_sha256"):
        if not SHA256.fullmatch(str(evidence.get(field, ""))):
            raise ProgressError("PC_HASH_INVALID_" + field)
    results=evidence.get("packet_results")
    if not isinstance(results,list) or not results or len(results)>100:
        raise ProgressError("PC_RESULTS_INVALID")
    indexed={p["packet_id"]:p for p in registry["sealed_packets"]}
    seen=set()
    restored=set(); scoped=set()
    for result in results:
        if not isinstance(result,dict):
            raise ProgressError("PC_PACKET_RESULT_INVALID")
        ident=result.get("packet_id")
        if not isinstance(ident,str) or ident in seen or ident not in indexed:
            raise ProgressError("PC_PACKET_UNKNOWN_OR_DUPLICATE")
        seen.add(ident)
        pack=indexed[ident]
        if (result.get("pinned_commit")!=pack["commit"] or
            result.get("restored_zip_sha256")!=pack["zip_sha256"]):
            raise ProgressError("PC_PACKET_PIN_OR_ZIP_MISMATCH")
        if result.get("windows_restore")!="PASS_REPORTED_BY_WINDOWS_CODEX":
            raise ProgressError("PC_RESTORE_UNSUPPORTED_STAGE")
        if result.get("studio_integration")!="SCOPED_PASS_REPORTED_BY_WINDOWS_CODEX":
            raise ProgressError("PC_STUDIO_STAGE_UNSUPPORTED")
        if result.get("studio_full_qa")!="NOT_COMPLETE":
            raise ProgressError("PC_FINAL_STUDIO_NOT_SUPPORTED")
        todo=result.get("remaining_qa")
        if not isinstance(todo,list) or not todo or not all(isinstance(x,str) and 4<=len(x)<=180 for x in todo):
            raise ProgressError("PC_QA_REMAINDERS_REQUIRED")
        restored.add(ident)
        scoped.update(pack["feature_ids"])
    return {"reported_restored":len(restored),"reported_scoped_feature_groups":len(scoped),
            "source_issue_comment":evidence["source_issue_comment"],
            "pc_local_head_sha1":evidence["pc_local_head_sha1"],
            "pc_place_sha256":evidence["pc_place_sha256"],
            "remaining_qa":list(dict.fromkeys(x for p in results for x in p["remaining_qa"])),
            "next_owner_codex_gate":evidence.get("next_owner_codex_gate", "RECHECK_ACTUAL_PC_STATUS"),
            "source_level":evidence["evidence_level"]}


def summarize(registry, comments=None, pc_evidence=None):
    if not isinstance(registry, dict) or registry.get("schema") != "P0D_READONLY_INTAKE_V1":
        raise ProgressError("BAD_REGISTRY_SCHEMA")
    if registry.get("game_id") != "TRAP_RAIDERS" or registry.get("work_id") != "p0d-siege-v19":
        raise ProgressError("WRONG_PROJECT")
    if registry.get("pc_status") != "PARTIAL_NOT_READY":
        raise ProgressError("UNVERIFIED_PC_STATUS")
    base = registry.get("baseline_feature_ids")
    if base != [f"D{i:02d}" for i in range(1, 18)]:
        raise ProgressError("BASELINE_CHANGED")
    pc = registry.get("pc_partial_feature_ids")
    if pc != [f"D{i:02d}" for i in range(1, 6)]:
        raise ProgressError("UNVERIFIED_PC_FEATURES")
    packets = registry.get("sealed_packets")
    if not isinstance(packets, list) or len(packets) > 100 or not packets:
        raise ProgressError("BAD_PACKETS")
    seen, files, ref_features = set(), set(), set()
    for p in packets:
        if not isinstance(p, dict):
            raise ProgressError("BAD_PACKET")
        pid, sha = p.get("packet_id"), p.get("commit")
        if not isinstance(pid, str) or not ID.fullmatch(pid) or pid in seen:
            raise ProgressError("BAD_OR_DUPLICATE_PACKET")
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise ProgressError("BAD_COMMIT")
        seen.add(pid)
        if p.get("windows_restore") != "NOT_TESTED" or p.get("studio_qa") != "NOT_TESTED":
            raise ProgressError("PUBLIC_METADATA_CANNOT_ATTEST_PC_PASS")
        fs = p.get("feature_ids")
        if not isinstance(fs, list) or not fs or not set(fs).issubset(set(base)):
            raise ProgressError("BAD_FEATURE_IDS")
        ref_features.update(fs)
        for kind in ("envelope", "readme"):
            path = p.get(kind + "_path")
            if not isinstance(path, str) or not re.fullmatch(r"handoffs/[A-Za-z0-9_.-]+", path):
                raise ProgressError("UNSAFE_REMOTE_PATH")
            pair = (sha, path)
            if pair in files:
                raise ProgressError("SAME_COMMIT_PATH_COLLISION")
            files.add(pair)
    extras = registry.get("new_design_feature_items", [])
    if not isinstance(extras, list) or len(extras) > 100:
        raise ProgressError("BAD_EXTRA_FEATURES")
    extra_ids = set()
    delivered_design_ids = set()
    for obj in extras:
        if not isinstance(obj, dict):
            raise ProgressError("BAD_EXTRA_FEATURE")
        fid = obj.get("feature_id")
        if not isinstance(fid, str) or not FEATURE.fullmatch(fid) or fid in base or fid in extra_ids:
            raise ProgressError("DUPLICATE_OR_BAD_EXTRA_FEATURE")
        if obj.get("status") not in ("SOFT_CLAIM_DESIGN_ONLY_NOT_REFERENCE_CODE", "DESIGN_ONLY", "DESIGN_ARTIFACT_DELIVERED_NO_GAME_CODE"):
            raise ProgressError("EXTRA_CANNOT_CLAIM_IMPLEMENTED")
        if obj.get("status") == "DESIGN_ARTIFACT_DELIVERED_NO_GAME_CODE":
            delivered_design_ids.add(fid)
        extra_ids.add(fid)
    known = len(base) + len(extra_ids)
    ready_ref = len(ref_features)
    discovered = parse_issue_comments(comments) if comments is not None else []
    unknown = [x for x in discovered if x["packet_id"] not in seen]
    # Only registered, source-linked PC evidence may contribute to PC stages.
    # Untrusted public Issue comments are discovery ONLY and never promote QA.
    pc_data = validate_pc_evidence(pc_evidence,registry) if pc_evidence is not None else None
    # Only feature groups counted. Multiple D07/D16/D17 packets do not double-count.
    return {
        "schema": "P0D_PROGRESS_V2", "game_id": registry["game_id"],
        "work_id": registry["work_id"], "pc_status": registry["pc_status"],
        "historical_baseline_features": len(base),
        "new_design_only_features": len(extra_ids), "new_design_artifact_delivered_groups": len(delivered_design_ids), "total_known_feature_groups": known,
        "candidate_features_in_historical_baseline": len(set(pc) | ref_features),
        "candidate_features_in_all_known_groups": len(set(pc) | ref_features),
        "github_reference_feature_groups": ready_ref,
        "indexed_sealed_packets": len(packets),
        "encrypted_artifact_files_indexed": len(packets) * 2,
        "windows_restored_packets_verified": 0,  # independent tool verification cannot be inferred
        "windows_restored_packets_pc_reported": pc_data["reported_restored"] if pc_data else 0,
        "github_reference_feature_groups_studio_qa_pass": 0,  # FULL QA remains unverified
        "github_reference_feature_groups_studio_scoped_pc_reported": pc_data["reported_scoped_feature_groups"] if pc_data else 0,
        "pc_evidence": pc_data if pc_data else {"status":"NOT_SUPPLIED_TO_THIS_COMMAND"},
        "pc_blocker": "V39_FINAL_MULTICLIENT_RECONNECT_REAL_PHONE_SOUND_OUTSTANDING" if pc_data else "PC_REPORT_NOT_SUPPLIED_V37_AND_V39_NEED_RECHECK",
        "next_gate": pc_data["next_owner_codex_gate"] if pc_data else "VERIFY_LATEST_PC_REPORT_BEFORE_V43A",
        "discovered_unindexed_delivery_claims": unknown,
        "issue_comments_are_pc_attestation": False,
        "remote_readback_performed_by_this_rollup": False,
    }


def to_markdown(s):
    return ("# TRAP RAIDERS P0-D progress (evidence-scoped)\n\n"
            f"- Historical D01-D17 candidate coverage: **{s['candidate_features_in_historical_baseline']}/{s['historical_baseline_features']}**; not gameplay completion.\n"
            f"- Added design-only groups: **{s['new_design_only_features']}** (design packages delivered **{s['new_design_artifact_delivered_groups']}**). Full known groups: **{s['candidate_features_in_all_known_groups']}/{s['total_known_feature_groups']}** with any code candidate.\n"
            f"- GitHub reference feature groups: **{s['github_reference_feature_groups']}**; sealed packets **{s['indexed_sealed_packets']}**, pinned public files **{s['encrypted_artifact_files_indexed']}**.\n"
            f"- Windows RESTORE **PC-reported**: **{s['windows_restored_packets_pc_reported']}/{s['indexed_sealed_packets']}**; scoped Studio integration **PC-reported**: **{s['github_reference_feature_groups_studio_scoped_pc_reported']}/{s['github_reference_feature_groups']}**. Full game QA: **PARTIAL_NOT_READY**.\n"
            f"- PC report source: **{s['pc_evidence'].get('source_issue_comment','NOT_SUPPLIED')}**; the rollup did not independently access Studio.\n"
            f"- Pending candidate deliveries (NOT verified): **{len(s['discovered_unindexed_delivery_claims'])}**.\n"
            f"- BLOCKER: `{s['pc_blocker']}`. Next: `{s['next_gate']}`.\n\n"
            "**Do not treat Python PASS, encrypted GitHub upload or public Issue comments as PC/Studio PASS.**\n")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--comments", type=Path, help="Optional saved list of GitHub Issue comments; read-only hints")
    p.add_argument("--pc-evidence", type=Path, help="Explicit source-linked PC report JSON; never self-attests actual Windows execution")
    p.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p.add_argument("--output", type=Path, help="Exclusive-new output; refuse overwrites")
    args = p.parse_args(argv)
    try:
        reg = load_file(args.registry)
        comments = load_file(args.comments) if args.comments else None
        pc_evidence = load_file(args.pc_evidence) if args.pc_evidence else None
        s = summarize(reg, comments, pc_evidence)
        out = (json.dumps(s, ensure_ascii=False, indent=2, sort_keys=True) + "\n" if args.format == "json" else to_markdown(s))
        if args.output:
            if not args.output.parent.is_dir() or args.output.parent.is_symlink():
                raise ProgressError("OUTPUT_PARENT_NOT_TRUSTED")
            with args.output.open("x", encoding="utf-8") as f:
                f.write(out)
        else:
            sys.stdout.write(out)
        return 0
    except (ProgressError, OSError, TypeError, ValueError) as exc:
        print("BLOCKED: " + type(exc).__name__ + " " + str(exc).split("\n")[0][:80], file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
