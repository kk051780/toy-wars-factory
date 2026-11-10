"""Independent Python reference for the v40 event lifecycle and bridge contract.

No Roblox engine behavior is modeled. This is not a translation or execution of Luau.
"""
from dataclasses import dataclass, field
from math import isfinite

WEATHER=[('WX01_METEOR',4),('WX02_SMALL',2),('WX03_CROWN',2),('WX04_GLIDE',1),('WX05_CLOCK',1)]
BOSSES={'S1':'GOROGAN','S2':'RAIGALD','S3':'GOROGAN','S4':'RAIGALD'}

class Rejected(Exception): pass

def classify(roll, stage):
    if stage not in BOSSES: raise Rejected('stage')
    if not isinstance(roll,int) or isinstance(roll,bool) or not 0<=roll<100: raise Rejected('roll')
    if roll<65: return 'NORMAL','NONE'
    if roll<90: return 'BOSS',BOSSES[stage]
    offset=roll-90
    for kind,n in WEATHER:
        if offset<n: return 'WEATHER',kind
        offset-=n
@dataclass
class BridgeReference:
    stage: str='S1'
    match_id: str='m1'
    epoch:int=1
    start:float=0
    deadline:float=100
    approved_ligardo_alias:bool=False
    approved_weather:bool=False
    active:bool=True
    enabled:bool=True
    last:float=0
    decided:bool=False
    kind:str='NONE'
    subtype:str='NONE'
    phase:str='WAIT'
    warn_end:float=0
    active_end:float=0
    roll_calls:int=0
    warnings:int=0
    activations:int=0
    cleanup_calls:int=0
    denied_reason:str=''
    history:list=field(default_factory=list)

    def deny(self,reason):
        if self.phase=='ACTIVE' or self.warnings:
            if self.cleanup_calls==0:
                self.cleanup_calls+=1
                self.history.append('CLEANUP')
        self.enabled=False
        self.denied_reason=reason
        self.phase='DONE'
        return reason

    def tick(self,now,roll=None,*,active=True,match_id=None,epoch=None,stage=None):
        if not self.enabled: return 'DISABLED'
        if not isinstance(now,(int,float)) or isinstance(now,bool) or not isfinite(now) or now<self.last:
            return self.deny('TIME_REVERSED')
        if match_id is not None and match_id!=self.match_id:
            return self.deny('ROUND_REPLACED')
        if epoch is not None and epoch!=self.epoch:
            return self.deny('ROUND_REPLACED')
        if stage is not None and stage!=self.stage:
            return self.deny('STAGE_REPLACED')
        self.last=now
        if not active or now>=self.deadline: return self.deny('ROUND_FINISHED')
        if self.phase=='DONE': return 'DONE'
        if not self.decided:
            if now-self.start<20:return 'WAIT'
            if self.deadline-now<19:
                self.decided=True;self.phase='DONE';return 'INSUFFICIENT_TIME'
            self.roll_calls+=1
            if roll is None:return self.deny('ROLL_UNAVAILABLE')
            try: kind,subtype=classify(roll,self.stage)
            except Rejected:return self.deny('ROLL_INVALID')
            self.decided=True;self.kind=kind;self.subtype=subtype
            if kind=='NORMAL':self.phase='DONE';return 'NORMAL'
            if kind=='BOSS' and subtype=='RAIGALD':
                if not self.approved_ligardo_alias:return self.deny('RAIGALD_LIGARDO_ALIAS_REVIEW_REQUIRED')
                self.subtype='LIGARDO'
            if kind=='WEATHER' and not self.approved_weather:
                return self.deny('WEATHER_RUNTIME_MISSING')
            dur=17 if kind=='BOSS' else {'WX01_METEOR':5,'WX02_SMALL':7,'WX03_CROWN':8,'WX04_GLIDE':6,'WX05_CLOCK':6}[subtype]
            warning=2.5 if kind=='BOSS' else 2
            if self.deadline-now<warning+dur+.5:
                self.kind='NORMAL';self.subtype='NONE';self.phase='DONE';return 'NORMAL_DUE_TIME'
            self.warn_end=now+warning;self.active_end=self.warn_end+dur
            self.warnings+=1;self.phase='TELEGRAPH';self.history.append('WARNING')
            return 'WARNING'
        if self.phase=='TELEGRAPH' and now>=self.warn_end:
            self.activations+=1;self.phase='ACTIVE';self.history.append('ACTIVATE');return 'ACTIVATE'
        if self.phase=='ACTIVE' and now>=self.active_end:
            self.cleanup_calls+=1;self.phase='DONE';self.history.append('CLEANUP');return 'CLEANUP'
        return self.phase

    def stop(self):
        self.deny('OWNER_STOP')
