import math
import random
import unittest
from pathlib import Path
from reference.raft_water_model import create, bind, step, close

ROOT=Path(__file__).resolve().parents[1]
ALLOW=lambda x,z,stage,raft: True
DENY=lambda x,z,stage,raft: False

def ctx(s,**overrides):
    c=dict(roundId=s.round_id,driverId=s.driver_id,seatEpoch=s.seat_epoch,stage=s.stage,
           alive=True,seated=True,sameTeam=True,eggCarrier=False,snared=False,rewinding=False)
    c.update(overrides)
    return c

def ready(stage=1,x=0,z=0,ms=1000):
    s,ok=create('round-1','raft-1',stage,x,4,z,0,ms)
    assert ok=='OK'
    s,ok=bind(s,'round-1','playerA',1,ms)
    assert ok=='BOUND'
    return s

class StartTests(unittest.TestCase):
    def test_default(self):
        s,status=create('r','v',1,0,2,0,0,0)
        self.assertEqual(status,'OK');self.assertFalse(s.active)
    def test_stages(self):
        for stage in [0,3,4,-1,'1',1.0,None]:
            with self.subTest(stage=stage): self.assertEqual(create('r','v',stage,0,0,0,0,0)[1],'BAD_START')
    def test_reject_id(self):
        for i in ['', 'bad/id','bad id','a'*97,None]:
            with self.subTest(id=i):self.assertEqual(create(i,'v',1,0,0,0,0,0)[1],'BAD_START')
    def test_reject_numeric(self):
        for v in (float('nan'),float('inf'),-float('inf')):
            self.assertEqual(create('r','v',1,v,0,0,0,0)[1],'BAD_START')
            self.assertEqual(create('r','v',1,0,0,0,v,0)[1],'BAD_START')
    def test_bounds(self):
        for x in (-2049,2049):self.assertEqual(create('r','v',1,x,0,0,0,0)[1],'BAD_START')
    def test_angle_wrap(self):
        s,_=create('r','v',1,0,0,0,4,0);self.assertTrue(-math.pi<=s.yaw<math.pi)
    def test_negative_time(self):self.assertEqual(create('r','v',1,0,0,0,0,-1)[1],'BAD_START')

class BindTests(unittest.TestCase):
    def test_bind_driver(self):
        s=ready();self.assertTrue(s.active);self.assertEqual(s.driver_id,'playerA')
    def test_wrong_round(self):
        s=ready();self.assertEqual(bind(s,'wrong','P',2,1000)[1],'DENY_BIND')
    def test_same_epoch(self):
        s=ready();self.assertEqual(bind(s,'round-1','P',1,1001)[1],'DENY_BIND')
    def test_older_epoch(self):
        s=ready();self.assertEqual(bind(s,'round-1','P',0,1001)[1],'DENY_BIND')
    def test_bad_epoch(self):
        s=ready();self.assertEqual(bind(s,'round-1','P',1.2,1001)[1],'DENY_BIND')
    def test_overflow_epoch(self):
        s=ready();self.assertEqual(bind(s,'round-1','P',2147483648,1001)[1],'DENY_BIND')
    def test_time_reverse(self):
        s=ready();self.assertEqual(bind(s,'round-1','P',2,999)[1],'DENY_BIND')
    def test_bad_driver(self):
        s=ready();self.assertEqual(bind(s,'round-1','a/b',2,1001)[1],'DENY_DRIVER')
    def test_unbind(self):
        s=ready();n,code=bind(s,'round-1',None,2,1050)
        self.assertEqual(code,'BOUND');self.assertFalse(n.active)
    def test_switch_resets_speed(self):
        s=ready();s,code=step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),ALLOW)
        self.assertGreater(s.speed,0)
        n,code=bind(s,'round-1','playerB',2,1300)
        self.assertEqual((n.speed,n.seq,n.driver_id),(0,0,'playerB'))

class MovementTests(unittest.TestCase):
    def test_move(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),ALLOW)
        self.assertEqual(code,'MOVE_OK');self.assertGreater(n.z,s.z)
    def test_turn_right(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,1,1200,ctx(s),ALLOW)
        self.assertEqual(code,'MOVE_OK');self.assertGreater(n.x,s.x)
    def test_turn_left(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,-1,1200,ctx(s),ALLOW)
        self.assertLess(n.x,s.x)
    def test_reverse_limited(self):
        s=ready();t=1000
        for i in range(1,30):
            t+=200;s,code=step(s,'round-1','playerA',1,i,-1,0,t,ctx(s),ALLOW)
            self.assertEqual(code,'MOVE_OK')
        self.assertAlmostEqual(s.speed,-3)
    def test_forward_limited(self):
        s=ready();t=1000
        for i in range(1,30):
            t+=200;s,code=step(s,'round-1','playerA',1,i,1,0,t,ctx(s),ALLOW)
            self.assertEqual(code,'MOVE_OK')
        self.assertLessEqual(s.speed,8)
    def test_acceleration_limited(self):
        s=ready();n,_=step(s,'round-1','playerA',1,1,1,0,1100,ctx(s),ALLOW)
        self.assertAlmostEqual(n.speed,1.2)
    def test_dt_limit(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,0,1201,ctx(s),ALLOW)
        self.assertEqual(code,'DENY_INPUT');self.assertEqual(n,s)
    def test_time_reverse(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,999,ctx(s),ALLOW)[1],'DENY_INPUT')
    def test_duplicate_seq(self):
        s=ready();s,code=step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),ALLOW)
        self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1300,ctx(s),ALLOW)[1],'DENY_INPUT')
    def test_old_seq(self):
        s=ready();s,_=step(s,'round-1','playerA',1,10,1,0,1200,ctx(s),ALLOW)
        self.assertEqual(step(s,'round-1','playerA',1,9,1,0,1400,ctx(s),ALLOW)[1],'DENY_INPUT')
    def test_overflow_seq(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,2**31,1,0,1200,ctx(s),ALLOW)[1],'DENY_INPUT')
    def test_wrong_driver(self):
        s=ready();self.assertEqual(step(s,'round-1','hacker',1,1,1,0,1200,ctx(s),ALLOW)[1],'DENY_AUTH')
    def test_wrong_epoch(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',2,1,1,0,1200,ctx(s),ALLOW)[1],'DENY_AUTH')
    def test_wrong_round(self):
        s=ready();self.assertEqual(step(s,'other','playerA',1,1,1,0,1200,ctx(s),ALLOW)[1],'DENY_AUTH')
    def test_unbound(self):
        s,_=create('r','v',1,0,0,0,0,1000)
        self.assertEqual(step(s,'r','x',0,1,1,0,1200,ctx(s),ALLOW)[1],'DENY_AUTH')
    def test_bad_throttle(self):
        s=ready()
        for v in [1.01,-1.01,float('nan'),float('inf'),None,'1']:
            self.assertEqual(step(s,'round-1','playerA',1,1,v,0,1200,ctx(s),ALLOW)[1],'DENY_INPUT')
    def test_bad_steer(self):
        s=ready()
        for v in [1.01,-1.01,float('nan'),float('inf'),None,'1']:
            self.assertEqual(step(s,'round-1','playerA',1,1,0,v,1200,ctx(s),ALLOW)[1],'DENY_INPUT')
    def test_zero_dt(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,0,1000,ctx(s),ALLOW)
        self.assertEqual(code,'MOVE_OK');self.assertEqual((n.x,n.z),(s.x,s.z))
    def test_surface_calls(self):
        s=ready();calls=[]
        def water(x,z,stage,raft):calls.append((x,z,stage,raft));return True
        n,code=step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),water)
        self.assertEqual(code,'MOVE_OK');self.assertEqual(len(calls),2)
        self.assertLess(calls[0][1],calls[1][1])
    def test_land_block(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),DENY)
        self.assertEqual(code,'BLOCK_WATER');self.assertEqual(n.z,s.z);self.assertEqual(n.speed,0)
    def test_partial_water_block(self):
        s=ready();count=[0]
        def water(*args):count[0]+=1;return count[0]==1
        n,code=step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),water)
        self.assertEqual(code,'BLOCK_WATER')
    def test_water_exception(self):
        s=ready();
        def water(*args):raise RuntimeError('no map')
        self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),water)[1],'BLOCK_WATER')
    def test_nonboolean_water(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),lambda *x: 1)[1],'BLOCK_WATER')
    def test_out_bounds(self):
        s=ready(x=0,z=2048);n,code=step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),ALLOW)
        self.assertEqual(code,'BLOCK_BOUNDS');self.assertEqual(n.speed,0)
    def test_no_teleport_even_large_input(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,1,1200,ctx(s),ALLOW)
        self.assertLess(math.hypot(n.x-s.x,n.z-s.z),1.7)
    def test_snapshot_unchanged_on_reject(self):
        s=ready();n,code=step(s,'round-1','playerA',1,1,1,0,1200,{},ALLOW)
        self.assertEqual(n,s)
    def test_restrict_egg(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,eggCarrier=True),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_restrict_snare(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,snared=True),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_restrict_rewind(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,rewinding=True),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_restrict_dead(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,alive=False),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_restrict_unseated(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,seated=False),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_restrict_enemy(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,sameTeam=False),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_restrict_unauth_round_snapshot(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,roundId='fake'),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_restrict_unauth_epoch_snapshot(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s,seatEpoch=0),ALLOW)[1],'DENY_SERVER_FACTS')
    def test_missing_water(self):
        s=ready();self.assertEqual(step(s,'round-1','playerA',1,1,1,0,1200,ctx(s),None)[1],'DENY_SERVER_FACTS')
    def test_close(self):
        s=ready();n,code=close(s,'round-1')
        self.assertEqual(code,'CLOSED');self.assertFalse(n.active)
        self.assertEqual(step(n,'round-1','playerA',1,1,1,0,1200,ctx(n),ALLOW)[1],'DENY_AUTH')
    def test_close_wrong_round(self):
        s=ready();self.assertEqual(close(s,'other')[1],'DENY_ROUND')
    def test_bind_after_close(self):
        s=ready();s,_=close(s,'round-1');self.assertEqual(bind(s,'round-1','new',2,1200)[1],'DENY_BIND')
    def test_seeded_long_random(self):
        rng=random.Random(20261110);s=ready();now=1000
        for i in range(1,3001):
            now+=rng.randrange(0,201)
            throttle=rng.uniform(-1,1);steer=rng.uniform(-1,1)
            old=s;s,code=step(s,'round-1','playerA',1,i,throttle,steer,now,ctx(s),lambda x,z,stage,r: abs(x)<=300 and abs(z)<=300)
            self.assertIn(code,('MOVE_OK','BLOCK_WATER','BLOCK_BOUNDS'))
            self.assertTrue(-2048<=s.x<=2048 and -2048<=s.z<=2048)
            self.assertTrue(-3-1e-7<=s.speed<=8+1e-7)
            self.assertLessEqual(math.hypot(s.x-old.x,s.z-old.z),1.7)
            self.assertEqual(s.seq,i)
    def test_seeded_fake_frames_no_mutation(self):
        rng=random.Random(24);s=ready()
        for j in range(1000):
            v=rng.choice(['wrong-round','bad-owner','bad-seat','bad-ctx','bad-input'])
            kw={'round_id':'round-1','driver_id':'playerA','epoch':1,'seq':j+1,'throttle':1,'steer':0,'now':1200,'trusted':ctx(s),'water_check':ALLOW}
            if v=='wrong-round':kw['round_id']='stale'
            if v=='bad-owner':kw['driver_id']='B'
            if v=='bad-seat':kw['epoch']=2
            if v=='bad-ctx':kw['trusted']=ctx(s,eggCarrier=True)
            if v=='bad-input':kw['throttle']=10
            n,code=step(s,**kw)
            self.assertTrue(code.startswith('DENY_'));self.assertEqual(n,s)

class StaticLuauTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core=(ROOT/'luau/RaftWaterMotionCore.luau').read_text()
        cls.adapt=(ROOT/'luau/RaftWaterServerAdapter.luau').read_text()
    def test_core_api(self):
        for word in ['function M.new(', 'function M.bindDriver(', 'function M.step(', 'function M.close(', 'function M.snapshot(']:
            self.assertIn(word,self.core)
    def test_no_forbidden_remote(self):
        for x in ('RemoteEvent.new','FireServer','DataStoreService','HttpService','InsertService','TeleportService'):
            self.assertNotIn(x,self.core+self.adapt)
    def test_server_snapshot_must_match(self):
        for field in ['trusted.eggCarrier~=false','trusted.sameTeam~=true','trusted.snared~=false','trusted.rewinding~=false','trusted.seatEpoch~=s.seatEpoch']:
            self.assertIn(field,self.core)
    def test_water_both_segment_checks(self):
        self.assertIn('pcall(waterCheck,mx,mz',self.core)
        self.assertIn('pcall(waterCheck,nx,nz',self.core)
    def test_adapter_disabled_default(self):
        self.assertIn('enabled~=true',self.adapt)
    def test_adapter_uses_server_hooks(self):
        for field in ('hooks.snapshot','hooks.waterCheck','hooks.isAuthorizedDriver','hooks.serverClockMs'):
            self.assertIn(field,self.adapt)
    def test_adapter_no_rider_move(self):
        self.assertIn(':PivotTo(',self.adapt)
        for x in ('HumanoidRootPart','AssemblyLinearVelocity','WeldConstraint.new','Seat.new','BodyVelocity','LinearVelocity'):
            self.assertNotIn(x,self.adapt)
    def test_adapter_model_fail_closed(self):
        for x in ('part.CanCollide','part.Anchored','part:IsA("Seat")','count>32'):
            self.assertIn(x,self.adapt)

if __name__=='__main__': unittest.main()
