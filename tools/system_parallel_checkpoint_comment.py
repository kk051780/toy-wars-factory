#!/usr/bin/env python3
"""P0 Issue #123 checkpoint comment wire format and readback comparator.

Pure, nonauthorizing serializer. A trusted caller separately appends via an
allowed GitHub connection, fetches comments, checks refs and validates readback.
A valid checkpoint is not a GitHub writer, run attestation or recovery grant.
"""
from __future__ import annotations
import base64
import hashlib
import json
import re

from system_parallel_chat_continuity import verify_packet

REPO = "kk051780/toy-wars-factory"
ISSUE = 123
KIND = "TWF_CHAT_CONTINUITY_V1"
MARKER = "TWF_CHECKPOINT_V1"
LIMIT = 16000
BODY = re.compile(
    r"\ATWF_CHECKPOINT_V1\nissue:123\nsha256:([0-9a-f]{64})\n"
    r"payload_b64url:([A-Za-z0-9_-]{1,24576})\nEND_TWF_CHECKPOINT_V1\Z"
)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf8")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON keys")
        result[key] = value
    return result


def render_comment(packet):
    """Return a complete append-only issue-comment body, without writing it."""
    verify_packet(packet)
    if packet["repository"] != REPO:
        raise ValueError("foreign repository")
    raw = canonical({"kind": KIND, "issue": ISSUE, "packet": packet})
    if len(raw) > LIMIT:
        raise ValueError("checkpoint too large")
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return (f"{MARKER}\nissue:{ISSUE}\nsha256:"
            f"{hashlib.sha256(raw).hexdigest()}\npayload_b64url:"
            f"{encoded}\nEND_{MARKER}")


def parse_comment(text):
    """Verify exact envelope and checksum, NOT GitHub provenance."""
    if type(text) is not str or len(text) > 36000:
        raise ValueError("comment shape")
    m = BODY.fullmatch(text)
    if m is None:
        raise ValueError("comment protocol")
    digest, encoded = m.groups()
    if len(encoded) % 4 == 1:
        raise ValueError("invalid base64 length")
    try:
        raw = base64.urlsafe_b64decode(encoded + "="*(-len(encoded) % 4))
    except (ValueError, base64.binascii.Error):
        raise ValueError("invalid base64") from None
    if not raw or len(raw) > LIMIT:
        raise ValueError("payload length")
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("envelope checksum")
    if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != encoded:
        raise ValueError("noncanonical base64")
    try:
        data = json.loads(raw.decode("utf8"), object_pairs_hook=_unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite")))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("invalid JSON") from None
    if canonical(data) != raw:
        raise ValueError("noncanonical JSON")
    if type(data) is not dict or set(data) != {"kind", "issue", "packet"}:
        raise ValueError("envelope schema")
    if data["kind"] != KIND or type(data["issue"]) is not int or data["issue"] != ISSUE:
        raise ValueError("foreign checkpoint")
    verify_packet(data["packet"])
    if data["packet"]["repository"] != REPO:
        raise ValueError("foreign repo")
    return data["packet"]


def compare_readback(*, posted_body, remote_comment, expected_comment_id):
    """Evaluate *claimed* original GET result; never assert provider trust."""
    def answer(status, packet=None):
        return {"status": status, "packet": packet,
                "body_match_advisory": status == "REMOTE_BODY_MATCH_UNVERIFIED",
                "provider_authenticated": False, "may_write": False,
                "may_recover": False, "may_dispatch": False}
    try:
        packet = parse_comment(posted_body)
        if type(expected_comment_id) is not int or expected_comment_id < 1:
            raise ValueError("comment ID")
        if type(remote_comment) is not dict or set(remote_comment) != {
                "id", "body", "html_url", "created_at"}:
            raise ValueError("comment receipt shape")
        if type(remote_comment["id"]) is not int or remote_comment["id"] != expected_comment_id:
            raise ValueError("comment ID mismatch")
        if remote_comment["body"] != posted_body:
            raise ValueError("comment body drift")
        expected_url = f"https://github.com/{REPO}/issues/{ISSUE}#issuecomment-{expected_comment_id}"
        if remote_comment["html_url"] != expected_url:
            raise ValueError("wrong comment URL")
        if type(remote_comment["created_at"]) is not str or not re.fullmatch(
                r"20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z",
                remote_comment["created_at"]):
            raise ValueError("time shape")
        if parse_comment(remote_comment["body"]) != packet:
            raise ValueError("roundtrip body")
        return answer("REMOTE_BODY_MATCH_UNVERIFIED", packet)
    except (ValueError, TypeError, KeyError, OverflowError):
        return answer("WAIT_UNTRUSTED_CHECKPOINT_READBACK")


def select_latest(comments):
    """Read-only display; callers must fetch ALL pages and recheck live refs."""
    if type(comments) is not list or len(comments) > 500:
        raise ValueError("pagination/size must be resolved by provider")
    rows = []
    for item in comments:
        if type(item) is not dict or type(item.get("id")) is not int:
            continue
        try:
            packet = parse_comment(item.get("body"))
            if item["id"] > 0:
                rows.append((item["id"], packet))
        except (ValueError, TypeError, KeyError, OverflowError):
            pass
    if not rows:
        return {"status": "NO_VALID_CHECKPOINT", "may_write": False}
    rows.sort(key=lambda v: v[0], reverse=True)
    return {"status": "LATEST_ADVISORY_UNVERIFIED", "comment_id": rows[0][0],
            "packet": rows[0][1], "may_write": False, "provider_authenticated": False}
