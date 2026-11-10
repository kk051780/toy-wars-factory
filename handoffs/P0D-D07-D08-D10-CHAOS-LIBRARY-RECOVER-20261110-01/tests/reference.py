"""Deterministic Python model, independent of Roblox Studio, for v40–42 reference.
Not a source of server authority; all evidence arguments require a trusted server caller.
"""
from dataclasses import dataclass, field
from math import isfinite
import re

STAGES={'S1':'GOROGAN','S2':'RAIGALD','S3':'GOROGAN','S4':'RAIGALD'}
JOBS={'WARRIOR','NINJA','TRAPPER','ZOMBIE_MASTER','BEAST_TAMER','MAGE','BUILDER'}
WEATHER=('WX01_METEOR','WX02_SMALL','WX03_CROWN','WX04_GLIDE','WX05_CLOCK')
WEIGHTS=(4,2,2,1,1)
DURATION=dict(zip(WEATHER,(5,7,8,6,6)))
PATTERN=re.compile(r'^[A-Za-z0-9_-]{1,96}$')

def finite(x): return isinstance(x,(float,int)) and not isinstance(x,bool) and isfinite(x)
def valid_id(x): return isinstance(x,str) and PATTERN.fullmatch(x) is not None

def classify(roll,stage):
    if stage not in STAGES: raise ValueError('STAGE_INVALID')
    if not finite(roll) or not float(roll).is_integer() or not 0<=roll<100:
        raise ValueError('ROLL_INVALID')
    if roll<65: return 'NORMAL','NONE'
    if roll<90: return 'BOSS',STAGES[stage]
    r=roll-90
    for kind,weight in zip(WEATHER,WEIGHTS):
        if r<weight: return 'WEATHER',kind
        r-=weight
    raise ValueError('CLASSIFY_FAILED')

@dataclass
class Chaos:
    match:str
    stage:str
    start:float=0
    last:float=0
    decided:bool=False
    kind:str='NONE'
    subtype:str='NONE'
    phase:str='WAIT'
    warning_end:float=0
    active_end:float=0
    finished:bool=False
    packets:list=field(default_factory=list)
    def __post_init__(self):
        if not valid_id(self.match) or self.stage not in STAGES or not finite(self.start) or self.start<0: raise ValueError('INIT_INVALID')
        self.last=self.start
    def advance(self,now,deadline,roll=None,active=True):
        if not finite(now) or not finite(deadline) or now<self.last: raise ValueError('TIME_NON_MONOTONIC')
        if self.finished: return None
        self.last=now
        if not active or now>=deadline:
            self.finished=True;self.phase='DONE';return {'event':'CLEANUP'}
        if not self.decided:
            if now-self.start<20:return None
            self.decided=True
            if deadline-now<19:
                self.kind='NORMAL';self.phase='DONE';return None
            if roll is None:raise ValueError('SERVER_ROLL_REQUIRED')
            self.kind,self.subtype=classify(roll,self.stage)
            if self.kind=='NORMAL':self.phase='DONE';return None
            warn=2.5 if self.kind=='BOSS' else 2
            duration=17 if self.kind=='BOSS' else DURATION[self.subtype]
            if deadline-now < warn+duration+.5:
                self.kind='NORMAL';self.subtype='NONE';self.phase='DONE';return None
            self.warning_end=now+warn;self.active_end=self.warning_end+duration
            self.phase='TELEGRAPH'
            return {'event':'WARNING','kind':self.kind,'subtype':self.subtype}
        if self.phase=='TELEGRAPH' and now>=self.warning_end:
            self.phase='ACTIVE';return {'event':'ACTIVATE','kind':self.kind,'subtype':self.subtype}
        if self.phase=='ACTIVE' and now>=self.active_end:
            self.phase='DONE';return {'event':'CLEANUP'}
        return None

@dataclass
class Boss:
    match:str
    last:float=0
    phase:str='NEUTRAL'
    owner:str|None=None
    expires:float=0
    present:bool=False
    boss:str|None=None
    used:set=field(default_factory=set)
    def spawn(self,boss,now):
        if not finite(now) or now<self.last:return False,'TIME_INVALID'
        if self.present or self.phase=='DONE' or boss not in ('GOROGAN','RAIGALD'):return False,'SPAWN_REJECTED'
        self.last=now;self.present=True;self.boss=boss;return True,'SPAWNED'
    def command(self,now,user,team,proof):
        if not finite(now) or now<self.last:return False,'TIME_REJECTED'
        self.last=now
        if not self.present or self.phase=='DONE':return False,'BOSS_NOT_PRESENT'
        if self.owner and now<self.expires:return False,'ALREADY_CONTROLLED'
        if team not in ('BLUE','RED') or not isinstance(user,int) or isinstance(user,bool) or user<1:return False,'IDENTITY_REJECTED'
        if not isinstance(proof,dict) or proof.get('matchId')!=self.match or proof.get('team')!=team or proof.get('userId')!=user or proof.get('serverRosterConfirmed') is not True or proof.get('alive') is not True or proof.get('hasRelicOrFreeTamerSkill') is not True or proof.get('inNeutralZone') is not True or proof.get('carryingEgg') is True:
            return False,'SERVER_EVIDENCE_REQUIRED'
        if user in self.used:return False,'ONE_COMMAND_PER_USER'
        self.used.add(user);self.owner=team;self.expires=now+7;self.phase='DIRECTED';return True,'DIRECTED'
    def tick(self,now,active=True):
        if not finite(now) or now<self.last:return False,'TIME_REJECTED'
        self.last=now
        if not active:self.phase='DONE';self.owner=None;self.present=False;return True,'CLEANUP'
        if self.phase=='DIRECTED' and now>=self.expires:self.phase='NEUTRAL';self.owner=None;return True,'RETURNED_NEUTRAL'
        return True,'NO_CHANGE'

@dataclass
class TimeSafety:
    match:str
    last:float=0
    samples:dict=field(default_factory=dict)
    used:set=field(default_factory=set)
    closed:bool=False
    def record(self,now,user,pos,proof):
        if self.closed or not finite(now) or now<self.last:return False,'TIME_INVALID'
        self.last=now
        if not isinstance(user,int) or user<1 or not isinstance(proof,dict) or proof.get('matchId')!=self.match or proof.get('alive') is not True or proof.get('safeFloor') is not True or proof.get('carryingEgg') is True:return False,'RECORD_BLOCKED'
        if not isinstance(pos,dict) or not all(finite(pos.get(k)) and abs(pos[k])<=10000 for k in 'xyz'):return False,'POSITION_INVALID'
        h=self.samples.setdefault(user,[])
        h.append((now,{k:pos[k] for k in 'xyz'}))
        while h and (now-h[0][0]>3 or len(h)>10):h.pop(0)
        return True,'RECORDED'
    def rewind(self,now,user,proof,validator):
        if self.closed or not finite(now) or now<self.last:return None,'TIME_INVALID'
        self.last=now
        if not isinstance(proof,dict) or proof.get('matchId')!=self.match or proof.get('userId')!=user or proof.get('alive') is not True or proof.get('carryingEgg') is True or proof.get('activeMatch') is not True or proof.get('serverRosterConfirmed') is not True or user in self.used:return None,'RECALL_BLOCKED'
        if not callable(validator):return None,'VALIDATOR_REQUIRED'
        target=None
        for at,p in self.samples.get(user,[]):
            if now-3<=at<=now-2:target=p
        if target is None or not validator(target,proof):return None,'NO_SAFE_SNAPSHOT'
        self.used.add(user)
        return dict(target),'RECALL_POSITION_ONLY'
    def close(self):self.closed=True;self.samples={}

def level(xp):
    if not finite(xp) or xp<0:return 1
    lv=1
    while lv<25:
        needed=40+30*(lv-1)
        if xp<needed:break
        xp-=needed;lv+=1
    return lv

def mastery(points):
    if not finite(points) or points<0:return 0
    return sum(points>=t for t in (100,250,500,1000,2000))

@dataclass
class Progression:
    scope:str
    users:dict=field(default_factory=dict)
    seen:set=field(default_factory=set)
    def finalize(self,e):
        if not isinstance(e,dict) or not valid_id(e.get('matchId')) or e.get('scope')!=self.scope or not isinstance(e.get('userId'),int) or isinstance(e.get('userId'),bool) or e['userId']<1 or e.get('job') not in JOBS or e.get('serverRoundFinalized') is not True or e.get('rosterConfirmed') is not True or not finite(e.get('duration')) or e['duration']<=0 or not finite(e.get('activeSeconds')) or not 0<=e['activeSeconds']<=e['duration']:
            return None,'INVALID_SERVER_EVIDENCE'
        key=(e['matchId'],e['userId'])
        if key in self.seen:return None,'ALREADY_FINALIZED'
        if len(self.seen)>=512:return None,'LEDGER_FULL'
        self.seen.add(key)
        prof=self.users.setdefault(e['userId'],{'xp':0,'jobs':{}})
        ok=e['activeSeconds']>=min(15,e['duration']*.3) and e.get('meaningfulActionConfirmed') is True
        cats=e.get('assistTypes',{})
        assists=sum(cats.get(k) is True for k in ('DEFENSE','ESCORT','SUPPORT')) if isinstance(cats,dict) else 0
        xp=min(104,45+20*(e.get('won') is True)+15*(e.get('eggDelivered') is True)+8*assists) if ok else 0
        mp=min(57,20+15*(e.get('won') is True)+10*(e.get('eggDelivered') is True)+4*assists) if ok else 0
        prof['xp']+=xp
        prof['jobs'][e['job']]=prof['jobs'].get(e['job'],0)+mp
        return {'xpAwarded':xp,'masteryAwarded':mp,'totalXp':prof['xp'],'level':level(prof['xp']),'jobMastery':mastery(prof['jobs'][e['job']]),'sessionOnly':True,'saved':False,'combatStatsChanged':False},'FINALIZED'
