"""Python control oracle for D13 pure rules; does not run Roblox Luau or verify an adapter."""
from dataclasses import dataclass, field
from math import isfinite

SEV={'CALM':0,'RESET':0,'WATCH':1,'ALERT':2,'CHASE':3}
DURATION={'gate_damage':4,'guard_los':7,'egg_picked':7,'egg_carrier_los':4}
DEST={'gate_damage':'FRONT','guard_los':'FLANK','egg_picked':'EXIT','egg_carrier_los':'EXIT'}
STATE={'gate_damage':'WATCH','guard_los':'ALERT','egg_picked':'ALERT','egg_carrier_los':'CHASE'}

@dataclass
class Director:
    round_id:str
    last_time:float=-1
    closed:bool=False
    seen:set=field(default_factory=set)
    order:list=field(default_factory=list)
    teams:dict=field(default_factory=dict)

    def step(self,now,event,guards):
        if not isinstance(now,(int,float)) or not isfinite(now) or now<0 or now<self.last_time:
            return {'status':'REJECT_TIME','intents':[]}
        if (not isinstance(event,dict) or not isinstance(event.get('id'),str) or not event['id'] or
            not isinstance(event.get('defenderTeam'),str) or not event['defenderTeam'] or
            event.get('roundId')!=self.round_id or not isinstance(event.get('type'),str) or event.get('type') not in (set(DEST)|{'egg_dropped','round_end'})):
            return {'status':'REJECT_EVENT','intents':[]}
        if self.closed:return {'status':'CLOSED','intents':[]}
        if event['id'] in self.seen:return {'status':'DUPLICATE','intents':[]}
        self.last_time=now
        self.seen.add(event['id']);self.order.append(event['id'])
        if len(self.order)>128:self.seen.remove(self.order.pop(0))
        if event['type']=='round_end':
            self.closed=True;self.teams={}
            return {'status':'ENDED','intents':[],'mode':'CALM'}
        team=event['defenderTeam']
        t=self.teams.setdefault(team,{'mode':'CALM','until':0,'retask':{}})
        if now>=t['until']:
            t['mode']='CALM';t['until']=now
        if event['type']=='egg_dropped':
            t['mode']='RESET';t['until']=now
            return {'status':'RESET','intents':[],'mode':'RESET'}
        typ=event['type'];proposed=STATE[typ]
        if SEV[proposed]>=SEV[t['mode']]:t['mode']=proposed
        t['until']=max(t['until'],now+DURATION[typ])
        posts=['EGG','FRONT','FLANK','RESERVE','EXIT']
        counts={p:sum(g.get('team')==team and g.get('alive') is True and g.get('post')==p for g in guards) for p in posts}
        eligible=[]
        for g in guards:
            if (g.get('team')==team and g.get('alive') is True and g.get('movable') is True
                and isinstance(g.get('id'),str) and isinstance(g.get('post'),str)
                and g['post'] in posts and g['post'] != DEST[typ]
                and now-t['retask'].get(g['id'],-100000)>=2
                and (g['post']=='RESERVE' or counts[g['post']]>1)):
                eligible.append((0 if g['post']=='RESERVE' else 1,g['id'],g['post']))
        intents=[]
        for _,gid,post in sorted(eligible):
            if len(intents)>=2:break
            if post=='RESERVE' or counts[post]>1:
                counts[post]-=1;t['retask'][gid]=now
                intents.append({'guardId':gid,'fromPost':post,'toPost':DEST[typ]})
        return {'status':'ACCEPTED','mode':t['mode'],'intents':intents,'untilTime':t['until']}
