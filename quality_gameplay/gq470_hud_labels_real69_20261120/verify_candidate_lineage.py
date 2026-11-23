#!/usr/bin/env python3
"""Bind historical HUD preparation to the current PR/RC without claiming adoption.

The immutable post-915 input remains pinned by the caller. This fence verifies
that its ancestor is still in the live RC lineage and that this checkout is the
actual current PR merge, or an explicit dispatch on the live canonical RC.
It does not certify that the historical preparation output is the current game.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

REPOSITORY = "kk051780/toy-wars-factory"
CANONICAL_BRANCH = "rc/p0d-s1-kids-rc01"
AUTHOR_BASE = "6c2338b44db1c772bab0d688b2aece2e3aa8aae2"
SHA = re.compile(r"[0-9a-f]{40}\Z")


class LineageError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise LineageError(reason)


def sha(value: object, field: str) -> str:
    require(isinstance(value, str) and SHA.fullmatch(value) is not None,
            "INVALID_SHA_" + field)
    return value


def context(env: dict, event: dict) -> dict:
    require(env.get("GITHUB_REPOSITORY") == REPOSITORY, "WRONG_REPOSITORY")
    require(event.get("repository", {}).get("full_name") == REPOSITORY,
            "WRONG_EVENT_REPOSITORY")
    build = sha(env.get("GITHUB_SHA"), "BUILD")
    name = env.get("GITHUB_EVENT_NAME")
    if name == "pull_request":
        pr = event.get("pull_request")
        require(isinstance(pr, dict), "MISSING_PULL_REQUEST")
        number = event.get("number")
        require(type(number) is int and number > 0 and pr.get("number") == number,
                "INVALID_PULL_REQUEST_NUMBER")
        require(env.get("GITHUB_REF") == f"refs/pull/{number}/merge", "WRONG_PR_REF")
        base, head = pr.get("base", {}), pr.get("head", {})
        require(base.get("repo", {}).get("full_name") == REPOSITORY
                and head.get("repo", {}).get("full_name") == REPOSITORY,
                "WRONG_PR_REPOSITORY")
        require(base.get("ref") == CANONICAL_BRANCH, "WRONG_PR_BASE_BRANCH")
        return {"event": name, "number": number, "build": build,
                "base": sha(base.get("sha"), "PR_BASE"),
                "head": sha(head.get("sha"), "PR_HEAD")}
    require(name == "workflow_dispatch", "UNSUPPORTED_EVENT")
    require(env.get("GITHUB_REF") == f"refs/heads/{CANONICAL_BRANCH}",
            "DISPATCH_NOT_CANONICAL")
    return {"event": name, "number": None, "build": build,
            "base": build, "head": build}


def compare_fence(comparison: dict, ancestor: str, descendant: str,
                  allow_identical: bool, label: str) -> None:
    require(isinstance(comparison, dict), label + "_MISSING_COMPARISON")
    expected = "identical" if ancestor == descendant else "ahead"
    require(allow_identical or ancestor != descendant, label + "_NO_CHANGE")
    require(comparison.get("status") == expected, label + "_NOT_DESCENDANT")
    require(comparison.get("base_commit", {}).get("sha") == ancestor,
            label + "_WRONG_BASE")
    require(comparison.get("merge_base_commit", {}).get("sha") == ancestor,
            label + "_DIVERGENT_MERGE_BASE")


def verify(env: dict, event: dict, live_head: str, author_lineage: dict,
           head_lineage: dict | None, build_commit: dict, checkout_sha: str) -> dict:
    ctx = context(env, event)
    live = sha(live_head, "LIVE_RC")
    require(sha(checkout_sha, "CHECKOUT") == ctx["build"], "CHECKOUT_SHA_MISMATCH")
    require(build_commit.get("sha") == ctx["build"], "BUILD_COMMIT_MISMATCH")
    require(ctx["base"] == live, "STALE_PR_BASE_OR_DISPATCH_HEAD")
    compare_fence(author_lineage, AUTHOR_BASE, live, True, "AUTHOR")
    if ctx["event"] == "pull_request":
        compare_fence(head_lineage, live, ctx["head"], False, "PR_HEAD")
        parents = build_commit.get("parents")
        require(isinstance(parents, list)
                and [p.get("sha") for p in parents] == [live, ctx["head"]],
                "SYNTHETIC_MERGE_PARENTS_MISMATCH")
        require(ctx["build"] not in (live, ctx["head"]), "NOT_A_PR_MERGE_CHECKOUT")
    return {
        "schema": "GQ470_HUD_HISTORICAL_PREP_LINEAGE_V1",
        "status": "PASS_HISTORICAL_SOURCE_PREP_ONLY",
        "repository": REPOSITORY,
        "event": ctx["event"],
        "pull_request": ctx["number"],
        "immutable_author_base": AUTHOR_BASE,
        "observed_canonical_head": live,
        "candidate_source_head": ctx["head"],
        "actual_checkout_head": ctx["build"],
        "formal_rc_adoption_proven": False,
        "prepared_output_is_current_rc_game": False,
        "studio": "NOT_TESTED",
        "owner_accepted": False,
    }


def api(path: str) -> dict:
    completed = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/{path}"],
                               check=True, capture_output=True, text=True)
    result = json.loads(completed.stdout)
    require(isinstance(result, dict), "INVALID_API_RESPONSE")
    return result


def run_live(env: dict, event: dict) -> dict:
    ctx = context(env, event)
    live = sha(api(f"git/ref/heads/{CANONICAL_BRANCH}").get("object", {}).get("sha"),
               "LIVE_RC")
    # Fail before additional API requests if the PR base or dispatch head moved.
    require(ctx["base"] == live, "STALE_PR_BASE_OR_DISPATCH_HEAD")
    author_lineage = api(f"compare/{AUTHOR_BASE}...{live}")
    head_lineage = (api(f"compare/{live}...{ctx['head']}")
                    if ctx["event"] == "pull_request" else None)
    build_commit = api(f"commits/{ctx['build']}")
    checkout = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    receipt = verify(env, event, live, author_lineage, head_lineage, build_commit, checkout)
    require(api(f"git/ref/heads/{CANONICAL_BRANCH}").get("object", {}).get("sha") == live,
            "CANONICAL_HEAD_MOVED_DURING_CHECK")
    receipt["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "OUTPUT_ALREADY_EXISTS")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    receipt = run_live(dict(os.environ), event)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print("GQ470_HUD_LIVE_LINEAGE_PASS_HISTORICAL_PREP_NOT_FORMAL", json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
