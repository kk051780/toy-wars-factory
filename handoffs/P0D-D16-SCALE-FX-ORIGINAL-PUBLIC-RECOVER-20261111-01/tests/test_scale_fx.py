import math
import pathlib
import sys
import unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reference.scale_fx import ScaleFx, valid_id, valid_time, DURATION

class ScaleFxTests(unittest.TestCase):
    def setUp(self):
        self.s=ScaleFx('round1')
    def begin(self, kind='GIANT_ONE', actor='a', roster=None, now=1, eid='evt1', mid='round1'):
        if roster is None: roster=['a','b','c']
        return self.s.begin(mid,eid,kind,actor,roster,now)
    def test_initial_idle(self):
        snap,err=self.s.snapshot('round1');self.assertIsNone(err);self.assertEqual(snap['scaleMilli'],1000);self.assertFalse(snap['used'])
    def test_giant_one(self):
        self.assertEqual(self.begin(),(True,'STARTED'))
        sn,_=self.s.snapshot('round1');self.assertEqual(sn['targets'],['a']);self.assertEqual(sn['scaleMilli'],1600)
    def test_mini_all(self):
        self.assertEqual(self.begin('MINI_ALL',None,roster=['z','a','q']),(True,'STARTED'))
        sn,_=self.s.snapshot('round1');self.assertEqual(sn['targets'],['a','q','z']);self.assertEqual(sn['scaleMilli'],700)
    def test_end_exact(self):
        self.begin(now=10);self.assertEqual(self.s.advance('round1',18),(True,'EXPIRED'))
        self.assertEqual(self.s.snapshot('round1')[0]['scaleMilli'],1000)
    def test_before_end(self):
        self.begin(now=10);self.assertEqual(self.s.advance('round1',17.999),(True,'ACTIVE'))
    def test_duplicate_rejected(self):
        self.begin();self.assertEqual(self.begin(eid='evt2'),(False,'EVENT_ALREADY_USED'))
    def test_reentry_after_expiry_rejected(self):
        self.begin();self.s.advance('round1',10);self.assertFalse(self.begin(now=11)[0])
    def test_stale_start(self):
        self.assertEqual(self.begin(mid='previous'),(False,'STALE_MATCH'));self.assertFalse(self.s.used)
    def test_stale_advance(self):
        self.begin();self.assertEqual(self.s.advance('another',3),(False,'STALE_MATCH'))
    def test_stale_leave(self):
        self.begin();self.assertEqual(self.s.leave('previous','a'),(False,'STALE_MATCH'))
    def test_stale_close(self):
        self.begin();self.assertEqual(self.s.close('previous'),(False,'STALE_MATCH'))
    def test_stale_snapshot(self):
        self.assertEqual(self.s.snapshot('previous'),(None,'STALE_MATCH'))
    def test_roster_empty(self):
        self.assertEqual(self.begin(roster=[]),(False,'INVALID_ROSTER'))
    def test_roster_duplicate(self):
        self.assertEqual(self.begin(roster=['a','a']),(False,'INVALID_ROSTER'))
    def test_roster_max(self):
        self.assertEqual(self.begin('MINI_ALL',None,roster=[str(i) for i in range(16)]),(True,'STARTED'))
    def test_roster_overlimit(self):
        self.assertEqual(self.begin(roster=[str(i) for i in range(17)]),(False,'INVALID_ROSTER'))
    def test_roster_nonstring(self):
        for bad in ([1,'a'],['a',None],['a',True]):
            self.assertEqual(self.begin(roster=bad),(False,'INVALID_ROSTER'))
    def test_actor_not_member(self):
        self.assertEqual(self.begin(actor='missing'),(False,'INVALID_ACTOR'))
    def test_giant_actor_required(self):
        self.assertEqual(self.begin(actor=None),(False,'INVALID_ACTOR'))
    def test_mini_actor_forbidden(self):
        self.assertEqual(self.begin(kind='MINI_ALL',actor='a'),(False,'ACTOR_NOT_APPLICABLE'))
    def test_event_id_invalid(self):
        for bad in ('', 'bad/a', 'x'*97, None):
            self.assertEqual(self.begin(eid=bad),(False,'INVALID_EVENT'))
    def test_kind_invalid(self):
        self.assertEqual(self.begin(kind='METEOR'),(False,'INVALID_EVENT'))
    def test_time_invalid(self):
        for bad in (-1,float('nan'),float('inf'),None,True):
            self.assertEqual(self.begin(now=bad),(False,'INVALID_TIME'))
    def test_advance_invalid_time(self):
        self.begin(now=3)
        for bad in (2,float('nan'),float('inf'),True):
            self.assertEqual(self.s.advance('round1',bad),(False,'INVALID_TIME'))
    def test_leave_giant_removes_effect(self):
        self.begin();self.assertEqual(self.s.leave('round1','a'),(True,'EXPIRED'));self.assertEqual(self.s.snapshot('round1')[0]['targets'],[])
    def test_leave_non_target_stays(self):
        self.begin();self.assertEqual(self.s.leave('round1','b'),(True,'ACTIVE'))
    def test_leave_mini_partial(self):
        self.begin(kind='MINI_ALL',actor=None);self.s.leave('round1','b');self.assertEqual(self.s.snapshot('round1')[0]['targets'],['a','c'])
    def test_leave_mini_all(self):
        self.begin(kind='MINI_ALL',actor=None)
        for p in 'abc': self.s.leave('round1',p)
        self.assertEqual(self.s.status,'EXPIRED')
    def test_leave_invalid_player(self):
        self.begin();self.assertEqual(self.s.leave('round1',''),(False,'INVALID_PLAYER'))
    def test_close_clears(self):
        self.begin();self.assertEqual(self.s.close('round1'),(True,'CLOSED'));self.assertEqual(self.s.targets,[])
    def test_begin_after_close(self):
        self.s.close('round1');self.assertEqual(self.begin(),(False,'ROUND_CLOSED'))
    def test_close_idle(self):
        self.assertEqual(self.s.close('round1'),(True,'CLOSED'));self.assertFalse(self.s.used)
    def test_same_match_reset_rejected(self):
        self.assertEqual(self.s.new_round('round1'),(False,'INVALID_NEW_MATCH'))
    def test_new_match_reset(self):
        self.begin();self.assertEqual(self.s.new_round('round2'),(True,'RESET'));self.assertFalse(self.s.used)
        self.assertEqual(self.s.begin('round2','evt2','GIANT_ONE','b',['b'],0),(True,'STARTED'))
    def test_new_round_bad(self):
        self.assertEqual(self.s.new_round('../x'),(False,'INVALID_NEW_MATCH'))
    def test_snapshot_copy_safe(self):
        self.begin();sn,_=self.s.snapshot('round1');sn['targets'].append('evil');self.assertEqual(self.s.targets,['a'])
    def test_epoch_nonbackwards(self):
        self.begin(now=12);self.s.advance('round1',14);self.assertEqual(self.s.advance('round1',13),(False,'INVALID_TIME'))
    def test_id_validation(self):
        for bad in ('', 'a/b', 'ä', 'x'*97, 1): self.assertFalse(valid_id(bad))
    def test_time_validation(self):
        self.assertTrue(valid_time(0));self.assertFalse(valid_time(float('-inf')))
    def test_compat_no_selection_logic(self):
        text=(ROOT/'src'/'ScaleFxCore.luau').read_text();self.assertNotIn('math.random',text);self.assertNotIn('RemoteEvent',text.split('local M = {}',1)[1]);self.assertNotIn('Instance.new',text)
    def test_compat_no_physics(self):
        text=(ROOT/'src'/'ScaleFxCore.luau').read_text();self.assertNotIn('HumanoidDescription',text);self.assertNotIn('BasePart',text);self.assertNotIn('WalkSpeed',text)

if __name__=='__main__': unittest.main()
