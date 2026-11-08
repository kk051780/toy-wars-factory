"""P0-C no-execution ACK-only candidate, NOT a deployed Windows receiver.

No network occurs unless a caller explicitly opts into a one-time receipt
POST with an existing OWNER-approved least-privilege GitHub credential.
A GitHub ACK is not a signature or permission to execute commands.
"""
from __future__ import annotations

import hashlib
import json
import re
from urllib.request import Request, build_opener, HTTPRedirectHandler

from tools.system_p0c_windows_receive_once import (
    HOST, REPO, ISSUE, PREFIX, _no_duplicates, examine_comment,
    fetch_comment_once,
)

ROOT = "https://api.github.com/repos/" + REPO
POST_URL = ROOT + "/issues/" + str(ISSUE) + "/comments"
ACK_PREFIX = "P0C_READONLY_RECEIPT_ACK_V1\n"
SHA = re.compile(r"[a-f0-9]{40}\Z")
MAX_BYTES = 65536


class AckBlocked(Exception):
    """Fail closed without exposing credentials or untrusted response content."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def make_ack_only(comment, *, now_utc, observed_host, expected_main_sha):
    """Construct bounded no-execution receipt; no network or local I/O."""
    if observed_host != HOST or not isinstance(expected_main_sha, str) or not SHA.fullmatch(expected_main_sha):
        raise AckBlocked("PINNED_HOST_OR_MAIN_SHA_REQUIRED")
    if type(comment) is not dict or type(comment.get("id")) is not int:
        raise AckBlocked("INVALID_SOURCE_COMMENT")
    decision = examine_comment(
        comment, comment_id=comment["id"], now_utc=now_utc,
        observed_host=observed_host,
    )
    if decision.get("status") != "READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION":
        raise AckBlocked("SOURCE_PING_NOT_VALID")
    try:
        body = comment["body"]
        data = json.loads(body[len(PREFIX):], object_pairs_hook=_no_duplicates)
        if data.get("main_sha") != expected_main_sha:
            raise AckBlocked("MAIN_SHA_MISMATCH")
        result = {
            "schema": 1, "kind": "UNATTESTED_PING_RECEIPT_CANDIDATE_NO_EXECUTION",
            "repo": REPO, "source_issue": ISSUE,
            "source_comment_id": source["id"],
            "work_id": data["work_id"], "host_claim": HOST,
            "pinned_main_sha": expected_main_sha,
            "source_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "host_attested": False, "host_origin_verified": False,
            "github_app_proves_owner_pc_authorization": False,
            "owner_execution_authorized": False,
            "codex_executed": False, "studio_executed": False,
            "git_source_written": False,
        }
        text = ACK_PREFIX + json.dumps(result, sort_keys=True, separators=(",", ":"))
        if len(text.encode("utf-8")) > 1300:
            raise AckBlocked("ACK_EXCEEDS_SIZE_LIMIT")
        return text
    except AckBlocked:
        raise
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise AckBlocked("MALFORMED_SOURCE_INTENT") from None


def post_ack_only_once(comment, *, now_utc, observed_host,
                       expected_main_sha, owner_opt_in=False,
                       approved_issues_write_token=None, transport=None,
                       source_fetcher=fetch_comment_once):
    """At most one POST attempt; no automatic retries or arbitrary commands.

    A token / opt-in permits only a receipt write, NEVER code execution.
    GitHub issue comments cannot enforce global exactly-once delivery.
    """
    if owner_opt_in is not True:
        raise AckBlocked("OWNER_OPT_IN_REQUIRED")
    # Caller opt-in is an assertion, not proof of original OWNER identity.
    # This transport can only acknowledge observation, never authorize PC work.
    token = approved_issues_write_token
    if (not isinstance(token, str) or not 12 <= len(token) <= 2048
            or any(c in token for c in ("\n", "\r", "\x00"))):
        raise AckBlocked("APPROVED_ISSUES_WRITE_TOKEN_REQUIRED")
    # Caller dictionaries are untrusted, even when their fields appear canonical.
    # Re-fetch the comment from the pinned GitHub REST endpoint (GET only).
    # This runs after both opt-in/token gates and before any POST.
    if type(comment) is not dict or type(comment.get("id")) is not int:
        raise AckBlocked("SOURCE_COMMENT_ID_REQUIRED")
    try:
        source = source_fetcher(comment["id"])
    except Exception:
        raise AckBlocked("GITHUB_SOURCE_GET_FAILED_NO_POST") from None
    if type(source) is not dict or type(source.get("id")) is not int or source["id"] != comment["id"]:
        raise AckBlocked("GITHUB_SOURCE_ID_MISMATCH_NO_POST")
    # Prevent a stale or edited caller-supplied body from being silently
    # interpreted as a new provider-verified receipt.
    if comment.get("body") != source.get("body"):
        raise AckBlocked("GITHUB_SOURCE_BODY_MISMATCH_NO_POST")
    text = make_ack_only(source, now_utc=now_utc,
                         observed_host=observed_host,
                         expected_main_sha=expected_main_sha)
    payload = json.dumps({"body": text}, separators=(",", ":")).encode("utf-8")
    req = Request(POST_URL, data=payload, method="POST", headers={
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "TWF-P0C-AckCandidate/1",
        "Authorization": "Bearer " + token,
    })
    try:
        opener = transport or build_opener(_NoRedirect()).open
        with opener(req, timeout=10) as response:
            if response.status != 201 or response.geturl() != POST_URL:
                raise AckBlocked("POST_ENDPOINT_OR_STATUS_MISMATCH")
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise AckBlocked("POST_RESPONSE_TOO_LARGE")
        posted = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicates)
        if (type(posted) is not dict or type(posted.get("id")) is not int
                or posted.get("body") != text
                or posted.get("issue_url") != ROOT + "/issues/" + str(ISSUE)):
            raise AckBlocked("POST_RESPONSE_UNVERIFIED")
        return {
            "status": "RECEIPT_POSTED_NO_EXECUTION_NOT_HOST_ATTESTATION",
            "ack_comment_id": posted["id"],
            "source_comment_id": comment["id"],
            "owner_execution_authorized": False,
            "codex_executed": False, "studio_executed": False,
            "globally_idempotent": False,
            "host_origin_verified": False,
        }
    except AckBlocked:
        raise
    except Exception:
        # Never include token or server response body in diagnostics.
        raise AckBlocked("POST_TRANSPORT_FAILED_OR_UNVERIFIED") from None
