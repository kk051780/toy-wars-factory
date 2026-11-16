#!/usr/bin/env python3
"""Reject stale or fabricated 'same HEAD' evidence for the eight-domain RC trace.

This is live GitHub source-identity verification, NOT Studio, gameplay or FUN QA.
It has no write permissions and never treats private preview artifacts as RC.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from check_trace import MATRIX, TraceFailure, require

REPO = "kk051780/toy-wars-factory"
BRANCH = "rc/p0d-s1-kids-rc01"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
RUN_URL = re.compile(
    r"^https://github[.]com/kk051780/toy-wars-factory/actions/runs/([1-9][0-9]*)$"
)


def verify_live_identity(matrix: dict, branch: dict, run: dict) -> dict:
    """Compare snapshot with independent live branch + Actions API objects."""
    record = matrix.get("official_rc_observation") or {}
    require(record.get("branch") == BRANCH, "snapshot official RC branch changed")
    pinned = record.get("head")
    require(isinstance(pinned, str) and SHA40.fullmatch(pinned) is not None,
            "snapshot official RC SHA malformed")
    require(record.get("head_source_build") == "SUCCESS",
            "snapshot did not claim source build SUCCESS")
    run_url = record.get("verified_source_build_run")
    match = RUN_URL.fullmatch(run_url or "")
    require(match is not None, "official run URL points outside canonical repo/actions")
    require(branch.get("name") == BRANCH, "live branch name mismatch")
    live_sha = (branch.get("commit") or {}).get("sha")
    require(isinstance(live_sha, str) and SHA40.fullmatch(live_sha) is not None,
            "live branch did not expose immutable HEAD")
    require(live_sha == pinned, "STALE_RC_HEAD: snapshot is not the live RC HEAD")
    require(run.get("id") == int(match.group(1)), "Actions run ID/URL mismatch")
    require(run.get("html_url") == run_url, "Actions run canonical URL mismatch")
    require((run.get("repository") or {}).get("full_name") == REPO,
            "Actions run belongs to another repository")
    require(run.get("head_branch") == BRANCH, "Actions run is not on official RC branch")
    require(run.get("head_sha") == live_sha,
            "SAME_HEAD_FAILURE: successful Actions belongs to another commit")
    require(run.get("status") == "completed" and run.get("conclusion") == "success",
            "official source workflow is not completed SUCCESS")
    return {
        "official_rc_branch": BRANCH,
        "verified_same_head": live_sha,
        "verified_actions_run": run.get("id"),
        "source_identity": "LIVE_SAME_HEAD_VERIFIED",
        "official_rc_zip_bytes": "UNKNOWN_NOT_MEASURED_BY_THIS_GATE",
        "studio_android_owner_fun": "NOT_VERIFIED_BY_THIS_GATE",
    }


def github_json(url: str) -> dict:
    """Read only, with GitHub Actions' ephemeral read token when supplied."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "P0D-GQ-readonly-same-head-identity",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return json.load(response)


def main() -> int:
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    observation = matrix.get("official_rc_observation") or {}
    run_url = observation.get("verified_source_build_run", "")
    match = RUN_URL.fullmatch(run_url)
    require(match is not None, "cannot query noncanonical Actions URL")
    # The branch and run must be retrieved independently, not copied from trace.
    api = "https://api.github.com/repos/" + REPO
    branch = github_json(api + "/branches/" + BRANCH)
    run = github_json(api + "/actions/runs/" + match.group(1))
    report = verify_live_identity(matrix, branch, run)
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (TraceFailure, HTTPError, URLError, TimeoutError, ValueError) as exc:
        print("RC_FRESHNESS_NO_GO: " + str(exc), file=sys.stderr)
        sys.exit(2)
