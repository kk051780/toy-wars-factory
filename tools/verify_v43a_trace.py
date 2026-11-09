#!/usr/bin/env python3
"""Public-safe, offline V43-A neutral capture trace acceptance guard.

Only checks structure/temporal invariants of a SANITIZED, server-produced trace.
It does not attest authenticity of server instrumentation or prove Roblox Studio QA.
No network, Roblox, GitHub, file writes, or private identity collection.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = 'P0D_NEUTRAL_TRACE_V1'
MAX_FILE_BYTES = 131072
MAX_EVENTS = 300
MAX_TIME = 3600
NPC_ID = 'S1_NEUTRAL_A'
PERSON = re.compile(r'[A-Z][A-Z0-9_]{0,15}\Z')
PHASES = {'WAIT', 'CLAIMING', 'CONTESTED', 'ACTIVE', 'COOLDOWN', 'ENDED'}
TEAM = {'BLUE', 'RED'}
OWNERS = TEAM | {'NONE'}
REASONS = {'EGG_CARRIER', 'DEAD', 'OUT_OF_RANGE', 'LEGACY_OWNED', 'COOLDOWN',
           'CONTESTED', 'RATE_LIMIT', 'STALE_MATCH', 'SPOOFED_TEAM', 'BAD_EVENT'}
FIELDS = {
    'MATCH_START': set(),
    'NPC_BASELINE': {'npc', 'legacy_owner', 'v43_owner'},
    'CLAIM_START': {'npc', 'actor', 'team', 'alive', 'egg_carrier', 'near', 'server_accepted'},
    'CLAIM_CONTEST': {'npc', 'actor', 'team'},
    'CLAIM_RESET': {'npc'},
    'CLAIM_COMMIT': {'npc', 'actor', 'team'},
    'CLAIM_DENIED': {'npc', 'reason'},
    'OWNER_SNAPSHOT': {'npc', 'legacy_owner', 'v43_owner'},
    'LEASE_EXPIRE': {'npc'},
    'COOLDOWN_EXPIRE': {'npc'},
    'MATCH_END': set(),
    'FINAL': set(),
}

class TraceContractError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def reject(code):
    raise TraceContractError(code)


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            reject('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def validate_ids(evt):
    if 'npc' in evt and evt['npc'] != NPC_ID:
        reject('NPC_NOT_WHITELISTED')
    if 'team' in evt and evt['team'] not in TEAM:
        reject('INVALID_TEAM')
    if 'actor' in evt and (not isinstance(evt['actor'], str) or not PERSON.fullmatch(evt['actor'])):
        reject('ACTOR_MUST_BE_PSEUDONYM')
    for k in ('legacy_owner', 'v43_owner'):
        if k in evt and evt[k] not in OWNERS:
            reject('INVALID_OWNER')


def check_trace(doc: dict) -> dict:
    if not isinstance(doc, dict) or set(doc) != {'schema', 'game_id', 'work_id', 'source', 'stage', 'events'}:
        reject('DOC_FIELDS_INVALID')
    if (doc['schema'], doc['game_id'], doc['work_id'], doc['stage']) != (
            SCHEMA, 'TRAP_RAIDERS', 'p0d-siege-v19', 'S1'):
        reject('IDENTITY_MISMATCH')
    if doc['source'] not in ('synthetic', 'studio_sanitized'):
        reject('INVALID_SOURCE')
    events = doc['events']
    if not isinstance(events, list) or len(events) < 5 or len(events) > MAX_EVENTS:
        reject('EVENT_COUNT_INVALID')

    state = 'INIT'
    t_last = -1.0
    owner = 'NONE'
    claim = None
    lease_deadline = None
    cooldown_deadline = None
    expect_snapshot = False
    snapshot_required = 0
    committed = 0
    denied = 0
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            reject('EVENT_NOT_OBJECT')
        if not isinstance(event.get('type'), str) or event['type'] not in FIELDS:
            reject('UNKNOWN_EVENT')
        kind = event['type']
        if set(event) != ({'type', 'seq', 't'} | FIELDS[kind]):
            reject('EVENT_FIELDS_INVALID')
        if type(event['seq']) is not int or event['seq'] != index + 1:
            reject('NONMONOTONIC_SEQUENCE')
        t = event['t']
        if type(t) not in (int, float) or not 0 <= t <= MAX_TIME or t != t or t < t_last:
            reject('NONMONOTONIC_TIME')
        t_last = t
        validate_ids(event)
        if expect_snapshot and kind != 'OWNER_SNAPSHOT':
            reject('MISSING_OWNER_SNAPSHOT')
        if state == 'INIT':
            if kind != 'MATCH_START' or t != 0:
                reject('MISSING_MATCH_START')
            state = 'BASELINE_PENDING'
            continue
        if state == 'BASELINE_PENDING':
            if kind != 'NPC_BASELINE' or (event['legacy_owner'], event['v43_owner']) != ('NONE', 'NONE'):
                reject('LEGACY_OWNERSHIP_CONFLICT')
            state = 'WAIT'
            continue
        if state == 'FINALIZED':
            reject('EVENT_AFTER_FINAL')
        if kind == 'MATCH_START' or kind == 'NPC_BASELINE':
            reject('DUPLICATE_START_OR_BASELINE')
        if kind == 'OWNER_SNAPSHOT':
            if event['legacy_owner'] != 'NONE' or event['v43_owner'] != owner:
                reject('DUAL_OWNER_OR_DESYNC')
            expect_snapshot = False
            snapshot_required += 1
            continue
        if kind == 'CLAIM_DENIED':
            if event['reason'] not in REASONS or state == 'ENDED':
                reject('INVALID_DENIAL')
            denied += 1
            continue
        if kind == 'CLAIM_START':
            if state != 'WAIT':
                reject('CLAIM_ILLEGAL_STATE')
            if any(type(event[k]) is not bool for k in ('alive', 'egg_carrier', 'near', 'server_accepted')):
                reject('INVALID_SERVER_FLAGS')
            if not (event['alive'] and not event['egg_carrier'] and event['near'] and event['server_accepted']):
                reject('UNTRUSTED_CLAIM_ACCEPTED')
            claim = (event['actor'], event['team'], t)
            state = 'CLAIMING'
            continue
        if kind == 'CLAIM_CONTEST':
            if state != 'CLAIMING' or claim is None or event['team'] == claim[1]:
                reject('INVALID_CONTEST')
            state = 'CONTESTED'
            claim = None
            continue
        if kind == 'CLAIM_RESET':
            if state not in ('CLAIMING', 'CONTESTED'):
                reject('INVALID_RESET')
            claim = None
            state = 'WAIT'
            continue
        if kind == 'CLAIM_COMMIT':
            if state != 'CLAIMING' or claim is None or (event['actor'], event['team']) != claim[:2]:
                reject('CLAIM_COMMIT_NOT_AUTHORIZED')
            if t - claim[2] + 1e-9 < 3.0:
                reject('CLAIM_BEFORE_3_SECONDS')
            # QA guard: a capture committed much later is a stale pending claim.
            # This 5s bound is a pilot acceptance threshold, not live game law.
            if t - claim[2] > 5.0:
                reject('STALE_CLAIM_COMMIT')
            state = 'ACTIVE'
            owner = claim[1]
            claim = None
            committed += 1
            lease_deadline = t + 8.0
            expect_snapshot = True
            continue
        if kind == 'LEASE_EXPIRE':
            if state != 'ACTIVE' or lease_deadline is None or t + 1e-9 < lease_deadline:
                reject('LEASE_END_TOO_EARLY_OR_INVALID')
            owner = 'NONE'
            lease_deadline = None
            cooldown_deadline = t + 4.0
            state = 'COOLDOWN'
            expect_snapshot = True
            continue
        if kind == 'COOLDOWN_EXPIRE':
            if state != 'COOLDOWN' or cooldown_deadline is None or t + 1e-9 < cooldown_deadline:
                reject('COOLDOWN_TOO_EARLY_OR_INVALID')
            cooldown_deadline = None
            state = 'WAIT'
            continue
        if kind == 'MATCH_END':
            if state == 'ENDED':
                reject('DUPLICATE_END')
            owner = 'NONE'
            state = 'ENDED'
            claim = None
            lease_deadline = None
            cooldown_deadline = None
            expect_snapshot = True
            continue
        if kind == 'FINAL':
            if state != 'ENDED' or owner != 'NONE' or index != len(events) - 1:
                reject('FINAL_WITHOUT_END_OR_NOT_LAST')
            state = 'FINALIZED'
            continue
        reject('ILLEGAL_TRANSITION')
    if state != 'FINALIZED' or expect_snapshot:
        reject('TRACE_INCOMPLETE')
    return {
        'ok': True, 'status': 'TRACE_CONTRACT_PASS_NOT_STUDIO_QA',
        'source': doc['source'], 'game_id': doc['game_id'],
        'events_checked': len(events), 'captures': committed,
        'denied_events': denied, 'owner_snapshots': snapshot_required,
        'studio_qa': 'NOT_VERIFIED_BY_THIS_TOOL',
    }


def load_trace(path: Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        reject('INPUT_SIZE_OR_SYMLINK_INVALID')
    with path.open('rb') as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        reject('INPUT_TOO_LARGE')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=strict_pairs,
                          parse_constant=lambda _: reject('INVALID_NUMBER'))
    except (UnicodeError, json.JSONDecodeError):
        reject('INVALID_JSON')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', type=Path, help='sanitized trace JSON; NOT raw client logs')
    args = p.parse_args()
    try:
        report = check_trace(load_trace(args.trace))
        print(json.dumps(report, sort_keys=True))
        return 0
    except (TraceContractError, OSError) as e:
        code = e.code if isinstance(e, TraceContractError) else 'INPUT_READ_FAILED'
        print(json.dumps({'ok': False, 'error': code, 'studio_qa': 'NOT_VERIFIED_BY_THIS_TOOL'}))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
