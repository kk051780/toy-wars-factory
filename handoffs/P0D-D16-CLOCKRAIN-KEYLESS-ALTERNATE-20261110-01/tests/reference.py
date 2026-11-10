"""Python reference for the NEW keyless Clock Rain visual-only state contract."""
import math

class ClockRain:
    def __init__(self):
        self.active = False
        self.last_key = None
        self.last_sequence = -1
        self.start_at = 0
        self.expires_at = 0
        self.match_id = None
        self.epoch = None
        self.parts = 0

    def start(self, s):
        if not isinstance(s, dict):
            return "REJECTED"
        required = ["server_event_approved", "event_name", "phase", "match_id",
                    "epoch", "sequence", "now", "event_started_at", "duration",
                    "reduced_motion"]
        if any(k not in s for k in required):
            return "REJECTED"
        if s["server_event_approved"] is not True or s["event_name"] != "CLOCK_RAIN" or s["phase"] != "ACTIVATE":
            return "REJECTED"
        mid = s["match_id"]
        if not isinstance(mid, str) or not 1 <= len(mid) <= 96:
            return "REJECTED"
        if type(s["epoch"]) is not int or s["epoch"] < 0 or type(s["sequence"]) is not int or s["sequence"] < 0:
            return "REJECTED"
        if any(type(s[k]) not in (int, float) or not math.isfinite(s[k]) for k in ("now","event_started_at","duration")):
            return "REJECTED"
        if type(s["reduced_motion"]) is not bool:
            return "REJECTED"
        if not 0 <= s["now"] - s["event_started_at"] <= 2.0 or not 0 < s["duration"] <= 12.0:
            return "REJECTED"
        if self.active:
            return "REJECTED"
        key = (mid, s["epoch"])
        if self.last_key == key and s["sequence"] <= self.last_sequence:
            return "REJECTED"
        self.last_key, self.last_sequence = key, s["sequence"]
        self.active = True
        self.match_id, self.epoch = key
        self.start_at, self.expires_at = s["event_started_at"], s["event_started_at"] + s["duration"]
        self.parts = 4 if s["reduced_motion"] else 12
        return "STARTED"

    def step(self, now, match_id, epoch):
        if not self.active:
            return ("IDLE", 0)
        if not isinstance(now, (int,float)) or not math.isfinite(now) or match_id != self.match_id or epoch != self.epoch:
            self.stop()
            return ("CLEARED", 0)
        if now < self.start_at or now >= self.expires_at:
            self.stop()
            return ("CLEARED", 0)
        return ("FRAME", self.parts)

    def stop(self):
        self.active = False
        self.parts = 0
