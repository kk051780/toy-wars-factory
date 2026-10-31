#!/usr/bin/env python3
"""Bounded GitHub GET collector for PR #168's read-only parallel-file advisory.

Runs only with a separately authorized read-only GitHub credential on a trusted
host. A positive result is NOT a provider-signed witness, source review, lease,
merge, runtime scheduling or write permission. Test callbacks never attest the
real GitHub service. No auto retries, token persistence, dispatch or writes.
"""
from __future__ import annotations

import json
import os
import re
from urllib import request

from system_parallel_pr_path_audit import audit, from_rest_observations, validate_candidate

REPO = "kk051780/toy-wars-factory"
REPO_ID = 1431683395
ROOT = "https://api.github.com/repos/" + REPO
MAIN_REF = ROOT + "/git/ref/heads/main"
OPEN_PRS = ROOT + "/pulls?state=open&per_page=100&page=1"
MAX_PR_COUNT = 99
MAX_RESPONSE_BYTES = 2_000_000
MAX_GET_COUNT = 104  # repo + main + two PR lists + main + up to 99 PR file pages
_API_VERSION = "2022-11-28"
_FILE_URL = re.compile(re.escape(ROOT) + r"/pulls/([1-9][0-9]*)/files\?per_page=100&page=1\Z")


class CollectorHold(ValueError):
    pass


def require(check, code):
    if not check:
        raise CollectorHold(code)


def _pairs_unique(pairs):
    row = {}
    for k, v in pairs:
        require(k not in row, "DUPLICATE_JSON_FIELD")
        row[k] = v
    return row


def _reject_nonfinite(_):
    raise CollectorHold("NONFINITE_JSON")


def parse_json(raw):
    require(type(raw) is bytes and len(raw) <= MAX_RESPONSE_BYTES, "INVALID_RESPONSE_BYTES")
    try:
        return json.loads(raw, object_pairs_hook=_pairs_unique, parse_constant=_reject_nonfinite)
    except CollectorHold:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise CollectorHold("INVALID_GITHUB_JSON") from None


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class GitHubGet:
    """Fixed URL + GET-only transport; host must independently attest identity."""
    def __init__(self, token, *, opener=None):
        require(type(token) is str and 0 < len(token) <= 4096, "TOKEN_NOT_AVAILABLE")
        self._token = token
        self._open = opener or request.build_opener(NoRedirect()).open

    @staticmethod
    def allowed_url(url):
        return type(url) is str and (
            url in (ROOT, MAIN_REF, OPEN_PRS) or _FILE_URL.fullmatch(url) is not None
        )

    def __call__(self, url):
        require(self.allowed_url(url), "URL_NOT_ALLOWLISTED")
        req = request.Request(url, method="GET", headers={
            "Authorization": "Bearer " + self._token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": "twf-parallel-pr-readonly-advisory",
        })
        try:
            with self._open(req, timeout=12) as resp:
                require(resp.getcode() == 200, "GITHUB_NON_200")
                content = resp.read(MAX_RESPONSE_BYTES + 1)
                require(len(content) <= MAX_RESPONSE_BYTES, "RESPONSE_TOO_LARGE")
                return parse_json(content)
        except CollectorHold:
            raise
        except Exception:
            raise CollectorHold("GITHUB_GET_FAILED") from None


def _read_main(reader):
    data = reader(MAIN_REF)
    require(type(data) is dict and data.get("ref") == "refs/heads/main" and
            type(data.get("object")) is dict and
            data["object"].get("type") == "commit" and
            type(data["object"].get("sha")) is str and
            re.fullmatch(r"[a-f0-9]{40}", data["object"]["sha"]) is not None,
            "INVALID_MAIN_REF")
    return data["object"]["sha"]


def _read_pr_list(reader):
    rows = reader(OPEN_PRS)
    require(type(rows) is list and len(rows) <= MAX_PR_COUNT,
            "PR_LIST_PAGINATION_REQUIRED")
    seen = set()
    for row in rows:
        require(type(row) is dict and type(row.get("number")) is int and
                row["number"] > 0 and row["number"] not in seen,
                "INVALID_PR_NUMBER")
        seen.add(row["number"])
    return rows


def collect(reader, candidate):
    """Read original GitHub observations twice and return advisory-only result.

    Caller supplies a bounded token-bearing read-only GET; passing fake callback
    evidence does NOT prove any real host, credential, task ID or API response.
    This adapter never writes or grants workflow/lease/merge permissions.
    """
    require(callable(reader), "READER_REQUIRED")
    # Validate candidate before any remote call; invalid paths never trigger GET.
    try:
        validate_candidate(candidate)
    except (ValueError, TypeError, KeyError):
        raise CollectorHold("INVALID_CANDIDATE") from None
    meta = reader(ROOT)
    require(type(meta) is dict and type(meta.get("id")) is int and
            meta["id"] == REPO_ID and meta.get("full_name") == REPO and
            meta.get("private") is True, "REPOSITORY_ID_MISMATCH")
    before_main = _read_main(reader)
    before_prs = _read_pr_list(reader)
    by_pr = {}
    for row in before_prs:
        n = row["number"]
        data = reader(f"{ROOT}/pulls/{n}/files?per_page=100&page=1")
        require(type(data) is list and 0 < len(data) < 100,
                "FILE_LIST_PAGINATION_OR_MISSING")
        by_pr[str(n)] = data
    after_prs = _read_pr_list(reader)
    after_main = _read_main(reader)
    # The pure reducer checks same-repo PR origin and unchanged heads/bases.
    try:
        snapshot = from_rest_observations(
            repository=REPO, main_before_sha=before_main,
            main_after_sha=after_main, candidate=candidate,
            prs_before=before_prs, prs_after=after_prs,
            changed_files_by_pr=by_pr)
        report = audit(snapshot)
    except (ValueError, TypeError, KeyError):
        raise CollectorHold("ORIGINAL_SNAPSHOT_MISMATCH") from None
    report.update({
        "adapter": "ORIGINAL_GITHUB_GET_CALLBACK_ONLY",
        "host_provider_authentication": "NOT_ATTESTED",
        "provider_authenticated": False,
        "may_dispatch": False, "may_merge": False,
        "may_write": False, "may_publish_roblox": False,
        "original_repo_id_matched": True,
        "same_main_and_pr_inventory_two_pass": True,
        "get_count": len(before_prs) + 5,
    })
    return report


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", required=True, help="JSON candidate {branch,paths}")
    args = p.parse_args()
    try:
        with open(args.candidate, encoding="utf-8") as handle:
            candidate = json.load(handle)
        report = collect(GitHubGet(os.environ.get("GITHUB_TOKEN", "")), candidate)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 1 if report["decision"] == "BLOCK_OVERLAP" else 0
    except (CollectorHold, OSError, TypeError, ValueError, KeyError) as exc:
        reason = str(exc) if isinstance(exc, CollectorHold) else "INVALID_INPUT_OR_READER"
        print(json.dumps({"status": "WAIT_METADATA", "reason": reason,
                          "provider_authenticated": False, "may_write": False,
                          "may_merge": False, "may_dispatch": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
