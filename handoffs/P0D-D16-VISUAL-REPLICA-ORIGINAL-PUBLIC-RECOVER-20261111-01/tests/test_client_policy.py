import copy
import math
import random
import unittest
from reference.client_policy import Policy

GIANT = dict(matchId='round-A',eventId='event-1',status='ACTIVE',kind='GIANT_ONE',targets=['101'],scaleMilli=1600,remainingSeconds=8)
MINI = dict(GIANT,kind='MINI_ALL',targets=['101','102','103'],scaleMilli=700)

class PolicyTests(unittest.TestCase):
    def setUp(self): self.p=Policy('round-A')
    def accept(self, packet=GIANT, now=50):return self.p.accept(copy.deepcopy(packet),'round-A',now)
    def test_happy_giant(self):
        self.assertEqual(self.accept(),(True,'DISPLAY_ONLY'))
        self.assertEqual(self.p.deadline,58)
        self.assertEqual(self.p.targets,['101'])
    def test_happy_mini(self):
        self.assertTrue(self.accept(MINI)[0]); self.assertEqual(len(self.p.targets),3)
    def test_round_validation(self):
        for value in ('',None,'a / b','a'*97,4,True):
            with self.subTest(value=value),self.assertRaises(ValueError):Policy(value)
    def test_reject_bad_packet_types(self):
        for data in (None,[],0,'hello',True):
            with self.subTest(data=data):self.assertFalse(self.accept(data)[0])
    def test_stale_round(self):
        for invalid in ('round-B',None,0,''):
            with self.subTest(invalid=invalid): self.assertFalse(self.p.accept(GIANT,invalid,50)[0])
    def test_bad_event_id(self):
        for id in ('','evil\nremote','a'*97,123,None):
            data=dict(GIANT,eventId=id)
            with self.subTest(id=id): self.assertFalse(self.accept(data)[0])
    def test_invalid_kind(self):
        for value in (None,'BIG','MINI','NORMAL','NORMAL_EVENT',12):
            with self.subTest(value=value): self.assertFalse(self.accept(dict(GIANT,kind=value))[0])
    def test_bad_ratio(self):
        for value in (1000,700,None,'1600',float('nan'),1600.1,True):
            with self.subTest(value=value): self.assertFalse(self.accept(dict(GIANT,scaleMilli=value))[0])
    def test_bad_times(self):
        for value in (float('nan'),float('inf'),-1,'10',None,True):
            with self.subTest(value=value): self.assertFalse(self.accept(GIANT,now=value)[0])
    def test_bad_ttl(self):
        for value in (None,0,-1,9,1e100,float('nan'),float('inf'),'8',True):
            with self.subTest(value=value): self.assertFalse(self.accept(dict(GIANT,remainingSeconds=value))[0])
    def test_zero_target(self):self.assertFalse(self.accept(dict(GIANT,targets=[]))[0])
    def test_large_target_list(self):self.assertFalse(self.accept(dict(MINI,targets=[str(i) for i in range(17)]))[0])
    def test_duplicate_target(self):self.assertFalse(self.accept(dict(MINI,targets=['101','101']))[0])
    def test_bad_target_id(self):
        for id in ('a!','a'*97,'',10,None):
            with self.subTest(id=id): self.assertFalse(self.accept(dict(GIANT,targets=[id]))[0])
    def test_giant_many_targets(self):self.assertFalse(self.accept(dict(GIANT,targets=['101','102']))[0])
    def test_deterministic_roster_sort(self):
        self.assertTrue(self.accept(dict(MINI,targets=['103','101','102']))[0]);self.assertEqual(self.p.targets,['101','102','103'])
    def test_second_event_block(self):
        self.assertTrue(self.accept()[0]); self.assertEqual(self.accept(dict(GIANT,eventId='event-2')),(False,'SECOND_EVENT_REJECTED'))
    def test_type_change_block(self):
        self.assertTrue(self.accept()[0]); self.assertEqual(self.accept(dict(MINI,targets=['101']),51),(False,'KIND_CHANGED'))
    def test_duplicate_never_extends_deadline(self):
        self.assertTrue(self.accept()[0]);self.assertTrue(self.accept(dict(GIANT,remainingSeconds=8),51)[0]);self.assertEqual(self.p.deadline,58)
    def test_packet_shortens_deadline(self):
        self.assertTrue(self.accept()[0]);self.assertTrue(self.accept(dict(GIANT,remainingSeconds=1),51)[0]);self.assertEqual(self.p.deadline,52)
    def test_active_target_reduction(self):
        self.assertTrue(self.accept(MINI)[0]);self.assertTrue(self.accept(dict(MINI,targets=['101','102']),51)[0]);self.assertEqual(self.p.targets,['101','102'])
    def test_reject_added_targets(self):
        self.assertTrue(self.accept(dict(MINI,targets=['101','102']))[0]);self.assertEqual(self.accept(MINI,51),(False,'TARGET_ADDED_AFTER_START'))
    def test_reject_repeated_end(self):
        self.assertTrue(self.accept()[0]);end=dict(GIANT,status='EXPIRED',targets=[])
        self.assertEqual(self.accept(end),(True,'CLEARED'))
        self.assertEqual(self.accept(end),(False,'TERMINAL_REPLAY'))
    def test_reject_unknown_end(self):self.assertEqual(self.accept(dict(GIANT,status='CLOSED')),(False,'UNKNOWN_TERMINAL'))
    def test_terminated_does_not_resume(self):
        self.assertTrue(self.accept()[0]);self.assertTrue(self.accept(dict(GIANT,status='CLOSED'))[0]);self.assertFalse(self.accept()[0])
    def test_timeout(self):
        self.assertTrue(self.accept()[0]);self.assertEqual(self.p.tick('round-A',57.99),'ACTIVE')
        self.assertEqual(self.p.tick('round-A',58),'EXPIRED');self.assertEqual(self.p.scale_milli,1000)
    def test_round_change_cleanup(self):
        self.assertTrue(self.accept()[0]);self.assertEqual(self.p.tick('round-B',51),'MATCH_CHANGED')
        self.assertEqual(self.p.targets,[])
    def test_nondeterministic_input_fuzzer(self):
        rng=random.Random(42)
        for _ in range(300):
            state=Policy('round-A');packet=copy.deepcopy(MINI)
            n=rng.randrange(0,20);packet['targets']=[str(rng.randrange(1000)) for _ in range(n)]
            ttl=rng.choice([1,2,8,0,-1,9,float('nan'),float('inf'),None,'1'])
            packet['remainingSeconds']=ttl
            result,_=state.accept(packet,'round-A',rng.randrange(10000))
            if result:
                self.assertTrue(1<=len(state.targets)<=16 and math.isfinite(state.deadline))
                self.assertTrue(0<state.scale_milli<1700)
    def test_not_authority(self):
        self.assertEqual(set(self.p.__dataclass_fields__),{'match_id','event_id','closed','status','kind','targets','scale_milli','deadline'})

if __name__=='__main__': unittest.main()
