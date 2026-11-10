"""Python oracle of D07 visual-only packet policy; not a Luau interpreter."""
from dataclasses import dataclass
import math
import re

MAX_COORD=2048
@dataclass
class VisualPolicy:
    match: str = 'ROUND_1'
    stage: str = 'S1'
    highest_seq: int = 0
    seen_start: bool = False
    active: bool = False
    event: str = ''
    phase: str = 'IDLE'
    pos: tuple | None = None
    expires_at: float = 0
    telegraph_until: float = 0
    stomp_count: int = 0
    last_now: float = 0

    def __post_init__(self):
        assert valid_id(self.match) and self.stage in ('S1','S3')

    def expire(self, now):
        if not finite(now,0,1e12) or now < self.last_now: return 'IGNORED_CLOCK'
        self.last_now=now
        if self.active:
            if now >= self.expires_at:
                self.active=False;self.phase='ENDED';self.pos=None
                return 'EXPIRED'
            if self.phase in ('STOMP','WARNING') and now >= self.telegraph_until:
                self.phase='ACTIVE'
                return 'STOMP_CLEARED'
        return 'UNCHANGED'

    def apply(self, msg, now):
        if self.expire(now)=='IGNORED_CLOCK':return 'REJECTED_CLOCK'
        if not isinstance(msg,dict):return 'REJECTED_PACKET'
        if msg.get('matchId')!=self.match or msg.get('stageId')!=self.stage or msg.get('bossId')!='GOROGAN' or not valid_id(msg.get('eventId')):
            return 'REJECTED_IDENTITY'
        seq=msg.get('seq')
        if not finite(seq,1,1e9) or int(seq)!=seq or seq<=self.highest_seq:return 'REJECTED_REPLAY'
        if msg.get('kind')=='START':
            if self.seen_start or self.active or not valid_pos(msg.get('position')):return 'REJECTED_START'
            self.highest_seq=seq;self.seen_start=True;self.active=True
            self.event=msg['eventId'];self.phase='WARNING'
            p=msg['position'];self.pos=(p['x'],p['y'],p['z'])
            self.expires_at=min(now+14,1e12);self.telegraph_until=now+2
            return 'STARTED'
        if not self.active or msg.get('eventId')!=self.event:return 'REJECTED_EVENT'
        if msg.get('kind')=='STOMP':
            if self.stomp_count>=3:return 'REJECTED_STOMP_LIMIT'
            if now+2>self.expires_at:return 'REJECTED_STOMP_TIME'
            self.highest_seq=seq;self.stomp_count+=1;self.phase='STOMP';self.telegraph_until=now+2
            return 'STOMP_STARTED'
        if msg.get('kind')=='END':
            self.highest_seq=seq;self.active=False;self.phase='ENDED';self.pos=None
            return 'ENDED'
        return 'REJECTED_KIND'

def finite(v,lo,hi):
    return type(v) in (float,int) and math.isfinite(v) and lo<=v<=hi

def valid_id(v):
    return isinstance(v,str) and bool(re.fullmatch('[A-Za-z0-9_-]{1,64}',v))

def valid_pos(v):
    return isinstance(v,dict) and finite(v.get('x'),-MAX_COORD,MAX_COORD) and finite(v.get('y'),-100,700) and finite(v.get('z'),-MAX_COORD,MAX_COORD)

def packet(kind='START', seq=1, **kwargs):
    a={'kind':kind,'matchId':'ROUND_1','stageId':'S1','bossId':'GOROGAN','eventId':'boss_1','seq':seq,'position':{'x':0,'y':4,'z':1}}
    a.update(kwargs)
    return a
