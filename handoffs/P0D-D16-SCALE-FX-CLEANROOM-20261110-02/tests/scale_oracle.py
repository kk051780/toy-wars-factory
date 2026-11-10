"""Independent Python model of D16 cosmetic-only no-key state contract.

This is a behavioral oracle, not execution of Luau or real Roblox gameplay.
"""
from dataclasses import dataclass
import math


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def valid_id(value):
    return isinstance(value, str) and 1 <= len(value) <= 96 and not any(ord(c) < 32 or ord(c) == 127 for c in value)


def valid_epoch(value):
    return finite(value) and int(value) == value and 1 <= value <= 2147483647


def valid_user_id(value):
    return finite(value) and int(value) == value and 1 <= value <= 9007199254740991


@dataclass
class ScaleState:
    seen: set = None
    active: dict = None
    newest_epoch: int = 0
    last_now: float = None

    def __post_init__(self):
        if self.seen is None:
            self.seen = set()

    def begin(self, *, match_id, event_id, epoch, now_ms, effect, roster, target=None):
        if not valid_id(match_id) or not valid_id(event_id) or not valid_epoch(epoch):
            return False, "INVALID_ID"
        if not finite(now_ms) or not (0 <= now_ms <= 10**14):
            return False, "INVALID_CLOCK"
        if effect not in ("GIANT_ONE", "MINI_ALL"):
            return False, "INVALID_EFFECT"
        if not isinstance(roster, list) or not (1 <= len(roster) <= 24) or any(not valid_user_id(x) for x in roster) or len(set(roster)) != len(roster):
            return False, "INVALID_ROSTER"
        if effect == "GIANT_ONE" and not valid_user_id(target):
            return False, "INVALID_TARGET"
        if effect == "GIANT_ONE" and target not in roster:
            return False, "TARGET_NOT_IN_ROSTER"
        if effect == "MINI_ALL" and target is not None:
            return False, "UNEXPECTED_TARGET"
        if epoch < self.newest_epoch:
            return False, "STALE_EPOCH"
        if self.last_now is not None and now_ms < self.last_now:
            return False, "CLOCK_BACKWARDS"
        key = (match_id, epoch)
        if key in self.seen or self.active is not None:
            return False, "DUPLICATE_OR_ACTIVE"
        if len(self.seen) >= 128:
            return False, "ANTI_REPLAY_CAPACITY"
        self.seen.add(key)
        self.newest_epoch = max(self.newest_epoch, epoch)
        self.last_now = now_ms
        self.active = dict(matchId=match_id, epoch=epoch, eventId=event_id,
                           effect=effect, visualScale=1.6 if effect == "GIANT_ONE" else 0.7,
                           startedAtMs=now_ms, expiresAtMs=now_ms + 8000,
                           userIds=[target] if effect == "GIANT_ONE" else sorted(roster))
        return True, "STARTED"

    def snapshot(self, now_ms, match_id, epoch):
        if not finite(now_ms) or now_ms < 0:
            return None, "INVALID_CLOCK_OR_STATE"
        if self.last_now is not None and now_ms < self.last_now:
            return None, "CLOCK_BACKWARDS"
        self.last_now = now_ms
        if self.active is None:
            return None, "INACTIVE"
        if (match_id, epoch) != (self.active['matchId'], self.active['epoch']) or now_ms >= self.active['expiresAtMs']:
            self.active = None
            return None, "CLOSED_OR_EXPIRED"
        return {**self.active, "userIds": self.active['userIds'][:]}, "ACTIVE"

    def close(self, match_id, epoch, now_ms):
        if not finite(now_ms) or now_ms < 0:
            return False, "INVALID_CLOCK_OR_STATE"
        if self.last_now is not None and now_ms < self.last_now:
            return False, "CLOCK_BACKWARDS"
        self.last_now = now_ms
        if self.active is None or (match_id, epoch) != (self.active['matchId'], self.active['epoch']):
            return False, "NOT_ACTIVE_MATCH"
        self.active = None
        return True, "CLOSED"
