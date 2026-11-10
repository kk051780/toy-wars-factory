"""Independent executable Python model for pure D07 synchronized warning contract."""
import math
import re


def finite(v, lo, hi):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and lo <= v <= hi


def ident(v):
    return isinstance(v, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", v))


class Server:
    def __init__(self, match='m1', event='e1', stage='S1', epoch=3, enabled=True, approved=True):
        if not (enabled and approved and ident(match) and ident(event)
                and stage in ('S1', 'S3') and finite(epoch, 0, 1023) and int(epoch)==epoch):
            raise ValueError('disabled or invalid')
        self.match, self.event, self.stage, self.epoch = match, event, stage, epoch
        self.last_attack = 0
        self.last_core = self.last_synced = None
        self.closed = False

    def stamp(self, w, clk):
        if self.closed: return None, 'CLOSED'
        if not (isinstance(w, dict) and w.get('kind')=='STOMP_WARNING'
                and w.get('roundId')==self.match and w.get('eventId')==self.event
                and finite(w.get('attackId'), 1, 3) and int(w['attackId'])==w['attackId']
                and w['attackId']>self.last_attack and finite(w.get('windupEnds'), 0, 1e12)
                and isinstance(clk, dict) and clk.get('roundLive') is True
                and finite(clk.get('coreNow'), 0, 1e12)
                and finite(clk.get('syncedServerNow'), 0, 1e12)):
            return None,'AUTHORITY_OR_COMMAND_INVALID'
        if (self.last_core is not None and clk['coreNow']<self.last_core) or (self.last_synced is not None and clk['syncedServerNow']<self.last_synced):
            self.closed=True;return None,'CLOCK_REVERSED'
        delta=w['windupEnds']-clk['coreNow']
        if not 0<delta<=2.05:return None,'WARNING_NOT_LIVE'
        self.last_attack,self.last_core,self.last_synced=w['attackId'],clk['coreNow'],clk['syncedServerNow']
        return dict(kind='STOMP_DEADLINE',bossId='GOROGAN',matchId=self.match,
                    eventId=self.event,stageId=self.stage,epoch=self.epoch,
                    attackId=w['attackId'],sentServerTime=clk['syncedServerNow'],
                    warningEndsServerTime=clk['syncedServerNow']+delta),'STAMPED'

    def close(self): self.closed=True


class Client:
    def __init__(self, match='m1', event='e1', stage='S1', epoch=3):
        if not (ident(match) and ident(event) and stage in ('S1','S3') and finite(epoch, 0, 1023) and int(epoch)==epoch):raise ValueError('invalid')
        self.match,self.event,self.stage,self.epoch=match,event,stage,epoch
        self.last_attack=0;self.last_now=None;self.deadline=None;self.closed=False

    def accept(self,p,now,active=True):
        if self.closed:return None,'CLOSED'
        if active is not True:self.closed=True;return None,'VISUAL_ENDED'
        if not finite(now,0,1e12) or (self.last_now is not None and now<self.last_now):
            self.closed=True;return None,'CLOCK_INVALID'
        self.last_now=now
        if not (isinstance(p,dict) and p.get('kind')=='STOMP_DEADLINE'
                and p.get('bossId')=='GOROGAN' and p.get('matchId')==self.match
                and p.get('eventId')==self.event and p.get('stageId')==self.stage
                and p.get('epoch')==self.epoch and finite(p.get('attackId'),1,3)
                and int(p['attackId'])==p['attackId'] and p['attackId']>self.last_attack
                and finite(p.get('sentServerTime'),0,1e12)
                and finite(p.get('warningEndsServerTime'),0,1e12)):
            return None,'INVALID_IDENTITY_OR_REPLAY'
        duration=p['warningEndsServerTime']-p['sentServerTime']
        if not 0<duration<=2.05 or p['sentServerTime']>now+0.2:return None,'BAD_SERVER_DEADLINE'
        self.last_attack=p['attackId'];self.deadline=p['warningEndsServerTime']
        if now>=self.deadline:return None,'LATE_EXPIRED'
        return dict(remainingSeconds=min(2,self.deadline-now),serverDelaySeconds=max(0,now-p['sentServerTime']),
                    warningEndsServerTime=self.deadline,attackId=self.last_attack),'RENDER_REMAINING'

    def remaining(self,now,active=True):
        if self.closed or active is not True or not finite(now,0,1e12) or self.deadline is None:return 0
        if self.last_now is not None and now<self.last_now:return 0
        self.last_now=now
        return max(0,min(2,self.deadline-now))
    def close(self):self.closed=True;self.deadline=None
