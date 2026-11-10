#!/usr/bin/env python3
"""Source-free D14 CART triad contract validator for *sanitized* PC traces.

This is an OFFLINE consistency checker, NOT a Roblox/Studio run or proof a
recording came from a trusted server. It never imports private gameplay code.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

SCHEMA = 'P0D_D14_TRIAD_TRACE_V1'
GAME = 'TRAP_RAIDERS'
WORK = 'p0d-siege-v19'
EXPECTED_REFS = {
    'seats': '0bcf39c22c583604d72ccac47d29fc9d87b7e662',
    'motion': '2cd3fb9b31bfe7817ca0ceba7456300c3a41bd12',
    'visual': '3c78cd0af618f320fe9d0aafe7569e1e9b95b4b0',
}
SUPERSEDED = 'cae5691b622045af57674d922a08a96764354412'
EVENT_TYPES = {'ROUND_START', 'BOARD', 'UNBOARD', 'DISABLE', 'ADVANCE', 'POSE', 'VISUAL', 'ROUND_END'}
MAX_FILE_BYTES = 2_000_000
MAX_EVENTS = 10_000
MAX_CARTS = 2
MAX_TIME_MS = 1_800_000
MAX_GAP_MS = 2000
EPS = 0.02
TOKEN = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,31}\Z')
PLAYER = re.compile(r'p_[A-Za-z0-9_-]{1,16}\Z')

class TraceError(ValueError):
    pass


def must(value, condition, code):
    if not condition:
        raise TraceError(code)
    return value


def strict_loads(data):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise TraceError('DUPLICATE_JSON_KEY')
            d[k] = v
        return d
    def invalid_constant(s):
        raise TraceError('NON_FINITE_JSON_CONSTANT')
    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=invalid_constant)
    except (ValueError, UnicodeError) as e:
        if isinstance(e, TraceError):
            raise
        raise TraceError('INVALID_JSON') from e


def number(v):
    return type(v) in (int, float) and math.isfinite(v)


def integer(v, lo, hi):
    return type(v) is int and lo <= v <= hi


def vector(v):
    must(v, isinstance(v, list) and len(v) == 3 and all(number(x) and abs(x) <= 2000 for x in v), 'BAD_POSITION')
    return tuple(v)


def dist(a, b):
    return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))


def lerp(a, b, f):
    return tuple(a[i]+(b[i]-a[i])*f for i in range(3))


def route_position(nodes, leg, progress):
    if leg == len(nodes):
        must(progress, abs(progress) < EPS, 'BAD_FINAL_PROGRESS')
        return nodes[-1]
    return lerp(nodes[leg-1], nodes[leg], progress)


def validated_routes(doc):
    routes = must(doc.get('routes'), isinstance(doc.get('routes'), list) and 1 <= len(doc['routes']) <= MAX_CARTS, 'BAD_ROUTE_SET')
    by_id = {}
    occupied_teams = set()
    for obj in routes:
        must(obj, isinstance(obj, dict) and set(obj) == {'cart_id','team','speed','nodes'}, 'BAD_ROUTE_FIELDS')
        cid, team = obj['cart_id'], obj['team']
        must(cid, isinstance(cid,str) and TOKEN.fullmatch(cid) and cid not in by_id, 'DUPLICATE_CART_ID')
        must(team, team in ('BLUE','RED') and team not in occupied_teams, 'DUPLICATE_OR_BAD_TEAM')
        speed = obj['speed']
        must(speed, number(speed) and 2 <= speed <= 16, 'BAD_SPEED')
        points = obj['nodes']
        must(points, isinstance(points, list) and 2 <= len(points) <= 24, 'BAD_NODES')
        nodes = [vector(n) for n in points]
        for a,b in zip(nodes,nodes[1:]):
            must(None, 6 <= dist(a,b) <= 80, 'BAD_LEG_DISTANCE')
        by_id[cid] = {'team':team,'speed':speed,'nodes':nodes,'seats':{},'last_pose':None,'last_pose_seq':None,'awaiting_advance':False,'last_advance':0,'issued_advance':False,'stopped_at':None}
        occupied_teams.add(team)
    return by_id


def _id(e, k, regex=TOKEN):
    v = e.get(k)
    must(v, isinstance(v,str) and regex.fullmatch(v), 'BAD_IDENTIFIER_'+k.upper())
    return v


def _assert_exact(e, keys, name):
    must(None, set(e) == set(keys), 'BAD_'+name+'_FIELDS')


def validate(doc):
    must(doc, isinstance(doc, dict), 'ROOT_NOT_OBJECT')
    must(doc, doc.get('schema') == SCHEMA and doc.get('game_id') == GAME and doc.get('work_id') == WORK, 'WRONG_PROJECT')
    must(None, doc.get('reference_commits') == EXPECTED_REFS, 'WRONG_OR_SUPERSEDED_REFERENCE')
    must(None, SUPERSEDED not in json.dumps(doc.get('reference_commits'), sort_keys=True), 'SUPERSEDED_PACKAGE')
    provenance = doc.get('provenance')
    must(None, provenance in ('SYNTHETIC', 'PC_SANITIZED_UNVERIFIED'), 'BAD_PROVENANCE')
    round_id = doc.get('round_id')
    must(None, isinstance(round_id,str) and TOKEN.fullmatch(round_id), 'BAD_ROUND_ID')
    carts=validated_routes(doc)
    events=doc.get('events')
    must(None, isinstance(events,list) and 2 <= len(events) <= MAX_EVENTS, 'BAD_EVENT_COUNT')
    last_seq=0
    last_time=-1
    started=False
    ended=False
    visuals=0
    poses=0
    # No client may grant a seat, issue commands or author movement; event source is
    # a field in a *sanitized trace*, NOT cryptographic provenance.
    for idx,e in enumerate(events):
        must(None, isinstance(e,dict), 'EVENT_NOT_OBJECT')
        kind=e.get('type')
        must(None, kind in EVENT_TYPES, 'UNKNOWN_EVENT_TYPE')
        seq=e.get('seq')
        ms=e.get('ms')
        must(None, integer(seq,1,1_000_000) and seq>last_seq, 'NONMONOTONIC_SEQUENCE')
        must(None, integer(ms,0,MAX_TIME_MS) and ms>=last_time, 'TIME_REGRESSION')
        last_seq,last_time=seq,ms
        must(None, e.get('round_id') == round_id, 'CROSS_ROUND_EVENT')
        source=e.get('source')
        must(None, source == ('CLIENT_VIEW' if kind=='VISUAL' else 'SERVER'), 'CLIENT_AUTHORITY_ATTEMPT')
        common={'type','seq','ms','round_id','source'}
        if kind=='ROUND_START':
            _assert_exact(e, common, 'ROUND_START')
            must(None, idx == 0 and not started, 'ROUND_START_NOT_FIRST')
            started=True
            continue
        must(None, started and not ended, 'EVENT_OUTSIDE_ROUND')
        if kind=='ROUND_END':
            _assert_exact(e, common, 'ROUND_END')
            must(None, idx == len(events)-1, 'ROUND_END_NOT_LAST')
            ended=True
            for state in carts.values():
                state['seats'].clear()
                state['awaiting_advance']=False
            continue
        cid=_id(e,'cart_id')
        must(None, cid in carts, 'UNKNOWN_CART')
        state=carts[cid]
        must(None, e.get('team') == state['team'], 'CART_TEAM_MISMATCH')
        if kind=='BOARD':
            _assert_exact(e, common|{'cart_id','team','player','seat','alive','mounted','carrier','snared'}, 'BOARD')
            player=_id(e,'player',PLAYER)
            seat=e['seat']
            must(None, seat in ('DRIVER','PASSENGER'), 'BAD_SEAT')
            must(None, e['alive'] is True and e['mounted'] is True and e['carrier'] is False and e['snared'] is False, 'INELIGIBLE_BOARD')
            must(None, seat not in state['seats'] and player not in state['seats'].values(), 'DOUBLE_SEAT')
            must(None, all(player not in c['seats'].values() for c in carts.values()), 'CROSS_CART_PLAYER')
            state['seats'][seat]=player
        elif kind=='UNBOARD':
            _assert_exact(e, common|{'cart_id','team','player','seat'}, 'UNBOARD')
            player=_id(e,'player',PLAYER)
            seat=e['seat']
            must(None, state['seats'].get(seat)==player, 'UNBOARD_NON_OCCUPANT')
            del state['seats'][seat]
            if seat=='DRIVER':
                state['awaiting_advance']=False
                state['issued_advance']=False
                state['stopped_at']=state['last_pose']['position'] if state['last_pose'] else None
        elif kind=='DISABLE':
            _assert_exact(e, common|{'cart_id','team','player','reason'}, 'DISABLE')
            player=_id(e,'player',PLAYER)
            must(None, e['reason'] in ('DIED','DISCONNECT','EGG','SNARED','ROUND_RESET'), 'BAD_DISABLE_REASON')
            seats=[key for key,value in state['seats'].items() if value==player]
            must(None, len(seats)==1, 'DISABLE_NON_OCCUPANT')
            key=seats[0]
            del state['seats'][key]
            if key=='DRIVER':
                state['awaiting_advance']=False
                state['issued_advance']=False
                state['stopped_at']=state['last_pose']['position'] if state['last_pose'] else None
        elif kind=='ADVANCE':
            _assert_exact(e, common|{'cart_id','team','player','command_seq','leg'}, 'ADVANCE')
            player=_id(e,'player',PLAYER)
            serial=e['command_seq']
            must(None, state['seats'].get('DRIVER')==player, 'NON_DRIVER_COMMAND')
            must(None, integer(serial,1,1_000_000) and serial>state['last_advance'], 'REPLAY_COMMAND')
            must(None, not state['awaiting_advance'], 'DOUBLE_COMMAND_BEFORE_POSE')
            previous=state['last_pose']
            must(None, previous is not None and previous['moving'] is False, 'ADVANCE_BEFORE_STOPPED_POSE')
            must(None, previous['leg']==e['leg'] and e['leg']<len(state['nodes']), 'WRONG_LEG_REQUEST')
            must(None, abs(previous['progress'])<EPS, 'NONZERO_PROGRESS_ON_ADVANCE')
            state['awaiting_advance']=True
            state['issued_advance']=True
            state['last_advance']=serial
        elif kind=='POSE':
            _assert_exact(e, common|{'cart_id','team','position','leg','progress','moving'}, 'POSE')
            leg,prog,moving=e['leg'],e['progress'],e['moving']
            must(None, integer(leg,1,len(state['nodes'])) and number(prog) and 0<=prog<=1 and type(moving) is bool, 'BAD_POSE_PROGRESS')
            p=vector(e['position'])
            if state['stopped_at'] is not None:
                must(None, not moving and dist(p,state['stopped_at'])<=EPS, 'MOVEMENT_AFTER_DRIVER_INVALIDATION')
                state['stopped_at']=None
            target=route_position(state['nodes'],leg,prog)
            must(None, dist(p,target)<=EPS, 'OFF_RAIL_POSE')
            prev=state['last_pose']
            if prev is None:
                must(None, leg==1 and prog==0 and not moving and dist(p,state['nodes'][0])<=EPS, 'INVALID_INITIAL_POSE')
            else:
                dt=(ms-prev['ms'])/1000
                must(None, ms>=prev['ms'] and ms-prev['ms']<=MAX_GAP_MS, 'POSE_GAP_UNVERIFIABLE')
                must(None, dist(prev['position'],p)<=state['speed']*dt+EPS, 'EXCESSIVE_SPEED_OR_TELEPORT')
                must(None, leg>=prev['leg'] and leg<=prev['leg']+1, 'LEG_SKIP_OR_REWIND')
                if leg==prev['leg']:
                    must(None, prog+EPS>=prev['progress'], 'BACKWARDS_PROGRESS')
                else:
                    must(None, not moving and prog<EPS and dist(p,state['nodes'][leg-1])<=EPS, 'LEG_CHANGE_WITHOUT_STOP')
                    state['issued_advance']=False
            if moving:
                must(None, state['seats'].get('DRIVER') is not None, 'MOVING_WITHOUT_DRIVER')
                must(None, state['issued_advance'], 'MOVING_WITHOUT_SERVER_ADVANCE')
                must(None, leg<len(state['nodes']), 'MOVING_AFTER_END')
            state['awaiting_advance']=False
            state['last_pose']={'ms':ms,'seq':seq,'position':p,'leg':leg,'progress':prog,'moving':moving}
            state['last_pose_seq']=seq
            poses+=1
        elif kind=='VISUAL':
            _assert_exact(e, common|{'cart_id','team','pose_seq','seat_count','visual_kind'}, 'VISUAL')
            must(None, e['visual_kind']=='CART', 'RAFT_NOT_THIS_CONTRACT')
            must(None, integer(e['pose_seq'],1,1_000_000) and e['pose_seq']==state['last_pose_seq'], 'STALE_OR_UNAUTHORIZED_VISUAL_POSE')
            must(None, integer(e['seat_count'],0,2) and e['seat_count']==len(state['seats']), 'VISUAL_SEAT_COUNT_MISMATCH')
            must(None, state['last_pose'] is not None and 0<=ms-state['last_pose']['ms']<=1000, 'STALE_VISUAL_TTL')
            visuals+=1
    must(None, started and ended, 'ROUND_NOT_CLOSED')
    must(None, poses>=1, 'NO_POSE_SNAPSHOTS')
    return {
        'schema':'P0D_D14_TRIAD_RESULT_V1',
        'result':'CONSISTENT_TRACE_REVIEW_ONLY',
        'source_provenance':provenance,
        'game_id':GAME,
        'work_id':WORK,
        'cart_routes':len(carts),
        'events_checked':len(events),
        'pose_events':poses,
        'visual_events':visuals,
        'studio_qa':'NOT_ATTESTED_BY_THIS_TOOL',
        'windows_restore':'NOT_ATTESTED_BY_THIS_TOOL',
        'next_gate':'OWNER_PC_CODEX_REVIEW_SOURCE_ADAPTERS_AND_REAL_STUDIO_QA',
    }


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('trace',type=Path)
    args=ap.parse_args(argv)
    try:
        if args.trace.is_symlink() or args.trace.stat().st_size>MAX_FILE_BYTES:
            raise TraceError('UNSAFE_TRACE_FILE')
        doc=strict_loads(args.trace.read_bytes())
        result=validate(doc)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (TraceError,OSError,ValueError,TypeError) as ex:
        print('D14_TRIAD_BLOCKED:'+str(ex).splitlines()[0][:150],file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
