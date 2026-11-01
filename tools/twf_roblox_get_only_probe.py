"""Candidate: at-most-two-GET Roblox Open Cloud inspector for a pre-existing task.

NO POST / PUBLISH / retry. Caller-provided authorization flags are NOT proof of
actual ownership or consent. Results are NEVER classified as engine-verified.
No logging of token or task/log body. Requires independent security review.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import re
import ssl
import urllib.request

HOST = 'https://apis.roblox.com'
ID = re.compile(r'[1-9][0-9]{0,18}\Z')
UUID = re.compile(r'[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}\Z')
MAX_BYTES = 65536
NETWORK_TIMEOUT_SECONDS = 8
STATES = frozenset(('QUEUED', 'PROCESSING', 'COMPLETE', 'FAILED', 'CANCELLED'))

class ProbeHold(ValueError):
    """Fixed non-secret diagnostic; never propagate transport error strings."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ProbeHold(reason)


@dataclass(frozen=True)
class TaskTarget:
    universe_id: str
    place_id: str
    saved_version_id: str
    execution_session_id: str
    task_id: str
    private_target_reviewed: bool = False
    original_create_receipt_reviewed: bool = False

    def path(self) -> str:
        for n in (self.universe_id, self.place_id, self.saved_version_id):
            require(type(n) is str and ID.fullmatch(n) is not None, 'INVALID_TARGET_ID')
        for n in (self.execution_session_id, self.task_id):
            require(type(n) is str and UUID.fullmatch(n) is not None, 'INVALID_TASK_ID')
        require(self.private_target_reviewed is True and
                self.original_create_receipt_reviewed is True,
                'APPROVED_PRIVATE_TASK_REQUIRED')
        return (f'universes/{self.universe_id}/places/{self.place_id}/'
                f'versions/{self.saved_version_id}/luau-execution-sessions/'
                f'{self.execution_session_id}/tasks/{self.task_id}')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, msg, headers, newurl):
        return None


def hardened_get_opener():
    """Explicit direct TLS with OS root store; do not inherit HTTPS_PROXY."""
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()))


def strict_json(data: bytes):
    try:
        def pairs(items):
            out = {}
            for key, value in items:
                require(key not in out, 'DUPLICATE_JSON_KEY')
                out[key] = value
            return out
        return json.loads(data.decode('utf-8', errors='strict'),
                          object_pairs_hook=pairs,
                          parse_constant=lambda _: require(False, 'NONFINITE_JSON'))
    except ProbeHold:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise ProbeHold('BAD_JSON') from None


def get_one(opener, url: str, api_key: str):
    # URL is always constructed internally from canonical, validated components.
    req = urllib.request.Request(url, method='GET', headers={
        'x-api-key': api_key, 'Accept': 'application/json'})
    try:
        with opener.open(req, timeout=NETWORK_TIMEOUT_SECONDS) as response:
            require(response.geturl() == url, 'UNEXPECTED_REDIRECT')
            require(response.status == 200, 'UNEXPECTED_STATUS')
            ct = response.headers.get('Content-Type', '').lower().split(';', 1)[0].strip()
            require(ct == 'application/json', 'UNEXPECTED_CONTENT_TYPE')
            raw = response.read(MAX_BYTES+1)
    except ProbeHold:
        raise
    except Exception:
        # Deliberately discard URL/header/body/tokens in OS/HTTP exceptions.
        raise ProbeHold('GET_FAILED_NO_RETRY') from None
    require(type(raw) is bytes and len(raw) <= MAX_BYTES, 'GET_RESPONSE_TOO_LARGE')
    return strict_json(raw), hashlib.sha256(raw).hexdigest()


def probe_existing_task(target: TaskTarget, api_key: str, *, opener=None, contract_checker=None) -> dict:
    """Execute at most two GETs, never create a Cloud execution task.

    Caller can still feed a forged opener, so no assertion of provider origin is
    possible here; a separate trusted host and original create receipt are needed.
    """
    path = target.path()
    require(contract_checker is None or callable(contract_checker), 'BAD_CONTRACT_CHECKER')
    require(type(api_key) is str and bool(api_key) and
            not any(c in api_key for c in '\r\n\x00'), 'API_KEY_MISSING_OR_BAD')
    if opener is None:
        opener = hardened_get_opener()
    task_url = f'{HOST}/cloud/v2/{path}'
    logs_url = f'{task_url}/logs'
    task, task_digest = get_one(opener, task_url, api_key)
    require(type(task) is dict and task.get('path') == path, 'TASK_ID_MISMATCH')
    state = task.get('state')
    require(type(state) is str and state in STATES, 'TASK_STATE_UNKNOWN')
    # Pending tasks need no log GET; a log call can be unavailable until
    # completion. Do not poll or start a new execution on a pending response.
    if state in ('QUEUED', 'PROCESSING'):
        return dict(status='UNTRUSTED_READ_ONLY_PENDING', task_path_claim=path,
                    task_state_claim=state, task_raw_sha256=task_digest,
                    logs_raw_sha256=None, log_record_count=0, log_message_count=0,
                    http_get_count=1, http_post_count=0, automatic_retries=0,
                    proxy_inheritance=False, api_key_returned=False,
                    raw_log_content_returned=False, local_contract_checked_untrusted=False,
                    original_create_ack_authenticated=False,
                    source_version_authenticated=False,
                    roblox_provider_authenticated=False, engine_verified=False,
                    mobile_verified=False, may_publish=False, may_merge=False,
                    may_spend=False)
    # Never label a terminal task's caller-provided output as engine proof.
    logs, logs_digest = get_one(opener, logs_url, api_key)
    require(type(logs) is dict and type(logs.get('luauExecutionSessionTaskLogs')) is list,
            'LOGS_SCHEMA_INVALID')
    require(type(logs.get('nextPageToken')) is str and logs['nextPageToken'] == '',
            'LOGS_NEXT_PAGE_UNRESOLVED')
    records = logs['luauExecutionSessionTaskLogs']
    require(len(records) <= 16, 'LOGS_TOO_MANY_RECORDS')
    count = 0
    for i, rec in enumerate(records, start=1):
        require(type(rec) is dict and rec.get('path') == path+f'/logs/{i}',
                'FOREIGN_LOG_RECORD')
        messages = rec.get('messages')
        require(type(messages) is list and len(messages) <= 100 and
                all(type(m) is str and len(m) <= 2048 for m in messages),
                'LOG_MESSAGE_BOUNDS')
        count += len(messages)
    contract_passed = False
    if contract_checker is not None and state == 'COMPLETE':
        # The checker sees in-memory parsed data, NOT the API key or opener.
        # Never propagate its exception: it may contain private data.
        try:
            verdict = contract_checker(task, logs, path)
        except Exception:
            raise ProbeHold('LOCAL_CONTRACT_REJECTED') from None
        require(type(verdict) is dict and
                verdict.get('status') == 'UNTRUSTED_OPEN_CLOUD_GET_LOGS_CONSISTENT' and
                verdict.get('task_path_claim') == path and
                verdict.get('create_response_path_matches_get') is True and
                verdict.get('create_ack_authenticated') is False and
                verdict.get('provider_authenticated') is False and
                verdict.get('engine_verified') is False and
                verdict.get('may_post') is False and
                verdict.get('may_publish') is False,
                'LOCAL_CONTRACT_REJECTED')
        contract_passed = True
    return dict(status='UNTRUSTED_READ_ONLY_GET_AND_LOGS_OBSERVED', task_path_claim=path,
                task_state_claim=state, task_raw_sha256=task_digest,
                logs_raw_sha256=logs_digest, log_record_count=len(records),
                log_message_count=count, http_get_count=2, http_post_count=0,
                automatic_retries=0, proxy_inheritance=False,
                api_key_returned=False, raw_log_content_returned=False,
                local_contract_checked_untrusted=contract_passed,
                original_create_ack_authenticated=False, source_version_authenticated=False,
                roblox_provider_authenticated=False, engine_verified=False,
                mobile_verified=False, may_publish=False, may_merge=False, may_spend=False)
