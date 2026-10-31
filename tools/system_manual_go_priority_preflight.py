#!/usr/bin/env python3
"""Read-only, *untrusted-input* stale-manual-GO priority detector.

This is a transport-neutral guard for future trusted host integration.  It does
NOT authenticate GitHub, peek a registered worker, acquire a coordinator lease,
change a saved automation, dispatch a run, merge a PR, or override a host denial.
The host must independently fetch current main and both files at one immutable
coordinator ref, check original provider provenance, then require this check to
pass *before* any separate DISPATCH authorization path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

REPO = 'kk051780/toy-wars-factory'
WORKER_TASK = '6adbf0d6a7d881918ce181dff2468867'
CONTROL_BRANCH = 'twf-repair-coordinator'
_SHA = re.compile(r'[0-9a-f]{40}\Z')
_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z')
_LIMIT = 2000
_DENIED = {name: False for name in (
    'provider_authenticated', 'current_main_authenticated', 'coordinator_authenticated',
    'work_requests_authenticated', 'registered_worker_run_authenticated',
    'may_dispatch', 'may_acquire_lease', 'may_start_ai', 'may_write',
    'may_retry', 'may_merge', 'may_publish', 'may_spend',
)}


class InvalidPreflight(ValueError):
    """Fixed diagnostic only; never copy untrusted original data to reports."""


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise InvalidPreflight(code)


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def preflight(*, repository: str, current_main_sha: str, coordinator_ref: str,
              work_requests_ref: str, coordinator: dict, work_requests: dict) -> dict:
    """Return a non-authorizing deterministic snapshot consistency verdict.

    Inputs are caller-controlled: matching refs and hashes do not authenticate
    provider origin. Correctness of the two files / ref must be established by
    the connected host using *original* GitHub responses, never JSON booleans.
    """
    base = dict(schema=1, repository=REPO, authority=dict(_DENIED),
                source_verification='UNTRUSTED_CALLER_INPUT',
                control_ref_authenticated=False, main_commit_authenticated=False,
                allow_worker_run_now=False, allow_dispatch_cas=False)

    def result(code: str, **items: object) -> dict:
        return dict(base, status=code, **items)

    if repository != REPO or type(repository) is not str:
        return result('BLOCK_REPOSITORY_BINDING')
    if not all(_sha(value) for value in (current_main_sha, coordinator_ref, work_requests_ref)):
        return result('BLOCK_UNVERIFIED_REF_SHAPE')
    if coordinator_ref != work_requests_ref:
        return result('BLOCK_MIXED_COORDINATOR_SNAPSHOTS')
    if not isinstance(coordinator, dict) or not isinstance(work_requests, dict):
        return result('BLOCK_MISSING_SOURCE')
    if (type(coordinator.get('schema')) is not int or coordinator['schema'] != 1
            or coordinator.get('task_id') != WORKER_TASK
            or type(coordinator.get('epoch')) is not int or coordinator['epoch'] < 0):
        return result('BLOCK_INVALID_COORDINATOR')
    auth = coordinator.get('authorized_tasks')
    if type(auth) is not dict or auth.get('WORKER') != WORKER_TASK:
        return result('BLOCK_UNREGISTERED_WORKER')
    if coordinator.get('holder') is not None:
        return result('WAIT_SHARED_LOCK', epoch=coordinator['epoch'])
    if (type(work_requests.get('schema')) is not int or work_requests['schema'] != 1
            or type(work_requests.get('requests')) is not list
            or len(work_requests['requests']) > _LIMIT):
        return result('BLOCK_INVALID_REQUESTS')
    by_id = {}
    for entry in work_requests['requests']:
        if (type(entry) is not dict or type(entry.get('id')) is not str
                or not _ID.fullmatch(entry['id'])
                or type(entry.get('status')) is not str
                or type(entry.get('assigned_role')) is not str
                or entry['id'] in by_id):
            return result('BLOCK_INVALID_OR_DUPLICATE_REQUESTS')
        by_id[entry['id']] = entry

    context = coordinator.get('manual_go_context')
    if type(context) is not dict:
        return result('WAIT_FRESH_ROUTING_CONTEXT')
    if not _sha(context.get('source_main_sha')):
        return result('BLOCK_INVALID_ROUTING_MAIN')
    if (context.get('mode') != 'FENCED_DISPATCH_EXISTING_WORKER_ONLY'
            or context.get('next_actor') != 'REGISTERED_WORKER'):
        return result('WAIT_FRESH_ROUTING_CONTEXT')
    ids = context.get('priority_request_ids')
    if (type(ids) is not list or len(ids) > 100
            or any(type(i) is not str or _ID.fullmatch(i) is None for i in ids)
            or len(ids) != len(set(ids))):
        return result('BLOCK_INVALID_PRIORITY_IDS')

    missing = sorted(i for i in ids if i not in by_id)
    resolved = sorted(i for i in ids if i in by_id and
                      by_id[i]['status'].startswith(('RESOLVED_', 'MERGED_', 'CLOSED_', 'SUPERSEDED_')))
    not_open = sorted(i for i in ids if i in by_id and
                      (by_id[i]['status'] != 'OPEN' or by_id[i]['assigned_role'] != 'WORKER'))
    if missing or not_open:
        # Report ID strings from strict bounded pattern only. No freeform
        # request descriptions, secrets or instructions are echoed.
        return result('WAIT_RESELECT_CURRENT_WORK', epoch=coordinator['epoch'],
                      missing_ids=missing, resolved_ids=resolved,
                      non_open_worker_ids=not_open, stale_main=(context['source_main_sha'] != current_main_sha))
    if context['source_main_sha'] != current_main_sha:
        return result('WAIT_RESELECT_CURRENT_WORK', epoch=coordinator['epoch'],
                      missing_ids=[], resolved_ids=[], non_open_worker_ids=[], stale_main=True)
    if not ids:
        return result('WAIT_SELECT_NEW_WORK', epoch=coordinator['epoch'],
                      open_worker_request_count=sum(x['status'] == 'OPEN' and x['assigned_role'] == 'WORKER'
                                                    for x in by_id.values()))
    # Green outcome is *only* a consistency check. It cannot prove a current
    # task run, active worker identity, host safety approval or dispatch CAS.
    return result('SNAPSHOT_CONSISTENT_FURTHER_HOST_CHECKS_REQUIRED', epoch=coordinator['epoch'],
                  selected_request_count=len(ids), priority_ids=list(ids),
                  required_host_checks=['ORIGINAL_GITHUB_MAIN_AND_REF',
                                        'ORIGINAL_REGISTERED_WORKER_RUN_ID',
                                        'FRESH_SHARED_LOCK_AND_POLICY',
                                        'PROVIDER_SUPPORTED_DISPATCH_AUTHORITY'])


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'DUPLICATE_JSON_FIELD')
        result[key] = value
    return result


def _nonfinite(_value):
    raise InvalidPreflight('NONFINITE_JSON')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Read-only stale GO route guard; never dispatches')
    parser.add_argument('--frame', required=True)
    args = parser.parse_args(argv)
    try:
        contents = Path(args.frame).read_bytes()
        _require(len(contents) < 4_000_000, 'INPUT_TOO_LARGE')
        obj = json.loads(contents, object_pairs_hook=_unique_json, parse_constant=_nonfinite)
        _require(type(obj) is dict and set(obj) == {
            'repository', 'current_main_sha', 'coordinator_ref',
            'work_requests_ref', 'coordinator', 'work_requests'
        }, 'INVALID_FRAME')
        verdict = preflight(**obj)
    except InvalidPreflight as exc:
        verdict = {'schema': 1, 'status': 'BLOCK_INPUT', 'reason': str(exc),
                   'authority': dict(_DENIED)}
    except Exception:
        verdict = {'schema': 1, 'status': 'BLOCK_INPUT', 'reason': 'INVALID_INPUT',
                   'authority': dict(_DENIED)}
    print(json.dumps(verdict, ensure_ascii=False, sort_keys=True))
    # Even the green status requires a real independent authenticated host path;
    # exit 0 only for the consistency green result, no dispatch permission.
    return 0 if verdict['status'] == 'SNAPSHOT_CONSISTENT_FURTHER_HOST_CHECKS_REQUIRED' else 2


if __name__ == '__main__':
    sys.exit(main())
