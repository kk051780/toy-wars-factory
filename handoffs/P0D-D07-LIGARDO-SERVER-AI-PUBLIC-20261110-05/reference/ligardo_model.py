"""Independent Python oracle of the bounded Ligardo server intent FSM.
Never apply actual damage. Main gameplay source/Studio remain Windows Codex-owned.
"""
from dataclasses import dataclass, field
from math import dist, isfinite


def valid_id(v):
    return isinstance(v, str) and 1 <= len(v) <= 64 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-' for c in v)


def point(v):
    return isinstance(v, dict) and set(v) == {'x', 'z'} and all(
        isinstance(v[k], (int, float)) and not isinstance(v[k], bool) and isfinite(v[k]) and abs(v[k]) < 100000 for k in ('x', 'z'))


def magnitude(a, b):
    return dist((a['x'], a['z']), (b['x'], b['z']))


@dataclass
class Ligardo:
    round_id: str
    event_id: str
    boss_id: str
    stage: str
    spawn: dict
    started: float
    pos: dict = field(default_factory=dict)
    last_time: float = 0
    seq: int = -1
    phase: str = 'SEEK'
    target_id: str | None = None
    charge_until: float | None = None
    cooldown_until: float = 0
    attempts: int = 0
    closed: bool = False

    def __post_init__(self):
        if not all(map(valid_id, (self.round_id, self.event_id, self.boss_id))) or self.stage not in ('S2', 'S4') or not point(self.spawn) or not isinstance(self.started, (int,float)) or not isfinite(self.started) or self.started < 0:
            raise ValueError('INVALID_START')
        self.pos = dict(self.spawn)
        self.last_time = self.started
        self.cooldown_until = self.started

    def stop(self):
        self.closed = True
        self.phase = 'CLOSED'
        self.target_id = None
        self.charge_until = None

    def eligible(self, p):
        return isinstance(p, dict) and valid_id(p.get('id')) and p['id'] != self.boss_id and p.get('alive') is True and p.get('team') == 'RAIDERS' and p.get('invulnerable') is not True and point(p.get('pos')) and magnitude(p['pos'], self.spawn) <= 55

    def target(self, roster):
        if not isinstance(roster,list) or len(roster)>16:
            return None
        ids=[p['id'] for p in roster if isinstance(p,dict) and valid_id(p.get('id'))]
        if len(ids) != len(set(ids)):
            return None
        return min((p for p in roster if self.eligible(p)),key=lambda p:(magnitude(p['pos'],self.pos),p['id']), default=None)

    def tick(self, round_, now, seq):
        if self.closed: return [], 'CLOSED'
        if not isinstance(round_,dict) or any((round_.get(k)!=v for k,v in (('roundId',self.round_id),('eventId',self.event_id),('bossId',self.boss_id),('stage',self.stage)))) or round_.get('running') is not True or round_.get('authorized') is not True:
            self.stop()
            return [{'kind':'STOP','why':'ROUND_MISMATCH'}],'ROUND_MISMATCH'
        if not isinstance(now,(int,float)) or not isfinite(now) or now<self.last_time or abs(now)>=100000 or not isinstance(seq,int) or isinstance(seq,bool) or seq<=self.seq or seq>=100000:
            return [], 'STALE_INPUT'
        roster=round_.get('roster')
        if not isinstance(roster,list) or len(roster)>16:
            return [], 'INVALID_ROSTER'
        dt=now-self.last_time
        self.last_time=now
        self.seq=seq
        if round_.get('bossAlive') is not True or now >= self.started+16:
            self.stop()
            return [{'kind':'STOP','why':'BOSS_DEAD_OR_EXPIRED'}],None
        if self.phase=='CHARGE':
            if now<self.charge_until: return [],None
            target=next((p for p in roster if isinstance(p,dict) and p.get('id')==self.target_id),None)
            matches=[p for p in roster if isinstance(p,dict) and p.get('id')==self.target_id]
            events=[]
            if len(matches)==1 and self.eligible(target) and magnitude(target['pos'],self.pos)<=12:
                events=[{'kind':'LIGHTNING_INTENT','targetId':target['id'],'damageCap':7,'roundId':self.round_id,'eventId':self.event_id,'attackNo':self.attempts,'bossPos':dict(self.pos)}]
            self.target_id=None;self.charge_until=None;self.phase='COOLDOWN';self.cooldown_until=now+2.5
            return events,None
        if self.phase=='COOLDOWN':
            if now < self.cooldown_until: return [],None
            self.phase='SEEK'
        if self.attempts>=3: return [],None
        target=self.target(roster)
        if target is None: return [],None
        d=magnitude(target['pos'],self.pos)
        if d<=12:
            self.phase='CHARGE';self.target_id=target['id'];self.charge_until=now+2;self.attempts+=1
            return [{'kind':'TELEGRAPH','targetId':target['id'],'seconds':2,'attackNo':self.attempts,'roundId':self.round_id,'eventId':self.event_id}],None
        if d<=0.001 or dt<=0: return [],None
        step=min(10*min(dt,0.5),d)
        move={k:self.pos[k]+(target['pos'][k]-self.pos[k])/d*step for k in ('x','z')}
        leash=magnitude(move,self.spawn)
        if leash>36:
            move={k:self.spawn[k]+(move[k]-self.spawn[k])/leash*36 for k in ('x','z')}
        self.pos=move
        return [{'kind':'MOVE_INTENT','position':move,'roundId':self.round_id,'eventId':self.event_id}],None


def authorize_lightning(intent,snapshot,los,ledger):
    if not isinstance(intent,dict) or intent.get('kind')!='LIGHTNING_INTENT': return False,'NO_INTENT'
    if not isinstance(snapshot,dict) or snapshot.get('authorized') is not True or snapshot.get('running') is not True: return False,'UNTRUSTED_ROUND'
    if not isinstance(ledger,dict) or ledger.get('roundId')!=intent.get('roundId') or ledger.get('eventId')!=intent.get('eventId') or not isinstance(ledger.get('consumed'),set): return False,'LEDGER_REQUIRED'
    if any(snapshot.get(k)!=intent.get(k) for k in ('roundId','eventId')): return False,'STALE_ROUND'
    if intent.get('attackNo') not in (1,2,3) or intent.get('damageCap')!=7: return False,'CAP'
    if not point(intent.get('bossPos')) or not point(snapshot.get('bossPos')) or magnitude(intent['bossPos'],snapshot['bossPos'])>2:return False,'BOSS_POSITION'
    if intent['attackNo'] in ledger['consumed']:return False,'REPLAY'
    roster=snapshot.get('roster')
    if not isinstance(roster,list) or len(roster)>16 or not callable(los):return False,'ROSTER_OR_LOS'
    matches=[p for p in roster if isinstance(p,dict) and p.get('id')==intent.get('targetId')]
    if len(matches)!=1:return False,'TARGET_COUNT'
    p=matches[0]
    if not p.get('alive') is True or p.get('team')!='RAIDERS' or p.get('invulnerable') is True or not point(p.get('pos')) or magnitude(snapshot['bossPos'],p['pos'])>12:return False,'INVALID_TARGET'
    if los(snapshot['bossPos'],p['pos'],p['id']) is not True:return False,'LOS_BLOCKED'
    ledger['consumed'].add(intent['attackNo'])
    return True,{'targetId':p['id'],'maxDamage':7,'roundId':intent['roundId'],'eventId':intent['eventId'],'attackNo':intent['attackNo']}
