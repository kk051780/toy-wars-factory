import importlib.util
import pathlib
import random
import unittest
from copy import deepcopy

from glide_oracle import new_state,step

ROOT=pathlib.Path(__file__).resolve().parents[1]

def valid(**kw):
    x=dict(userId=12,epoch=3,seq=1,now=100.,alive=True,activeRound=True,teamValid=True,teamToken='BLUE',onGround=False,hasEgg=False,mounted=False,snared=False,rewinding=False,verticalVelocity=-4.,fallDistance=8.)
    x.update(kw)
    return x

class GlideTests(unittest.TestCase):
    def setUp(self):
        self.s=new_state(12,3)

    def runstep(self,act='START',**kw):
        return step(self.s,act,valid(**kw),dict(enabled=True))

    def test_01_defaults_disabled(self):
        self.assertEqual(step(self.s,'START',valid())[1]['reason'],'DISABLED')
    def test_02_enabled_starts(self):
        s,d=self.runstep()
        self.assertEqual((s['mode'],d['action'],d['expiresAt']),('ACTIVE','START',105))
    def test_03_immutable_input(self):
        before=deepcopy(self.s);self.runstep();self.assertEqual(self.s,before)
    def test_04_active_heartbeat(self):
        s,_=self.runstep();n,d=step(s,'TICK',valid(seq=2,now=101),{'enabled':True});self.assertEqual(d['action'],'MAINTAIN')
    def test_05_timeout_at_boundary(self):
        s,_=self.runstep();n,d=step(s,'TICK',valid(seq=2,now=105),{'enabled':True});self.assertEqual((n['cooldownUntil'],d['reason']),(130,'TIME_LIMIT'))
    def test_06_stop_user(self):
        s,_=self.runstep();_,d=step(s,'STOP',valid(seq=2,now=101),{'enabled':True});self.assertEqual(d['reason'],'USER_STOP')
    def test_07_stop_on_land(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,onGround=True),{'enabled':True});self.assertEqual(d['action'],'STOP')
    def test_08_stop_on_egg(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,hasEgg=True),{'enabled':True});self.assertEqual(d['reason'],'AUTHORITY_LOST')
    def test_09_stop_on_vehicle(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,mounted=True),{'enabled':True});self.assertEqual(d['action'],'STOP')
    def test_10_stop_on_snare(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,snared=True),{'enabled':True});self.assertEqual(d['action'],'STOP')
    def test_11_stop_on_rewind(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,rewinding=True),{'enabled':True});self.assertEqual(d['action'],'STOP')
    def test_12_stop_on_death(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,alive=False),{'enabled':True});self.assertEqual(d['action'],'STOP')
    def test_13_stop_on_team_change(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,teamToken='RED'),{'enabled':True});self.assertEqual(d['action'],'STOP')
    def test_14_stop_on_end_round(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101,activeRound=False),{'enabled':True});self.assertEqual(d['action'],'STOP')
    def test_15_round_advance_stops(self):
        s,_=self.runstep();n,d=step(s,'START',valid(epoch=4,seq=2,now=101),{'enabled':True});self.assertEqual((n['mode'],n['epoch'],d['action']),('IDLE',4,'STOP'))
    def test_16_new_round_no_instant_start(self):
        n,d=self.runstep(epoch=4);self.assertEqual((n['mode'],d['action']),('IDLE','NONE'))
    def test_17_old_epoch_rejected(self):
        _,d=self.runstep(epoch=2);self.assertEqual(d['reason'],'STALE_AUTHORITY')
    def test_18_replay_sequence_rejected(self):
        s,_=self.runstep();_,d=step(s,'STOP',valid(seq=1,now=101),{'enabled':True});self.assertEqual(d['reason'],'STALE_AUTHORITY')
    def test_19_retrograde_clock_rejected(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=99),{'enabled':True});self.assertEqual(d['reason'],'STALE_AUTHORITY')
    def test_20_other_user_rejected(self):
        _,d=self.runstep(userId=13);self.assertEqual(d['action'],'STOP')
    def test_21_missing_authority_rejected(self):
        _,d=self.runstep(hasEgg=None);self.assertEqual(d['reason'],'AUTHORITY_INCOMPLETE')
    def test_22_nan_clock_rejected(self):
        _,d=self.runstep(now=float('nan'));self.assertEqual(d['action'],'STOP')
    def test_23_grounded_start_denied(self):
        _,d=self.runstep(onGround=True);self.assertEqual(d['reason'],'NOT_ELIGIBLE')
    def test_24_not_descending_denied(self):
        _,d=self.runstep(verticalVelocity=0.0);self.assertEqual(d['action'],'DENY')
    def test_25_too_small_fall_denied(self):
        _,d=self.runstep(fallDistance=2.9);self.assertEqual(d['action'],'DENY')
    def test_26_too_high_fall_denied(self):
        _,d=self.runstep(fallDistance=61);self.assertEqual(d['action'],'DENY')
    def test_27_start_bounds_allowed(self):
        for h in (3,60):
            with self.subTest(h=h):self.assertEqual(self.runstep(fallDistance=h)[1]['action'],'START')
    def test_28_stop_cooldown(self):
        s,_=self.runstep();s,_=step(s,'STOP',valid(seq=2,now=101),{'enabled':True});_,d=step(s,'START',valid(seq=3,now=125),{'enabled':True});self.assertEqual(d['reason'],'COOLDOWN')
    def test_29_cooldown_boundary(self):
        s,_=self.runstep();s,_=step(s,'STOP',valid(seq=2,now=101),{'enabled':True});_,d=step(s,'START',valid(seq=3,now=126),{'enabled':True});self.assertEqual(d['action'],'START')
    def test_30_stop_if_switch_disabled(self):
        s,_=self.runstep();_,d=step(s,'TICK',valid(seq=2,now=101),{'enabled':False});self.assertEqual(d['reason'],'DISABLED')
    def test_31_unknown_intent_fail_closed(self):
        _,d=self.runstep(act='FLY');self.assertEqual(d['action'],'STOP')
    def test_32_all_seven_jobs_same_policy(self):
        for _ in range(7):self.assertEqual(self.runstep()[1]['action'],'START')
    def test_33_no_data_write_in_luau(self):
        src=(ROOT/'luau'/'GlidePermissionPolicy.luau').read_text()
        for token in ('TakeDamage(', 'UpdateAsync(', 'SetAsync(', 'FireServer(', 'AssemblyLinearVelocity =', 'PivotTo('):self.assertNotIn(token,src)
    def test_34_luau_constraints_in_spec(self):
        src=(ROOT/'luau'/'GlidePermissionPolicy.luau').read_text()
        for token in ('MAX_SECONDS = 5','COOLDOWN_SECONDS = 25','MAX_HORIZONTAL = 18','MIN_DESCENT_VELOCITY = -10'):
            self.assertIn(token,src)
    def test_35_1000_randomized_no_bad_grants(self):
        rand=random.Random(429)
        for i in range(1000):
            x=valid(seq=i+1,now=100+i/10)
            for k in ('alive','activeRound','teamValid','onGround','hasEgg','mounted','snared','rewinding'):
                x[k]=bool(rand.getrandbits(1))
            _,d=step(new_state(12,3),'START',x,{'enabled':True})
            ok=x['alive'] and x['activeRound'] and x['teamValid'] and not (x['onGround'] or x['hasEgg'] or x['mounted'] or x['snared'] or x['rewinding'])
            self.assertEqual(d['action']=='START',ok)
    def test_36_server_tick_not_start(self):
        _,d=self.runstep(act='TICK');self.assertEqual(d['action'],'NONE')
    def test_37_unauthorized_team_denied(self):
        _,d=self.runstep(teamValid=False);self.assertEqual(d['action'],'DENY')
    def test_38_missing_team_denied(self):
        _,d=self.runstep(teamToken='');self.assertEqual(d['action'],'STOP')
    def test_39_negative_clock_denied(self):
        _,d=self.runstep(now=-1);self.assertEqual(d['action'],'STOP')
    def test_40_sequence_must_be_positive(self):
        _,d=self.runstep(seq=0);self.assertEqual(d['action'],'STOP')

    def test_41_new_epoch_allows_seq_reset(self):
        s,_=self.runstep()
        s,d=step(s,'TICK',valid(seq=2,now=101),{'enabled':True})
        s,d=step(s,'START',valid(epoch=4,seq=1,now=102),{'enabled':True})
        self.assertEqual((s['epoch'],s['lastSeq'],d['reason']),(4,1,'ROUND_CHANGED'))
    def test_42_missing_authority_active_enters_cooldown(self):
        s,_=self.runstep()
        s,d=step(s,'TICK',valid(seq=2,now=101,hasEgg=None),{'enabled':True})
        self.assertEqual((s['mode'],d['reason']),('COOLDOWN','AUTHORITY_INCOMPLETE'))
    def test_43_unknown_intent_active_enters_cooldown(self):
        s,_=self.runstep()
        s,d=step(s,'BOGUS',valid(seq=2,now=101),{'enabled':True})
        self.assertEqual((s['mode'],d['reason']),('COOLDOWN','UNKNOWN_INTENT'))

if __name__=='__main__':unittest.main()
