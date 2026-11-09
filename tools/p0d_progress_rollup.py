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


def summarize(registry, comments=None):
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
    for obj in extras:
        if not isinstance(obj, dict):
            raise ProgressError("BAD_EXTRA_FEATURE")
        fid = obj.get("feature_id")
        if not isinstance(fid, str) or not FEATURE.fullmatch(fid) or fid in base or fid in extra_ids:
            raise ProgressError("DUPLICATE_OR_BAD_EXTRA_FEATURE")
        if obj.get("status") not in ("SOFT_CLAIM_DESIGN_ONLY_NOT_REFERENCE_CODE", "DESIGN_ONLY"):
            raise ProgressError("EXTRA_CANNOT_CLAIM_IMPLEMENTED")
        extra_ids.add(fid)
    known = len(base) + len(extra_ids)
    ready_ref = len(ref_features)
    discovered = parse_issue_comments(comments) if comments is not None else []
    unknown = [x for x in discovered if x["packet_id"] not in seen]
    # Only feature groups counted. Two D16 or D17 packets cannot double-count a feature.
    return {
        "schema": "P0D_PROGRESS_V2", "game_id": registry["game_id"],
        "work_id": registry["work_id"], "pc_status": registry["pc_status"],
        "historical_baseline_features": len(base),
        "new_design_only_features": len(extra_ids), "total_known_feature_groups": known,
        "candidate_features_in_historical_baseline": len(set(pc) | ref_features),
        "candidate_features_in_all_known_groups": len(set(pc) | ref_features),
        "github_reference_feature_groups": ready_ref,
        "indexed_sealed_packets": len(packets),
        "encrypted_artifact_files_indexed": len(packets) * 2,
        "windows_restored_packets_verified": 0,
        "github_reference_feature_groups_studio_qa_pass": 0,
        "pc_blocker": "V37_FINAL_SAVED_PLACE_MULTICLIENT_QA_NOT_ATTESTED",
        "next_gate": "OWNER_DIRECT_PC_V37_QA_THEN_V39_SINGLE_PACKET",
        "discovered_unindexed_delivery_claims": unknown,
        "issue_comments_are_pc_attestation": False,
        "remote_readback_performed_by_this_rollup": False,
    }


def to_markdown(s):
    return ("# TRAP RAIDERS P0-D progress (evidence-scoped)\n\n"
            f"- Historical D01-D17 candidate coverage: **{s['candidate_features_in_historical_baseline']}/{s['historical_baseline_features']}**; not gameplay completion.\n"
            f"- Added design-only groups: **{s['new_design_only_features']}**. Full known groups: **{s['candidate_features_in_all_known_groups']}/{s['total_known_feature_groups']}** with any code candidate.\n"
            f"- GitHub reference feature groups: **{s['github_reference_feature_groups']}**; sealed packets **{s['indexed_sealed_packets']}**, pinned public files **{s['encrypted_artifact_files_indexed']}**.\n"
            f"- Windows RESTORE verified: **0/{s['indexed_sealed_packets']}**; reference Studio QA: **0/{s['github_reference_feature_groups']}**. PC v37: **{s['pc_status']}**.\n"
            f"- Pending candidate deliveries (NOT verified): **{len(s['discovered_unindexed_delivery_claims'])}**.\n"
            f"- BLOCKER: `{s['pc_blocker']}`. Next: `{s['next_gate']}`.\n\n"
            "**Do not treat Python PASS, encrypted GitHub upload or public Issue comments as PC/Studio PASS.**\n")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--comments", type=Path, help="Optional saved list of GitHub Issue comments; read-only hints")
    p.add_argument("--format", choices=("json", "markdown"), default="markdown")
    p.add_argument("--output", type=Path, help="Exclusive-new output; refuse overwrites")
    args = p.parse_args(argv)
    try:
        reg = load_file(args.registry)
        comments = load_file(args.comments) if args.comments else None
        s = summarize(reg, comments)
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
