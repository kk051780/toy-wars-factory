#!/usr/bin/env python3
"""Public-safe, source-free Gorogan S1 *trace contract* verifier.

It cannot attest log provenance or actual Roblox Studio behavior. See docs/TRACE_CONTRACT.md.
"""
import argparse
import json
import math
import os
from pathlib import Path
import re
import sys

SCHEMA = 'P0D_GOROGAN_STUDIO_TRACE_V1'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
TOKEN = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
MAX_FILE = 1_000_000
ALLOWED = {'ROUND_START', 'TRIGGER', 'SPAWN', 'NAV_REQUEST', 'MOVE_SAMPLE',
           'TELEGRAPH', 'ATTACK_RESOLVE', 'HIT', 'HIT_DENIED',
           'REMOTE_REJECTED', 'ROUND_END', 'CLEANUP'}

class InvalidTrace(ValueError):
    pass


def unique_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise InvalidTrace('duplicate JSON key: ' + k)
        result[k] = v
    return result


def bad_constant(value):
    raise InvalidTrace('non-finite JSON constant: ' + value)


def read_trace(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise InvalidTrace('missing or symlinked input file')
    if p.stat().st_size > MAX_FILE:
        raise InvalidTrace('trace file too large')
    try:
        return json.loads(p.read_text(encoding='utf-8'), object_pairs_hook=unique_pairs,
                          parse_constant=bad_constant)
    except (UnicodeError, OSError, json.JSONDecodeError) as exc:
        raise InvalidTrace('malformed trace JSON: ' + str(exc)) from exc


def is_int(x, minimum=0, maximum=10_000_000):
    return type(x) is int and minimum <= x <= maximum


def token(x):
    return isinstance(x, str) and TOKEN.fullmatch(x) is not None


def finite_num(x, lo=-100_000, hi=100_000):
    return type(x) in (float, int) and math.isfinite(x) and lo <= x <= hi


def pos(x):
    return isinstance(x, list) and len(x) == 3 and all(finite_num(i) for i in x)


def dist(a, b):
    return math.dist(a, b)


def require(errors, ok, code):
    if not ok:
        errors.append(code)
    return bool(ok)


def validate(trace):
    """Return stable error codes. Empty means *shape/contract* PASS, never Studio PASS."""
    e = []
    if not isinstance(trace, dict):
        return ['ROOT_NOT_OBJECT']
    for k, value in [('schema', SCHEMA), ('game_id', 'TRAP_RAIDERS'),
                     ('work_id', 'p0d-siege-v19'), ('feature_id', 'D07'), ('stage', 'S1'),
                     ('environment', 'UNPUBLISHED_STUDIO'), ('trigger_mode', 'SERVER_QA_ONLY')]:
        require(e, trace.get(k) == value, 'INVALID_' + k.upper())
    for k in ('round_id', 'run_id'):
        require(e, token(trace.get(k)), 'INVALID_' + k.upper())
    require(e, is_int(trace.get('clients'), 2, 4), 'CLIENTS_REQUIRE_2_TO_4')
    require(e, trace.get('trace_origin') in ('SYNTHETIC', 'STUDIO_SERVER_OUTPUT'),
            'INVALID_TRACE_ORIGIN')
    for k in ('place_sha256', 'source_sha256', 'output_sha256'):
        require(e, isinstance(trace.get(k), str) and HEX64.fullmatch(trace[k]) is not None,
                'INVALID_' + k.upper())
    evidence = trace.get('evidence')
    if not isinstance(evidence, dict):
        e.append('MISSING_EVIDENCE'); evidence = {}
    for k in ('stop_edit_save', 'owned_studio_pid_exited'):
        require(e, evidence.get(k) is True, 'MISSING_' + k.upper())
    require(e, evidence.get('saved_place_sha256') == trace.get('place_sha256'),
            'SAVED_PLACE_SHA_MISMATCH')
    require(e, evidence.get('log_sha256') == trace.get('output_sha256'),
            'LOG_SHA_MISMATCH')
    require(e, evidence.get('local_source_sha256') == trace.get('source_sha256'),
            'LOCAL_SOURCE_SHA_MISMATCH')

    events = trace.get('events')
    if not isinstance(events, list) or not 5 <= len(events) <= 1000:
        return e + ['INVALID_EVENTS_COUNT']
    prev_seq, prev_ms, state, start_ms, spawn_ms = 0, -1, 'INIT', None, None
    boss_id = None
    round_done = False
    last_pos, last_pos_ms = None, None
    distance_moved = 0.0
    nav_t = []
    attacks = {}
    hit_pairs = set()
    n_spawn = n_cleanup = n_telegraph = n_hits = n_denied = n_rejected = 0
    stage_end = False
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            e.append(f'EVENT_{i}_NOT_OBJECT'); continue
        kind = event.get('kind')
        if not isinstance(kind, str) or kind not in ALLOWED:
            e.append(f'UNKNOWN_KIND_{i}'); continue
        seq, now = event.get('seq'), event.get('ms')
        if not is_int(seq, 1) or seq != prev_seq + 1:
            e.append(f'INVALID_SEQ_{i}')
        if not is_int(now, 0, 600_000) or now < prev_ms:
            e.append(f'INVALID_TIME_{i}')
            continue
        prev_seq, prev_ms = seq if is_int(seq, 1) else prev_seq, now
        if event.get('authority') != 'SERVER':
            e.append(f'UNTRUSTED_AUTHORITY_{i}')
        if event.get('round_id') != trace.get('round_id'):
            e.append(f'ROUND_MISMATCH_{i}')
        if state == 'INIT' and kind != 'ROUND_START':
            e.append(f'EVENT_BEFORE_ROUND_START_{i}')
        if boss_id is not None and kind in ('NAV_REQUEST','MOVE_SAMPLE','TELEGRAPH','ATTACK_RESOLVE','HIT','HIT_DENIED','CLEANUP') and event.get('boss_id') != boss_id:
            e.append(f'BOSS_ID_MISMATCH_{i}')
        if stage_end:
            e.append(f'AFTER_CLEANUP_{i}')
            continue
        if round_done and kind not in ('CLEANUP',):
            e.append(f'AFTER_ROUND_END_{i}')
            continue
        if kind == 'ROUND_START':
            if state != 'INIT': e.append('DUPLICATE_ROUND_START')
            else: state = 'ROUND'; start_ms = now
        elif kind == 'TRIGGER':
            if state != 'ROUND' or event.get('mode') != 'SERVER_QA_ONLY' or event.get('source') != 'SERVER_TEST_COMMAND':
                e.append('INVALID_TRIGGER')
            else: state = 'TRIGGERED'
        elif kind == 'SPAWN':
            if state != 'TRIGGERED' or not token(event.get('boss_id')) or event.get('server_owned') is not True or not pos(event.get('pos')):
                e.append('INVALID_SPAWN')
            else:
                n_spawn += 1; state = 'SPAWNED'; spawn_ms = now; boss_id = event['boss_id']
                last_pos, last_pos_ms = event['pos'], now
        elif kind == 'NAV_REQUEST':
            if state != 'SPAWNED' or event.get('mechanism') != 'PATHFINDING_MOVETO':
                e.append('INVALID_NAV_REQUEST')
            if nav_t and now - nav_t[-1] < 750:
                e.append('NAV_SPAM')
            nav_t.append(now)
            if len(nav_t) > 20: e.append('NAV_REQUEST_OVER_LIMIT')
        elif kind == 'MOVE_SAMPLE':
            if state != 'SPAWNED' or not pos(event.get('pos')):
                e.append('INVALID_MOVE_SAMPLE'); continue
            if (event.get('source') != 'SERVER_HUMANOID_ROOT' or
                event.get('server_owned') is not True or event.get('grounded') is not True or
                event.get('root_anchored') is not False):
                e.append('NOT_REAL_SERVER_MOVEMENT')
            if last_pos is not None:
                delta = dist(last_pos, event['pos'])
                gap = now - last_pos_ms
                if gap == 0 and delta > 0:
                    e.append('ZERO_TIME_TELEPORT')
                if gap > 0 and delta > 16.0 * gap / 1000.0 + 0.1:
                    e.append('IMPLAUSIBLE_MOVEMENT_SPEED')
                distance_moved += delta
            last_pos, last_pos_ms = event['pos'], now
        elif kind == 'TELEGRAPH':
            aid = event.get('attack_id')
            if state != 'SPAWNED' or not token(aid) or aid in attacks:
                e.append('INVALID_OR_DUPLICATE_TELEGRAPH')
            else:
                attacks[aid] = {'start': now, 'resolve': None}
                n_telegraph += 1
                if n_telegraph > 3: e.append('ATTACK_COUNT_OVER_LIMIT')
            if event.get('visible_blue') is not True or event.get('visible_red') is not True:
                e.append('TELEGRAPH_NOT_VISIBLE_BOTH_TEAMS')
        elif kind == 'ATTACK_RESOLVE':
            aid = event.get('attack_id')
            a = attacks.get(aid) if token(aid) else None
            if state != 'SPAWNED' or a is None or a['resolve'] is not None:
                e.append('INVALID_OR_DUPLICATE_RESOLVE')
            else:
                gap = now - a['start']
                if not 2000 <= gap <= 5000:
                    e.append('TELEGRAPH_NOT_2S')
                a['resolve'] = now
            if event.get('receipt') != 'CORE_STOMP_RESOLVE' or event.get('fresh_server_snapshot') is not True:
                e.append('NONCANONICAL_ATTACK_RECEIPT')
        elif kind == 'HIT':
            aid, target = event.get('attack_id'), event.get('target_token')
            a = attacks.get(aid) if token(aid) else None
            if a is None or a['resolve'] is None or not 0 <= now-a['resolve'] <= 150:
                e.append('HIT_WITHOUT_RECENT_RESOLVE')
            if not token(aid) or not token(target) or (aid, target) in hit_pairs:
                e.append('DUPLICATE_OR_INVALID_HIT_TARGET')
            else: hit_pairs.add((aid, target))
            if not is_int(event.get('damage'), 1, 8): e.append('INVALID_DAMAGE')
            if (event.get('server_los') is not True or event.get('safezone') is not False or
                event.get('invulnerable') is not False or event.get('target_alive') is not True or
                event.get('server_roster_verified') is not True):
                e.append('UNAUTHORIZED_HIT')
            d, maximum = event.get('distance_studs'), event.get('max_range_studs')
            if not finite_num(d,0,1000) or not finite_num(maximum,0,12) or d > maximum:
                e.append('INVALID_HIT_DISTANCE')
            n_hits += 1
        elif kind == 'HIT_DENIED':
            aid = event.get('attack_id')
            if not token(aid) or aid not in attacks or attacks[aid]['resolve'] is None or event.get('reason') not in ('LOS', 'SAFEZONE', 'IMMUNE', 'STALE_ROUND', 'DEAD'):
                e.append('INVALID_HIT_DENIAL')
            n_denied += 1
        elif kind == 'REMOTE_REJECTED':
            if event.get('reason') not in ('CLIENT_DAMAGE', 'CLIENT_BOSS_SPAWN', 'CLIENT_CFRAME'):
                e.append('INVALID_REMOTE_REJECTION')
            n_rejected += 1
        elif kind == 'ROUND_END':
            if state != 'SPAWNED' or round_done: e.append('INVALID_ROUND_END')
            round_done = True
        elif kind == 'CLEANUP':
            if state != 'SPAWNED' or n_cleanup or not round_done or event.get('boss_instances_remaining') != 0:
                e.append('INVALID_CLEANUP')
            else:
                n_cleanup += 1; stage_end = True
                if spawn_ms is not None and now - spawn_ms > 14_000:
                    e.append('BOSS_TTL_EXCEEDED')
    if state == 'INIT' or start_ms is None: e.append('MISSING_ROUND_START')
    if not stage_end or n_cleanup != 1: e.append('MISSING_FINAL_CLEANUP')
    if n_spawn != 1: e.append('SPAWN_NOT_EXACTLY_ONE')
    if not nav_t or distance_moved < 0.5: e.append('NO_OBSERVED_PATHFINDING_MOVEMENT')
    if not n_telegraph or not n_hits: e.append('NO_OBSERVED_TELEGRAPH_AND_HIT')
    if not n_denied or not n_rejected: e.append('MISSING_NEGATIVE_ATTACK_OR_REMOTE_TEST')
    return sorted(set(e))


def main(argv=None):
    p = argparse.ArgumentParser(description='Validate anonymous Gorogan server trace contract, NOT Studio provenance.')
    p.add_argument('trace', help='Local anonymized JSON path; read-only, symlink rejected')
    p.add_argument('--format', choices=('text', 'json'), default='text')
    a = p.parse_args(argv)
    try:
        obj = read_trace(a.trace)
        errs = validate(obj)
    except InvalidTrace as exc:
        errs = ['INPUT_BLOCKED:' + str(exc)]
        obj = {}
    ok = len(errs) == 0
    status = ('TRACE_CONTRACT_PASS_NOT_STUDIO_QA' if ok and obj.get('trace_origin') == 'STUDIO_SERVER_OUTPUT' else
              'SYNTHETIC_PASS_NOT_STUDIO_QA' if ok else 'TRACE_CONTRACT_FAIL_OR_BLOCKED')
    result = {'packet_id':'P0D-D07-GOROGAN-STUDIO-TRACE-GATE-20261110-01',
              'status':status, 'pass':ok, 'errors':errs,
              'evidence_note':'Trace data and declared server authority are not independently authenticated; Studio QA needs OWNER PC corroboration.'}
    if a.format == 'json': print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(status)
        for item in errs: print(' - ' + item)
        print(result['evidence_note'])
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
