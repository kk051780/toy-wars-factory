"""Offline deterministic behavioral model of S1 objective/authority invariants.

This is Python standard-library reference testing. It does NOT execute Roblox Luau.
"""
from dataclasses import dataclass, field
from math import isfinite

ROLES = {'RAIDER': (100, 19, 24, 14), 'GUARDIAN': (135, 15, 18, 10)}

@dataclass
class Player:
    team: str
    role: str = 'RAIDER'
    alive: bool = True
    carrying: str | None = None
    last_seq: int = 0
    last_attack: float = float('-inf')
    last_role_change: float = float('-inf')
    invulnerable_until: float = 0
    hp: int = 100

@dataclass
class S1:
    players: dict[str, Player] = field(default_factory=dict)
    phase: str = 'LOBBY'
    serial: int = 0
    score: dict[str, int] = field(default_factory=lambda: {'RED': 0, 'BLUE': 0})
    castle: dict[str, int] = field(default_factory=lambda: {'RED': 300, 'BLUE': 300})
    egg_owner: dict[str, str | None] = field(default_factory=lambda: {'RED': None, 'BLUE': None})
    winner: str | None = None
    reason: str = ''
    now: float = 0
    alarm: str = 'IDLE'
    next_alarm: float = 55
    alarm_until: float = 0

    def join(self, pid: str):
        red = sum(p.team == 'RED' for p in self.players.values())
        blue = sum(p.team == 'BLUE' for p in self.players.values())
        self.players[pid] = Player(team='RED' if red <= blue else 'BLUE')

    def start(self):
        if len(self.players) < 2 or len({p.team for p in self.players.values()}) < 2:
            return False
        self.serial += 1
        self.phase = 'ACTIVE'
        self.score = {'RED': 0, 'BLUE': 0}
        self.castle = {'RED': 300, 'BLUE': 300}
        self.egg_owner = {'RED': None, 'BLUE': None}
        self.winner = None
        self.reason = ''
        self.alarm = 'IDLE'
        self.next_alarm = self.now + 55
        for p in self.players.values():
            p.carrying = None
            p.alive = True
            p.hp = ROLES[p.role][0]
            p.invulnerable_until = self.now + 2.5
        return True

    def advance(self, seconds: float):
        if not isfinite(seconds) or seconds < 0:
            raise ValueError('clock')
        self.now += seconds
        if self.phase != 'ACTIVE':
            return
        if self.alarm == 'IDLE' and self.now >= self.next_alarm:
            self.alarm = 'WARNING'
            self.alarm_until = self.now + 3
        elif self.alarm == 'WARNING' and self.now >= self.alarm_until:
            self.alarm = 'SIGNAL'
            self.alarm_until = self.now + 6
        elif self.alarm == 'SIGNAL' and self.now >= self.alarm_until:
            self.alarm = 'IDLE'
            self.next_alarm = self.now + 62

    def _check(self, pid, seq):
        if pid not in self.players or type(seq) is not int or not 1 <= seq <= 10**9:
            return False
        p = self.players[pid]
        if seq <= p.last_seq:
            return False
        p.last_seq = seq  # consume monotonic seq even for denied intents
        return True

    def role(self, pid, seq, new_role):
        if not self._check(pid, seq):
            return False
        p = self.players[pid]
        if self.phase == 'ACTIVE' or new_role not in ROLES or self.now - p.last_role_change < 2:
            return False
        p.role = new_role
        p.last_role_change = self.now
        return True

    def steal(self, pid, egg_team, distance=2):
        p = self.players[pid]
        if (self.phase != 'ACTIVE' or not p.alive or not 0 <= distance <= 12
            or egg_team not in self.egg_owner or p.team == egg_team
            or p.carrying is not None or self.egg_owner[egg_team] is not None):
            return False
        self.egg_owner[egg_team] = pid
        p.carrying = egg_team
        return True

    def drop(self, pid):
        p = self.players.get(pid)
        if p is None or p.carrying is None:
            return False
        egg = p.carrying
        p.carrying = None
        if self.egg_owner[egg] == pid:
            self.egg_owner[egg] = None
        return True

    def deliver(self, pid, pad_team, distance=2):
        p = self.players[pid]
        other = 'BLUE' if p.team == 'RED' else 'RED'
        if (self.phase != 'ACTIVE' or not p.alive or not 0 <= distance <= 12
            or pad_team != p.team or p.carrying != other
            or self.egg_owner[other] != pid or self.egg_owner[p.team] is not None):
            return False
        self.drop(pid)
        self.score[p.team] += 1
        if self.score[p.team] >= 2:
            self.finish(p.team, 'EGG_CAPTURE')
        return True

    def finish(self, team, reason):
        if self.phase != 'ACTIVE':
            return False
        self.phase = 'RESULTS'
        self.winner = team
        self.reason = reason
        self.alarm = 'IDLE'
        for pid in list(self.players):
            self.drop(pid)
        return True

    def death(self, pid):
        self.drop(pid)
        self.players[pid].alive = False

    def quit(self, pid):
        if pid not in self.players:
            return False
        team = self.players[pid].team
        self.drop(pid)
        del self.players[pid]
        if self.phase == 'ACTIVE' and not any(p.team == team for p in self.players.values()):
            self.finish('BLUE' if team == 'RED' else 'RED', 'OPPONENT_LEFT')
        return True

    def attack(self, pid, seq, *, enemy_pid=None, enemy_distance=6, target_dot=.8,
               line_of_sight=True, castle_distance=9, castle_dot=.8):
        if not self._check(pid, seq):
            return False
        p = self.players[pid]
        if (self.phase != 'ACTIVE' or not p.alive or not isfinite(self.now)
            or self.now - p.last_attack < .85):
            return False
        p.last_attack = self.now  # consume cooldown if misses
        if enemy_pid is not None and enemy_pid in self.players:
            q = self.players[enemy_pid]
            if (q.alive and q.team != p.team and self.now >= q.invulnerable_until
                and 0 <= enemy_distance <= 10 and target_dot >= .1 and line_of_sight):
                q.hp -= ROLES[p.role][2]
                if q.hp <= 0:
                    self.death(enemy_pid)
                return True
        if 0 <= castle_distance <= 18 and castle_dot >= .1:
            other = 'BLUE' if p.team == 'RED' else 'RED'
            self.castle[other] = max(0, self.castle[other] - ROLES[p.role][3])
            if self.castle[other] == 0:
                self.finish(p.team, 'CASTLE_DESTROYED')
            return True
        return False
