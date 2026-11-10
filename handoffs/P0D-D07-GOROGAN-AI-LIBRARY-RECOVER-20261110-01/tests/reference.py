"""Independent Python behavior oracle for D07 neutral boss core. NOT Luau VM."""
from math import isfinite, hypot


def valid_id(s):
    return isinstance(s, str) and 1 <= len(s) <= 64 and all(c.isalnum() or c in '_-' for c in s) and s.isascii()


def valid_pos(p):
    return isinstance(p, dict) and set(('x','y','z')) <= p.keys() and all(isinstance(p[k],(int,float)) and not isinstance(p[k],bool) and isfinite(p[k]) and -2048 <= p[k] <= 2048 and (-100 <= p['y'] <= 700) for k in ('x','y','z'))


class Boss:
    def __init__(self):
        self.seen = set(); self.active = None

    def start(self, round_id='round_1', event_id='evt_1', stage='S1', kind='BOSS', subtype='GOROGAN', origin=None, now=0.0, ends_at=14.0):
        origin = origin if origin is not None else dict(x=0.,y=0.,z=0.)
        if self.active is not None or round_id in self.seen or len(self.seen) >= 128 or not valid_id(round_id) or not valid_id(event_id) or stage not in ('S1','S3') or kind != 'BOSS' or subtype != 'GOROGAN' or not valid_pos(origin) or not (isinstance(now,(int,float)) and isfinite(now) and 0<=now<=1e12) or not (isinstance(ends_at,(int,float)) and isfinite(ends_at) and ends_at>now and ends_at-now<=14):
            return False
        self.seen.add(round_id)
        self.active = dict(round_id=round_id, event_id=event_id, stage=stage, origin=origin, ends_at=ends_at, last_now=now, attack_id=0, stomps=0, phase='ACTIVE', windup_ends=0, center=None, next_attack_at=now+2, next_move_at=now)
        return True

    def stop(self, round_id, event_id):
        s=self.active
        if s is None or s['round_id']!=round_id or s['event_id']!=event_id: return None
        self.active=None
        return dict(kind='END',reason='ROUND_END')

    def tick(self, now, boss_position, players=(), round_id='round_1', event_id='evt_1', active=True):
        s=self.active
        if s is None: return None, 'INACTIVE'
        if s['round_id']!=round_id or s['event_id']!=event_id or not isinstance(now,(int,float)) or not isfinite(now) or now < s['last_now'] or not valid_pos(boss_position): return None,'STALE_OR_INVALID'
        s['last_now']=now
        if not active or now>=s['ends_at']:
            self.active=None
            return dict(kind='END'),None
        if (boss_position['x']-s['origin']['x'])**2+(boss_position['z']-s['origin']['z'])**2>42**2:
            return dict(kind='MOVE',reason='LEASH_RETURN',position=s['origin']),None
        if s['phase']=='WINDUP':
            if now < s['windup_ends']: return None,None
            s['phase']='ACTIVE';s['next_attack_at']=now+2
            return dict(kind='STOMP_RESOLVE',attackId=s['attack_id'],center=s['center'],damage=8,radius=7),None
        if not isinstance(players,(list,tuple)) or len(players)>24: return None,'INVALID_ROSTER'
        ids=set(); qualified=[]
        for p in players:
            if not isinstance(p,dict) or not valid_id(p.get('playerId')) or p['playerId'] in ids: return None,'INVALID_ROSTER'
            ids.add(p['playerId'])
            if p.get('alive') is True and p.get('team') in ('BLUE','RED') and p.get('inSafeZone') is not True and valid_pos(p.get('position')):
                v=p['position'];d2=(v['x']-boss_position['x'])**2+(v['z']-boss_position['z'])**2
                if abs(v['y']-boss_position['y'])<=12 and d2<=45**2: qualified.append((d2,p['playerId'],p))
        if not qualified: return None,None
        qualified.sort(key=lambda p:(p[0],p[1])); distance,pid,target=qualified[0]
        if s['stomps']<3 and now >= s['next_attack_at'] and now+2<s['ends_at'] and distance<=9**2:
            s['stomps']+=1;s['attack_id']+=1;s['phase']='WINDUP';s['center']=dict(boss_position);s['windup_ends']=now+2
            return dict(kind='STOMP_WARNING',attackId=s['attack_id'],center=dict(boss_position),windupEnds=now+2),None
        if now < s['next_move_at'] or distance<=8**2: return None,None
        dx=target['position']['x']-boss_position['x'];dz=target['position']['z']-boss_position['z'];norm=hypot(dx,dz)
        if norm==0:return None,None
        step=min(8,norm); dest=dict(x=boss_position['x']+dx/norm*step,y=boss_position['y'],z=boss_position['z']+dz/norm*step)
        if (dest['x']-s['origin']['x'])**2+(dest['z']-s['origin']['z'])**2>42**2: dest=s['origin']
        s['next_move_at']=now+.75
        return dict(kind='MOVE',reason='CHASE',position=dest,targetId=pid),None
