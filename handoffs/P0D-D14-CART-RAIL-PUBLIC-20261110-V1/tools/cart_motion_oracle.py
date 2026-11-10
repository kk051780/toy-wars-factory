"""Independent bounded D14 cart rail-motion reference; never touches Roblox."""
from dataclasses import dataclass
import math

class PolicyError(ValueError): pass

def finite_number(v):
    return type(v) in (float, int) and math.isfinite(v)

def distance(a,b): return math.sqrt(sum((b[k]-a[k])**2 for k in ('x','y','z')))

def check_route(route):
    if type(route) is not dict or not isinstance(route.get('id'),str) or not 1<=len(route['id'])<=48 or not all(ch.isascii() and (ch.isalnum() or ch in '_-') for ch in route['id']):
        raise PolicyError('BAD_ROUTE_ID')
    nodes=route.get('nodes')
    if type(nodes) is not list or not 2<=len(nodes)<=24: raise PolicyError('NODE_COUNT')
    speed=route.get('speed')
    if not finite_number(speed) or not 2<=speed<=16: raise PolicyError('SPEED_LIMIT')
    for i,p in enumerate(nodes):
        if type(p) is not dict or any(not finite_number(p.get(k)) or abs(p[k])>2000 for k in ('x','y','z')): raise PolicyError('BAD_POSITION')
        if i and not 6<=distance(nodes[i-1],p)<=80: raise PolicyError('EDGE_RANGE')
    return True

@dataclass
class Cart:
    route:dict
    round_id:str
    team_id:str
    leg:int=0
    progress:float=0
    moving:bool=False
    ended:bool=False
    last_command:int=0
    position:dict=None
    def __post_init__(self):
        check_route(self.route)
        if not isinstance(self.round_id,str) or not 1<=len(self.round_id)<=80: raise PolicyError('ROUND_ID')
        if self.team_id not in ('RED','BLUE'): raise PolicyError('TEAM_ID')
        self.position=dict(self.route['nodes'][0])
    def request(self,f):
        if self.ended:return False,'ENDED'
        if type(f) is not dict or f.get('roundId')!=self.round_id or f.get('teamId')!=self.team_id:return False,'WRONG_ROUND_TEAM'
        if f.get('isCurrentDriver') is not True or f.get('alive') is not True or f.get('carrier') is True or f.get('mounted') is not True or f.get('isTrapped') is True:return False,'DRIVER_AUTH'
        seq=f.get('sequence')
        if not finite_number(seq) or seq!=int(seq) or seq<=self.last_command:return False,'REPLAY'
        if self.moving:return False,'ALREADY_MOVING'
        if self.leg>=len(self.route['nodes'])-1:return False,'ROUTE_END'
        self.last_command=seq
        self.moving=True
        return True,'OK'
    def step(self,dt,f):
        if self.ended:return 'ENDED'
        if not finite_number(dt) or not 0<=dt<=0.1:
            self.moving=False
            return 'BAD_DT_STOP'
        if type(f) is not dict or f.get('roundId')!=self.round_id or f.get('teamId')!=self.team_id or f.get('active') is not True or f.get('driverStillValid') is not True or f.get('alive') is not True or f.get('mounted') is not True or f.get('carrier') is True or f.get('isTrapped') is True:
            self.moving=False
            return 'AUTH_STOP'
        if not self.moving:return 'STOPPED'
        a,b=self.route['nodes'][self.leg:self.leg+2]
        length=distance(a,b)
        self.progress=min(1.,self.progress+dt*self.route['speed']/length)
        self.position={k:a[k]+(b[k]-a[k])*self.progress for k in ('x','y','z')}
        if self.progress>=1.-1e-9:
            self.position=dict(b)
            self.leg+=1;self.progress=0;self.moving=False
            return 'LEG_COMPLETE'
        return 'MOVING'
    def stop(self):self.moving=False
    def end(self):self.moving=False;self.ended=True
