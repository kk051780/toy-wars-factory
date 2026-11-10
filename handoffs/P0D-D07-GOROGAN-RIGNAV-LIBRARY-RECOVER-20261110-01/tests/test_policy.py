import unittest
from random import Random
from tests.reference import RigPolicy,DamagePolicy,safe_id,valid_time,is_xyz

class TestRig(unittest.TestCase):
    def setUp(self):
        self.r=RigPolicy()
        self.assertTrue(self.r.start("r1","event1","S1",0))
    def test_start_authority(self):
        for bad in (("r2","e2","S2",0,True,True),("r2","e2","S1",0,False,True),("r2","e2","S1",0,True,False)):
            p=RigPolicy();self.assertFalse(p.start(*bad))
    def test_round_replay(self):
        self.assertFalse(self.r.start("r1","event1","S1",1))
        self.assertTrue(self.r.stop("r1","event1"))
        self.assertFalse(self.r.start("r1","event2","S3",5))
    def test_stale_stop(self):
        self.assertFalse(self.r.stop("r2","event1"));self.assertTrue(self.r.active)
    def test_nav_rate(self):
        self.assertTrue(self.r.request(0,(2,2,0),(0,2,0))[0])
        self.assertEqual(self.r.request(.74,(2,2,0),(0,2,0))[1],"RATE_OR_BUDGET")
        self.assertTrue(self.r.request(.75,(2,2,0),(0,2,0))[0])
    def test_nav_budget(self):
        for k in range(19):self.assertTrue(self.r.request(k*.75,(2,2,0),(0,2,0))[0])
        self.r.count=20;self.r.last_nav=0
        self.assertEqual(self.r.request(2.0,(2,2,0),(0,2,0))[1],"RATE_OR_BUDGET")
    def test_lifetime(self):
        self.assertFalse(self.r.request(14,(2,2,0),(0,2,0))[0])
    def test_path_blocked_fail_closed(self):
        self.assertFalse(self.r.request(0,(2,2,0),(0,2,0),path=False)[0])
        self.assertFalse(self.r.request(.75,(2,2,0),(0,2,0),num_waypoints=17)[0])
    def test_after_yield(self):
        self.assertEqual(self.r.request(0,(2,2,0),(0,2,0),after_yield_ok=False)[1],"STALE_AFTER_YIELD")
    def test_chase_limit(self):
        self.assertFalse(self.r.request(0,(8.11,0,0),(0,0,0))[0])
        self.assertTrue(self.r.request(0,(45,0,0),(0,0,0),reason="LEASH_RETURN")[0])
    def test_unknown_reason(self):
        self.assertFalse(self.r.request(0,(1,0,0),(0,0,0),reason="Teleport")[0])
    def test_terrain(self):
        self.assertFalse(self.r.request(0,(1,0,0),(0,0,0),terrain=False)[0])
    def test_busy(self):
        self.r.busy=True;self.assertEqual(self.r.request(0,(2,2,0),(0,2,0))[1],"INACTIVE_OR_BUSY")
    def test_rollback(self):
        self.r.request(1,(1,0,0),(0,0,0));self.assertFalse(self.r.request(.9,(1,0,0),(0,0,0))[0])
    def test_epoch(self):
        self.assertFalse(self.r.request(0,(1,0,0),(0,0,0),epoch_ok=False)[0])
    def test_randomized_no_over_budget(self):
        rng=Random(17321)
        t=0
        for _ in range(2000):
            t+=rng.uniform(0,.03)
            self.r.request(t,(rng.uniform(-2,2),0,1),(0,0,0),path=rng.choice([True,False]))
            self.assertLessEqual(self.r.count,20)
            self.assertGreaterEqual(self.r.last_nav,-float('inf'))
    def test_round_limit(self):
        p=RigPolicy()
        for i in range(128):
            self.assertTrue(p.start('r'+str(i),'e'+str(i),'S1',i))
            self.assertTrue(p.stop('r'+str(i),'e'+str(i)))
        self.assertFalse(p.start('new','e','S1',130))

class TestDamage(unittest.TestCase):
    def setUp(self):
        self.g=DamagePolicy();self.assertTrue(self.g.start('r1','e1'))
    def hit(self,p='p1',attack=1,**kw):
        return self.g.resolve(p,8,attack,'r1','e1',**kw)
    def test_success(self):
        self.assertEqual(self.hit(),(True,"APPLIED"))
    def test_duplicate(self):
        self.hit();self.assertEqual(self.hit()[1],"DUPLICATE")
    def test_team_neutrality(self):
        self.assertTrue(self.hit('blue')[0]);self.assertTrue(self.hit('red')[0])
    def test_multiple_attacks(self):
        for a in (1,2,3):self.assertTrue(self.hit('p1',a)[0])
    def test_unauthenticated_attack(self):
        self.assertFalse(self.hit(canonical=False)[0])
    def test_inactive_round(self):
        self.assertFalse(self.hit(live=False)[0])
    def test_dead(self):
        self.assertFalse(self.hit(alive=False)[0])
    def test_safezone(self):
        self.assertFalse(self.hit(safe=True)[0])
    def test_immune(self):
        self.assertFalse(self.hit(immune=True)[0])
    def test_los(self):
        self.assertFalse(self.hit(los=False)[0])
    def test_distance(self):
        self.assertFalse(self.hit(in_range=False)[0])
    def test_fake_player(self):
        self.assertFalse(self.hit(valid_player=False)[0])
    def test_wrong_round(self):
        self.assertFalse(self.g.resolve('p',8,1,'rOLD','e1')[0])
    def test_wrong_event(self):
        self.assertFalse(self.g.resolve('p',8,1,'r1','eOLD')[0])
    def test_invalid_id(self):
        for s in ('','a/b','a'*65,'💥'):
            self.assertFalse(self.g.resolve(s,8,1,'r1','e1')[0])
    def test_invalid_damage(self):
        for damage in (0,9,float('nan'),float('inf'),-1,True):
            self.assertFalse(self.g.resolve('p',damage,1,'r1','e1')[0])
    def test_invalid_attack(self):
        for a in (0,4,1.25,False):
            self.assertFalse(self.g.resolve('p',8,a,'r1','e1')[0])
    def test_stop_clears(self):
        self.g.stop('r1','e1');self.assertFalse(self.hit()[0]);self.assertFalse(self.g.start('r1','eNEW'))
    def test_stale_stop(self):
        self.assertFalse(self.g.stop('r2','e1'));self.assertTrue(self.g.active)
    def test_budget(self):
        for i in range(72):self.assertTrue(self.hit(f'p{i}',1)[0])
        self.assertFalse(self.hit('p72',1)[0])
    def test_failed_attempt_not_consume(self):
        self.assertFalse(self.hit(los=False)[0]);self.assertTrue(self.hit()[0])
    def test_random_attack_receipts(self):
        rng=Random(321)
        for _ in range(1000):
            a=rng.randint(1,3);p='p'+str(rng.randrange(28))
            self.hit(p,a,canonical=rng.random()>.2,los=rng.random()>.3)
            self.assertLessEqual(self.g.total,72)
            self.assertEqual(self.g.total,len(self.g.receipts))
    def test_refuse_replay_after_stop(self):
        self.g.stop('r1','e1');self.assertFalse(self.g.start('r1','e1'))
    def test_max_rounds(self):
        g=DamagePolicy()
        for i in range(128):
            self.assertTrue(g.start(f'r{i}',f'e{i}'));self.assertTrue(g.stop(f'r{i}',f'e{i}'))
        self.assertFalse(g.start('one_more','e'))

class TestPurePredicates(unittest.TestCase):
    def test_identifiers(self):
        for x in ['a','r_1-0','A_22']:self.assertTrue(safe_id(x))
        for x in ['a b','','1/3','🔥','x'*65,0,None]:self.assertFalse(safe_id(x))
    def test_times(self):
        for x in [0,1,3.2,1e12]:self.assertTrue(valid_time(x))
        for x in [float('nan'),float('inf'),-1,1e13,True,'1']:self.assertFalse(valid_time(x))
    def test_positions(self):
        self.assertTrue(is_xyz((1,2,3)))
        for x in [(9999,0,0),(0,float('nan'),0),(1,2),{},[1,2,True]]:self.assertFalse(is_xyz(x))

if __name__ == '__main__':unittest.main()
