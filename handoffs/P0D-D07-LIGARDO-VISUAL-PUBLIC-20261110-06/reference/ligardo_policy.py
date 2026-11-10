"""Independent executable model for D07 S2/S4 LIGARDO visual policy.

This module does not verify server-origin authentication and is not boss gameplay AI.
"""
import math
import re

_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def valid_id(value):
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def valid_int(v, low, high):
    return type(v) is int and low <= v <= high


def valid_time(v):
    return type(v) in (int, float) and math.isfinite(v) and 0 <= v < 1e10


class Visual:
    def __init__(self, round_id):
        if not valid_id(round_id):
            raise ValueError("roundId")
        self.round_id = round_id
        self.closed = False
        self.used = False
        self.event_id = None
        self.last_seq = 0
        self.phase = "IDLE"
        self.deadline = None
        self.last_now = 0.0

    @staticmethod
    def _output(kind, reason=None, phase=None, remaining_ms=None):
        x = {"kind": kind}
        if reason is not None:
            x["reason"] = reason
        if phase is not None:
            x["phase"] = phase
        if remaining_ms is not None:
            x["remainingMs"] = remaining_ms
        return x

    def snapshot(self, p, now):
        if self.closed or not isinstance(p, dict) or not valid_time(now) or now < self.last_now:
            return self._output("IGNORE", "INVALID_STATE_OR_TIME")
        if (p.get("roundId") != self.round_id or p.get("boss") != "LIGARDO" or
            not valid_int(p.get("stage"), 1, 4) or p["stage"] not in (2, 4) or
            not valid_id(p.get("eventId")) or not valid_int(p.get("seq"), 1, 10000000) or
            not valid_int(p.get("remainingMs"), 0, 20000) or
            p.get("phase") not in ("TELEGRAPH", "ACTIVE", "END")):
            return self._output("IGNORE", "INVALID_PAYLOAD")
        if self.used and p["eventId"] != self.event_id:
            return self._output("IGNORE", "ALREADY_USED_THIS_ROUND")
        if self.used and p["seq"] <= self.last_seq:
            return self._output("IGNORE", "STALE_SEQUENCE")
        if self.phase == "ENDED":
            return self._output("IGNORE", "TERMINATED")
        if not self.used:
            if p["phase"] != "TELEGRAPH" or p["remainingMs"] == 0:
                return self._output("IGNORE", "MUST_TELEGRAPH_FIRST")
            self.used = True
            self.event_id = p["eventId"]
            self.last_seq = p["seq"]
            self.phase = "TELEGRAPH"
            self.deadline = now + min(p["remainingMs"] / 1000, 20)
            self.last_now = now
            return self._output("SPAWN", phase="TELEGRAPH", remaining_ms=p["remainingMs"])
        if now >= self.deadline or p["phase"] == "END" or p["remainingMs"] == 0:
            self.last_now, self.last_seq, self.phase = now, p["seq"], "ENDED"
            return self._output("DESPAWN", "END_OR_TIMEOUT")
        if self.phase == "ACTIVE" and p["phase"] == "TELEGRAPH":
            return self._output("IGNORE", "PHASE_ROLLBACK")
        self.deadline = min(self.deadline, now + p["remainingMs"] / 1000)
        self.last_now, self.last_seq, self.phase = now, p["seq"], p["phase"]
        return self._output("UPDATE", phase=p["phase"],
                            remaining_ms=math.floor(max(0, (self.deadline - now) * 1000)))

    def tick(self, now):
        if not valid_time(now) or now < self.last_now:
            return self._output("IGNORE", "INVALID_TIME")
        self.last_now = now
        if self.closed or self.phase == "ENDED":
            return self._output("IGNORE", "CLOSED")
        if self.used and self.deadline is not None and now >= self.deadline:
            self.phase = "ENDED"
            return self._output("DESPAWN", "TTL")
        return self._output("NOOP")

    def close(self):
        self.closed, self.phase = True, "ENDED"
        return self._output("DESPAWN", "ROUND_CLOSED")


def part_budget(low_detail=False):
    # 6 or 4 body + head + jaw + 2 horns + 4 fins + 4 or 2 decorative streaks
    return (4 if low_detail else 6) + 1 + 1 + 2 + 4 + (2 if low_detail else 4)
