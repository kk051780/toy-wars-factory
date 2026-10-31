#!/usr/bin/env python3
"""Read-only, caller-supplied original GitHub work-registry snapshot validator.

Reuses the *interface* of the prior manual-GO GitHubGet endpoint fetcher.
There are no credentials, HTTP/network calls, Git writes, claims or scheduling
in this file. A caller-supplied get(url) is UNTRUSTED even if its result
matches real GitHub response shapes; tests never attest provider identity.

This candidate is a source adapter for Issue #123 stacked PR #174, not a live
work registration/atomic CAS or an approval/dispatch authority.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from typing import Any, Callable

REPOSITORY = 'kk051780/toy-wars-factory'
REPOSITORY_ID = 1431683395
API_ROOT = f'https://api.github.com/repos/{REPOSITORY}'
COORDINATOR_BRANCH = 'twf-repair-coordinator'
COORDINATOR_PATH = 'ops/REPAIR_COORDINATOR.json'
SHA = re.compile(r'[0-9a-f]{40}\Z')
MAX_FILE_BYTES = 1_000_000
MAX_REGISTRY_ROWS = 512


class SnapshotRejected(ValueError):
    """Fail-closed fixed-code rejection, never include supplied source values."""


def check(ok: Any, code: str) -> None:
    if not ok:
        raise SnapshotRejected(code)


def strict_json(data: bytes) -> dict:
    check(type(data) is bytes and 0 < len(data) <= MAX_FILE_BYTES,
          'INVALID_CONTENT_BYTES')

    def unique(pairs):
        d = {}
        for key, val in pairs:
            check(key not in d, 'DUPLICATE_JSON_KEY')
            d[key] = val
        return d

    def reject_const(_):
        raise SnapshotRejected('NONFINITE_JSON')

    try:
        parsed = json.loads(data, object_pairs_hook=unique,
                            parse_constant=reject_const)
    except SnapshotRejected:
        raise
    except (ValueError, UnicodeDecodeError, TypeError):
        raise SnapshotRejected('INVALID_JSON') from None
    check(type(parsed) is dict, 'NOT_JSON_OBJECT')
    return parsed


def git_blob_sha(data: bytes) -> str:
    check(type(data) is bytes, 'INVALID_BLOB_INPUT')
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def _call(get: Callable, url: str) -> dict:
    try:
        value = get(url)
    except Exception:
        raise SnapshotRejected('GITHUB_GET_FAILED') from None
    check(type(value) is dict, 'INVALID_API_RESPONSE')
    return value


def _get_ref(get: Callable, name: str) -> str:
    check(name in ('main', COORDINATOR_BRANCH), 'REF_NOT_ALLOWED')
    url = f'{API_ROOT}/git/ref/heads/{name}'
    row = _call(get, url)
    obj = row.get('object')
    check(row.get('ref') == f'refs/heads/{name}' and
          type(obj) is dict and obj.get('type') == 'commit' and
          type(obj.get('sha')) is str and bool(SHA.fullmatch(obj['sha'])),
          'INVALID_GIT_REF')
    return obj['sha']


def _get_state(get: Callable, commit_sha: str) -> dict:
    check(type(commit_sha) is str and bool(SHA.fullmatch(commit_sha)),
          'INVALID_COORDINATOR_SHA')
    url = f'{API_ROOT}/contents/{COORDINATOR_PATH}?ref={commit_sha}'
    row = _call(get, url)
    check(row.get('type') == 'file' and
          row.get('path') == COORDINATOR_PATH and
          row.get('encoding') == 'base64' and
          type(row.get('content')) is str and
          type(row.get('size')) is int and 0 < row['size'] <= MAX_FILE_BYTES and
          type(row.get('sha')) is str and bool(SHA.fullmatch(row['sha'])),
          'INVALID_CONTENTS_ENVELOPE')
    try:
        data = base64.b64decode(row['content'].replace('\r', '').replace('\n', ''),
                                validate=True)
    except (ValueError, binascii.Error):
        raise SnapshotRejected('INVALID_CONTENT_BASE64') from None
    check(len(data) == row['size'] and len(data) <= MAX_FILE_BYTES and
          git_blob_sha(data) == row['sha'], 'CONTENTS_HASH_MISMATCH')
    state = strict_json(data)
    check(type(state.get('schema')) is int and
          type(state.get('epoch')) is int and state['epoch'] >= 1 and
          'holder' in state, 'COORDINATOR_SHAPE_INVALID')
    registry = state.get('work_registrations')
    if 'work_registrations' in state:
        check(type(registry) is dict and set(registry) == {'schema', 'entries'} and
              type(registry['schema']) is int and registry['schema'] == 1 and
              type(registry['entries']) is list and
              len(registry['entries']) <= MAX_REGISTRY_ROWS,
              'WORK_REGISTRY_SHAPE_INVALID')
        # Full per-row canonical work-ID review belongs to parent PR174's
        # _registry() validator. Do not reimplement/duplicate it here.
    return state


def capture_snapshot(get: Callable) -> dict:
    """Six fixed original-GitHub GET observations, no write or authorization.

    Contract matches PR165's GitHubGet(url) callback. A caller may invoke that
    connector *after* separately approved integration, but even then this
    adapter itself is not host/provider-attested.
    """
    check(callable(get), 'GET_CALLBACK_NOT_AVAILABLE')
    metadata = _call(get, API_ROOT)
    check(type(metadata.get('id')) is int and metadata['id'] == REPOSITORY_ID and
          metadata.get('full_name') == REPOSITORY and
          metadata.get('private') is True, 'REPOSITORY_IDENTITY_MISMATCH')
    main_head = _get_ref(get, 'main')
    coordinator_head = _get_ref(get, COORDINATOR_BRANCH)
    state = _get_state(get, coordinator_head)
    check(main_head == _get_ref(get, 'main') and
          coordinator_head == _get_ref(get, COORDINATOR_BRANCH),
          'REF_MOVED_DURING_CAPTURE')
    # Caller can only use this as an input to PR174's independent fail-closed
    # plan() AFTER a genuinely authenticated host passes trust boundaries.
    return {
        'schema': 1,
        'status': 'CALLBACK_SNAPSHOT_NOT_PROVIDER_ATTESTED',
        'capture_input_class': 'CALLBACK_JSON_UNTRUSTED',
        'capture_get_count': 6,
        'work_registry_initialized': 'work_registrations' in state,
        'snapshot': {
            'repository': REPOSITORY,
            'coordination_branch': COORDINATOR_BRANCH,
            'ref_sha': coordinator_head,
            'main_sha': main_head,
            'state': state,
        },
        'github_authenticated': False,
        'provider_run_authenticated': False,
        'may_claim': False,
        'may_write': False,
        'may_dispatch': False,
        'may_merge': False,
        'cas_performed': False,
    }
