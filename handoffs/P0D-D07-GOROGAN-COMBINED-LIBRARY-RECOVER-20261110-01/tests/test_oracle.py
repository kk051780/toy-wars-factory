import unittest
import random
from tests.reference import Round

class TestStart(unittest.TestCase):
    def test_s1(self): self.assertEqual(Round('r').start(),'STARTED')
    def test_s3(self): self.assertEqual(Round('r',stage='S3').start(),'STARTED')
    def test_s2(self): self.assertEqual(Round('r',stage='S2').start(),'NOT_CANONICAL')
    def test_s4(self): self.assertEqual(Round('r',stage='S4').start(),'NOT_CANONICAL')
    def test_not_canonical(self): self.assertEqual(Round('r',canonical=False).start(),'NOT_CANONICAL')
    def test_dead_round(self): self.assertEqual(Round('r',round_live=False).start(),'NOT_CANONICAL')
    def test_client_owner(self): self.assertEqual(Round('r',owner='CLIENT').start(),'UNSAFE_SERVER')
    def test_low_ttl(self): self.assertEqual(Round('r',deadline=101).start(),'UNSAFE_SERVER')
    def test_long_ttl_caps_14(self):
        r=Round('r',deadline=200);r.start();self.assertEqual(r.expiry,114)
    def test_replayed_start(self):
        r=Round('r');self.assertEqual(r.start(),'STARTED');self.assertEqual(r.start(),'REPLAY_OR_ACTIVE')
    def test_replayed_start_after_stop(self):
        r=Round('r');r.start();r.stop();self.assertEqual(r.start(),'REPLAY_OR_ACTIVE')
    def test_bad_origin(self): self.assertEqual(Round('r').start(origin=(9000,0,0)),'BAD_ORIGIN')
    def test_bad_event(self):
        for k,v in [('event','WARNING'),('kind','WEATHER'),('subtype','LIGARDO'),('matchId','r2')]:
            c={'event':'ACTIVATE','kind':'BOSS','subtype':'GOROGAN','matchId':'r'};c[k]=v
            with self.subTest(field=k):self.assertEqual(Round('r').start(claim=c),'UNSAFE_EVENT')

class TestMovement(unittest.TestCase):
    def test_bounded_nav(self):
        r=Round('r');r.start();self.assertEqual(r.tick(101,'MOVE',distance=8,target='A'),'MOVED')
    def test_nav_beyond_intent(self):
        r=Round('r');r.start();self.assertEqual(r.tick(101,'MOVE',distance=8.2),'NAV_REJECTED')
    def test_stale_path(self):
        r=Round('r');r.start();self.assertEqual(r.tick(101,'MOVE',path_yield_round='other'),'STALE_AFTER_YIELD');self.assertFalse(r.active)
    def test_client_nav(self):
        r=Round('r');r.start();r.owner='CLIENT';self.assertEqual(r.tick(101,'MOVE',distance=1),'NAV_REJECTED')
    def test_expiry(self):
        r=Round('r');r.start();self.assertEqual(r.tick(114,'MOVE'),'CLOSED');self.assertFalse(r.active)
    def test_late_ended(self):
        r=Round('r');r.start();self.assertEqual(r.tick(101,'END'),'CLOSED');self.assertEqual(r.tick(102,'MOVE'),'INACTIVE')
    def test_clock_regression(self):
        r=Round('r');r.start();self.assertEqual(r.tick(99,'MOVE'),'CLOSED')
    def test_round_loss(self):
        r=Round('r');r.start();r.round_live=False;self.assertEqual(r.tick(102,'MOVE'),'CLOSED')
    def test_reentrant(self):
        r=Round('r');r.start();r.reentrant=True;self.assertEqual(r.tick(101,'MOVE'),'REENTRANT')

class TestStomp(unittest.TestCase):
    def setUp(self): self.r=Round('r');self.r.start()
    def test_warn(self):
        self.assertEqual(self.r.tick(101,'STOMP_WARNING'),'WARNED');self.assertEqual(self.r.visual[-1][-1],'STOMP')
    def test_real_damage(self):
        self.assertEqual(self.r.tick(101,'STOMP_RESOLVE',authorized=True,attack=1,player='A'),'RESOLVED')
        self.assertEqual(self.r.damage,[(1,'A',8)])
    def test_fake_receipt(self):
        self.assertEqual(self.r.tick(101,'STOMP_RESOLVE',authorized=False,attack=1,player='A'),'UNATTESTED');self.assertEqual(self.r.damage,[])
    def test_attack_limit(self):
        self.assertEqual(self.r.tick(101,'STOMP_RESOLVE',authorized=True,attack=4,player='A'),'UNATTESTED')
    def test_behind_wall(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True,player='A',wall=True);self.assertEqual(self.r.damage,[])
    def test_safe_zone(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True,player='A',in_safe=True);self.assertEqual(self.r.damage,[])
    def test_dead_target(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True,player='A',dead=True);self.assertEqual(self.r.damage,[])
    def test_far_target(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True,player='A',distance=7.1);self.assertEqual(self.r.damage,[])
    def test_no_target(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True);self.assertEqual(self.r.damage,[])
    def test_window_always_closed(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True,player='A');self.assertIsNone(self.r.damage_receipt)
    def test_window_closed_on_error(self):
        self.r.callback_errors.add('damage');self.assertEqual(self.r.tick(101,'STOMP_RESOLVE',authorized=True,player='A'),'FAIL_CLOSED');self.assertIsNone(self.r.damage_receipt)
    def test_no_dmg_after_end(self):
        self.r.stop();self.assertEqual(self.r.tick(102,'STOMP_RESOLVE',authorized=True,player='B'),'INACTIVE')
    def test_different_attacks_same_player(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True,attack=1,player='A');self.r.tick(102,'STOMP_RESOLVE',authorized=True,attack=2,player='A');self.assertEqual(len(self.r.damage),2)
    def test_warning_never_damages(self):
        self.r.tick(101,'STOMP_WARNING');self.assertEqual(self.r.damage,[])
    def test_invalid_event_closes(self):
        self.assertEqual(self.r.tick(101,'INVENTED'),'INVALID_COMMAND');self.assertFalse(self.r.active)
    def test_visual_seq(self):
        self.r.tick(101,'STOMP_WARNING');self.r.stop();self.assertEqual([x[3] for x in self.r.visual],[1,2,3])
    def test_no_double_end(self):
        self.r.stop();self.r.stop();self.assertEqual([x[4] for x in self.r.visual].count('END'),1)
    def test_no_receipt_after_stop(self):
        self.r.tick(101,'STOMP_RESOLVE',authorized=True,player='A');self.r.stop();self.assertIsNone(self.r.damage_receipt)
    def test_random_1000_round_actions(self):
        rg=random.Random(7019)
        for i in range(60):
            r=Round('r'+str(i),stage=rg.choice(['S1','S3']));self.assertEqual(r.start(),'STARTED')
            t=100
            for _ in range(20):
                t+=rg.random()*.25
                kind=rg.choice(['MOVE','STOMP_WARNING','STOMP_RESOLVE'])
                r.tick(t,kind,authorized=(kind=='STOMP_RESOLVE'),attack=rg.randint(1,3),player='p'+str(rg.randint(1,4)),distance=rg.random()*10)
                self.assertIsNone(r.damage_receipt)
                self.assertLessEqual(len(r.damage),12)
                if not r.active:break
            r.stop();self.assertFalse(r.active)

if __name__=='__main__':unittest.main()
