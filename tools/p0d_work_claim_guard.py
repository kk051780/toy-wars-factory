#!/usr/bin/env python3
"""Offline P0D claim collision gate. Fail closed; no network/writes/merge.

Registry must be read from an authorized coordination ref with pinned blob
SHA. Candidate and changed paths must come from live same-HEAD GitHub API.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import fnmatch
import json
from pathlib import PurePosixPath
import re
import sys
from typing import Any

SHA = re.compile(r"[0-9a-f]{40}\Z")
TOKEN = re.compile(r"[A-Z][A-Z0-9_-]{2,79}\Z")
BUSY = {"GRANTED", "SOURCE_WIP", "PREP_READY", "HANDOFF_PENDING", "BLOCKED"}


def fail(reason: str) -> None:
    raise ValueError(reason)


def valid_paths(paths: Any) -> set[str]:
    if not isinstance(paths, list) or not paths:
        fail("MISSING_CHANGED_PATHS")
    result: set[str] = set()
    for p in paths:
        if not isinstance(p, str) or len(p) > 250 or not p or "\\" in p or p.startswith("/") or ".." in PurePosixPath(p).parts:
            fail("INVALID_TARGET_PATH")
        result.add(p.casefold())
    return result


def pat_overlap(a: str, b: str) -> bool:
    if fnmatch.fnmatchcase(a, b) or fnmatch.fnmatchcase(b, a):
        return True
    wild = "*?["
    pa = a[:min([a.find(c) for c in wild if c in a], default=len(a))]
    pb = b[:min([b.find(c) for c in wild if c in b], default=len(b))]
    return (any(x in a for x in wild) and any(x in b for x in wild) and
            (pa.startswith(pb) or pb.startswith(pa)))


def canonical(s: Any, aliases: dict[str, str]) -> str:
    if not isinstance(s, str):
        fail("INVALID_FEATURE_OR_RESOURCE")
    key = s.upper().replace("-", "_")
    if not TOKEN.fullmatch(key):
        fail("INVALID_FEATURE_OR_RESOURCE")
    seen = set()
    while key in aliases:
        if key in seen:
            fail("ALIAS_CYCLE")
        seen.add(key)
        key = aliases[key]
    return key


def iso(s: Any) -> datetime:
    if not isinstance(s, str):
        fail("INVALID_LEASE_TIME")
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        fail("INVALID_LEASE_TIME")
    if t.tzinfo is None:
        fail("MISSING_LEASE_TIMEZONE")
    return t


def check(registry: dict[str, Any], candidate: dict[str, Any], actual_paths: list[str], official_head: str,
          now: datetime) -> dict[str, Any]:
    if registry.get("schema") != "P0D_EXCLUSIVE_CLAIMS_V1":
        fail("UNTRUSTED_REGISTRY_SCHEMA")
    if not SHA.fullmatch(official_head):
        fail("INVALID_OFFICIAL_HEAD")
    if now.tzinfo is None:
        fail("INVALID_NOW_TIMEZONE")
    raw_aliases = registry.get("aliases", {})
    if not isinstance(raw_aliases, dict):
        fail("INVALID_ALIAS_TABLE")
    aliases: dict[str, str] = {}
    for k, v in raw_aliases.items():
        ka = str(k).upper().replace("-", "_")
        va = str(v).upper().replace("-", "_")
        if not TOKEN.fullmatch(ka) or not TOKEN.fullmatch(va):
            fail("INVALID_ALIAS_TABLE")
        aliases[ka] = va
    claims = registry.get("claims")
    if not isinstance(claims, list):
        fail("INVALID_CLAIMS")
    active = []
    claim_ids = set()
    for c in claims:
        if not isinstance(c, dict):
            fail("INVALID_CLAIM_ROW")
        cid = c.get("claim_id")
        if not isinstance(cid, str) or not cid or cid in claim_ids:
            fail("DUPLICATE_CLAIM_ID")
        claim_ids.add(cid)
        state = c.get("state")
        if state not in BUSY and state not in {"RELEASED", "RC_INTEGRATED", "REVOKED"}:
            fail("INVALID_CLAIM_STATE")
        if state not in BUSY:
            continue
        if not isinstance(c.get("owner"), str) or not c["owner"]:
            fail("INVALID_CLAIM_OWNER")
        c = dict(c)
        c["feature_id"] = canonical(c.get("feature_id"), aliases)
        resources = c.get("resources")
        if not isinstance(resources, list) or not resources:
            fail("MISSING_CLAIM_RESOURCES")
        c["resources"] = {canonical(r, aliases) for r in resources}
        c["target_paths"] = valid_paths(c.get("target_paths"))
        c["expires_at"] = iso(c.get("expires_at"))
        active.append(c)
    for i, a in enumerate(active):
        for b in active[i+1:]:
            if (a["feature_id"] == b["feature_id"] or a["resources"] & b["resources"] or
                any(pat_overlap(p, q) for p in a["target_paths"] for q in b["target_paths"])):
                fail("REGISTRY_CONFLICT_ACTIVE_CLAIMS")
    if not isinstance(candidate, dict):
        fail("INVALID_CANDIDATE")
    for k in ("source_head", "base_rc"):
        if not isinstance(candidate.get(k), str) or not SHA.fullmatch(candidate[k]):
            fail("INVALID_CANDIDATE_SHA")
    if candidate["base_rc"] != official_head:
        fail("STALE_RC_BASE_RECHECK_REQUIRED")
    f = canonical(candidate.get("feature_id"), aliases)
    cr = candidate.get("resources")
    if not isinstance(cr, list) or not cr:
        fail("MISSING_CANDIDATE_RESOURCES")
    resources = {canonical(x, aliases) for x in cr}
    paths = valid_paths(actual_paths)
    claim_id = candidate.get("claim_id")
    owner = candidate.get("owner")
    matching = [c for c in active if c["claim_id"] == claim_id and c["feature_id"] == f and c["owner"] == owner]
    if len(matching) != 1:
        fail("CLAIM_NOT_GRANTED_OR_OWNER_MISMATCH")
    grant = matching[0]
    if grant["expires_at"] <= now.astimezone(timezone.utc):
        fail("STALE_CLAIM_REQUIRES_COORDINATED_HANDOFF")
    if not resources.issubset(grant["resources"]):
        fail("RESOURCE_SCOPE_EXCEEDS_GRANT")
    if any(not any(fnmatch.fnmatchcase(p, allowed) for allowed in grant["target_paths"]) for p in paths):
        fail("CHANGED_FILES_EXCEED_GRANT")
    return {"schema": "P0D_CLAIM_GATE_V1", "result": "CLAIM_SCOPE_PASS_NOT_RC_ADOPTION", "claim_id": claim_id,
            "feature_id": f, "owner": owner, "source_head": candidate["source_head"], "official_head": official_head,
            "changed_files": len(paths), "no_merge": True, "art_mobile_fun_verified": False}


SOURCE_POLICY = {"schema": "P0D_SOURCE_INCREMENT_POLICY_V1", "kind": "IN_PLACE_REGULAR_BLOBS"}
LEGACY_SOURCE_FLAGS = {
    "requires_actual_GitHub_compare_newHEAD", "requires_actual_cumulative_PR_diff9",
    "requires_frozen7_blob_readback", "guard_PASS_alone_does_not_grant_frozen_paths",
    "requires_independent_prepublication_actual_commit_tree_review",
    "candidate_must_descend_from_expected_donor_head",
    "only_modify_existing_two_regular_blob_files_in_place",
    "no_add_delete_rename_copy_or_type_mode_change",
    "must_include_previous_filename_or_old_path_in_complete_delta",
    "frozen7_must_preserve_path_type_mode_blob", "nonforce_expected_source_branch_HEAD_required",
    "repeat_actual_API_readback_after_publish",
}


def _source_require(condition: bool, reason: str) -> None:
    if not condition:
        fail("SOURCE_INCREMENT_" + reason)


def _source_object(value: Any, keys: set[str], reason: str) -> dict[str, Any]:
    _source_require(isinstance(value, dict) and set(value) == keys, reason)
    return value


def _source_sha(value: Any) -> str:
    _source_require(isinstance(value, str) and SHA.fullmatch(value) is not None, "INVALID_SHA")
    return value


def _source_text(value: Any) -> str:
    _source_require(isinstance(value, str) and bool(value) and not any(ord(c) < 32 for c in value),
                    "INVALID_TEXT")
    return value


def _source_path(value: Any) -> str:
    _source_text(value)
    _source_require("\\" not in value and all(x not in {"", ".", ".."} for x in value.split("/"))
                    and not any(c in value for c in "*?["), "INVALID_LITERAL_PATH")
    return value


def _source_paths(value: Any) -> set[str]:
    _source_require(isinstance(value, list) and bool(value), "MISSING_PATHS")
    paths = [_source_path(x) for x in value]
    _source_require(len({x.casefold() for x in paths}) == len(paths), "DUPLICATE_PATH")
    return set(paths)


def _source_tree(value: Any, tree_sha: str) -> dict[str, tuple[str, str, str]]:
    obj = _source_object(value, {"sha", "truncated", "entries"}, "INVALID_TREE")
    _source_require(obj["sha"] == tree_sha and obj["truncated"] is False
                    and isinstance(obj["entries"], list), "INCOMPLETE_TREE")
    entries: dict[str, tuple[str, str, str]] = {}
    modes = {"tree": {"040000"}, "blob": {"100644", "100755", "120000"}, "commit": {"160000"}}
    for item in obj["entries"]:
        item = _source_object(item, {"path", "type", "mode", "sha"}, "INVALID_TREE_ENTRY")
        path = _source_path(item["path"])
        kind, mode = item["type"], item["mode"]
        _source_require(isinstance(kind, str) and isinstance(mode, str)
                        and mode in modes.get(kind, set()), "INVALID_TREE_TYPE_MODE")
        _source_require(path not in entries, "DUPLICATE_TREE_PATH")
        entries[path] = (kind, mode, _source_sha(item["sha"]))
    for path in entries:
        parts = path.split("/")
        for length in range(1, len(parts)):
            parent = entries.get("/".join(parts[:length]))
            _source_require(parent is not None and parent[:2] == ("tree", "040000"),
                            "MISSING_PARENT_TREE")
    return entries


def _source_delta(before: dict, after: dict) -> dict[str, tuple[Any, Any]]:
    leaves_before = {p: v for p, v in before.items() if v[0] != "tree"}
    leaves_after = {p: v for p, v in after.items() if v[0] != "tree"}
    delta = {p: (leaves_before.get(p), leaves_after.get(p))
             for p in leaves_before.keys() | leaves_after.keys()
             if leaves_before.get(p) != leaves_after.get(p)}
    directories_before = {p: v for p, v in before.items() if v[0] == "tree"}
    directories_after = {p: v for p, v in after.items() if v[0] == "tree"}
    changed_directories = {p for p in directories_before.keys() | directories_after.keys()
                           if directories_before.get(p) != directories_after.get(p)}
    ancestors = {"/".join(p.split("/")[:n]) for p in delta for n in range(1, len(p.split("/")))}
    _source_require(changed_directories == ancestors, "DIRECTORY_DELTA_MISMATCH")
    return delta


def _source_files(files: Any, delta: dict, in_place: bool) -> None:
    _source_require(isinstance(files, list), "INVALID_FILE_LIST")
    observed = set()
    for item in files:
        item = _source_object(item, {"filename", "status", "old_path", "previous_filename", "sha"},
                              "INVALID_FILE_RECORD")
        path = _source_path(item["filename"])
        _source_require(path not in observed and path in delta, "FILE_LIST_DELTA_MISMATCH")
        observed.add(path)
        old, new = delta[path]
        _source_require(new is not None and new[0] == "blob" and new[1] in {"100644", "100755"},
                        "UNSUPPORTED_FILE_CHANGE")
        _source_require(_source_sha(item["sha"]) == new[2], "FILE_BLOB_MISMATCH")
        if old is None:
            _source_require(not in_place and item["status"] == "added" and item["old_path"] is None
                            and item["previous_filename"] is None, "UNSUPPORTED_ADDITION_OR_RENAME")
        else:
            _source_require(old[:2] == new[:2] and item["status"] == "modified"
                            and item["old_path"] == path and item["previous_filename"] in (None, path),
                            "UNSUPPORTED_RENAME_COPY_TYPE_MODE")
    _source_require(observed == set(delta), "INCOMPLETE_FILE_LIST")


def check_source_increment(registry: dict[str, Any], candidate: dict[str, Any], actual_paths: list[str],
                           official_head: str, now: datetime, evidence: dict[str, Any]) -> dict[str, Any]:
    """Check caller-supplied evidence, not provider authenticity or publication authority.

    Complete recursive inventories and complete old/new path records are required.
    The ordinary claim gate runs first and is unchanged. Neither a supplied SHA nor
    a provenance label authenticates data; the caller must pin real provider reads,
    review the actual candidate independently, and enforce lease/CAS/CI separately.
    """
    try:
        scope = check(registry, candidate, actual_paths, official_head, now)
    except (AttributeError, TypeError, KeyError) as exc:
        raise ValueError("SOURCE_INCREMENT_INVALID_SCOPE_INPUT") from exc
    grant = next(c for c in registry["claims"] if c["claim_id"] == candidate["claim_id"])
    target = _source_paths(grant.get("target_paths"))
    mutable = _source_paths(grant.get("mutable_paths"))
    frozen = grant.get("preserved_pr_diff_blobs")
    _source_require(isinstance(frozen, dict), "INVALID_FROZEN_PINS")
    frozen_paths = {_source_path(p) for p in frozen}
    _source_require(len({p.casefold() for p in frozen_paths}) == len(frozen_paths)
                    and not mutable & frozen_paths and target == mutable | frozen_paths,
                    "INVALID_SCOPE_PARTITION")
    for sha in frozen.values():
        _source_sha(sha)
    anchor = _source_sha(grant.get("source_head_before"))
    _source_require(grant.get("maintenance_base_sha") == anchor, "ANCHOR_MISMATCH")
    head = _source_sha(candidate["source_head"])
    base = _source_sha(grant.get("pr_base_sha"))
    branch = _source_text(grant.get("prep_branch"))
    base_ref = _source_text(grant.get("pr_base_ref"))
    number = grant.get("pr")
    _source_require(type(number) is int and number > 0 and head != anchor, "INVALID_CANDIDATE_IDENTITY")
    if "source_increment_policy" in grant:
        _source_require(grant["source_increment_policy"] == SOURCE_POLICY
                        and "source_increment_validation" not in grant, "UNSUPPORTED_OR_CONFLICTING_POLICY")
        policy = "P0D_SOURCE_INCREMENT_POLICY_V1"
    else:
        legacy = _source_object(grant.get("source_increment_validation"), LEGACY_SOURCE_FLAGS |
                                {"compare_base", "allowed_changed_paths", "type_mode_reference"},
                                "UNSUPPORTED_LEGACY_POLICY")
        _source_require(all(legacy[k] is True for k in LEGACY_SOURCE_FLAGS)
                        and legacy["compare_base"] == anchor
                        and _source_paths(legacy["allowed_changed_paths"]) == mutable
                        and (len(mutable), len(frozen_paths), len(target)) == (2, 7, 9),
                        "UNSUPPORTED_LEGACY_POLICY")
        _source_text(legacy["type_mode_reference"])
        policy = "LEGACY_G4_STRUCTURED_IN_PLACE_CONTRACT"
    ev = _source_object(evidence, {"schema", "phase", "repository_full_name", "source_ref",
                                   "observed_source_head", "pr", "commits", "trees", "increment",
                                   "cumulative", "provenance"}, "INVALID_EVIDENCE")
    _source_require(ev["schema"] == "P0D_SOURCE_INCREMENT_EVIDENCE_V1"
                    and ev["phase"] in ("PREPARED", "PUBLISHED"), "UNSUPPORTED_EVIDENCE_SCHEMA_PHASE")
    repo = _source_text(ev["repository_full_name"])
    _source_require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) is not None,
                    "INVALID_REPOSITORY")
    observed_head = anchor if ev["phase"] == "PREPARED" else head
    _source_require(ev["source_ref"] == branch and ev["observed_source_head"] == observed_head,
                    "SOURCE_REF_HEAD_MISMATCH")
    pr = _source_object(ev["pr"], {"number", "repository_full_name", "base_ref", "base_sha", "head_sha"},
                        "INVALID_PR")
    _source_require(type(pr["number"]) is int and pr["number"] == number
                    and pr["repository_full_name"] == repo and pr["base_ref"] == base_ref
                    and pr["base_sha"] == base and pr["head_sha"] == observed_head, "PR_BINDING_MISMATCH")
    commits = _source_object(ev["commits"], {"anchor", "candidate", "pr_base", "merge_base"},
                             "INVALID_COMMITS")
    identities = {}
    for commit in commits.values():
        commit = _source_object(commit, {"sha", "tree_sha", "parents"}, "INVALID_COMMIT")
        sha = _source_sha(commit["sha"])
        _source_sha(commit["tree_sha"])
        parents = commit["parents"]
        _source_require(isinstance(parents, list), "INVALID_PARENTS")
        for parent in parents:
            _source_sha(parent)
        _source_require(len(set(parents)) == len(parents) and sha not in parents, "INVALID_PARENTS")
        _source_require(sha not in identities or identities[sha] == commit, "CONFLICTING_COMMIT_IDENTITY")
        identities[sha] = commit
    merge_base = commits["merge_base"]["sha"]
    _source_require(commits["anchor"]["sha"] == anchor and commits["candidate"]["sha"] == head
                    and commits["pr_base"]["sha"] == base, "COMMIT_BINDING_MISMATCH")
    _source_require(bool(commits["candidate"]["parents"]), "NON_DESCENDANT_ROOT_COMMIT")
    if "maintenance_tree_sha" in grant:
        _source_require(grant["maintenance_tree_sha"] == commits["anchor"]["tree_sha"], "ANCHOR_TREE_MISMATCH")
    tree_ids = {c["tree_sha"] for c in commits.values()}
    trees = _source_object(ev["trees"], tree_ids, "MISSING_OR_UNBOUND_TREES")
    parsed = {sha: _source_tree(trees[sha], sha) for sha in tree_ids}
    a_tree, h_tree, m_tree = (parsed[commits[k]["tree_sha"]] for k in ("anchor", "candidate", "merge_base"))
    _source_require(set(a_tree) == set(h_tree)
                    and all(a_tree[p][:2] == h_tree[p][:2] for p in a_tree), "PATH_TYPE_MODE_CHANGED")
    for path in mutable:
        _source_require(path in a_tree and a_tree[path][0] == "blob"
                        and a_tree[path][1] in {"100644", "100755"}, "MUTABLE_NOT_REGULAR_BLOB")
    for path, sha in frozen.items():
        _source_require(path in a_tree and a_tree[path][0] == "blob"
                        and a_tree[path][2] == sha and h_tree[path] == a_tree[path], "FROZEN_PIN_CHANGED")
    delta = _source_delta(a_tree, h_tree)
    _source_require(bool(delta) and set(delta).issubset(mutable), "INCREMENT_EXCEEDS_MUTABLE_PATHS")
    _source_require(commits["anchor"]["tree_sha"] != commits["candidate"]["tree_sha"], "UNCHANGED_ROOT_TREE")
    inc = _source_object(ev["increment"], {"base_sha", "head_sha", "merge_base_sha", "status", "ahead_by",
                                           "behind_by", "complete", "truncated", "files"}, "INVALID_INCREMENT")
    _source_require(inc["base_sha"] == anchor and inc["head_sha"] == head
                    and inc["merge_base_sha"] == anchor and inc["status"] == "ahead"
                    and type(inc["ahead_by"]) is int and inc["ahead_by"] > 0
                    and type(inc["behind_by"]) is int and inc["behind_by"] == 0
                    and inc["complete"] is True and inc["truncated"] is False, "INCOMPLETE_OR_NON_DESCENDANT_INCREMENT")
    _source_files(inc["files"], delta, True)
    cumulative = _source_object(ev["cumulative"], {"base_sha", "head_sha", "merge_base_sha", "complete",
                                                  "truncated", "changed_files", "files"}, "INVALID_CUMULATIVE")
    total = _source_delta(m_tree, h_tree)
    _source_require(cumulative["base_sha"] == base and cumulative["head_sha"] == head
                    and cumulative["merge_base_sha"] == merge_base
                    and cumulative["complete"] is True and cumulative["truncated"] is False
                    and type(cumulative["changed_files"]) is int
                    and cumulative["changed_files"] == len(total), "INCOMPLETE_CUMULATIVE")
    _source_require(set(total) == target == _source_paths(actual_paths), "CUMULATIVE_SCOPE_MISMATCH")
    _source_files(cumulative["files"], total, False)
    provenance = _source_object(ev["provenance"], {"kind", "repository_full_name", "candidate_sha",
                                                  "observed_source_head", "observed_pr_head", "observed_refs"},
                                "INVALID_PROVENANCE")
    kind = "LOCAL_PREPARED_GIT" if ev["phase"] == "PREPARED" else "GITHUB_API_READBACK"
    _source_require(provenance["kind"] == kind and provenance["repository_full_name"] == repo
                    and provenance["candidate_sha"] == head
                    and provenance["observed_source_head"] == observed_head
                    and provenance["observed_pr_head"] == observed_head, "PROVENANCE_HEAD_MISMATCH")
    refs = provenance["observed_refs"]
    _source_require(isinstance(refs, list), "INVALID_REF_OBSERVATIONS")
    expected_refs = {"source": (branch, observed_head), "pr_head": (f"pull/{number}/head", observed_head),
                     "pr_base": (base_ref, base), "official_rc": (None, official_head)}
    roles = set()
    for ref in refs:
        ref = _source_object(ref, {"role", "repository_full_name", "ref", "sha"}, "INVALID_REF_OBSERVATION")
        role = _source_text(ref["role"])
        _source_require(role in expected_refs and role not in roles, "MISSING_OR_DUPLICATE_REF_ROLE")
        roles.add(role)
        expected_ref, expected_sha = expected_refs[role]
        _source_text(ref["ref"])
        _source_require(ref["repository_full_name"] == repo and ref["sha"] == expected_sha
                        and (expected_ref is None or ref["ref"] == expected_ref), "REF_BINDING_MISMATCH")
    _source_require(roles == set(expected_refs), "MISSING_OR_DUPLICATE_REF_ROLE")
    return {"schema": "P0D_SOURCE_INCREMENT_GATE_V1",
            "result": "SOURCE_INCREMENT_EVIDENCE_CONSISTENT_NOT_RC_ADOPTION",
            "phase": ev["phase"], "policy": policy, "claim_id": candidate["claim_id"],
            "source_anchor": anchor, "source_head": head, "official_head": official_head,
            "pr_base": base, "merge_base": merge_base,
            "tree_shas": {k: c["tree_sha"] for k, c in commits.items()},
            "incremental_changed_files": len(delta), "cumulative_changed_files": len(total),
            "frozen_files": len(frozen), "provider_evidence_authenticated": False,
            "independent_approval_verified": False, "publication_authorized": False,
            "same_head_ci_verified": False, "no_merge": True, "scope_result": scope["result"]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for x in ("registry", "candidate", "changed-files", "official-head"):
        p.add_argument("--" + x, required=True)
    p.add_argument("--now", help="Test override, otherwise system UTC")
    p.add_argument("--source-evidence", help="Opt-in complete source increment evidence JSON")
    a = p.parse_args()
    try:
        with open(a.registry, encoding="utf-8") as f:
            r = json.load(f)
        with open(a.candidate, encoding="utf-8") as f:
            c = json.load(f)
        with open(a.changed_files, encoding="utf-8") as f:
            files = json.load(f)
        now = iso(a.now) if a.now else datetime.now(timezone.utc)
        if a.source_evidence is not None:
            with open(a.source_evidence, encoding="utf-8") as f:
                evidence = json.load(f)
            ans = check_source_increment(r, c, files, a.official_head, now, evidence)
        else:
            ans = check(r, c, files, a.official_head, now)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        schema = "P0D_SOURCE_INCREMENT_GATE_V1" if a.source_evidence is not None else "P0D_CLAIM_GATE_V1"
        print(json.dumps({"schema": schema, "result": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(ans, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
