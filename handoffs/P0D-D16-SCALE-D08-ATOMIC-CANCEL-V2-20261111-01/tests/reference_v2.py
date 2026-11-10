"""Offline Python analogue for D16-D08 cancellable adapter; NOT native Luau execution."""
import math

WEATHER = {'WX01_METEOR','WX02_SMALL','WX03_CROWN','WX04_GLIDE','WX05_CLOCK'}
STAGES = {'S1','S2','S3','S4'}

def finite(v):
    return type(v) in (int,float) and math.isfinite(v)

def valid_id(v):
    return isinstance(v,str) and 1 <= len(v) <= 96 and all(c.isascii() and (c.isalnum() or c in '_-') for c in v)

def norm_roster(v):
    if type(v) not in (tuple,list) or not 1 <= len(v) <= 24: return None
    if any(not finite(i) or not 1 <= i <= 9007199254740991 or i%1 != 0 for i in v):return None
    if len(set(v))!=len(v):return None
    return sorted(v)

class ScaleCoreStub:
    def __init__(self):self.active=None;self.last_ms=None;self.seen=set();self.close_count=0
    def begin(self, d):
        key=(d['matchId'],d['epoch'])
        if self.active is not None or key in self.seen:return False,'DUPLICATE_OR_ACTIVE'
        if d['effect']=='GIANT_ONE' and d['targetUserId'] not in d['serverRoster']:return False,'TARGET_NOT_IN_ROSTER'
        self.active=dict(d,expiresAtMs=d['nowMs']+8000,visualScale={'GIANT_ONE':1.6,'MINI_ALL':.7}[d['effect']])
        self.seen.add(key);self.last_ms=d['nowMs']
        return True,'STARTED'
    def snapshot(self,ms,match,epoch):
        if self.last_ms is not None and ms<self.last_ms:return None,'CLOCK_BACKWARDS'
        self.last_ms=ms
        a=self.active
        if a is None:return None,'INACTIVE'
        if ms>=a['expiresAtMs'] or (a['matchId'],a['epoch'])!=(match,epoch):self.active=None;return None,'CLOSED_OR_EXPIRED'
        return dict(a),'ACTIVE'
    def close(self,match,epoch,ms):
        if self.last_ms is not None and ms<self.last_ms:return False,'CLOCK_BACKWARDS'
        self.last_ms=ms
        if self.active is None or (self.active['matchId'],self.active['epoch'])!=(match,epoch):return False,'NOT_ACTIVE_MATCH'
        self.active=None;self.close_count+=1;return True,'CLOSED'

class GateV2:
    def __init__(self, read_round, read_roster, choose_target=None, mapping=None,
                 enabled=False, approved=False, visual=False):
        self.read_round=read_round;self.read_roster=read_roster;self.choose_target=choose_target
        self.mapping=mapping;self.enabled=enabled is True and approved is True and visual is True
        self.core=ScaleCoreStub();self.active=None;self.pending=None;self.cancel_gen=0
        self.busy=False;self.last_ms=None;self.reason=None
    def _is_current(self, token, pending):return self.enabled and self.cancel_gen==token and self.pending is pending
    def _cancel(self):self.cancel_gen+=1;self.pending=None
    def _round(self):
        if not callable(self.read_round):return None,'READ_ROUND_MISSING'
        try:x=self.read_round()
        except Exception:return None,'READ_ROUND_FAILED'
        if type(x) is not dict or not valid_id(x.get('matchId')) or x.get('stage') not in STAGES \
           or not finite(x.get('epoch')) or not 1<=x['epoch']<1024 or x['epoch']%1 != 0 \
           or not finite(x.get('now')) or not 0<=x['now']<=1e10 \
           or not finite(x.get('startedAt')) or not finite(x.get('deadline')) \
           or not 0<=x['startedAt']<=x['now'] or not x['startedAt']<x['deadline']<=1e10 \
           or type(x.get('active')) is not bool:return None,'ROUND_INVALID'
        ms=math.floor(x['now']*1000+1e-6)
        if self.last_ms is not None and ms<self.last_ms:return None,'CLOCK_BACKWARDS'
        self.last_ms=ms
        return {k:x[k] for k in ['matchId','stage','epoch','now','startedAt','deadline','active']},None
    def _roster(self):
        try:return norm_roster(self.read_roster())
        except Exception:return None
    def _close(self, reason):
        a=self.active
        if a is None:return True,'NOT_ACTIVE'
        self.active=None
        ms=max(a['startedAtMs'],self.last_ms or a['startedAtMs'],self.core.last_ms or a['startedAtMs'])
        ok,_=self.core.close(a['matchId'],a['epoch'],ms)
        if not ok:self.enabled=False;self.reason='CORE_CLOSE_FAILED';return False,'CORE_CLOSE_FAILED'
        return True,reason
    @staticmethod
    def same_event(a,e):return type(e) is dict and e.get('kind')=='WEATHER' and all(e.get(k)==a[k] for k in ['matchId','stage','epoch','subtype'])
    def activate(self,e):
        if not self.enabled:return False,self.reason or 'DISABLED_DEFAULT'
        if self.busy:return False,'BUSY'
        if type(e) is not dict or e.get('kind')!='WEATHER' or e.get('phase')!='ACTIVATE' \
           or e.get('subtype') not in WEATHER or not valid_id(e.get('matchId')) \
           or e.get('stage') not in STAGES or not finite(e.get('epoch')) or not 1<=e['epoch']<1024 or e['epoch']%1!=0 \
           or not finite(e.get('validUntil')) or e['validUntil']>1e10:return False,'INVALID_D08_ENVELOPE'
        if type(self.mapping) is not dict:return False,'NO_EXPLICIT_MAPPING'
        effect=self.mapping.get(e['subtype'])
        if effect not in ('GIANT_ONE','MINI_ALL'):return False,'UNAPPROVED_SUBTYPE'
        pending={k:e[k] for k in ['kind','matchId','stage','epoch','subtype','validUntil']}
        token=self.cancel_gen;self.pending=pending;self.busy=True
        try:
            s,why=self._round()
            if not self._is_current(token,pending):return False,'CANCELLED_DURING_CALLBACK'
            if s is None:return False,why
            if not s['active'] or any(e[k]!=s[k] for k in ('matchId','stage','epoch')):return False,'ROUND_MISMATCH'
            if not s['now']<e['validUntil']<=s['now']+9:return False,'INVALID_EVENT_DEADLINE'
            roster=self._roster()
            if not self._is_current(token,pending):return False,'CANCELLED_DURING_CALLBACK'
            if roster is None:return False,'ROSTER_UNAVAILABLE'
            target=None
            if effect=='GIANT_ONE':
                if not callable(self.choose_target):return False,'TARGET_CALLBACK_MISSING'
                try:target=self.choose_target(roster)
                except Exception:return False,'TARGET_CALLBACK_FAILED'
                if not self._is_current(token,pending):return False,'CANCELLED_DURING_CALLBACK'
            fresh,why=self._round()
            if not self._is_current(token,pending):return False,'CANCELLED_DURING_CALLBACK'
            if fresh is None:return False,why
            if not fresh['active'] or any(s[k]!=fresh[k] for k in ('matchId','stage','epoch','startedAt','deadline')) or fresh['now']<s['now'] or fresh['now']>=e['validUntil']:
                return False,'ROUND_CHANGED_DURING_CALLBACK'
            roster2=self._roster()
            if not self._is_current(token,pending):return False,'CANCELLED_DURING_CALLBACK'
            if roster2!=roster:return False,'ROSTER_CHANGED'
            ms=math.floor(fresh['now']*1000+1e-6)
            started,why=self.core.begin({'matchId':pending['matchId'],'eventId':pending['subtype']+':'+str(pending['epoch']),
                  'epoch':pending['epoch'],'nowMs':ms,'effect':effect,'targetUserId':target,'serverRoster':roster2})
            if not self._is_current(token,pending):
                if started:
                    self.active=dict(pending,startedAtMs=ms)
                    self._close('CANCELLED_AFTER_BEGIN')
                return False,'CANCELLED_DURING_CALLBACK'
            if not started:return False,why
            self.active=dict(pending,deadlineMs=math.floor(pending['validUntil']*1000),startedAtMs=ms)
            return True,'STARTED'
        except Exception:
            self._cancel();self._close('DISPATCH_EXCEPTION');self.enabled=False;self.reason='DISPATCH_EXCEPTION'
            return False,'DISPATCH_EXCEPTION'
        finally:
            self.busy=False
            if self.pending is pending:self.pending=None
    def cleanup(self,e):
        if type(e) is not dict or e.get('phase') is not None or e.get('kind')!='WEATHER':return False,'INVALID_CLEANUP'
        if self.pending is not None and self.same_event(self.pending,e):
            self._cancel()
            if self.active is None:return True,'CANCELLED_PENDING'
        if self.active is None:return False,'INACTIVE'
        if not self.same_event(self.active,e):return False,'CLEANUP_MISMATCH'
        self._cancel()
        return self._close('CLOSED')
    def snapshot(self):
        if not self.enabled or self.active is None:return None,'INACTIVE'
        token,a=self.cancel_gen,self.active
        s,why=self._round()
        if self.cancel_gen!=token or self.active is not a or not self.enabled:return None,'CANCELLED_DURING_CALLBACK'
        if s is None:
            self._cancel();self._close(why);self.enabled=False;self.reason=why;return None,why
        ms=math.floor(s['now']*1000+1e-6)
        if not s['active'] or any(s[k]!=a[k] for k in ('matchId','stage','epoch')) or ms>=a['deadlineMs']:
            self._cancel();self._close('ROUND_CLOSED_OR_EXPIRED');return None,'ROUND_CLOSED_OR_EXPIRED'
        output,why=self.core.snapshot(ms,s['matchId'],s['epoch'])
        if output is None:
            self.active=None
            if why in ('CLOCK_BACKWARDS','INVALID_CLOCK_OR_STATE'):self.enabled=False;self.reason=why
        return output,why
    def stop(self):
        self._cancel();self.enabled=False
        ok,_=self._close('OWNER_STOP')
        self.reason='OWNER_STOP' if ok else 'CORE_CLOSE_FAILED'
        return ok,self.reason
