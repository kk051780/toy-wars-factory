"""Independent offline oracle for D14 server-bound raft navigation rules; not Roblox physics."""
from __future__ import annotations
from dataclasses import dataclass, replace
from math import isfinite, pi, sin, cos, radians
import re

MAX_SPEED=8.0
MAX_REVERSE=-3.0
MAX_ACCEL=12.0
MAX_TURN=radians(75)
MAX_DT_MS=200
ID_RE=re.compile(r'[A-Za-z0-9_.-]{1,96}\Z')

@dataclass(frozen=True)
class Raft:
    round_id: str
    raft_id: str
    stage: int
    x:float
    y:float
    z:float
    yaw:float
    last_ms:int
    driver_id:str|None=None
    seat_epoch:int=0
    speed:float=0
    seq:int=0
    active:bool=False
    closed:bool=False

def create(round_id,raft_id,stage,x,y,z,yaw,t):
    if (not isinstance(round_id,str) or not ID_RE.fullmatch(round_id) or
        not isinstance(raft_id,str) or not ID_RE.fullmatch(raft_id) or
        type(stage)!=int or stage not in (1,2) or
        any(not isinstance(v,(float,int)) or not isfinite(v) for v in (x,y,z,yaw,t)) or
        max(abs(x),abs(y),abs(z))>2048 or abs(yaw)>8*pi or t<0):
        return None,'BAD_START'
    return Raft(round_id,raft_id,stage,x,y,z,(yaw+pi)%(2*pi)-pi,t),'OK'

def bind(s,round_id,driver_id,epoch,now):
    if (s.closed or round_id!=s.round_id or not isinstance(now,(float,int)) or not isfinite(now)
        or now<s.last_ms or type(epoch)!=int or epoch<=s.seat_epoch or epoch>2147483647):
        return s,'DENY_BIND'
    if driver_id is not None and (not isinstance(driver_id,str) or not ID_RE.fullmatch(driver_id)):
        return s,'DENY_DRIVER'
    return replace(s,driver_id=driver_id,seat_epoch=epoch,speed=0,seq=0,active=driver_id is not None,last_ms=now),'BOUND'

def step(s,round_id,driver_id,epoch,seq,throttle,steer,now,trusted,water_check):
    if (s.closed or not s.active or round_id!=s.round_id or driver_id!=s.driver_id
        or epoch!=s.seat_epoch):
        return s,'DENY_AUTH'
    if (type(seq)!=int or seq<=s.seq or seq>2147483647 or
        not isinstance(now,(float,int)) or not isfinite(now) or now<s.last_ms or now-s.last_ms>MAX_DT_MS or
        any(not isinstance(v,(float,int)) or not isfinite(v) or abs(v)>1 for v in (throttle,steer))):
        return s,'DENY_INPUT'
    if (not isinstance(trusted,dict) or trusted.get('roundId')!=s.round_id or
        trusted.get('driverId')!=s.driver_id or trusted.get('seatEpoch')!=s.seat_epoch or
        trusted.get('stage')!=s.stage or any(trusted.get(k) is not flag for k,flag in
        [('alive',True),('seated',True),('sameTeam',True),('eggCarrier',False),('snared',False),('rewinding',False)]) or
        not callable(water_check)):
        return s,'DENY_SERVER_FACTS'
    dt=(now-s.last_ms)/1000
    desired=throttle*8 if throttle>=0 else throttle*3
    delta=max(-MAX_ACCEL*dt,min(MAX_ACCEL*dt,desired-s.speed))
    speed=max(MAX_REVERSE,min(MAX_SPEED,s.speed+delta))
    yaw=(s.yaw+steer*MAX_TURN*dt+pi)%(2*pi)-pi
    dx,dz=sin(yaw)*speed*dt,cos(yaw)*speed*dt
    if dx*dx+dz*dz>1.7**2+1e-6:return s,'DENY_TRAVEL'
    n=replace(s,last_ms=now,seq=seq,speed=speed,yaw=yaw)
    nx,nz=s.x+dx,s.z+dz
    if any(not isfinite(v) or abs(v)>2048 for v in (nx,nz)):
        return replace(n,speed=0),'BLOCK_BOUNDS'
    try:
        a=water_check(s.x+dx/2,s.z+dz/2,s.stage,s.raft_id)
    except Exception:
        a=False
    try:
        b=water_check(nx,nz,s.stage,s.raft_id)
    except Exception:
        b=False
    if a is not True or b is not True:return replace(n,speed=0),'BLOCK_WATER'
    return replace(n,x=nx,z=nz),'MOVE_OK'

def close(s,round_id):
    if round_id!=s.round_id:return s,'DENY_ROUND'
    return replace(s,closed=True,active=False,driver_id=None,speed=0),'CLOSED'
