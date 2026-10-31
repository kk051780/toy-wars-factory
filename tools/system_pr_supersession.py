"""Read-only, fail-closed advisory for draft PRs possibly superseded by integration.

This reducer does not fetch GitHub, authenticate adoption receipts, change queue
eligibility, close PRs, merge code, or grant a lease. The caller must obtain
fresh GitHub snapshots and independently audit any suggested supersession.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import PurePosixPath
import re

SHA = re.compile(r"[0-9a-f]{40}\\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\\Z")
PATH = re.compile(r"[A-Za-z0-9_./-]+\\Z")


class UnsafeEvidence(ValueError):
    pass


def need(condition, reason):
    if not condition:
        raise UnsafeEvidence(reason)


def sha(value):
    need(type(value) is str and SHA.fullmatch(value) is not None, "invalid SHA")
    return value


def number(value):
    need(type(value) is int and value > 0, "invalid PR number")
    return value


def instant(value):
    need(type(value) is str, "missing observed time")
    try:
        at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise UnsafeEvidence("invalid observed time") from None
    need(at.tzinfo is not None, "naive observed time")
    return at


def paths(value):
    need(type(value) is list and 0 < len(value) <= 200, "missing or oversized changed path list")
    result = []
    for item in value:
        need(type(item) is str and 0 < len(item) <= 256
             and PATH.fullmatch(item) is not None and "\\\\" not in item
             and not item.startswith("/") and not any(
                 part in ("", ".", "..") or part.startswith(".")
                 for part in PurePosixPath(item).parts
             ), "unsafe path")
        result.append(item)
    need(len(result) == len(set(result)), "duplicate changed path")
    return frozenset(result)


def result(status, **extra):
    return dict(status=status, mode="READ_ONLY_PR_SUPERSESSION_ADVISORY",
                may_close=False, may_merge=False, may_skip_review=False,
                may_write=False, independently_verified=False, **extra)


def evaluate(data):
    """Suggest exact-head candidates without converting metadata into authority.

    Receipt truth, Git ancestry and actual behavioral equivalence are deliberately
    NOT established here; even a complete path manifest is a review hint only.
    """
    try:
        need(type(data) is dict and set(data) == {
            "repository", "main_head", "observed_at", "open_prs", "adoptions"
        }, "invalid snapshot fields")
        repo = data["repository"]
        need(type(repo) is str and REPO.fullmatch(repo) is not None,
             "invalid repository")
        current_main = sha(data["main_head"])
        now = instant(data["observed_at"])
        drafts, adoptions = data["open_prs"], data["adoptions"]
        need(type(drafts) is list and len(drafts) <= 300, "invalid PR inventory")
        need(type(adoptions) is list and len(adoptions) <= 300,
             "invalid adoption inventory")
        known = {}
        for pr in drafts:
            need(type(pr) is dict and set(pr) == {
                "number", "head", "state", "base", "changed_paths"
            }, "invalid PR snapshot")
            n = number(pr["number"])
            sha(pr["head"])
            need(pr["state"] == "open" and type(pr["base"]) is str
                 and pr["base"], "invalid open PR state or base")
            p = paths(pr["changed_paths"])
            need(n not in known, "duplicate PR inventory")
            known[n] = dict(head=pr["head"], paths=p)
        receipts = {}
        for row in adoptions:
            need(type(row) is dict and set(row) == {
                "source_pr", "source_head", "via_pr", "via_merge_sha",
                "observed_main", "observed_at", "main_contains_merge",
                "adopted_paths", "evidence_url"
            }, "invalid adoption receipt")
            n, via = number(row["source_pr"]), number(row["via_pr"])
            need(via != n, "self adoption not independently attributable")
            sha(row["source_head"])
            sha(row["via_merge_sha"])
            sha(row["observed_main"])
            need(instant(row["observed_at"]) <= now, "future adoption observation")
            need(type(row["main_contains_merge"]) is bool, "invalid ancestry hint")
            adopted = paths(row["adopted_paths"])
            need(row["evidence_url"] == f"https://github.com/{repo}/pull/{via}",
                 "unscoped evidence URL")
            need(n not in receipts, "duplicate/conflicting adoption receipts")
            receipts[n] = (row, adopted)
        items = []
        for n in sorted(known):
            pr = known[n]
            receipt = receipts.get(n)
            if receipt is None:
                items.append({"pr": n, "status": "NO_ADOPTION_RECEIPT",
                              "needs_independent_review": True})
                continue
            row, adopted = receipt
            if row["source_head"] != pr["head"]:
                status = "STALE_SOURCE_HEAD"
            elif row["observed_main"] != current_main:
                status = "STALE_MAIN_HEAD"
            elif row["main_contains_merge"] is not True:
                status = "ANCESTRY_UNPROVEN"
            elif not pr["paths"].issubset(adopted):
                status = "INCOMPLETE_PATH_COVERAGE"
            else:
                status = "POSSIBLY_SUPERSEDED_REVIEW_ONLY"
            items.append({"pr": n, "status": status, "needs_independent_review": True,
                          "source_head": pr["head"], "via_pr": row["via_pr"],
                          "evidence_url": row["evidence_url"]})
        candidates = sum(row["status"] == "POSSIBLY_SUPERSEDED_REVIEW_ONLY"
                         for row in items)
        return result("ADVISORY_READY", observed_main=current_main,
                      candidates=candidates, scanned=len(items), items=items,
                      warning="Caller-supplied receipts are not provider-attested; "
                              "never auto-close, auto-merge or suppress independent review.")
    except (UnsafeEvidence, TypeError, AttributeError, KeyError, OverflowError) as ex:
        return result("WAIT_METADATA", reason=str(ex))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    args = p.parse_args()
    with open(args.input, encoding="utf-8") as handle:
        payload = json.load(handle)
    print(json.dumps(evaluate(payload), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
