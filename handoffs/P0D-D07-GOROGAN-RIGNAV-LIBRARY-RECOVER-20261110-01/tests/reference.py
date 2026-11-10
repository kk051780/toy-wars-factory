"""Deliberately independent Python policy oracle for D07 server-only rig/navigation/damage gate.
Not a Luau interpreter or Roblox Studio simulation.
"""
from dataclasses import dataclass, field
from math import isfinite, hypot

@dataclass
class RigPolicy:
    active: bool = False
    round_id: str = ""
    event_id: str = ""
    now_started: float = 0
    last_nav: float = float("-inf")
    count: int = 0
    busy: bool = False
    seen: set = field(default_factory=set)

    def start(self, round_id, event_id, stage, now, authorized=True, safe=True):
        if self.active or round_id in self.seen or len(self.seen) >= 128:
            return False
        if not authorized or not safe or stage not in ("S1", "S3"):
            return False
        if not safe_id(round_id) or not safe_id(event_id) or not valid_time(now):
            return False
        self.seen.add(round_id)
        self.active = True
        self.round_id, self.event_id = round_id, event_id
        self.now_started, self.last_nav, self.count = now, float("-inf"), 0
        return True

    def stop(self, round_id, event_id):
        if not self.active or (round_id, event_id) != (self.round_id, self.event_id):
            return False
        self.active = False
        return True

    def request(self, now, dst, src, reason="CHASE", terrain=True, path=True, num_waypoints=3, epoch_ok=True, after_yield_ok=True):
        if not self.active or not valid_time(now) or not epoch_ok or self.busy:
            return False, "INACTIVE_OR_BUSY"
        if now < self.now_started or now - self.now_started >= 14 or now < self.last_nav:
            return False, "BAD_TIME"
        if now-self.last_nav < .75 or self.count >= 20:
            return False, "RATE_OR_BUDGET"
        if reason not in ("CHASE", "LEASH_RETURN") or not is_xyz(dst):
            return False, "BAD_DEST"
        if reason == "CHASE" and planar(dst, src) > 8.1:
            return False, "TOO_FAR"
        if not terrain:
            return False, "TERRAIN"
        # Rate and count are consumed for a real path request even if pathfinding fails.
        self.last_nav, self.count = now, self.count+1
        if not path or not (2 <= num_waypoints <= 16):
            return False, "PATH_BLOCKED"
        if not after_yield_ok:
            return False, "STALE_AFTER_YIELD"
        return True, "MOVE"

@dataclass
class DamagePolicy:
    active: bool = False
    round_id: str = ""
    event_id: str = ""
    seen_rounds: set = field(default_factory=set)
    receipts: set = field(default_factory=set)
    total: int = 0

    def start(self, round_id, event_id, canonical=True):
        if self.active or not canonical or round_id in self.seen_rounds or len(self.seen_rounds) >= 128:
            return False
        if not safe_id(round_id) or not safe_id(event_id):
            return False
        self.active=True
        self.round_id,self.event_id=round_id,event_id
        self.receipts=set()
        self.total=0
        self.seen_rounds.add(round_id)
        return True

    def stop(self, round_id, event_id):
        if not self.active or (self.round_id,self.event_id)!=(round_id,event_id):
            return False
        self.active=False
        self.receipts.clear()
        return True

    def resolve(self, player_id, damage, attack_id, round_id, event_id, *, canonical=True,live=True,
                alive=True, safe=False, immune=False, in_range=True, los=True, valid_player=True):
        if not self.active or (round_id,event_id)!=(self.round_id,self.event_id):
            return False,"STALE"
        if not safe_id(player_id) or isinstance(damage,bool) or not isinstance(damage,(float,int)) or not isfinite(damage) or not (0 < damage <= 8):
            return False,"INVALID_DAMAGE"
        if not isinstance(attack_id,int) or isinstance(attack_id,bool) or not (1<=attack_id<=3):
            return False,"INVALID_ATTACK"
        if not canonical or not live:
            return False,"UNTRUSTED"
        key=(attack_id,player_id)
        if key in self.receipts:
            return False,"DUPLICATE"
        if self.total >= 72:
            return False,"BUDGET"
        if not valid_player or not alive or safe or immune or not in_range or not los:
            return False,"NOT_HIT"
        self.receipts.add(key)
        self.total+=1
        return True,"APPLIED"

def safe_id(x):
    return isinstance(x,str) and 1<=len(x)<=64 and all(c.isascii() and (c.isalnum() or c in '_-') for c in x)

def valid_time(x):
    return isinstance(x,(float,int)) and not isinstance(x,bool) and isfinite(x) and 0<=x<=1e12

def is_xyz(v):
    return isinstance(v,(tuple,list)) and len(v)==3 and all(isinstance(x,(float,int)) and not isinstance(x,bool) and isfinite(x) for x in v) and abs(v[0])<=2048 and -100<=v[1]<=700 and abs(v[2])<=2048

def planar(a,b):
    return hypot(a[0]-b[0],a[2]-b[2])
