#!/usr/bin/env python3
"""P0D multi-writer source-integrity and staged-CAS gate (no network/no writes).

Registry and current-ref snapshots MUST be fetched by a trusted workflow from a
protected coordinator ref and the real GitHub API respectively, not PR content.
This tool evaluates evidence; it does not issue permissions or move refs.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import re
from pathlib import PurePosixPath
import sys

SHA40 = re.compile(r"^[0-9a-f]{40}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{2,99}$")
SCHEMA = "P0D_MULTIWRITER_CAS_V1"
EXCLUSIVE_PATH_TOKENS = (
    "/game.server.luau", "/soloTeamBots.luau", "/horde", "/store",
    "/remote", "/egg", "/match", "/score", "/hp", "/canonical",
)


class Reject(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def need(check, code):
    if not check:
        raise Reject(code)


def sha(value):
    return isinstance(value, str) and bool(SHA40.fullmatch(value))


def check_id(value, code="INVALID_ID"):
    need(isinstance(value, str) and bool(IDENT.fullmatch(value)), code)
    return value


def path(value):
    need(isinstance(value, str) and value and "\\" not in value and "\x00" not in value, "INVALID_PATH")
    need(not value.startswith("/") and not value.endswith("/") and "//" not in value, "INVALID_PATH")
    parts = value.split("/")
    need(all(x not in ("", ".", "..") for x in parts), "PATH_TRAVERSAL")
    need(str(PurePosixPath(value)) == value, "NONCANONICAL_PATH")
    return value


def prefix_match(fpath, root):
    return fpath == root or fpath.startswith(root.rstrip("/") + "/")


def path_overlap(p, q):
    return prefix_match(p.lower(), q.lower()) or prefix_match(q.lower(), p.lower())


def parse_time(value):
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        need(t.tzinfo is not None, "TIME_MISSING_ZONE")
        return t.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        raise Reject("TIME_INVALID") from None


def requires_exclusive(p):
    low = "/" + p.lower()
    return any(t.lower() in low for t in EXCLUSIVE_PATH_TOKENS)


def evaluate(candidate, registry, current, authenticated_actor, now_iso):
    """Fail-closed trusted-input validator; no repo side effects."""
    try:
        need(registry.get("schema") == SCHEMA and candidate.get("schema") == SCHEMA, "SCHEMA_MISMATCH")
        branch = registry.get("release_branch")
        need(branch == "rc/p0d-s1-kids-rc01", "BRANCH_NOT_ALLOWED")
        need(current.get("branch") == branch, "CURRENT_BRANCH_MISMATCH")
        need(sha(current.get("head_sha")), "CURRENT_HEAD_INVALID")
        need(authenticated_actor == candidate.get("actor") and isinstance(authenticated_actor, str), "ACTOR_MISMATCH")
        feature = check_id(candidate.get("feature_id"), "FEATURE_INVALID")
        check_id(authenticated_actor, "ACTOR_INVALID")
        need(sha(candidate.get("base_head")) and sha(candidate.get("proposed_commit_sha")), "PROPOSAL_SHA_INVALID")
        need(sha(candidate.get("proposed_parent_sha")), "PARENT_SHA_INVALID")
        now = parse_time(now_iso)
        grants = registry.get("grants")
        need(isinstance(grants, list), "GRANTS_INVALID")
        grants_for_feature = [g for g in grants if g.get("feature_id") == feature and g.get("status") == "GRANTED"]
        need(len(grants_for_feature) == 1, "GRANT_MISSING_OR_DUPLICATE")
        grant = grants_for_feature[0]
        need(grant.get("actor") == authenticated_actor, "WRITER_NOT_AUTHORIZED")
        need(parse_time(grant.get("expires_at")) > now, "GRANT_EXPIRED")
        scope = grant.get("allowed_paths")
        need(isinstance(scope, list) and len(scope) > 0, "GRANT_NO_PATHS")
        scopes = [path(x) for x in scope]
        need(len({x.lower() for x in scopes}) == len(scopes), "GRANT_DUPLICATE_SCOPE")
        group = grant.get("exclusive_groups", [])
        need(isinstance(group, list), "BAD_GROUPS")
        group = [check_id(x) for x in group]
        changes = candidate.get("changes")
        need(isinstance(changes, list) and 0 < len(changes) <= 50, "BAD_CHANGES")
        changed_paths = [path(x.get("path")) for x in changes]
        need(len({x.lower() for x in changed_paths}) == len(changed_paths), "DUPLICATE_CHANGED_PATH")
        need(all(any(prefix_match(p.lower(), root.lower()) for root in scopes) for p in changed_paths), "UNGRANTED_PATH")
        need(not any(p.lower().startswith(".github/") or p.lower().startswith(".git/") for p in changed_paths), "FORBIDDEN_POLICY_EDIT")
        for change in changes:
            need(sha(change.get("new_blob_sha")), "INVALID_NEW_BLOB")
            need(change.get("base_blob_sha") is None or sha(change.get("base_blob_sha")), "INVALID_BASE_BLOB")
        blobs = current.get("file_blobs")
        need(isinstance(blobs, dict), "CURRENT_BLOBS_MISSING")
        for p in changed_paths:
            need(p in blobs, "CURRENT_PATH_EVIDENCE_MISSING")
        for change in changes:
            p = change["path"]
            cur = blobs[p]
            need(cur is None or sha(cur), "CURRENT_BLOB_INVALID")
            need(cur == change["base_blob_sha"], "EDIT_CONFLICT_CHANGED_SINCE_BASE")
            need(cur != change["new_blob_sha"], "NOOP_CHANGE")
        for other in grants:
            if other is grant or other.get("status") != "GRANTED":
                continue
            need(other.get("feature_id") != feature, "DUPLICATE_FEATURE_WRITER")
            others = [path(x) for x in other.get("allowed_paths", [])]
            need(not any(path_overlap(a, b) for a in scopes for b in others), "ACTIVE_PATH_CLAIM_OVERLAP")
            need(not (set(group) & set(other.get("exclusive_groups", []))), "AUTHORITY_LEASE_OVERLAP")
        if any(requires_exclusive(p) for p in changed_paths):
            need("authority:game" in group or "authority:ui" in group, "MISSING_AUTHORITY_LEASE")
        validation = candidate.get("validation", {})
        need(validation.get("commit_sha") == candidate["proposed_commit_sha"], "CI_NOT_SAME_HEAD")
        need(validation.get("conclusion") == "success", "CI_NOT_GREEN")
        need(validation.get("source_exact") is True and validation.get("source_lock") is True, "SOURCE_PROOF_MISSING")
        need(validation.get("no_high_critical") is True, "SAFETY_QA_MISSING")
        need(validation.get("unique_game_authority") is True, "AUTHORITY_PROOF_MISSING")
        if current["head_sha"] != candidate["proposed_parent_sha"] or current["head_sha"] != candidate["base_head"]:
            return {"status": "REBUILD_RETEST_REQUIRED", "reason": "RC_HEAD_MOVED", "current_head": current["head_sha"], "feature_id": feature, "rc_write_allowed": False, "product_quality": "NO_GO_UNTIL_HUMAN_ACCEPTANCE"}
        need(candidate["proposed_commit_sha"] != current["head_sha"], "EMPTY_PROPOSAL")
        return {"status": "STAGED_CAS_ELIGIBLE", "reason": "PREFLIGHT_PASS", "current_head": current["head_sha"], "feature_id": feature, "expected_head": current["head_sha"], "proposed_commit": candidate["proposed_commit_sha"], "rc_write_allowed": False, "next": "AUTHORIZED_OPERATOR_NONFORCE_EXPECTED_SHA_CAS_AND_READBACK", "product_quality": "NO_GO_UNTIL_HUMAN_ACCEPTANCE"}
    except (Reject, KeyError, TypeError, AttributeError) as exc:
        return {"status": "HOLD", "reason": exc.code if isinstance(exc, Reject) else "MALFORMED_INPUT", "rc_write_allowed": False, "product_quality": "NO_GO_UNTIL_HUMAN_ACCEPTANCE"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--trusted-registry", required=True)
    ap.add_argument("--trusted-current", required=True)
    ap.add_argument("--actor", required=True)
    ap.add_argument("--now", required=True)
    args = ap.parse_args()
    try:
        with open(args.candidate, encoding="utf-8") as f: candidate = json.load(f)
        with open(args.trusted_registry, encoding="utf-8") as f: registry = json.load(f)
        with open(args.trusted_current, encoding="utf-8") as f: current = json.load(f)
        result = evaluate(candidate, registry, current, args.actor, args.now)
    except (OSError, ValueError):
        result = {"status": "HOLD", "reason": "UNREADABLE_INPUT", "rc_write_allowed": False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "STAGED_CAS_ELIGIBLE" else 2


if __name__ == "__main__":
    sys.exit(main())
