"""Untrusted-data reducer for one global Roblox Open Cloud POST intent.

NO GitHub/Roblox I/O, credentials, dispatch, lease acquisition or permissions.
A trusted host must do exact-parent GitHub CAS on twf-repair-coordinator,
re-read the entire state, and separately validate authorization before POST.
Intent records are immutable tombstones: expiry is never permission to retry.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
import uuid

REPO = 'kk051780/toy-wars-factory'
TASK_ID = '6adbf0d6a7d881918ce181dff2468867'
FIELD = 'cloud_execution_intents_v1'
SHA1 = re.compile(r'[0-9a-f]{40}\Z')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
MAX_INT = 2**63 - 1
MAX_RECORDS = 1000
REQUEST_FIELDS = {'repository', 'source_main_sha', 'artifact_zip_sha256',
                  'rbxlx_sha256', 'luau_sha256', 'universe_id', 'place_id',
                  'version_id', 'intent_type'}
RECORD_FIELDS = {'fingerprint', 'resource', 'source_main_sha', 'owner_id',
                 'epoch', 'claim_ref', 'reserved_at', 'phase'}

class Blocked(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise Blocked(reason)

def sha(value, regex):
    return type(value) is str and regex.fullmatch(value) is not None

def positive(value):
    return type(value) is int and 1 <= value <= MAX_INT

def canonical_uuid(value):
    try:
        return type(value) is str and str(uuid.UUID(value)) == value
    except (ValueError, AttributeError, TypeError):
        return False

def moment(value):
    require(type(value) is str, 'INVALID_TIME')
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, OverflowError):
        raise Blocked('INVALID_TIME') from None
    require(date.tzinfo is not None and date.utcoffset() is not None,
            'INVALID_TIME')
    return date.astimezone(timezone.utc)

def request_id(request):
    require(type(request) is dict and set(request) == REQUEST_FIELDS,
            'INVALID_REQUEST_SCHEMA')
    require(request['repository'] == REPO, 'FOREIGN_REPO')
    require(sha(request['source_main_sha'], SHA1), 'INVALID_MAIN_SHA')
    for key in ('artifact_zip_sha256', 'rbxlx_sha256', 'luau_sha256'):
        require(sha(request[key], SHA256), 'INVALID_DIGEST')
    for key in ('universe_id', 'place_id', 'version_id'):
        require(positive(request[key]), 'INVALID_TARGET')
    require(request['intent_type'] == 'HEADLESS_SERVER_SMOKE_V1',
            'INVALID_TEST_TYPE')
    payload = json.dumps(request, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True).encode('ascii')
    fingerprint = hashlib.sha256(payload).hexdigest()
    resource = f"{request['universe_id']}/{request['place_id']}/{request['version_id']}"
    return fingerprint, resource

def ledger(state):
    require(type(state) is dict and type(state.get('schema')) is int and
            state.get('schema') == 1 and state.get('task_id') == TASK_ID and type(state.get('epoch')) is int and
            state['epoch'] >= 0, 'INVALID_COORDINATOR')
    records = state.get(FIELD, [])
    require(type(records) is list and len(records) <= MAX_RECORDS,
            'INVALID_LEDGER')
    ids, resources = set(), set()
    for record in records:
        require(type(record) is dict and set(record) == RECORD_FIELDS,
                'INVALID_RECORD_SCHEMA')
        require(sha(record['fingerprint'], SHA256) and
                type(record['resource']) is str and
                re.fullmatch(r'[1-9][0-9]{0,18}/[1-9][0-9]{0,18}/[1-9][0-9]{0,18}',
                             record['resource']) is not None and
                sha(record['source_main_sha'], SHA1) and
                canonical_uuid(record['owner_id']) and
                positive(record['epoch']) and
                sha(record['claim_ref'], SHA1) and
                record['phase'] == 'POST_CONSUMED_NEVER_AUTO_RETRY',
                'INVALID_RECORD')
        moment(record['reserved_at'])
        require(all(positive(int(value)) for value in record['resource'].split('/')),
                'INVALID_RECORD')
        require(record['fingerprint'] not in ids and record['resource'] not in resources,
                'DUPLICATE_LEDGER_HISTORY')
        ids.add(record['fingerprint']);resources.add(record['resource'])
    return records

def active_controller(state, owner_id, epoch, now):
    require(canonical_uuid(owner_id) and positive(epoch), 'INVALID_ACTOR')
    require(state['epoch'] == epoch, 'WRONG_EPOCH')
    holder = state.get('holder')
    require(type(holder) is dict and
            holder.get('kind') == 'CONTROLLER' and
            holder.get('owner_id') == owner_id and
            type(holder.get('epoch')) is int and holder['epoch'] == epoch and
            holder.get('task_id') is None and
            holder.get('origin') == 'controller', 'FOREIGN_HOLDER')
    branch = holder.get('work_branch')
    require(type(branch) is str and branch.startswith('controller/roblox-cloud-'),
            'FOREIGN_WORK_BRANCH')
    opened, until, at = moment(holder.get('acquired_at')), moment(holder.get('expires_at')), moment(now)
    require(opened <= at < until and
            (until - opened).total_seconds() <= 1800,
            'LEASE_NOT_LIVE')
    return holder

def propose(state, request, *, owner_id, epoch, now, expected_ref):
    """Prepare a single strictly fenced append. Caller-supplied data not authority."""
    fingerprint, resource = request_id(request)
    records = ledger(state)
    require(sha(expected_ref, SHA1), 'INVALID_EXPECTED_REF')
    holder = active_controller(state, owner_id, epoch, now)
    require(holder.get('base_main_sha') == request['source_main_sha'],
            'STALE_SOURCE')
    require(len(records) < MAX_RECORDS, 'LEDGER_FULL')
    for record in records:
        require(record['fingerprint'] != fingerprint and record['resource'] != resource,
                'ALREADY_CONSUMED_NO_RETRY')
    next_state = deepcopy(state)
    new_record = {'fingerprint': fingerprint, 'resource': resource,
                  'source_main_sha': request['source_main_sha'],
                  'owner_id': owner_id, 'epoch': epoch,
                  'claim_ref': expected_ref,
                  'reserved_at': moment(now).isoformat(),
                  'phase': 'POST_CONSUMED_NEVER_AUTO_RETRY'}
    next_state[FIELD] = deepcopy(records) + [new_record]
    return {'status': 'CANDIDATE_ONLY_NO_WRITE', 'expected_sha': expected_ref,
            'next_state': next_state, 'record': new_record,
            'post_authorized': False, 'provider_attested': False,
            'roblox_engine_verified': False, 'main_merge_authorized': False}

def confirm_readback(plan, *, actual_ref, cas_ack_ref, actual_state, current_holder_state,
                     owner_id, epoch, now):
    """Structural commit readback only; host must authenticate GitHub/provider.

    Never turns a self-supplied Git SHA or a callback JSON into execution rights.
    """
    require(type(plan) is dict and plan.get('status') == 'CANDIDATE_ONLY_NO_WRITE',
            'INVALID_PLAN')
    require(sha(actual_ref, SHA1) and actual_ref != plan.get('expected_sha'),
            'NO_NEW_COMMIT')
    require(sha(cas_ack_ref, SHA1) and actual_ref == cas_ack_ref,
            'CAS_ACK_NOT_CONFIRMED')
    require(type(actual_state) is dict and actual_state == plan.get('next_state'),
            'READBACK_MISMATCH')
    require(type(current_holder_state) is dict, 'NO_HOLDER_READBACK')
    rec = plan.get('record')
    require(type(rec) is dict and rec.get('owner_id') == owner_id and
            rec.get('epoch') == epoch, 'WRONG_RECORD_OWNER')
    records = ledger(actual_state)
    require(bool(records) and records[-1] == rec and
            actual_state.get('holder') == current_holder_state.get('holder'),
            'HISTORY_OR_HOLDER_CHANGED')
    active_controller(current_holder_state, owner_id, epoch, now)
    require(actual_state['epoch'] == current_holder_state['epoch'],
            'STALE_GENERATION')
    return {'status': 'STRUCTURAL_CAS_READBACK_CANDIDATE_ONLY',
            'record_fingerprint': rec['fingerprint'],
            'github_provider_authenticated': False,
            'post_authorized': False, 'roblox_engine_verified': False,
            'merge_authorized': False, 'replay_authorized': False}


# Host-application contract: separate this from credentialed GitHub operations.
# These callbacks MUST be bound by a trusted controller to genuine provider API
# responses. No callback-origin proof, user-supplied token or permission is granted
# by this module. In particular, successful CAS never authorizes a Roblox POST.
CONTROL_BRANCH = 'twf-repair-coordinator'
CONTROL_PATH = 'ops/REPAIR_COORDINATOR.json'


def persist_proposal_via_trusted_callbacks(*, request, owner_id, epoch, now,
                                           read, cas, read_commit):
    """One-shot GitHub CAS proposal and exact-parent/readback gate, no retries.

    read(repo, branch, path) -> {'repository', 'branch', 'ref', 'state'}
    cas(repo, branch, expected_sha=<sha>, state=<dict>, force=False) -> new SHA
    read_commit(repo, new SHA) -> {'sha':new SHA,'parents':[old SHA]}

    All three must be genuine independently authenticated provider connections.
    An ambiguous CAS result must HOLD even if the write might have succeeded.
    Unlike an execution dispatcher, this NEVER grants any right to POST, publish,
    merge, spend, release a lease or run a Roblox game.
    """
    require(callable(read) and callable(cas) and callable(read_commit),
            'TRUSTED_CALLBACKS_MISSING')

    def snapshot():
        try:
            row = read(REPO, CONTROL_BRANCH, CONTROL_PATH)
        except Exception:
            raise Blocked('READBACK_UNAVAILABLE_HOLD') from None
        require(type(row) is dict and set(row) ==
                {'repository', 'branch', 'ref', 'state'} and
                row['repository'] == REPO and
                row['branch'] == CONTROL_BRANCH and
                sha(row['ref'], SHA1) and type(row['state']) is dict,
                'INVALID_GITHUB_SNAPSHOT')
        return row

    before = snapshot()
    plan = propose(before['state'], request, owner_id=owner_id,
                   epoch=epoch, now=now, expected_ref=before['ref'])
    try:
        ack = cas(REPO, CONTROL_BRANCH,
                  expected_sha=before['ref'],
                  state=deepcopy(plan['next_state']), force=False)
    except Exception:
        raise Blocked('CAS_ACK_UNKNOWN_HOLD_NO_RETRY') from None
    # Do NOT ever repeat the CAS here. A lost response could mean a prior write.
    require(sha(ack, SHA1) and ack != before['ref'],
            'CAS_ACK_UNKNOWN_HOLD_NO_RETRY')
    try:
        meta = read_commit(REPO, ack)
    except Exception:
        raise Blocked('COMMIT_PARENT_NOT_PROVEN_HOLD') from None
    require(type(meta) is dict and
            set(meta) == {'sha', 'parents'} and
            meta['sha'] == ack and
            type(meta['parents']) is list and meta['parents'] == [before['ref']],
            'COMMIT_PARENT_NOT_PROVEN_HOLD')
    after = snapshot()
    validated = confirm_readback(plan, actual_ref=after['ref'],
                                 cas_ack_ref=ack, actual_state=after['state'],
                                 current_holder_state=after['state'],
                                 owner_id=owner_id, epoch=epoch, now=now)
    return {
        **validated,
        'status': 'EXACT_PARENT_CAS_READBACK_STRUCTURAL_ONLY',
        'source_ref': before['ref'], 'observed_ref': after['ref'],
        'post_authorized': False, 'github_provider_authenticated': False,
        'roblox_engine_verified': False, 'replay_authorized': False,
        'merge_authorized': False,
    }

if __name__ == '__main__':
    print(json.dumps({'status': 'DISABLED_LIBRARY_ONLY',
                      'github_writes': 0, 'roblox_requests': 0}))
