"""P0-C Windows one-shot READ-ONLY GitHub comment receipt preflight.

This program NEVER starts Codex, Roblox Studio, PowerShell, shell processes, or a
background service. It makes one GitHub HTTPS GET and prints a diagnostic only.
Command intent and GitHub metadata cannot grant code execution authority.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from urllib.request import Request, build_opener, HTTPRedirectHandler

from tools.system_p0c_command_intake import inspect_untrusted_intent

REPO = "kk051780/toy-wars-factory"
ISSUE = 204
HOST = "DESKTOP-EASS441"
APP_SLUG = "chatgpt-codex-connector"
OWNER_LOGIN = "kk051780"
PREFIX = "P0C_READONLY_INTENT_V1\n"
MAX_RESPONSE_BYTES = 16384
MAX_COMMENT_ID = 10 ** 16
GITHUB_URL_ROOT = "https://api.github.com/repos/" + REPO


def _result(reason, *, status="REJECTED_NO_PC_ACTION", comment_id=None, work_id=None, metadata_matched=False):
    return {
        "status": status, "reason": reason, "comment_id": comment_id, "work_id": work_id,
        "github_metadata_matched": metadata_matched,
        "github_identity_cryptographically_verified": False,
        "owner_authorized": False, "codex_execution_authorized": False,
        "may_run_commands": False, "pc_action_executed": False,
        "is_background_receiver": False,
    }


def _no_duplicates(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError("duplicate JSON field")
        out[key] = value
    return out


def api_url(comment_id):
    if type(comment_id) is not int or not 0 < comment_id < MAX_COMMENT_ID:
        raise ValueError("invalid comment id")
    return GITHUB_URL_ROOT + "/issues/comments/" + str(comment_id)


class _NoRedirect(HTTPRedirectHandler):
    """Never forward an HTTP request to any redirected endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_comment_once(comment_id):
    """One GET only, fixed host and path, no redirects accepted."""
    url = api_url(comment_id)
    request = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "TOY-WARS-P0C-ReadOnly-Preflight/1",
    }, method="GET")
    with build_opener(_NoRedirect()).open(request, timeout=10) as response:
        if response.geturl() != url or response.status != 200:
            raise ValueError("unexpected GitHub response URL/status")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("oversized GitHub response")
    obj = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_no_duplicates)
    if type(obj) is not dict:
        raise ValueError("nonobject GitHub response")
    return obj


def examine_comment(comment, *, comment_id, now_utc, observed_host, seen_work_ids=()):
    """Check provider-supplied metadata, then parse intent. Still NO AUTHORITY."""
    try:
        expected_url = api_url(comment_id)
        if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
            return _result("untrusted clock", comment_id=comment_id)
        if observed_host != HOST:
            return _result("not pinned PC host", comment_id=comment_id)
        if type(comment) is not dict:
            return _result("not GitHub object", comment_id=comment_id)
        user = comment.get("user")
        app = comment.get("performed_via_github_app")
        if type(comment.get("id")) is not int or comment["id"] != comment_id:
            return _result("comment id mismatch", comment_id=comment_id)
        if comment.get("url") != expected_url:
            return _result("wrong canonical comment endpoint", comment_id=comment_id)
        if comment.get("issue_url") != GITHUB_URL_ROOT + "/issues/" + str(ISSUE):
            return _result("wrong issue", comment_id=comment_id)
        if comment.get("html_url") != (
            "https://github.com/" + REPO + "/issues/" + str(ISSUE)
            + "#issuecomment-" + str(comment_id)
        ):
            return _result("wrong HTML comment URL", comment_id=comment_id)
        if type(user) is not dict or user.get("login") != OWNER_LOGIN or user.get("type") != "User":
            return _result("wrong GitHub actor", comment_id=comment_id)
        if comment.get("author_association") != "OWNER":
            return _result("not repository owner attribution", comment_id=comment_id)
        if type(app) is not dict or app.get("slug") != APP_SLUG:
            return _result("not ChatGPT GitHub connector attribution", comment_id=comment_id)
        if (type(comment.get("created_at")) is not str
                or comment["created_at"] != comment.get("updated_at")):
            return _result("edited or missing original timestamp", comment_id=comment_id)
        body = comment.get("body")
        if type(body) is not str or not body.startswith(PREFIX):
            return _result("not dedicated P0C intent format", comment_id=comment_id)
        remainder = body[len(PREFIX):]
        if not remainder or remainder.strip() != remainder:
            return _result("extra body content", comment_id=comment_id)
        inspected = inspect_untrusted_intent(
            remainder, now_utc=now_utc, expected_host=HOST,
            seen_work_ids=seen_work_ids,
        )
        if not inspected["read_only_intent_valid"]:
            return _result("invalid untrusted intent: " + inspected["reason"], comment_id=comment_id)
        data = json.loads(remainder, object_pairs_hook=_no_duplicates)
        created = datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        issued = datetime.strptime(data["issued_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        expires = datetime.strptime(data["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if not issued <= created < expires:
            return _result("GitHub create time outside intent bounds", comment_id=comment_id)
        if now_utc.astimezone(timezone.utc) < created:
            return _result("provider comment created in future", comment_id=comment_id)
        return _result(
            "GitHub comment format and metadata match; NO Codex execution",
            status="READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION",
            comment_id=comment_id, work_id=data["work_id"], metadata_matched=True,
        )
    except (ValueError, TypeError, KeyError, OverflowError):
        return _result("malformed source metadata", comment_id=comment_id)


def run_once(comment_id, *, now_utc=None, observed_host=None, fetcher=fetch_comment_once):
    """Manual opt-in, one fetch, no side effects except stdout from CLI."""
    try:
        api_url(comment_id)
    except ValueError:
        return _result("invalid comment id")
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    if observed_host is None:
        observed_host = platform.node().upper()
    if sys.platform != "win32" and fetcher is fetch_comment_once:
        return _result("one-shot PC CLI requires Windows", comment_id=comment_id)
    if observed_host != HOST:
        return _result("host mismatch before network", comment_id=comment_id)
    try:
        comment = fetcher(comment_id)
    except Exception as error:
        return _result(
            "GitHub GET failed without execution: " + type(error).__name__,
            comment_id=comment_id,
        )
    return examine_comment(comment, comment_id=comment_id, now_utc=now_utc, observed_host=observed_host)


def main(argv=None):
    parser = argparse.ArgumentParser(description="C2A: one-shot read-only P0C GitHub receipt, no execution")
    parser.add_argument("--comment-id", type=int, required=True, help="Pinned GitHub comment ID")
    args = parser.parse_args(argv)
    result = run_once(args.comment_id)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0 if result["status"] == "READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
