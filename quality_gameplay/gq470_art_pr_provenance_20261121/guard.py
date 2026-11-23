"""Fail-closed receipt provenance for the legacy REAL69 art source workflow.

A pull_request checkout is a synthetic merge commit, NOT a formal RC build.
The independent live canonical ref must still equal the PR's base SHA.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

CANONICAL_BRANCH = "rc/p0d-s1-kids-rc01"
CANONICAL_REF = f"refs/heads/{CANONICAL_BRANCH}"
LEGACY_REF = "refs/heads/integration/gq8-real63-fourlane-20261119-0618"
_SHA = re.compile(r"[0-9a-f]{40}\Z")


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise ValueError(f"RED_BAD_{field}")
    return value


def verify_receipt(
    receipt: Mapping[str, Any],
    env: Mapping[str, str],
    event: Mapping[str, Any],
    live_official_sha: str,
) -> str:
    """Return OFFICIAL / PR_CANDIDATE / LEGACY_CANDIDATE or fail closed."""
    run_sha = _sha(env.get("GITHUB_SHA"), "RUN_SHA")
    live_sha = _sha(live_official_sha, "LIVE_OFFICIAL_SHA")
    ref = env.get("GITHUB_REF", "")
    kind = env.get("GITHUB_EVENT_NAME", "")
    if _sha(receipt.get("build_head"), "RECEIPT_HEAD") != run_sha:
        raise ValueError("RED_RECEIPT_NOT_SAME_CHECKOUT_HEAD")
    canonical_flag = receipt.get("canonical_build")
    if type(canonical_flag) is not bool:
        raise ValueError("RED_CANONICAL_FLAG_NOT_BOOLEAN")
    if canonical_flag is not (ref == CANONICAL_REF):
        raise ValueError("RED_FALSE_FORMAL_BUILD_CLASSIFICATION")

    if kind == "pull_request":
        pr = event.get("pull_request")
        if not isinstance(pr, dict):
            raise ValueError("RED_NO_PR_EVENT_PAYLOAD")
        base = pr.get("base")
        head = pr.get("head")
        if not isinstance(base, dict) or not isinstance(head, dict):
            raise ValueError("RED_PR_REF_PAYLOAD_MISSING")
        number = event.get("number")
        if type(number) is not int or number <= 0:
            raise ValueError("RED_PR_NUMBER_MISSING")
        if ref != f"refs/pull/{number}/merge":
            raise ValueError("RED_NOT_ACTUAL_PR_MERGE_REF")
        if base.get("ref") != CANONICAL_BRANCH:
            raise ValueError("RED_WRONG_PR_TARGET_BRANCH")
        if _sha(base.get("sha"), "PR_BASE_SHA") != live_sha:
            raise ValueError("RED_PR_BASE_NOT_LIVE_FORMAL_HEAD")
        _sha(head.get("sha"), "PR_HEAD_SHA")
        if canonical_flag:
            raise ValueError("RED_PR_CANNOT_BE_FORMAL")
        return "PR_CANDIDATE"

    if kind in {"push", "workflow_dispatch"} and ref == CANONICAL_REF:
        if live_sha != run_sha:
            raise ValueError("RED_FORMAL_HEAD_MOVED")
        if not canonical_flag:
            raise ValueError("RED_FORMAL_HEAD_FALSE_FLAG")
        return "OFFICIAL"

    # Preserve the historic pinned exploration branch without calling it formal.
    if kind == "push" and ref == LEGACY_REF:
        original = _sha(env.get("EXPECTED_OFFICIAL"), "PINNED_BASE")
        if live_sha != original or canonical_flag:
            raise ValueError("RED_LEGACY_AUTHOR_OR_FORMAL_DRIFT")
        return "LEGACY_CANDIDATE"

    raise ValueError("RED_UNSUPPORTED_RUN_PROVENANCE")
