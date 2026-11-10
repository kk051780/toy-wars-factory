"""Server-only Python reference model for D15 TrapRescueCore.luau, not a Roblox runtime."""
import math

CAST_RANGE = 16
RESCUE_RANGE = 10
COOLDOWN = 12
ROOT = 2
ESCAPE_AT = 1.25
RESCUE_AT = .5
TICKS = 3
TICK_INTERVAL = 1
DAMAGE = 3
IMMUNITY = 6
MAX_ROSTER = 24


def valid_id(x):
    return isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= 10**15


def finite(n):
    return isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)


class TrapState:
    def __init__(self, match_id='round-test'):
        if not isinstance(match_id, str) or not (1 <= len(match_id) <= 96):
            raise ValueError('invalid match id')
        self.match_id = match_id
        self.now = 0
        self.closed = False
        self.roster = {}
        self.effects = {}
        self.immune_until = {}
        self.next_cast_at = {}

    def release(self, target_id):
        if self.effects.pop(target_id, None) is not None:
            self.immune_until[target_id] = max(self.immune_until.get(target_id, 0), self.now + IMMUNITY)

    def sync(self, user_id, team, job, alive, x, z):
        if self.closed: return False, 'MATCH_CLOSED'
        if (not valid_id(user_id) or team not in ('BLUE','RED') or not isinstance(job,str)
                or not isinstance(alive,bool) or not finite(x) or not finite(z)
                or abs(x)>100000 or abs(z)>100000): return False, 'BAD_SERVER_ROSTER'
        prev = self.roster.get(user_id)
        if prev is None and len(self.roster) >= MAX_ROSTER: return False, 'ROSTER_FULL'
        if prev and (prev['team'] != team or prev['job'] != job or (prev['alive'] and not alive)):
            self.release(user_id)
            for tid, fx in list(self.effects.items()):
                if fx['caster'] == user_id: self.release(tid)
        self.roster[user_id] = dict(team=team,job=job,alive=alive,x=x,z=z)
        return True, 'SYNCED'

    def remove(self, user_id):
        if self.closed: return
        self.release(user_id)
        for tid, fx in list(self.effects.items()):
            if fx['caster'] == user_id: self.release(tid)
        self.roster.pop(user_id, None)

    def advance(self, now):
        if self.closed: return False,'MATCH_CLOSED',[]
        if not finite(now) or now < self.now or now > 3600: return False,'BAD_CLOCK',[]
        self.now = now
        out = []
        for target_id,fx in list(self.effects.items()):
            target = self.roster.get(target_id)
            source = self.roster.get(fx['caster'])
            if (target is None or source is None or not target['alive'] or not source['alive']
                    or target['team'] == source['team']):
                self.release(target_id)
                continue
            while fx['ticks'] < TICKS and self.now >= fx['started'] + (fx['ticks']+1)*TICK_INTERVAL:
                fx['ticks'] += 1
                out.append(dict(kind='POISON_DAMAGE',targetId=target_id,casterId=fx['caster'],damage=DAMAGE,
                                tick=fx['ticks'],matchId=self.match_id))
            if self.now >= fx['started'] + TICKS*TICK_INTERVAL:
                self.release(target_id)
        return True,'ADVANCED',out

    def cast(self,caster_id,target_id):
        if self.closed:return False,'MATCH_CLOSED'
        if not valid_id(caster_id) or not valid_id(target_id) or caster_id==target_id:return False,'BAD_IDS'
        a,b=self.roster.get(caster_id),self.roster.get(target_id)
        if not a or not b or not a['alive'] or not b['alive']:return False,'NO_LIVE_PLAYER'
        if a['job']!='TRAPPER':return False,'WRONG_JOB'
        if a['team']==b['team']:return False,'FRIENDLY_FIRE'
        if (a['x']-b['x'])**2+(a['z']-b['z'])**2>CAST_RANGE**2:return False,'OUT_OF_RANGE'
        if self.now<self.next_cast_at.get(caster_id,0):return False,'COOLDOWN'
        if target_id in self.effects:return False,'ALREADY_TRAPPED'
        if self.now<self.immune_until.get(target_id,0):return False,'TARGET_IMMUNE'
        if sum(v['caster']==caster_id for v in self.effects.values())>=1:return False,'CASTER_LIMIT'
        self.effects[target_id]=dict(caster=caster_id,started=self.now,ticks=0)
        self.next_cast_at[caster_id]=self.now+COOLDOWN
        return True,'TRAPPED'

    def rescue(self,rescuer_id,target_id):
        if self.closed:return False,'MATCH_CLOSED'
        if not valid_id(rescuer_id) or not valid_id(target_id) or rescuer_id==target_id:return False,'BAD_IDS'
        a,b=self.roster.get(rescuer_id),self.roster.get(target_id)
        fx=self.effects.get(target_id)
        if fx is None:return False,'NOT_TRAPPED'
        if not a or not b or not a['alive'] or not b['alive']:return False,'NO_LIVE_PLAYER'
        if a['team']!=b['team']:return False,'NOT_ALLY'
        if self.now < fx['started']+RESCUE_AT:return False,'RESCUE_TOO_EARLY'
        if (a['x']-b['x'])**2+(a['z']-b['z'])**2>RESCUE_RANGE**2:return False,'OUT_OF_RANGE'
        self.release(target_id)
        return True,'RESCUED'

    def escape(self,target_id):
        if self.closed:return False,'MATCH_CLOSED'
        if not valid_id(target_id):return False,'BAD_IDS'
        fx=self.effects.get(target_id)
        if fx is None:return False,'NOT_TRAPPED'
        p=self.roster.get(target_id)
        if not p or not p['alive']:return False,'NO_LIVE_PLAYER'
        if self.now < fx['started']+ESCAPE_AT:return False,'ESCAPE_TOO_EARLY'
        self.release(target_id)
        return True,'ESCAPED'

    def status(self,user_id):
        fx=self.effects.get(user_id)
        if not fx:
            return dict(trapped=False,rooted=False,poison=False,immunityRemaining=max(0,self.immune_until.get(user_id,0)-self.now))
        return dict(trapped=True,rooted=self.now<fx['started']+ROOT,poison=fx['ticks']<TICKS,immunityRemaining=0)

    def end_match(self):
        self.closed=True
        self.effects.clear();self.roster.clear();self.immune_until.clear();self.next_cast_at.clear()
