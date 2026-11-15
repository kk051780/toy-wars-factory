#!/usr/bin/env python3
"""Transactional non-force GitHub RC update primitive (NO executable CLI).

This module cannot grant release rights. An independent protected workflow
must FIRST verify authenticated actor, protected coordinator registry, claim,
actual PR paths, source-lock, review, and same-SHA CI. The primitive uses one
linear Git commit with parent=observed RC HEAD, and force=False ref update.
A competing writer that wins first makes our commit non-fast-forward: REBASE,
RE-RUN TESTS and retry from the new RC HEAD, NEVER force/merge blindly.
"""
from __future__ import annotations

import re
from typing import Protocol, Any

SHA=re.compile(r"[0-9a-f]{40}\Z")

class CASBlocked(RuntimeError):
    pass

class CASConflict(CASBlocked):
    pass

class Git(Protocol):
    def is_protected(self, branch: str) -> bool: ...
    def get_head(self, branch: str) -> str: ...
    def get_commit(self, sha: str) -> dict[str,Any]: ...
    def source_blobs(self, head: str, paths: list[str]) -> dict[str,str]: ...
    def create_tree(self, base_tree: str, blobs: dict[str,str]) -> str: ...
    def create_commit(self, message: str, tree: str, parents: list[str]) -> str: ...
    def patch_ref(self, branch: str, new_sha: str, force: bool) -> None: ...

RC="rc/p0d-s1-kids-rc01"
COORD="coord/p0d-work-claims"
SHARED_DENY={"main", "master"}

def require_sha(x: str) -> str:
    if not isinstance(x,str) or not SHA.fullmatch(x):
        raise CASBlocked("INVALID_PINNED_SHA")
    return x

def atomic_source_selective_cas(
    git: Git, *, official_branch: str, expected_head: str,
    source_head: str, exact_paths: list[str], independent_authorization: dict,
    message: str,
) -> dict:
    """One RC feature commit; no broad merge, no force, no automatic retry.

    The caller *must* be a protected execution context. This API checks
    immutable data contract and branch protection, but cannot itself verify
    the trust of a Python dict: its inputs must come from live GitHub APIs.
    """
    if official_branch!=RC or official_branch in SHARED_DENY:
        raise CASBlocked("ONLY_CANONICAL_RC_BRANCH")
    if not git.is_protected(RC) or not git.is_protected(COORD):
        raise CASBlocked("MISSING_GITHUB_BRANCH_PROTECTION")
    expected_head=require_sha(expected_head)
    source_head=require_sha(source_head)
    if not isinstance(independent_authorization,dict):
        raise CASBlocked("NO_INDEPENDENT_AUTHORIZATION")
    if independent_authorization.get("decision")!="PROTECTED_WORKFLOW_AUTHORIZE_SINGLE_CAS":
        raise CASBlocked("NOT_AUTHORIZED_BY_PROTECTED_WORKFLOW")
    if (independent_authorization.get("source_sha")!=source_head or
        independent_authorization.get("expected_rc_head")!=expected_head or
        independent_authorization.get("paths")!=exact_paths):
        raise CASBlocked("AUTHORIZATION_NOT_BOUND_TO_EXACT_SOURCE_BASE_PATHS")
    if not isinstance(exact_paths,list) or not exact_paths or len(set(exact_paths))!=len(exact_paths):
        raise CASBlocked("NO_UNIQUE_PATHS")
    from pathlib import PurePosixPath
    for path in exact_paths:
        if (not isinstance(path,str) or not path or len(path)>240
            or path.startswith("/") or "\\" in path or "//" in path
            or "." in PurePosixPath(path).parts
            or ".." in PurePosixPath(path).parts
            or path != str(PurePosixPath(path))):
            raise CASBlocked("INVALID_TARGET_PATH")
        if path.startswith((".github/","multiwriter/")):
            raise CASBlocked("SHARED_META_NEEDS_SEPARATE_COORDINATION")
    if not isinstance(message,str) or not message.startswith("P0D/") or len(message)>200:
        raise CASBlocked("MISSING_AUDIT_TRAIL")
    if git.get_head(RC)!=expected_head:
        raise CASConflict("BASE_MOVED_BEFORE_CAS_REBASE_AND_RETEST")
    old_commit=git.get_commit(expected_head)
    base_tree=require_sha(old_commit["tree"])
    blobs=git.source_blobs(source_head,exact_paths)
    if set(blobs)!=set(exact_paths):
        raise CASBlocked("SOURCE_BLOB_PATH_MISSING_OR_DELETED")
    for b in blobs.values():
        require_sha(b)
    # A single new tree consists solely of source-approved exact paths
    # transplanted onto official HEAD. No whole-branch merge.
    new_tree=require_sha(git.create_tree(base_tree,blobs))
    new_commit=require_sha(git.create_commit(message,new_tree,[expected_head]))
    created=git.get_commit(new_commit)
    if created.get("parents")!=[expected_head] or created.get("tree")!=new_tree:
        raise CASBlocked("BAD_COMMIT_PARENT_OR_TREE")
    try:
        # force=False is essential; with two disjoint fast-forward writers,
        # exactly one old-parent commit wins. The loser must rebuild a new
        # commit from the winner's RC HEAD and obtain new CI and approval.
        git.patch_ref(RC,new_commit,force=False)
    except Exception as exc:
        raise CASConflict("NON_FAST_FORWARD_REBASE_RETEST_REQUIRED") from exc
    # The branch may already be advanced by another later writer; our commit
    # was still atomically accepted. Record our own commit SHA for audit.
    return {"schema":"P0D_SCOPED_CAS_RECEIPT_V1",
            "result":"CAS_REF_PATCH_ACCEPTED_SOURCE_QA_NOT_STUDIO_GO",
            "old_head":expected_head,"adopted_commit":new_commit,
            "source_head":source_head,"paths":exact_paths,
            "same_head_full_ci":"PENDING","place_bytes":None,
            "zip_bytes":None,"owner_studio":"NOT_TESTED"}
