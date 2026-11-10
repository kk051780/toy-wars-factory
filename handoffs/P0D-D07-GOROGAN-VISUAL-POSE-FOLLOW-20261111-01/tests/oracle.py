"""Pure Python independent behavior model for optional D07 visual-only pose sidecar."""
from dataclasses import dataclass
import math
import re


def valid_id(v):
    return isinstance(v, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", v))


def finite(v, lo, hi):
    return type(v) in (int, float) and math.isfinite(v) and lo <= v <= hi


def good_pos(p):
    return isinstance(p, dict) and finite(p.get('x'), -2048, 2048) and finite(p.get('y'), -100, 700) and finite(p.get('z'), -2048, 2048)


@dataclass
class Producer:
    match_id: str
    event_id: str
    stage: str
    epoch: int
    started_at: float
    ends_at: float
    enabled: bool = False
    owner_approved: bool = False
    last_at: float | None = None
    count: int = 0
    closed: bool = False

    def __post_init__(self):
        if not (self.enabled is True and self.owner_approved is True):
            raise ValueError("D07_POSE_FOLLOW_DISABLED_DEFAULT")
        if not valid_id(self.match_id) or not valid_id(self.event_id) or self.stage not in ("S1", "S3"):
            raise ValueError("BAD_SERVER_IDENTITY")
        if not finite(self.epoch, 0, 1023) or self.epoch % 1:
            raise ValueError("BAD_EPOCH")
        if not finite(self.started_at, 0, 1e12) or not finite(self.ends_at, self.started_at, self.started_at + 14):
            raise ValueError("BAD_LIFETIME")

    def sample(self, s):
        if self.closed:
            return None, 'CLOSED'
        if not isinstance(s, dict) or s.get('matchId') != self.match_id or s.get('eventId') != self.event_id or s.get('stageId') != self.stage or s.get('epoch') != self.epoch or s.get('active') is not True or not finite(s.get('now'), self.started_at, self.ends_at) or not good_pos(s.get('position')):
            self.closed = True
            return None, 'AUTHORITY_OR_ROUND_INVALID'
        t = s['now']
        if t >= self.ends_at:
            self.closed = True
            return None, 'EXPIRED'
        if self.last_at is not None:
            if t < self.last_at:
                self.closed = True
                return None, 'CLOCK_REVERSED'
            if t - self.last_at < .20:
                return None, 'RATE_LIMIT'
        if self.count >= 64:
            self.closed = True
            return None, 'SAMPLE_CAP'
        self.last_at = t
        self.count += 1
        return {'kind': 'POSE', 'bossId':'GOROGAN', 'matchId': self.match_id,
                'eventId':self.event_id, 'stageId':self.stage, 'epoch':self.epoch,
                'poseSeq':self.count, 'position':dict(s['position'])}, 'EMIT'


@dataclass
class Follower:
    match_id: str
    event_id: str
    stage: str
    epoch: int
    initial_position: dict
    start_local_now: float
    current: dict | None = None
    last_now: float | None = None
    last_accepted: float | None = None
    last_seq: int = 0
    closed: bool = False
    invalid_count: int = 0

    def __post_init__(self):
        if not valid_id(self.match_id) or not valid_id(self.event_id) or self.stage not in ('S1', 'S3') or not finite(self.epoch, 0, 1023) or self.epoch % 1 or not good_pos(self.initial_position) or not finite(self.start_local_now, 0, 1e12):
            raise ValueError('INVALID_FOLLOWER_START')
        self.current = dict(self.initial_position)
        self.last_now = self.start_local_now

    def accept(self, p, now, active):
        if self.closed:
            return None, 'CLOSED'
        if active is not True:
            self.closed = True
            return None, 'VISUAL_ENDED'
        if not finite(now, 0, 1e12) or now < self.last_now:
            self.closed = True
            return None, 'LOCAL_CLOCK_REVERSED'
        self.last_now = now
        if not isinstance(p, dict) or p.get('kind') != 'POSE' or p.get('bossId') != 'GOROGAN' or p.get('matchId') != self.match_id or p.get('eventId') != self.event_id or p.get('stageId') != self.stage or p.get('epoch') != self.epoch or not finite(p.get('poseSeq'), 1, 64) or p['poseSeq'] % 1 or not good_pos(p.get('position')):
            self.invalid_count += 1
            return None, 'INVALID_POSE'
        if p['poseSeq'] <= self.last_seq:
            return None, 'POSE_REPLAY'
        dt = now - (self.last_accepted if self.last_accepted is not None else self.start_local_now)
        if self.last_accepted is not None and dt < .12:
            return None, 'RATE_LIMIT'
        if dt > 1.5:
            self.closed = True
            return None, 'CLIENT_SUSPENDED_REQUIRES_NEW_AUTH_START'
        a, b = self.current, p['position']
        distance = math.sqrt(sum((a[k]-b[k])**2 for k in ('x','y','z')))
        if distance > 48*dt+2:
            self.invalid_count += 1
            return None, 'IMPOSSIBLE_VISUAL_JUMP'
        self.current = dict(p['position'])
        self.last_seq = p['poseSeq']
        self.last_accepted = now
        return dict(self.current), 'FOLLOW'
