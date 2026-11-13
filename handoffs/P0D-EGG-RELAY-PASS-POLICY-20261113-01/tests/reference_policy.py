"""Independent Python reference for deterministic policy behavior (NOT Luau runtime)."""
from __future__ import annotations
from copy import deepcopy
from math import isfinite


def integer(v):
    return type(v) in (int, float) and isfinite(v) and v % 1 == 0 and abs(v) < 1e9


def number(v):
    return type(v) in (int, float) and isfinite(v) and abs(v) < 1e9


def point(p):
    return isinstance(p, dict) and all(number(p.get(k)) for k in ('x','y','z'))


def check(w, r):
    if not isinstance(w, dict) or not isinstance(r,dict): return 'INVALID_INPUT'
    if w.get('phase') != 'PLAYING' or not integer(w.get('roundEpoch')) or w['roundEpoch'] < 1: return 'ROUND_NOT_PLAYING'
    if not integer(r.get('roundEpoch')) or r['roundEpoch'] != w['roundEpoch']: return 'STALE_ROUND'
    if not integer(r.get('actorUserId')) or not integer(r.get('targetUserId')) or r['actorUserId'] == r['targetUserId']: return 'INVALID_PARTICIPANTS'
    if not isinstance(r.get('eggId'),str) or not 1 <= len(r['eggId']) <= 64: return 'INVALID_EGG_ID'
    if not integer(r.get('seq')) or r['seq'] < 1 or not integer(r.get('expectedTransferSeq')) or r['expectedTransferSeq'] < 0: return 'INVALID_REQUEST_SEQUENCE'
    if not number(w.get('nowSec')) or w['nowSec'] < 0: return 'INVALID_SERVER_CLOCK'
    if not all(isinstance(w.get(k),dict) for k in ('players','eggs','lastAcceptedSeqByUser')): return 'MISSING_AUTHORITY_STATE'
    last=w['lastAcceptedSeqByUser'].get(r['actorUserId'])
    if last is not None and (not integer(last) or r['seq'] <= last): return 'REPLAYED_REQUEST'
    egg=w['eggs'].get(r['eggId'])
    if not isinstance(egg,dict) or egg.get('id') != r['eggId'] or egg.get('phase') != 'CARRIED' or egg.get('carrierUserId') != r['actorUserId'] or egg.get('relayEligible') is not True: return 'NOT_AUTHORIZED_CARRIER'
    if not integer(egg.get('transferSeq')) or r['expectedTransferSeq'] != egg['transferSeq']: return 'STALE_EGG_VERSION'
    t=egg.get('lastRelayAtSec')
    if t is not None:
        if not number(t) or t > w['nowSec']: return 'CLOCK_OR_COOLDOWN_INVALID'
        if w['nowSec'] - t < 12: return 'EGG_PASS_COOLDOWN'
    a=w['players'].get(r['actorUserId']); b=w['players'].get(r['targetUserId'])
    if not isinstance(a,dict) or not isinstance(b,dict): return 'PLAYER_MISSING'
    if a.get('alive') is not True or b.get('alive') is not True or a.get('stunned') is True or b.get('stunned') is True or a.get('restrained') is True or b.get('restrained') is True: return 'PLAYER_NOT_ELIGIBLE'
    if a.get('team') not in ('RED','BLUE') or a.get('team') != b.get('team'): return 'WRONG_TEAM'
    if a.get('carriedEggId') != r['eggId'] or b.get('carriedEggId') is not None: return 'CARRIER_INVENTORY_CONFLICT'
    if not point(a.get('serverPosition')) or not point(b.get('serverPosition')): return 'UNVERIFIED_POSITIONS'
    x=a['serverPosition']; y=b['serverPosition']; dx=x['x']-y['x']; dy=x['y']-y['y']; dz=x['z']-y['z']
    if abs(dy)>4 or dx*dx+dz*dz>64: return 'OUT_OF_PASS_RANGE'
    if w.get('serverLineOfSightClear') is not True: return 'PASS_LINE_OF_SIGHT_BLOCKED'
    return 'ACCEPT_POLICY_ONLY'


def fixture():
    w={'phase':'PLAYING','roundEpoch':7,'nowSec':100,
      'lastAcceptedSeqByUser':{1:4},'serverLineOfSightClear':True,
      'eggs':{'E2':{'id':'E2','phase':'CARRIED','carrierUserId':1,
                    'relayEligible':True,'transferSeq':3,'lastRelayAtSec':80}},
      'players':{
        1:{'alive':True,'stunned':False,'restrained':False,'team':'RED',
          'carriedEggId':'E2','serverPosition':{'x':0,'y':0,'z':0}},
        2:{'alive':True,'stunned':False,'restrained':False,'team':'RED',
          'carriedEggId':None,'serverPosition':{'x':8,'y':0,'z':0}},
      }}
    r={'actorUserId':1,'targetUserId':2,'roundEpoch':7,'eggId':'E2','seq':5,'expectedTransferSeq':3}
    return deepcopy(w),deepcopy(r)
