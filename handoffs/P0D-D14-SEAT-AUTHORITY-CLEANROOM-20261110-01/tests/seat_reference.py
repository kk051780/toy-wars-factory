"""Python behavioral reference for NEW non-original server-only seat-intent policy."""
from dataclasses import dataclass
from math import isfinite


def ident(v):
    return isinstance(v, str) and 1 <= len(v) <= 96


def integer(v):
    return type(v) is int and 0 <= v < 100000000


def number(v):
    return type(v) in (float, int) and isfinite(v) and abs(v) < 100000000


@dataclass
class Holder:
    player_id: str
    generation: int
    expires: float


class Seats:
    def __init__(self):
        self.active = False
        self.ctx = None
        self.now = None
        self.sequence = -1
        self.occupants = {}

    def stop(self):
        self.active = False
        self.ctx = None
        self.now = None
        self.sequence = -1
        self.occupants.clear()
        return 'STOPPED'

    def begin(self, s):
        if (self.active or not isinstance(s, dict) or s.get('server_authorized') is not True
            or not ident(s.get('match_id')) or not ident(s.get('vehicle_id'))
            or not integer(s.get('epoch')) or not integer(s.get('stage'))
            or not 1 <= s['stage'] <= 4 or not number(s.get('now'))):
            return 'REJECTED'
        self.ctx = (s['match_id'], s['epoch'], s['stage'], s['vehicle_id'])
        self.now = s['now']
        self.sequence = -1
        self.active = True
        self.occupants.clear()
        return 'STARTED'

    def validate(self, s):
        if not self.active:
            return False
        if (not isinstance(s, dict) or s.get('server_authorized') is not True
            or (s.get('match_id'), s.get('epoch'), s.get('stage'), s.get('vehicle_id')) != self.ctx
            or not number(s.get('now')) or not integer(s.get('sequence'))):
            self.stop()
            return False
        return s['now'] > self.now and s['sequence'] > self.sequence

    @staticmethod
    def real_occupant(s):
        return (s.get('role') in ('DRIVER','PASSENGER') and ident(s.get('player_id'))
                and integer(s.get('character_generation')) and s.get('player_alive') is True
                and s.get('server_seat_occupant_verified') is True)

    def assign(self, s):
        if not self.validate(s) or not self.real_occupant(s):
            return 'REJECTED'
        if s['role'] in self.occupants or any(x.player_id == s['player_id'] for x in self.occupants.values()):
            return 'REJECTED'
        self.sequence, self.now = s['sequence'], s['now']
        self.occupants[s['role']] = Holder(s['player_id'], s['character_generation'], s['now']+1.5)
        return 'MOUNT_INTENT'

    def refresh(self, s):
        if not self.validate(s) or not self.real_occupant(s):
            return 'REJECTED'
        h = self.occupants.get(s['role'])
        if h is None or h.player_id != s['player_id'] or h.generation != s['character_generation'] or s['now'] > h.expires:
            self.occupants.pop(s['role'], None)
            return 'REJECTED'
        self.sequence, self.now = s['sequence'], s['now']
        h.expires = s['now']+1.5
        return 'REFRESHED'

    def release(self, s):
        if not self.validate(s) or s.get('role') not in ('DRIVER','PASSENGER') or not ident(s.get('player_id')) or not integer(s.get('character_generation')):
            return 'REJECTED'
        h = self.occupants.get(s['role'])
        if not h or h.player_id != s['player_id'] or h.generation != s['character_generation']:
            return 'REJECTED'
        self.sequence, self.now = s['sequence'], s['now']
        del self.occupants[s['role']]
        return 'RELEASED'

    def tick(self, s):
        if not self.active:
            return 'REJECTED'
        if (not isinstance(s,dict) or s.get('server_authorized') is not True
            or tuple(s.get(k) for k in ('match_id','epoch','stage','vehicle_id')) != self.ctx
            or not number(s.get('now')) or s['now'] < self.now):
            self.stop()
            return 'STOPPED'
        self.now = s['now']
        for role, h in list(self.occupants.items()):
            if s['now'] > h.expires:
                del self.occupants[role]
        return 'TICK'
