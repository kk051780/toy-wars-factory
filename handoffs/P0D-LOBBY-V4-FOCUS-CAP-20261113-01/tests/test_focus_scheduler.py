"""Python executable reference/oracle tests, NOT native Luau execution."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import re
import pytest

SKILLS = ('BEAST', 'MAGIC', 'WEAPON', 'ZOMBIE', 'VEHICLE', 'BUILDING')
JST = 9*3600
DAY = 86400
CAP = 1800
SLOT = 600
MAX_TICK = 120
MOD = 2147483647
SRC = (Path(__file__).parent.parent/'src/FocusTrainingScheduler.luau').read_text()


def day(now): return (now+JST)//DAY

def shuffle(user, cyc):
    seed = (((user % 100_000_000)+1)*16807 + (cyc % 1_000_000)*101390)%MOD
    if not seed: seed=1
    bag = list(SKILLS)
    for i in range(len(bag),1,-1):
        seed=(seed*48271)%MOD
        j=seed%i
        bag[i-1],bag[j]=bag[j],bag[i-1]
    if cyc > 0:
        old=shuffle_base(user,cyc-1)
        if bag[0]==old[5]: bag[0],bag[1]=bag[1],bag[0]
    return bag

def shuffle_base(user,cyc):
    seed=(((user % 100_000_000)+1)*16807+(cyc % 1_000_000)*101390)%MOD
    if not seed: seed=1
    bag=list(SKILLS)
    for i in range(6,1,-1):
        seed=(seed*48271)%MOD
        j=seed%i
        bag[i-1],bag[j]=bag[j],bag[i-1]
    return bag

@dataclass
class State:
    user: int = 42
    day_index: int = 0
    used: int = 0
    focus: str|None = None
    cycle: int = 0
    pos: int = 0
    remaining: int = 600
    tick: int = 0


def init(now, focus=None, used=0, day_index=None):
    return State(day_index=day(now) if day_index is None else day_index,
                 used=used if day_index is None or day_index==day(now) else 0,
                 focus=focus,tick=now)

def settle(s, now, active=True, friends=0, premium=False):
    if now <= s.tick: return []
    st=max(s.tick,now-MAX_TICK)
    s.tick=now
    segments=[]
    if not active:
        if s.day_index!=day(now): s.day_index=day(now);s.used=0
        return segments
    friends=max(0,min(4,friends)); bps=10000+friends*2500
    while st<now:
        if s.day_index!=day(st): s.day_index=day(st);s.used=0
        available=min(now-st, (day(st)+1)*DAY-JST-st)
        focused=s.focus is not None and (premium or s.used<CAP)
        if focused:
            dt=available if premium else min(available,CAP-s.used)
            segments.append((s.focus,dt,bps,'FOCUS'))
            if not premium: s.used+=dt
        else:
            dt=min(available,s.remaining)
            segments.append((shuffle(s.user,s.cycle)[s.pos],dt,bps,'RANDOM'))
            s.remaining-=dt
            if s.remaining==0:
                s.pos+=1
                if s.pos==6:s.pos=0;s.cycle+=1
                s.remaining=SLOT
        st+=dt
    if s.day_index!=day(now): s.day_index=day(now);s.used=0
    return segments


def advance(s,n,active=True,friends=0,premium=False):
    xs=[]
    for _ in range(n):
        xs+=settle(s,s.tick+60,active,friends,premium)
    return xs


@pytest.mark.parametrize('friends,bps',[(0,10000),(1,12500),(2,15000),(3,17500),(4,20000),(5,20000),(-1,10000)])
def test_friend_bonus(friends,bps):
    s=init(1000000,'MAGIC'); assert settle(s,1000060,True,friends)[0][2]==bps


@pytest.mark.parametrize('skill',SKILLS)
def test_focus_select_each_skill(skill):
    s=init(1000000,skill); got=settle(s,1000060)
    assert got==[(skill,60,10000,'FOCUS')]

def test_after_30_min_focus_random_continues():
    s=init(1000000,'BEAST'); x=advance(s,31)
    assert sum(z[1] for z in x if z[3]=='FOCUS')==CAP
    assert sum(z[1] for z in x if z[3]=='RANDOM')==60
    assert s.used==CAP

def test_focus_cap_across_session_splitting():
    s=init(1000000,'BEAST');advance(s,29)
    s.focus='WEAPON'; xs=advance(s,2)
    assert xs[0][0]=='WEAPON' and xs[0][1]==60
    assert xs[1][3]=='RANDOM'
    assert sum(z[1] for z in xs)==120

def test_premium_does_not_consume_free_budget():
    s=init(1000000,'WEAPON');x=advance(s,41,premium=True)
    assert sum(z[1] for z in x)==2460
    assert s.used==0

def test_premium_does_not_raise_xp_multiplier():
    a=init(1000000,'BEAST');b=init(1000000,'BEAST')
    assert settle(a,1000060,True,2)[0][2] == settle(b,1000060,True,2,True)[0][2]

def test_no_progress_on_paused_station():
    s=init(1000000,'MAGIC');assert not settle(s,1000060,False)
    assert s.used==0

def test_no_double_award_same_timestamp():
    s=init(1000000,'MAGIC');settle(s,1000060)
    assert not settle(s,1000060)
    assert s.used==60

def test_rollback_clock_fails_closed():
    s=init(1000000,'MAGIC');assert not settle(s,999999)
    assert s.used==0 and s.tick==1000000

def test_tick_long_delay_no_backpay():
    s=init(1000000,'WEAPON');x=settle(s,1000500)
    assert sum(z[1] for z in x)==MAX_TICK
    assert s.tick==1000500

def test_day_just_before_reset_split():
    midnight=(day(1000000)+1)*DAY-JST
    s=init(midnight-30,'MAGIC');s.used=CAP-15
    segments=settle(s,midnight+30)
    assert sum(z[1] for z in segments)==60
    assert segments[0][1]==15 and segments[0][3]=='FOCUS'
    assert segments[1][1]==15 and segments[1][3]=='RANDOM'
    assert segments[2][1]==30 and segments[2][3]=='FOCUS'
    assert s.used==30 and s.day_index==day(midnight+30)

def test_day_reset_without_training():
    midnight=(day(1000000)+1)*DAY-JST
    s=init(midnight-10,'BEAST');s.used=CAP
    assert settle(s,midnight+10,False)==[]
    assert s.used==0

def test_rejoin_resets_unlimited_offline_elapsed():
    stored={'dayIndex':day(1000000),'focusedSeconds':700}
    s=init(1000000+12*3600,'WEAPON',stored['focusedSeconds'],stored['dayIndex'])
    assert s.tick==1000000+12*3600
    assert settle(s,s.tick)==[]

def test_shuffle_each_six_unique():
    for user in (1,42,999999999):
        for cyc in range(5):assert set(shuffle(user,cyc))==set(SKILLS)

def test_shuffle_boundary_no_repeat():
    for user in (1,42,999999999):
        for cyc in range(1,25):assert shuffle(user,cyc)[0]!=shuffle(user,cyc-1)[-1]

def test_random_timing_crosses_ten_minutes():
    s=init(1000000)
    x=advance(s,11)
    assert sum(z[1] for z in x)==660
    assert len(set(z[0] for z in x))==2
    assert s.pos==1 and s.remaining==540

def test_random_no_reset_when_reenter():
    s=init(1000000)
    advance(s,2); assert s.remaining==480
    advance(s,1,active=False);assert s.remaining==480
    advance(s,1); assert s.remaining==420

def test_user_skill_can_change_pre_limit():
    s=init(1000000,'BEAST');advance(s,5)
    s.focus='MAGIC';x=advance(s,1)
    assert x[0][0]=='MAGIC' and s.used==360

def test_at_limit_changing_choice_does_not_bypass():
    s=init(1000000,'BEAST');s.used=CAP;s.focus='MAGIC'
    assert settle(s,1000060)[0][3]=='RANDOM'

def test_source_module_no_datastore_write_or_purchases():
    for dangerous in ('UpdateAsync(', 'SetAsync(', 'ProcessReceipt', 'PromptProductPurchase', 'RemoteEvent', 'MarketplaceService', 'DataStoreService'):
        assert dangerous not in SRC

def test_source_contract_exports_present():
    for name in ('newState','selectSkill','clearSelection','getStatus','settle','snapshot'):
        assert re.search(r'function Scheduler\.'+name+r'\(', SRC)
    assert 'FREE_FOCUS_SECONDS = 30 * 60' in SRC
    assert 'RANDOM_SLOT_SECONDS = 10 * 60' in SRC
    assert 'MAX_SETTLE_SECONDS = 120' in SRC
    assert 'JST_OFFSET = 9 * 3600' in SRC

def test_source_has_no_runservice_or_renderstep_idle_bypass():
    for dangerous in ('VirtualUser', 'RenderStepped', 'RunService', 'Humanoid:Move', 'UserInputService'):
        assert dangerous not in SRC

def test_source_static_skills_are_exactly_six():
    line=[x for x in SRC.splitlines() if 'Scheduler.DISCIPLINES = ' in x][0]
    assert all('"'+x+'"' in line for x in SKILLS)

if __name__=='__main__':
    import pytest
    raise SystemExit(pytest.main([__file__,'-q']))
