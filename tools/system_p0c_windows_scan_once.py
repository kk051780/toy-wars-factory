"""P0-C Windows one-shot scan of GitHub intent comments; NEVER executes tasks.

A local operator must explicitly run this command. It never stays resident,
starts a child process, writes a file, calls Codex, or manipulates Studio.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from urllib.request import Request, build_opener
from tools.system_p0c_windows_receive_once import (
    HOST, PREFIX, REPO, ISSUE, _NoRedirect, _no_duplicates, examine_comment,
)

PAGE_SIZE = 100
MAX_PAGES = 5
MAX_PAGE_BYTES = 2000000
ROOT = "https://api.github.com/repos/" + REPO


def _blocked(reason, *, page_count=0):
    return {
        "status": "READ_ONLY_RECEIVER_BLOCKED",
        "reason": reason, "pages_checked": page_count,
        "github_metadata_matched": False,
        "owner_authorized": False, "codex_execution_authorized": False,
        "may_run_commands": False, "pc_action_executed": False,
        "is_background_receiver": False,
    }


def page_url(page):
    if type(page) is not int or page < 1 or page > MAX_PAGES:
        raise ValueError("page outside bounded range")
    return ROOT + "/issues/" + str(ISSUE) + "/comments?per_page=100&page=" + str(page)


def fetch_issue_comments_page(page, *, token, opener=None):
    """GET only an allowlisted GitHub path; reject every redirect before following."""
    url = page_url(page)
    if not isinstance(token, str) or not token or "\n" in token or "\r" in token:
        raise ValueError("missing or invalid GitHub read token")
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "TOY-WARS-P0C-ReadOnly-Scan/1",
        "Authorization": "Bearer " + token,
    }, method="GET")
    opener = opener or build_opener(_NoRedirect())
    with opener.open(request, timeout=10) as response:
        if response.status != 200 or response.geturl() != url:
            raise ValueError("not same GitHub endpoint")
        payload = response.read(MAX_PAGE_BYTES + 1)
        if len(payload) > MAX_PAGE_BYTES:
            raise ValueError("oversized comments page")
    obj = json.loads(payload.decode("utf-8", errors="strict"),
                     object_pairs_hook=_no_duplicates)
    if type(obj) is not list or len(obj) > PAGE_SIZE:
        raise ValueError("malformed comments page")
    if any(type(item) is not dict for item in obj):
        raise ValueError("malformed comment item")
    return obj


def inspect_issue_intents(*, fetcher, observed_host, now_utc, seen_work_ids=()):
    """Review at most five pages, return latest valid diagnostic (never execute)."""
    if observed_host != HOST:
        return _blocked("host mismatch before network")
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
        return _blocked("invalid clock before network")
    candidates = []
    pages = 0
    try:
        for page in range(1, MAX_PAGES + 1):
            items = fetcher(page)
            if type(items) is not list or len(items) > PAGE_SIZE:
                raise ValueError("malformed scan page")
            if any(type(item) is not dict for item in items):
                raise ValueError("malformed scanned comment")
            pages += 1
            for comment in items:
                body = comment.get("body")
                if not isinstance(body, str) or not body.startswith(PREFIX):
                    continue
                comment_id = comment.get("id")
                if type(comment_id) is not int:
                    continue
                decision = examine_comment(
                    comment, comment_id=comment_id, now_utc=now_utc,
                    observed_host=observed_host, seen_work_ids=seen_work_ids,
                )
                if decision["status"] == "READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION":
                    candidates.append(decision)
            if len(items) < PAGE_SIZE:
                break
        else:
            # Never present an incomplete scan as the latest comment.
            return _blocked("bounded pagination incomplete", page_count=pages)
    except Exception as exc:
        # Do not leak tokens or raw response body into diagnostic logs.
        return _blocked("GitHub read failed: " + type(exc).__name__, page_count=pages)
    if not candidates:
        return {
            **_blocked("no active validated P0C intent", page_count=pages),
            "status": "READ_ONLY_NO_VALID_INTENT",
        }
    # Highest GitHub comment id within bounded complete scan is the latest.
    selected = max(candidates, key=lambda x: x["comment_id"])
    return {
        **selected, "pages_checked": pages,
        "validated_candidates": len(candidates),
        "is_background_receiver": False,
    }


def run_scan_once(*, now_utc=None, observed_host=None, token=None,
                  fetcher=None):
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if observed_host is None:
        observed_host = platform.node().upper()
    if observed_host != HOST:
        return _blocked("host mismatch before network")
    if fetcher is None:
        if sys.platform != "win32":
            return _blocked("network scan only allowed on Windows")
        if token is None:
            token = os.environ.get("GITHUB_TOKEN")
        if not token:
            return _blocked("GitHub read credential absent; no network request")
        fetcher = lambda page: fetch_issue_comments_page(page, token=token)
    return inspect_issue_intents(
        fetcher=fetcher, observed_host=observed_host, now_utc=now_utc,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="P0-C single read-only GitHub queue scan, no Codex execution")
    parser.add_argument("--scan-once", action="store_true", required=True)
    parser.parse_args(argv)
    result = run_scan_once()
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["status"] == "READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
