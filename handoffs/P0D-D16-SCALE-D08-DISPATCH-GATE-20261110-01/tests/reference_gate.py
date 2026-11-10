"""Pure stdlib oracle for D08-to-D16 scale FX gate interface.
No Roblox/Luau runtime execution is implied by passing these checks.
"""
import math

WEATHER = {'WX01_METEOR','WX02_SMALL','WX03_CROWN','WX04_GLIDE','WX05_CLOCK'}
STAGES = {'S1','S2','S3','S4'}

def finite(v):
    return type(v) in (int,float) and math.isfinite(v)

def valid_id(x):
    return type(x) is str and 1 <= len(x) <= 96 and all(c.isascii() and (c.isalnum() or c in '_-') for c in x)

def norm_roster(raw):
    if type(raw) not in (list,tuple) or not 1 <= len(raw) <= 24:
        return None
    if not all(finite(x) and x == int(x) and 1 <= x <= 9007199254740991 for x in raw):
        return None
    if len(set(raw)) != len(raw):
        return None
    return sorted(raw)

class ScaleCoreStub:
    def __init__(self):
        self.active = None;self.seen=set();self.last_ms=None
    def begin(self, a):
        key=(a['matchId'],a['epoch'])
        if key in self.seen or self.active is not None:return False,'DUPLICATE_OR_ACTIVE'
        if a['effect']=='GIANT_ONE' and (not finite(a['targetUserId']) or a['targetUserId'] != int(a['targetUserId']) or a['targetUserId'] not in a['serverRoster']):return False,'TARGET_NOT_IN_ROSTER'
        self.seen.add(key)
        self.last_ms=a['nowMs']
        users=[a['targetUserId']] if a['effect']=='GIANT_ONE' else list(a['serverRoster'])
        self.active=dict(a, expiresAtMs=a['nowMs']+8000,userIds=users,visualScale=1.6 if a['effect']=='GIANT_ONE' else .7)
        return True,'STARTED'
    def snapshot(self,ms,match_id,epoch):
        if self.last_ms is not None and ms<self.last_ms:return None,'CLOCK_BACKWARDS'
        self.last_ms=ms
        a=self.active
        if a is None:return None,'INACTIVE'
        if ms>=a['expiresAtMs'] or (a['matchId'],a['epoch'])!=(match_id,epoch):
            self.active=None;return None,'CLOSED_OR_EXPIRED'
        return dict(a),'ACTIVE'
    def close(self,match_id,epoch,ms):
        if self.last_ms is not None and ms<self.last_ms:return False,'CLOCK_BACKWARDS'
        self.last_ms=ms
        if self.active is None or (self.active['matchId'],self.active['epoch'])!=(match_id,epoch):
            return False,'NOT_ACTIVE'
        self.active=None;return True,'CLOSED'

class Gate:
    def __init__(self, *, read_round, read_roster, mapping=None, choose_target=None, enabled=False, owner_approved=False, renderer_ready=False):
        self.read_round=read_round;self.read_roster=read_roster;self.mapping=mapping
        self.choose_target=choose_target
        self.enabled=enabled is True and owner_approved is True and renderer_ready is True
        self.active=None;self.busy=False;self.stopped_reason=None;self.core=ScaleCoreStub()
    def _round(self):
        try:s=self.read_round()
        except Exception:return None,'READ_ROUND_FAILED'
        if type(s) is not dict:return None,'READ_ROUND_FAILED'
        if (not valid_id(s.get('matchId')) or s.get('stage') not in STAGES
            or not finite(s.get('epoch')) or not 1 <= s['epoch'] < 1024 or s['epoch']!=int(s['epoch'])
            or not finite(s.get('now')) or not 0 <= s['now'] <= 1e10
            or not finite(s.get('startedAt')) or not finite(s.get('deadline'))
            or not 0<=s['startedAt']<=s['now'] or not s['startedAt']<s['deadline']<=1e10
            or type(s.get('active')) is not bool):return None,'ROUND_INVALID'
        return s.copy(),None
    def _roster(self):
        try:return norm_roster(self.read_roster())
        except Exception:return None
    @staticmethod
    def matches(s,e):
        return (s['active'] is True and s['matchId']==e['matchId']
                and s['stage']==e['stage'] and s['epoch']==e['epoch'])
    def activate(self,e):
        if not self.enabled:return False,self.stopped_reason or 'DISABLED_DEFAULT'
        if self.busy:return False,'BUSY'
        self.busy=True
        try:
            if (type(e) is not dict or e.get('kind')!='WEATHER' or e.get('phase')!='ACTIVATE'
                or e.get('subtype') not in WEATHER or not valid_id(e.get('matchId'))
                or e.get('stage') not in STAGES or not finite(e.get('epoch'))
                or not 1 <= e['epoch'] <1024 or e['epoch'] != int(e['epoch'])
                or not finite(e.get('validUntil'))):return False,'INVALID_D08_ENVELOPE'
            effect=self.mapping.get(e['subtype']) if type(self.mapping) is dict else None
            if type(self.mapping) is not dict:return False,'NO_EXPLICIT_MAPPING'
            if effect not in ('GIANT_ONE','MINI_ALL'):return False,'UNAPPROVED_SUBTYPE'
            s,why=self._round()
            if s is None:return False,why
            if not self.matches(s,e):return False,'ROUND_MISMATCH'
            if not s['now']<e['validUntil']<=s['now']+9:return False,'INVALID_EVENT_DEADLINE'
            roster=self._roster()
            if roster is None:return False,'ROSTER_UNAVAILABLE'
            target=None
            if effect=='GIANT_ONE':
                if self.choose_target is None:return False,'TARGET_CALLBACK_MISSING'
                try:target=self.choose_target(roster)
                except Exception:return False,'TARGET_CALLBACK_FAILED'
            s2,why=self._round()
            if s2 is None:return False,why
            if (not self.matches(s2,e) or s2['now']<s['now']
                or s['startedAt']!=s2['startedAt'] or s['deadline']!=s2['deadline']
                or s2['now']>=e['validUntil']):return False,'ROUND_CHANGED_DURING_CALLBACK'
            roster2=self._roster()
            if roster2!=roster:return False,'ROSTER_CHANGED'
            ms=math.floor(s2['now']*1000+1e-6)
            ok,why=self.core.begin({'matchId':e['matchId'],'epoch':e['epoch'],
                'eventId':e['matchId']+':'+str(e['epoch'])+':'+e['subtype'],
                'nowMs':ms,'effect':effect,'targetUserId':target,'serverRoster':roster2})
            if not ok:return False,why
            self.active=dict(matchId=e['matchId'],stage=e['stage'],epoch=e['epoch'],
                             subtype=e['subtype'],deadlineMs=math.floor(e['validUntil']*1000))
            return True,'STARTED'
        except Exception:
            self.enabled=False;self.stopped_reason='DISPATCH_EXCEPTION'
            return False,'DISPATCH_EXCEPTION'
        finally:self.busy=False
    def snapshot(self):
        if not self.enabled or self.active is None:return None,'INACTIVE'
        s,why=self._round()
        if s is None:
            self.enabled=False;self.stopped_reason=why;return None,why
        a=self.active;ms=math.floor(s['now']*1000+1e-6)
        if not self.matches(s,a) or ms>=a['deadlineMs']:
            ok,_=self.core.close(a['matchId'],a['epoch'],ms)
            self.active=None
            if not ok:
                self.enabled=False;self.stopped_reason='CLOSE_FAILED';return None,'CLOSE_FAILED'
            return None,'ROUND_CLOSED_OR_EXPIRED'
        snap,why=self.core.snapshot(ms,s['matchId'],s['epoch'])
        if snap is None:
            self.active=None
            if why in ('CLOCK_BACKWARDS','INVALID_CLOCK_OR_STATE'):
                self.enabled=False;self.stopped_reason=why
        return snap,why
    def cleanup(self,e):
        a=self.active
        if a is None:return False,'INACTIVE'
        if (type(e) is not dict or 'phase' in e and e['phase'] is not None
            or e.get('kind')!='WEATHER'
            or any(e.get(k)!=a[k] for k in ('matchId','stage','epoch','subtype'))):
            return False,'CLEANUP_MISMATCH'
        s,why=self._round()
        if s is None:
            self.enabled=False;self.stopped_reason=why;return False,why
        ok,why=self.core.close(a['matchId'],a['epoch'],math.floor(s['now']*1000+1e-6))
        self.active=None
        if not ok:self.enabled=False;self.stopped_reason='CLOSE_FAILED'
        return ok,why
    def stop(self):
        self.enabled=False;self.stopped_reason='OWNER_STOP';self.active=None
