"""Independent Python behavior model for server-only reference glide permission.

NOT an original-source reproduction or Roblox physics implementation.
"""
from __future__ import annotations

import math

BOOLEANS = ('alive','activeRound','teamValid','onGround','hasEgg','mounted','snared','rewinding')


def is_num(x):
    return isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x)


def positive_int(x):
    return is_num(x) and x >= 1 and x <= 2**53 - 1 and x == int(x)


def new_state(user_id, epoch):
    if not positive_int(user_id) or not positive_int(epoch):
        raise ValueError('invalid user or epoch')
    return dict(userId=user_id, epoch=epoch, lastSeq=0, lastNow=-1,
                mode='IDLE',activeUntil=0,cooldownUntil=0,teamToken=None)


def decision(action, reason, expires_at=None):
    out={'action':action, 'reason':reason}
    if expires_at is not None:
        out.update(horizontalSpeedCeiling=18, descentVelocityFloor=-10, expiresAt=expires_at)
    return out


def stop(s, now, reason):
    s.update(mode='COOLDOWN', activeUntil=0, teamToken=None, cooldownUntil=now+25)
    return s,decision('STOP',reason)


def complete(x):
    return isinstance(x, dict) and all(type(x.get(k)) is bool for k in BOOLEANS) and isinstance(x.get('teamToken'), str) and 0 < len(x['teamToken']) <= 96 and is_num(x.get('fallDistance')) and x['fallDistance'] >= 0 and is_num(x.get('verticalVelocity'))


def eligible(x, original_team):
    return (x['alive'] and x['activeRound'] and x['teamValid'] and x['teamToken']==original_team and not x['onGround'] and x['verticalVelocity'] < 0 and not any(x[k] for k in ('hasEgg','mounted','snared','rewinding')))


def step(state, intent, snapshot, config=None):
    if not isinstance(state,dict) or not isinstance(snapshot,dict):
        return state,decision('STOP','SNAPSHOT_MISSING')
    if not positive_int(snapshot.get('userId')) or snapshot['userId']!=state['userId'] or not positive_int(snapshot.get('epoch')) or not positive_int(snapshot.get('seq')) or not is_num(snapshot.get('now')) or snapshot['now'] < 0:
        return state,decision('STOP','IDENTITY_OR_CLOCK_INVALID')
    if snapshot['epoch'] < state['epoch'] or (snapshot['epoch'] == state['epoch'] and snapshot['seq'] <= state['lastSeq']) or snapshot['now'] < state['lastNow']:
        return state,decision('STOP','STALE_AUTHORITY')
    if intent not in ('START','STOP','TICK'):
        if state['mode']=='ACTIVE':
            failed=dict(state,lastSeq=snapshot['seq'],lastNow=snapshot['now'])
            return stop(failed,snapshot['now'],'UNKNOWN_INTENT')
        return state,decision('STOP','UNKNOWN_INTENT')
    if not complete(snapshot):
        if state['mode']=='ACTIVE':
            failed=dict(state,lastSeq=snapshot['seq'],lastNow=snapshot['now'])
            return stop(failed,snapshot['now'],'AUTHORITY_INCOMPLETE')
        return state,decision('STOP','AUTHORITY_INCOMPLETE')
    s=dict(state,lastSeq=snapshot['seq'],lastNow=snapshot['now'])
    if snapshot['epoch'] > state['epoch']:
        was_active=state['mode']=='ACTIVE'
        s.update(epoch=snapshot['epoch'],mode='IDLE',activeUntil=0,cooldownUntil=0,teamToken=None)
        return s,decision('STOP' if was_active else 'NONE','ROUND_CHANGED')
    if not isinstance(config,dict) or config.get('enabled') is not True:
        if state['mode']=='ACTIVE':
            return stop(s,snapshot['now'],'DISABLED')
        return s,decision('NONE','DISABLED')
    if state['mode']=='ACTIVE':
        if not eligible(snapshot,state['teamToken']):
            return stop(s,snapshot['now'],'AUTHORITY_LOST')
        if snapshot['now']>=state['activeUntil']:
            return stop(s,snapshot['now'],'TIME_LIMIT')
        if intent=='STOP':
            return stop(s,snapshot['now'],'USER_STOP')
        return s,decision('MAINTAIN','ACTIVE',s['activeUntil'])
    if intent!='START':
        return s,decision('NONE','NO_REQUEST')
    if snapshot['now']<state['cooldownUntil']:
        return s,decision('DENY','COOLDOWN')
    if not eligible(snapshot,snapshot['teamToken']) or not 3<=snapshot['fallDistance']<=60:
        return s,decision('DENY','NOT_ELIGIBLE')
    s.update(mode='ACTIVE',teamToken=snapshot['teamToken'],activeUntil=snapshot['now']+5)
    return s,decision('START','ELIGIBLE',s['activeUntil'])
