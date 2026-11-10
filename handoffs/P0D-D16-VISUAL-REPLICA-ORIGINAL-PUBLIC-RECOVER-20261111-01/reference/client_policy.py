"""Independent Python model of D16 *display-only* client input policy.
No game authority, no Roblox APIs, no currency or identity persistence.
"""
import math
import re
from dataclasses import dataclass, field

SCALES = {'GIANT_ONE': 1600, 'MINI_ALL': 700}
ID = re.compile(r'^[A-Za-z0-9_.-]{1,96}$')

def valid_id(value):
    return type(value) is str and ID.fullmatch(value) is not None

def valid_number(value):
    return type(value) in (int, float) and math.isfinite(value)

@dataclass
class Policy:
    match_id: str
    event_id: str | None = None
    closed: bool = False
    status: str = 'IDLE'
    kind: str | None = None
    targets: list[str] = field(default_factory=list)
    scale_milli: int = 1000
    deadline: float | None = None

    def __post_init__(self):
        if not valid_id(self.match_id):
            raise ValueError('INVALID_MATCH')

    def accept(self, packet, expected_match, now):
        if not valid_number(now) or now < 0: return False, 'BAD_CLIENT_TIME'
        if type(packet) is not dict: return False, 'BAD_PACKET'
        if not valid_id(expected_match) or self.match_id != expected_match or packet.get('matchId') != expected_match:
            return False, 'STALE_MATCH'
        event_id = packet.get('eventId')
        if not valid_id(event_id): return False, 'BAD_EVENT_ID'
        if self.event_id is not None and event_id != self.event_id: return False, 'SECOND_EVENT_REJECTED'
        status = packet.get('status')
        if status not in ('ACTIVE','EXPIRED','CLOSED'): return False, 'BAD_STATUS'
        if status != 'ACTIVE':
            if self.closed: return False, 'TERMINAL_REPLAY'
            if self.event_id is None: return False, 'UNKNOWN_TERMINAL'
            self.status, self.closed, self.targets, self.deadline, self.scale_milli = status, True, [], None, 1000
            return True, 'CLEARED'
        if self.closed: return False, 'CLOSED_EVENT_REPLAY'
        kind = packet.get('kind')
        if kind not in SCALES or packet.get('scaleMilli') != SCALES[kind]: return False, 'BAD_SCALE'
        ttl = packet.get('remainingSeconds')
        if not valid_number(ttl) or not 0 < ttl <= 8: return False, 'BAD_TTL'
        targets = packet.get('targets')
        if type(targets) is not list or not 1 <= len(targets) <= 16: return False, 'BAD_TARGETS'
        if kind == 'GIANT_ONE' and len(targets) != 1: return False, 'BAD_TARGETS'
        if any(not valid_id(t) for t in targets) or len(set(targets)) != len(targets):return False, 'BAD_TARGETS'
        deadline = now + ttl
        if self.event_id is not None:
            if self.kind != kind: return False, 'KIND_CHANGED'
            if not set(targets).issubset(self.targets): return False, 'TARGET_ADDED_AFTER_START'
            deadline = min(self.deadline, deadline)
            if deadline <= now: return False, 'ALREADY_EXPIRED'
        self.status, self.event_id, self.kind = 'ACTIVE', event_id, kind
        self.targets, self.scale_milli, self.deadline = sorted(targets), SCALES[kind], deadline
        return True, 'DISPLAY_ONLY'

    def tick(self, expected_match, now):
        if self.match_id != expected_match:
            self.status, self.targets, self.deadline, self.closed, self.scale_milli = 'EXPIRED', [], None, True, 1000
            return 'MATCH_CHANGED'
        if not valid_number(now): return 'TIME_UNAVAILABLE'
        if self.status == 'ACTIVE' and now >= self.deadline:
            self.status, self.targets, self.deadline, self.closed, self.scale_milli = 'EXPIRED', [], None, True, 1000
            return 'EXPIRED'
        return self.status
