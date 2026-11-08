#!/usr/bin/env python3
"""P0: GitHub Actions runner provenance probe, read-only and never a writer grant.

This verifies that GitHub API run/PR metadata agrees with context supplied
by the Actions runner. It cannot identify an OpenAI ChatGPT automation, grant
GitHub write/merge rights, attest runner fleet drain or activate scoped v2.
No GitHub POST/PATCH/PUT/DELETE requests and no secrets in the JSON output.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

REPO = "kk051780/toy-wars-factory"
SHA = re.compile(r"[0-9a-f]{40}\Z")
BRANCH = re.compile(r"controller/p0-[a-z0-9/-]+\Z")
NUM = re.compile(r"[1-9][0-9]{0,18}\Z")
URL_ROOT = "https://api.github.com/repos/" + REPO
PATH = ".github/workflows/bootstrap-quality.yml"


def _check(ok, reason):
    if not ok:
        raise ValueError(reason)


def _context(env):
    names = ("TWF_RUN_ID", "TWF_RUN_ATTEMPT", "TWF_PR_NUMBER",
             "TWF_HEAD_SHA", "TWF_BASE_SHA", "TWF_HEAD_BRANCH",
             "TWF_ACTOR_ID", "TWF_EVENT_NAME", "TWF_REPOSITORY")
    _check(all(type(env.get(k)) is str for k in names),
           "missing GitHub runner context")
    _check(env["TWF_REPOSITORY"] == REPO, "foreign repo")
    _check(env["TWF_EVENT_NAME"] == "pull_request", "wrong trigger")
    for key in ("TWF_RUN_ID", "TWF_RUN_ATTEMPT", "TWF_PR_NUMBER", "TWF_ACTOR_ID"):
        _check(NUM.fullmatch(env[key]) is not None, "invalid run or PR number")
    _check(env["TWF_PR_NUMBER"] == "203", "outside P0 probe PR")
    for key in ("TWF_HEAD_SHA", "TWF_BASE_SHA"):
        _check(SHA.fullmatch(env[key]) is not None, "invalid SHA")
    _check(BRANCH.fullmatch(env["TWF_HEAD_BRANCH"]) is not None,
           "unexpected branch")
    return {name: env[name] for name in names}


def verify(context, run, pr):
    """Deterministic fail-closed cross-check; data provenance is caller's job."""
    c = _context(context)
    _check(type(run) is dict and type(pr) is dict, "bad GitHub API payload")
    _check(run.get("id") == int(c["TWF_RUN_ID"]), "run ID mismatch")
    _check(run.get("run_attempt") == int(c["TWF_RUN_ATTEMPT"]),
           "run attempt mismatch")
    _check(run.get("event") == "pull_request", "run event mismatch")
    _check(run.get("path") == PATH, "workflow path mismatch")
    _check(type(run.get("repository")) is dict and
           run["repository"].get("full_name") == REPO, "run repository mismatch")
    _check(type(run.get("head_repository")) is dict and
           run["head_repository"].get("full_name") == REPO, "head repo mismatch")
    _check(run.get("head_sha") == c["TWF_HEAD_SHA"] and
           run.get("head_branch") == c["TWF_HEAD_BRANCH"],
           "run head identity mismatch")
    _check(type(run.get("actor")) is dict and
           run["actor"].get("id") == int(c["TWF_ACTOR_ID"]),
           "run actor mismatch")
    _check(type(run.get("pull_requests")) is list and
           any(type(item) is dict and
               item.get("number") == int(c["TWF_PR_NUMBER"])
               for item in run["pull_requests"]), "run not attached to PR")
    _check(pr.get("number") == int(c["TWF_PR_NUMBER"]) and
           pr.get("state") == "open" and pr.get("draft") is True,
           "PR changed or not draft")
    head, base = pr.get("head"), pr.get("base")
    _check(type(head) is dict and type(base) is dict, "PR refs missing")
    _check(head.get("sha") == c["TWF_HEAD_SHA"] and
           head.get("ref") == c["TWF_HEAD_BRANCH"] and
           type(head.get("repo")) is dict and
           head["repo"].get("full_name") == REPO,
           "PR head drift/fork")
    _check(base.get("sha") == c["TWF_BASE_SHA"] and
           base.get("ref") == "main", "PR base drift")
    return {
        "schema": 1, "kind": "P0_ACTIONS_RUN_PR_READONLY_MATCH",
        "repository": REPO, "run_id": int(c["TWF_RUN_ID"]),
        "run_attempt": int(c["TWF_RUN_ATTEMPT"]),
        "workflow_path": PATH, "pr_number": int(c["TWF_PR_NUMBER"]),
        "head_sha": c["TWF_HEAD_SHA"], "base_sha": c["TWF_BASE_SHA"],
        "head_branch": c["TWF_HEAD_BRANCH"],
        "github_actions_api_metadata_matched": True,
        "provider_write_attempted": False, "may_write": False,
        "may_merge": False, "may_release": False,
        "openai_chatgpt_task_authenticated": False,
        "old_runner_fleet_drained": False,
        "source_branch_action_cas_verified": False,
        "real_two_gpt_writers_verified": False,
        "scoped_parallel_activation_authorized": False,
    }


def github_get(path, token):
    # Fixed host/path, repo and int IDs validated before caller invokes us.
    _check(path.startswith(URL_ROOT + "/"), "invalid API URL")
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "toy-wars-p0-readonly-evidence",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(path, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=12) as response:
        _check(response.status == 200, "GitHub API non-200")
        raw = response.read(2 * 1024 * 1024 + 1)
        _check(len(raw) < 2 * 1024 * 1024, "GitHub API size cap")
        return json.loads(raw)


def main():
    c = _context(os.environ)
    token = os.environ.get("TWF_ACTIONS_READ_TOKEN", "")
    _check(type(token) is str and token != "", "missing read-only workflow token")
    run = github_get(URL_ROOT + "/actions/runs/" + c["TWF_RUN_ID"], token)
    pr = github_get(URL_ROOT + "/pulls/" + c["TWF_PR_NUMBER"], token)
    proof = verify(c, run, pr)
    dest = Path(".qa/p0-actions-run-readonly.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    print("P0_HOST_RUN_READONLY_MATCH run=" + c["TWF_RUN_ID"] +
          " head=" + c["TWF_HEAD_SHA"] +
          " token_not_emitted=true no_write=true no_parallel_grant=true")


if __name__ == "__main__":
    main()
