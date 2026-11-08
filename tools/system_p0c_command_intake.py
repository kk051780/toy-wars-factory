"""P0-C read-only untrusted intent validator. Never authorizes execution."""
import json
import re
from datetime import datetime, timezone

MAX_BYTES = 2048
FIELDS = frozenset(("schema","repo","issuer_claim","source_kind","action",
                    "work_id","nonce","host_id","target_branch","main_sha",
                    "issued_at","expires_at"))
WORK_RE = re.compile(r"P0C_[A-Z0-9_]{8,100}\Z")
NONCE_RE = re.compile(r"[a-f0-9]{32}\Z")
SHA_RE = re.compile(r"[a-f0-9]{40}\Z")
TIME_RE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")

def _refuse(reason):
    return dict(status="REJECTED_INVALID_INTENT", reason=reason,
                read_only_intent_valid=False, provider_authenticated=False,
                owner_authorized=False, host_authorized=False,
                codex_execution_authorized=False, may_run_commands=False)

def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result

def _time(value):
    if not isinstance(value, str) or not TIME_RE.fullmatch(value):
        raise ValueError("not strict UTC timestamp")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def inspect_untrusted_intent(raw, *, now_utc, expected_host, seen_work_ids=()):
    """Pure diagnostic. Do not execute shell, Codex, Studio, or GitHub writes."""
    if not isinstance(now_utc, datetime) or now_utc.tzinfo is None or now_utc.utcoffset() is None:
        return _refuse("untrusted clock")
    if not isinstance(expected_host, str) or not expected_host:
        return _refuse("host not pinned")
    try:
        if isinstance(raw, bytes):
            if len(raw) > MAX_BYTES: return _refuse("oversized")
            raw = raw.decode("utf-8", errors="strict")
        if not isinstance(raw, str): return _refuse("unsupported input")
        if len(raw.encode("utf-8")) > MAX_BYTES: return _refuse("oversized")
        data = json.loads(raw, object_pairs_hook=_pairs)
        if type(data) is not dict or frozenset(data) != FIELDS:
            return _refuse("invalid fields")
        if type(data["schema"]) is not int or data["schema"] != 1:
            return _refuse("invalid schema")
        expected = {"repo":"kk051780/toy-wars-factory",
                    "issuer_claim":"kk051780",
                    "source_kind":"CHATGPT_GITHUB_INTENT_UNTRUSTED",
                    "action":"PING_STATUS_READONLY",
                    "host_id":expected_host, "target_branch":"main"}
        for key, value in expected.items():
            if data[key] != value: return _refuse("mismatched "+key)
        work_id, nonce, sha = data["work_id"],data["nonce"],data["main_sha"]
        if not isinstance(work_id, str) or not WORK_RE.fullmatch(work_id):
            return _refuse("invalid work_id")
        if not isinstance(nonce, str) or not NONCE_RE.fullmatch(nonce):
            return _refuse("invalid nonce")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            return _refuse("invalid main_sha")
        if work_id in seen_work_ids: return _refuse("replayed work_id")
        issued, expires = _time(data["issued_at"]), _time(data["expires_at"])
        ttl = (expires-issued).total_seconds()
        now = now_utc.astimezone(timezone.utc)
        if not 0 < ttl <= 600: return _refuse("invalid ttl")
        if (issued-now).total_seconds() > 30: return _refuse("future issue")
        if now >= expires: return _refuse("expired")
    except (ValueError, TypeError, UnicodeError, KeyError, OverflowError):
        return _refuse("malformed intent")
    return dict(status="READ_ONLY_INTENT_VALID_BUT_UNTRUSTED", work_id=work_id,
                read_only_intent_valid=True, provider_authenticated=False,
                owner_authorized=False, host_authorized=False,
                codex_execution_authorized=False, may_run_commands=False)
