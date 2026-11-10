"""Independent Python model of server-only Gorogan composition safety.
No Roblox APIs or live game access. Deliberately conservative oracle.
"""
from dataclasses import dataclass, field

@dataclass
class Round:
    name: str
    stage: str = 'S1'
    now: float = 100.0
    deadline: float = 120.0
    canonical: bool = True
    round_live: bool = True
    event: str = 'ev_01'
    active: bool = False
    closed: bool = False
    damage_receipt: int | None = None
    hit_players: set = field(default_factory=set)
    seen: set = field(default_factory=set)
    callback_errors: set = field(default_factory=set)
    owner: str = 'SERVER'
    boss_pos: tuple = (0.0, 5.5, 0.0)
    visual: list = field(default_factory=list)
    navigation: list = field(default_factory=list)
    damage: list = field(default_factory=list)
    seq: int = 0
    spawn_at: float = 100
    expiry: float = 114
    attacks: int = 0
    reentrant: bool = False

    def start(self, *, claim=None, origin=(0,0,0)):
        if self.active or self.closed or self.name in self.seen: return 'REPLAY_OR_ACTIVE'
        if not self.canonical or not self.round_live or self.stage not in {'S1','S3'}: return 'NOT_CANONICAL'
        if claim is not None and (claim.get('event')!='ACTIVATE' or claim.get('kind')!='BOSS' or claim.get('subtype')!='GOROGAN' or claim.get('matchId')!=self.name):return 'UNSAFE_EVENT'
        if self.deadline-self.now<=2 or self.owner!='SERVER':return 'UNSAFE_SERVER'
        if any(abs(x)>2048 for x in origin) or not 0<=self.now<=1e12:return 'BAD_ORIGIN'
        self.spawn_at=self.now
        self.expiry=min(self.now+14,self.deadline)
        self.seen.add(self.name)
        self.active=True
        self._visual('START')
        return 'STARTED'

    def _visual(self,kind):
        self.seq+=1;self.visual.append((self.name,self.event,self.stage,self.seq,kind))

    def tick(self, now, kind, *, path_yield_round=None, target=None, authorized=False, attack=1, player=None, distance=0, in_safe=False, wall=False, dead=False):
        if not self.active:return 'INACTIVE'
        if self.reentrant:return 'REENTRANT'
        self.reentrant=True
        try:
            if now<self.now or not self.round_live or now>=self.expiry:
                self.stop();return 'CLOSED'
            self.now=now
            if kind=='MOVE':
                if path_yield_round is not None and path_yield_round!=self.name:
                    self.stop();return 'STALE_AFTER_YIELD'
                if distance>8.1 or self.owner!='SERVER':return 'NAV_REJECTED'
                self.navigation.append((self.event,now,target));return 'MOVED'
            if kind=='STOMP_WARNING':
                self._visual('STOMP');return 'WARNED'
            if kind=='STOMP_RESOLVE':
                if not authorized or not 1<=attack<=3 or attack in self.hit_players:
                    return 'UNATTESTED'
                self.damage_receipt=attack
                try:
                    if 'damage' in self.callback_errors:raise RuntimeError('simulated failure')
                    if player and not (in_safe or wall or dead or distance>7) and (attack,player) not in self.hit_players:
                        self.hit_players.add((attack,player))
                        self.damage.append((attack,player,8))
                except RuntimeError:
                    self.stop();return 'FAIL_CLOSED'
                finally:
                    self.damage_receipt=None
                return 'RESOLVED'
            if kind=='END':
                self.stop();return 'CLOSED'
            self.stop();return 'INVALID_COMMAND'
        finally:
            self.reentrant=False

    def stop(self):
        if not self.active:return False
        self.active=False;self.closed=True;self.damage_receipt=None;self._visual('END');return True
