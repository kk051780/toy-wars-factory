"""Independent deterministic Python oracle for D14 server-supplied RiderMount snapshot decisions.
Not an interpreter of Luau, not a Roblox engine test.
"""
from dataclasses import dataclass
import re

ROLES=('DRIVER','PASSENGER')
LEASE_MS=1500
FRESH_MS=350

def identifier(s):
    return isinstance(s,str) and 1<=len(s)<=80 and re.fullmatch(r'[A-Za-z0-9_.-]+',s)!=None

def integer(x,lo,hi):
    return type(x)==int and lo<=x<=hi

def number(x,lo,hi):
    return type(x) in (int,float) and x==x and lo<=x<=hi

@dataclass(frozen=True)
class Actor:
    role:str
    userId:int
    characterEpoch:int
    seatEpoch:int
    team:str
    alive:bool=True
    isSeated:bool=True
    hasEgg:bool=False
    isSnared:bool=False
    isRewinding:bool=False
    isGliding:bool=False
    distanceStuds:float=2.0

class RiderModel:
    def __init__(self,round_id='round123',vehicle_id='vehicle45',vehicle_type='RAFT'):
        assert identifier(round_id) and identifier(vehicle_id) and vehicle_type in ('CART','RAFT')
        self.round_id=round_id
        self.vehicle_id=vehicle_id
        self.vehicle_type=vehicle_type
        self.epoch=0
        self.seq=0
        self.now=0
        self.expires=0
        self.closed=False
        self.slots={r:None for r in ROLES}

    def _unmount(self,why):
        result=[]
        for role in ROLES:
            a=self.slots[role]
            if a:
                result.append({'role':role,'userId':a.userId,'characterEpoch':a.characterEpoch,'reason':why})
            self.slots[role]=None
        return result

    def close(self,why='ROUND_CLOSED'):
        self.closed=True
        self.expires=0
        return {'ok':True,'reason':'CLOSED','mounts':[],'unmounts':self._unmount(why)}

    def watchdog(self,now):
        if not integer(now,0,2147483647):return {'ok':False,'reason':'INVALID_TIME','mounts':[],'unmounts':[]}
        if now<self.now:return {'ok':False,'reason':'TIME_ROLLBACK','mounts':[],'unmounts':[]}
        self.now=now
        if self.closed:return {'ok':False,'reason':'CLOSED','mounts':[],'unmounts':[]}
        if self.expires>0 and now>=self.expires:
            self.expires=0
            return {'ok':True,'reason':'AUTH_LEASE_EXPIRED','mounts':[],'unmounts':self._unmount('AUTH_EXPIRED')}
        return {'ok':True,'reason':'NO_CHANGE','mounts':[],'unmounts':[]}

    def update(self,snapshot,now):
        reject=lambda reason:{'ok':False,'reason':reason,'mounts':[],'unmounts':[]}
        if self.closed:return reject('CLOSED')
        if not integer(now,0,2147483647) or now<self.now:return reject('INVALID_OR_REWOUND_CLOCK')
        if isinstance(snapshot,dict) and snapshot.get('roundId')!=self.round_id:
            self.now=now
            result=self.close('ROUND_CHANGED')
            result['reason']='ROUND_CHANGED'
            return result
        if isinstance(snapshot,dict) and snapshot.get('roundId')==self.round_id and snapshot.get('roundOpen') is False:
            self.now=now
            result=self.close('ROUND_CLOSED')
            result['reason']='ROUND_CLOSED'
            return result
        if not isinstance(snapshot,dict) or snapshot.get('vehicleId')!=self.vehicle_id or snapshot.get('vehicleType')!=self.vehicle_type:
            return reject('INVALID_AUTHORITY_SNAPSHOT')
        if (snapshot.get('stage') not in ('S1','S2') or not identifier(snapshot.get('team'))
            or not integer(snapshot.get('authorityEpoch'),1,2147483647)
            or not integer(snapshot.get('seq'),1,2147483647)
            or not integer(snapshot.get('issuedAtMs'),0,2147483647)
            or snapshot['issuedAtMs']>now or now-snapshot['issuedAtMs']>FRESH_MS
            or not isinstance(snapshot.get('slots'),dict) or snapshot.get('roundOpen') is not True):
            return reject('INVALID_AUTHORITY_SNAPSHOT')
        e=snapshot['authorityEpoch']; seq=snapshot['seq']; team=snapshot['team']; slots=snapshot['slots']
        if e<self.epoch or e==self.epoch and seq<=self.seq:return reject('REPLAY_OR_OLD_EPOCH')
        driver=slots.get('DRIVER'); passenger=slots.get('PASSENGER')
        def good(a,role):
            if a is None:return True
            return isinstance(a,Actor) and a.role==role and integer(a.userId,1,2147483647) and integer(a.characterEpoch,1,2147483647) and a.seatEpoch==e and a.team==team and a.alive is True and a.isSeated is True and a.hasEgg is False and a.isSnared is False and a.isRewinding is False and a.isGliding is False and number(a.distanceStuds,0,8)
        if not good(driver,'DRIVER') or not good(passenger,'PASSENGER') or passenger is not None and driver is None or driver is not None and passenger is not None and driver.userId==passenger.userId:
            self.now=now
            self.seq=seq
            self.epoch=e
            self.expires=0
            return {'ok':False,'reason':'INVALID_ROSTER','mounts':[],'unmounts':self._unmount('INVALID_ROSTER')}
        changed=e!=self.epoch
        mounts=[]; unmounts=[]
        for role,now_actor in [('DRIVER',driver),('PASSENGER',passenger)]:
            prior=self.slots[role]
            if prior is not None and (changed or (prior.userId,prior.characterEpoch,prior.seatEpoch,prior.role)!=(getattr(now_actor,'userId',None),getattr(now_actor,'characterEpoch',None),getattr(now_actor,'seatEpoch',None),getattr(now_actor,'role',None))):
                unmounts.append({'role':role,'userId':prior.userId,'characterEpoch':prior.characterEpoch,'reason':'NEW_AUTH_EPOCH' if changed else 'SEAT_CHANGED'})
            if now_actor is not None and (changed or prior is None or (prior.userId,prior.characterEpoch,prior.seatEpoch,prior.role)!=(now_actor.userId,now_actor.characterEpoch,now_actor.seatEpoch,now_actor.role)):
                mounts.append({'role':role,'userId':now_actor.userId,'characterEpoch':now_actor.characterEpoch,'seatEpoch':now_actor.seatEpoch})
            self.slots[role]=now_actor
        self.epoch=e;self.seq=seq;self.now=now;self.expires=now+LEASE_MS
        return {'ok':True,'reason':'AUTH_SYNC','mounts':mounts,'unmounts':unmounts}


def snapshot(*,seq=1,epoch=1,now=1000,round_id='round123',vehicle_id='vehicle45',vehicle_type='RAFT',stage='S1',team='BLUE',driver=Actor('DRIVER',100,1,1,'BLUE'),passenger=None,round_open=True):
    return {'seq':seq,'authorityEpoch':epoch,'issuedAtMs':now,'roundId':round_id,'vehicleId':vehicle_id,'vehicleType':vehicle_type,'stage':stage,'team':team,'roundOpen':round_open,'slots':{'DRIVER':driver,'PASSENGER':passenger}}
