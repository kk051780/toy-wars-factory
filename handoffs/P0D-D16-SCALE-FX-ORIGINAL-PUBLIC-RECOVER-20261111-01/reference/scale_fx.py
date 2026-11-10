"""Reference oracle for D16 server-authoritative cosmetic-only transformations."""
import math
import re

DURATION = 8
SCALES = {'GIANT_ONE': 1600, 'MINI_ALL': 700}
MAX_PLAYERS = 16
ID = re.compile(r'^[A-Za-z0-9_.-]{1,96}$')

def valid_id(s):
    return type(s) is str and bool(ID.fullmatch(s))

def valid_time(t):
    return type(t) in (int, float) and math.isfinite(t) and t >= 0

class ScaleFx:
    def __init__(self, match_id):
        if not valid_id(match_id):
            raise ValueError('invalid match')
        self.match_id = match_id
        self.last_time = 0
        self.used = False
        self.status = 'IDLE'
        self.kind = None
        self.event_id = None
        self.expires_at = None
        self.targets = []

    def begin(self, match_id, event_id, kind, actor_id, roster, now):
        if match_id != self.match_id:
            return False, 'STALE_MATCH'
        if self.status == 'CLOSED':
            return False, 'ROUND_CLOSED'
        if self.used:
            return False, 'EVENT_ALREADY_USED'
        if not valid_time(now) or now < self.last_time:
            return False, 'INVALID_TIME'
        if not valid_id(event_id) or kind not in SCALES:
            return False, 'INVALID_EVENT'
        if type(roster) is not list or not (1 <= len(roster) <= MAX_PLAYERS) or any(not valid_id(x) for x in roster) or len(set(roster)) != len(roster):
            return False, 'INVALID_ROSTER'
        targets = sorted(roster)
        if kind == 'GIANT_ONE':
            if not valid_id(actor_id) or actor_id not in targets:
                return False, 'INVALID_ACTOR'
            targets = [actor_id]
        elif actor_id is not None:
            return False, 'ACTOR_NOT_APPLICABLE'
        self.used, self.status = True, 'ACTIVE'
        self.kind, self.event_id, self.expires_at = kind, event_id, now + DURATION
        self.targets, self.last_time = targets, now
        return True, 'STARTED'

    def advance(self, match_id, now):
        if match_id != self.match_id:
            return False, 'STALE_MATCH'
        if not valid_time(now) or now < self.last_time:
            return False, 'INVALID_TIME'
        self.last_time = now
        if self.status == 'ACTIVE' and (now >= self.expires_at or not self.targets):
            self.status, self.targets = 'EXPIRED', []
        return True, self.status

    def leave(self, match_id, player_id):
        if match_id != self.match_id:
            return False, 'STALE_MATCH'
        if not valid_id(player_id):
            return False, 'INVALID_PLAYER'
        if self.status != 'ACTIVE':
            return True, 'NO_ACTIVE_EFFECT'
        self.targets = [x for x in self.targets if x != player_id]
        if not self.targets:
            self.status = 'EXPIRED'
        return True, self.status

    def close(self, match_id):
        if match_id != self.match_id:
            return False, 'STALE_MATCH'
        self.status, self.targets = 'CLOSED', []
        return True, 'CLOSED'

    def new_round(self, next_id):
        if not valid_id(next_id) or next_id == self.match_id:
            return False, 'INVALID_NEW_MATCH'
        self.__init__(next_id)
        return True, 'RESET'

    def snapshot(self, match_id):
        if match_id != self.match_id:
            return None, 'STALE_MATCH'
        return ({'matchId': self.match_id, 'status': self.status, 'used': self.used,
                 'kind': self.kind, 'eventId': self.event_id,
                 'expiresAt': self.expires_at, 'targets': self.targets[:],
                 'scaleMilli': SCALES[self.kind] if self.status == 'ACTIVE' else 1000}, None)
