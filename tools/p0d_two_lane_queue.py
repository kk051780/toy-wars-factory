#!/usr/bin/env python3
"""P0D two-lane latest verified PREP inbox. Strictly READ ONLY, never merges."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.request
from typing import Any, Callable

REPO = "kk051780/toy-wars-factory"
OFFICIAL = "rc/p0d-s1-kids-rc01"
RUN_NAME = "P0D canonical RC fast-lane Studio build"
PIN = re.compile(r"^[0-9a-f]{40}$")
FEATURE = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")

class GitHubReadOnly:
    def __init__(self, token: str):
        self.token = token

    def __call__(self, path: str) -> Any:
        req = urllib.request.Request("https://api.github.com" + path, headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "p0d-two-lane-readonly/1.0",
            **({"Authorization": "Bearer " + self.token} if self.token else {}),
        })
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)

def manifest(body: str) -> dict[str, Any]:
    rows = [x.strip() for x in body.splitlines()]
    if rows.count("P0D_PREP_READY_V1") != 1:
        raise ValueError("MISSING_UNIQUE_PREP_READY_CONTRACT")
    values: dict[str, str] = {}
    for row in rows:
        m = re.fullmatch(r"(PINNED_HEAD|BASE_RC|FEATURE_IDS|SOURCE_LOCK|ROLLBACK):\s*(\S.*)", row)
        if m:
            if m.group(1) in values:
                raise ValueError("DUPLICATE_CONTRACT_FIELD_" + m.group(1))
            values[m.group(1)] = m.group(2).strip()
    missing = set(("PINNED_HEAD", "BASE_RC", "FEATURE_IDS", "SOURCE_LOCK", "ROLLBACK")) - set(values)
    if missing:
        raise ValueError("MISSING_FIELDS_" + ",".join(sorted(missing)))
    if not PIN.fullmatch(values["PINNED_HEAD"]) or not PIN.fullmatch(values["BASE_RC"]):
        raise ValueError("INVALID_SHA")
    feature_ids = [s.strip() for s in values["FEATURE_IDS"].split(",")]
    if not feature_ids or len(feature_ids) > 8 or len(set(feature_ids)) != len(feature_ids) or not all(FEATURE.fullmatch(s) for s in feature_ids):
        raise ValueError("INVALID_FEATURE_IDS")
    lock = values["SOURCE_LOCK"]
    if lock.startswith("/") or ".." in lock.split("/") or not lock.endswith(".json"):
        raise ValueError("INVALID_SOURCE_LOCK_PATH")
    if len(values["ROLLBACK"]) < 12:
        raise ValueError("MISSING_REAL_ROLLBACK")
    return {"head": values["PINNED_HEAD"], "base": values["BASE_RC"], "features": feature_ids,
            "source_lock": lock, "rollback": values["ROLLBACK"]}

def choose_latest(official_sha: str, pull_requests: list[dict], api: Callable[[str], Any], repo: str = REPO) -> dict[str, Any]:
    if not PIN.fullmatch(official_sha):
        raise ValueError("INVALID_OFFICIAL_HEAD")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("INVALID_REPO")
    examined: list[dict[str, Any]] = []
    for pr in pull_requests:
        number = pr.get("number")
        if not isinstance(number, int):
            continue
        if "P0D_PREP_READY_V1" not in (pr.get("body") or ""):
            continue
        item = {"pr": number, "title": pr.get("title", ""), "status": "REJECTED", "reason": "UNKNOWN",
                "updated_at": pr.get("updated_at", "")}
        examined.append(item)
        if pr.get("draft") or pr.get("state") != "open":
            item["reason"] = "DRAFT_OR_CLOSED"
            continue
        base, head = pr.get("base") or {}, pr.get("head") or {}
        sha = head.get("sha", "")
        if base.get("ref") != OFFICIAL or base.get("sha") != official_sha:
            item["reason"] = "NOT_BASED_ON_LATEST_OFFICIAL_RC"
            continue
        if (head.get("repo") or {}).get("full_name") != repo or not PIN.fullmatch(sha):
            item["reason"] = "UNTRUSTED_SOURCE_OR_HEAD"
            continue
        try:
            m = manifest(pr.get("body") or "")
        except ValueError as exc:
            item["reason"] = str(exc)
            continue
        item.update({"head": sha, "features": m["features"], "source_lock": m["source_lock"]})
        if m["head"] != sha or m["base"] != official_sha:
            item["reason"] = "STALE_PREP_MANIFEST_SHA"
            continue
        compare = api(f"/repos/{repo}/compare/{official_sha}...{sha}")
        if compare.get("behind_by") != 0 or compare.get("ahead_by", 0) <= 0 or compare.get("status") != "ahead":
            item["reason"] = "NOT_A_FAST_FORWARD_FROM_OFFICIAL"
            continue
        runs = api(f"/repos/{repo}/actions/runs?head_sha={sha}&per_page=100").get("workflow_runs", [])
        matching = [x for x in runs if x.get("head_sha") == sha and x.get("name") == RUN_NAME]
        matching.sort(key=lambda x: (x.get("created_at", ""), x.get("id", 0)), reverse=True)
        if not matching or matching[0].get("status") != "completed" or matching[0].get("conclusion") != "success":
            item["reason"] = "LATEST_SAME_HEAD_FULL_RC_CI_NOT_GREEN"
            continue
        item["status"] = "READY_FOR_SOLE_WRITER_REVIEW"
        item["reason"] = "EXACT_HEAD_FF_AND_BUILD_GREEN; LIVE_SECURITY_CAS_REVIEW_REQUIRED"
        commit = api(f"/repos/{repo}/commits/{sha}")
        stamp = ((commit.get("commit") or {}).get("committer") or {}).get("date", "")
        if not stamp:
            item["status"] = "REJECTED"
            item["reason"] = "COMMIT_TIMESTAMP_UNVERIFIED"
            continue
        item["commit_time"] = stamp
        item["ci_run"] = matching[0]["id"]
        item["ci_url"] = matching[0].get("html_url")
        item["ahead_commits"] = compare["ahead_by"]
        item["rollback"] = m["rollback"]
    ready = [x for x in examined if x["status"] == "READY_FOR_SOLE_WRITER_REVIEW"]
    ready.sort(key=lambda x: (x["commit_time"], x["pr"]), reverse=True)
    selected, consumed = [], set()
    for item in ready:
        if set(item["features"]) & consumed:
            item["status"] = "SUPERSEDED_SAME_FEATURE"
            item["reason"] = "NEWER_VERIFIED_CANDIDATE_WINS"
        else:
            selected.append(item)
            consumed.update(item["features"])
    examined.sort(key=lambda x: x["pr"])
    return {"schema": "P0D_TWO_LANES_V1", "official_head": official_sha,
            "ready_count": len(selected), "selected": selected, "all_labeled_candidates": examined,
            "next_owner": "SOLE_AUTHENTICATED_ISSUE_220_INTEGRATOR_CAS_ONLY",
            "no_auto_merge": True, "studio_and_fun_not_inferred": True}

def read_queue(api: Callable[[str], Any], repo: str = REPO) -> dict[str, Any]:
    ref = api(f"/repos/{repo}/git/ref/heads/{OFFICIAL}")
    official_sha = (ref.get("object") or {}).get("sha", "")
    prs = []
    for page in range(1, 4):
        page_rows = api(f"/repos/{repo}/pulls?state=open&per_page=100&page={page}")
        prs += page_rows
        if len(page_rows) < 100:
            break
    return choose_latest(official_sha, prs, api, repo)

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default=REPO)
    p.add_argument("--out", default="-")
    p.add_argument("--fixture", help="offline fixture JSON, no network")
    opts = p.parse_args(argv)
    if opts.fixture:
        with open(opts.fixture, encoding="utf-8") as f:
            paths = json.load(f)["api"]
        result = read_queue(lambda path: paths[path], opts.repo)
    else:
        result = read_queue(GitHubReadOnly(os.environ.get("GITHUB_TOKEN", "")), opts.repo)
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if opts.out == "-":
        sys.stdout.write(body)
    else:
        with open(opts.out, "w", encoding="utf-8") as f:
            f.write(body)
    print(f"P0D_TWO_LANE_QUEUE_PASS official={result['official_head']} ready={result['ready_count']} NO_AUTOMERGE", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
