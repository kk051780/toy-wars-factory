"""Deterministic Python interleaving regressions (no Roblox Studio or native Luau)."""
import unittest
from reference_v2 import GateV2


def round_(**kw):
    r=dict(matchId='M1',stage='S1',epoch=1,now=23.0,startedAt=0.0,deadline=80.0,active=True)
    r.update(kw);return r

def event(**kw):
    e=dict(matchId='M1',stage='S1',epoch=1,kind='WEATHER',subtype='WX02_SMALL',phase='ACTIVATE',validUntil=29.0)
    e.update(kw);return e

def cleanup(**kw):
    e=event(**kw);e.pop('phase');e.pop('validUntil');return e

def build(*,effect='GIANT_ONE',mapped=True,enabled=True,approved=True,visual=True):
    state={'round':round_(),'roster':[1,2,3]}
    g=GateV2(lambda:state['round'],lambda:state['roster'],lambda r:2,
             mapping={'WX02_SMALL':effect} if mapped else None,
             enabled=enabled,approved=approved,visual=visual)
    return g,state

class GateV2Tests(unittest.TestCase):
    def test_default_disabled(self):
        g,_=build(enabled=False);self.assertEqual(g.activate(event()),(False,'DISABLED_DEFAULT'))
    def test_owner_approval_required(self):
        g,_=build(approved=False);self.assertFalse(g.enabled)
    def test_renderer_required(self):
        g,_=build(visual=False);self.assertFalse(g.enabled)
    def test_no_mapping(self):
        g,_=build(mapped=False);self.assertEqual(g.activate(event()),(False,'NO_EXPLICIT_MAPPING'))
    def test_wrong_weather_not_claimed(self):
        g,_=build();self.assertEqual(g.activate(event(subtype='WX05_CLOCK')),(False,'UNAPPROVED_SUBTYPE'))
    def test_unknown_weather(self):
        g,_=build();self.assertEqual(g.activate(event(subtype='OTHER')),(False,'INVALID_D08_ENVELOPE'))
    def test_giant_success(self):
        g,_=build();self.assertEqual(g.activate(event()),(True,'STARTED'));self.assertEqual(g.core.active['visualScale'],1.6)
    def test_mini_success(self):
        g,_=build(effect='MINI_ALL');self.assertEqual(g.activate(event()),(True,'STARTED'));self.assertEqual(g.core.active['visualScale'],.7)
    def test_target_not_roster(self):
        g,_=build();g.choose_target=lambda r:77;self.assertEqual(g.activate(event()),(False,'TARGET_NOT_IN_ROSTER'))
    def test_early_cleanup_closes_core(self):
        g,_=build();g.activate(event());self.assertEqual(g.cleanup(cleanup()),(True,'CLOSED'));self.assertIsNone(g.core.active);self.assertEqual(g.core.close_count,1)
    def test_owner_stop_closes_core(self):
        g,_=build();g.activate(event());self.assertEqual(g.stop(),(True,'OWNER_STOP'));self.assertIsNone(g.core.active);self.assertEqual(g.core.close_count,1)
    def test_owner_stop_idempotent(self):
        g,_=build();g.activate(event());g.stop();self.assertTrue(g.stop()[0]);self.assertEqual(g.core.close_count,1)
    def test_wrong_cleanup_does_not_close(self):
        g,_=build();g.activate(event());self.assertEqual(g.cleanup(cleanup(epoch=2)),(False,'CLEANUP_MISMATCH'));self.assertIsNotNone(g.core.active)
    def test_cleanup_must_lack_phase(self):
        g,_=build();g.activate(event());self.assertEqual(g.cleanup(event()),(False,'INVALID_CLEANUP'))
    def test_double_activation(self):
        g,_=build();g.activate(event());self.assertEqual(g.activate(event()),(False,'DUPLICATE_OR_ACTIVE'))
    def test_later_round_allowed_when_closed(self):
        g,state=build();g.activate(event());g.cleanup(cleanup());state['round']=round_(matchId='M2',epoch=2,now=26.0)
        self.assertTrue(g.activate(event(matchId='M2',epoch=2,validUntil=31.0))[0])
    def test_replay_old_round(self):
        g,_=build();g.activate(event());g.cleanup(cleanup());self.assertFalse(g.activate(event())[0])
    def test_expiry_closes(self):
        g,state=build();g.activate(event());state['round']['now']=29.0;self.assertEqual(g.snapshot()[1],'ROUND_CLOSED_OR_EXPIRED');self.assertIsNone(g.core.active)
    def test_match_stop_closes(self):
        g,state=build();g.activate(event());state['round']['active']=False;self.assertEqual(g.snapshot()[1],'ROUND_CLOSED_OR_EXPIRED');self.assertIsNone(g.core.active)
    def test_clock_reversal_fails_closed(self):
        g,state=build();g.activate(event());state['round']['now']=22.0;self.assertEqual(g.snapshot()[1],'CLOCK_BACKWARDS');self.assertIsNone(g.core.active)
    def test_round_change_closes(self):
        g,state=build();g.activate(event());state['round']['matchId']='M2';state['round']['now']=24.0;self.assertEqual(g.snapshot()[1],'ROUND_CLOSED_OR_EXPIRED')
    def test_end_before_target_callback_returns(self):
        g,_=build()
        def cb(roster):
            self.assertEqual(g.cleanup(cleanup()),(True,'CANCELLED_PENDING'))
            return 2
        g.choose_target=cb
        self.assertEqual(g.activate(event()),(False,'CANCELLED_DURING_CALLBACK'))
        self.assertIsNone(g.active);self.assertIsNone(g.core.active)
    def test_stop_before_target_callback_returns(self):
        g,_=build()
        def cb(roster):
            g.stop();return 2
        g.choose_target=cb
        self.assertEqual(g.activate(event()),(False,'CANCELLED_DURING_CALLBACK'))
        self.assertIsNone(g.core.active);self.assertFalse(g.enabled)
    def test_end_during_first_roster_callback(self):
        g,state=build()
        def rr():
            g.cleanup(cleanup());return state['roster']
        g.read_roster=rr
        self.assertEqual(g.activate(event()),(False,'CANCELLED_DURING_CALLBACK'))
        self.assertIsNone(g.core.active)
    def test_end_during_second_roster_callback(self):
        g,state=build();counter=[0]
        def rr():
            counter[0]+=1
            if counter[0]==2:g.cleanup(cleanup())
            return state['roster']
        g.read_roster=rr
        self.assertEqual(g.activate(event()),(False,'CANCELLED_DURING_CALLBACK'))
        self.assertIsNone(g.core.active)
    def test_end_during_round_callback(self):
        g,state=build();counter=[0]
        def rd():
            counter[0]+=1
            if counter[0]==1:g.cleanup(cleanup())
            return state['round']
        g.read_round=rd
        self.assertEqual(g.activate(event()),(False,'CANCELLED_DURING_CALLBACK'))
        self.assertIsNone(g.core.active)
    def test_stop_during_snapshot_round_callback(self):
        g,state=build();g.activate(event())
        def rd():
            g.stop();return state['round']
        g.read_round=rd
        self.assertEqual(g.snapshot()[1],'CANCELLED_DURING_CALLBACK')
        self.assertIsNone(g.core.active)
    def test_wrong_cleanup_during_pending_cannot_cancel(self):
        g,_=build()
        def cb(roster):
            self.assertEqual(g.cleanup(cleanup(epoch=9)),(False,'INACTIVE'))
            return 2
        g.choose_target=cb
        self.assertTrue(g.activate(event())[0])
    def test_target_callback_exception(self):
        g,_=build()
        def blow(_):raise ValueError('synthetic')
        g.choose_target=blow
        self.assertEqual(g.activate(event()),(False,'TARGET_CALLBACK_FAILED'))
    def test_stale_roster(self):
        g,state=build();n=[0]
        def rd():
            n[0]+=1
            if n[0]==2:state['roster']=[1,2,8]
            return state['round']
        g.read_round=rd
        self.assertEqual(g.activate(event()),(False,'ROSTER_CHANGED'))
    def test_stale_round(self):
        g,state=build()
        def cb(_):state['round']=round_(now=25.0,epoch=2);return 2
        g.choose_target=cb
        self.assertEqual(g.activate(event()),(False,'ROUND_CHANGED_DURING_CALLBACK'))
    def test_invalid_roster(self):
        g,state=build();state['roster']=[1,1]
        self.assertEqual(g.activate(event()),(False,'ROSTER_UNAVAILABLE'))
    def test_invalid_deadline(self):
        g,_=build();self.assertEqual(g.activate(event(validUntil=36.0)),(False,'INVALID_EVENT_DEADLINE'))
    def test_rejected_epoch(self):
        g,_=build();self.assertEqual(g.activate(event(epoch=1024)),(False,'INVALID_D08_ENVELOPE'))
    def test_bad_event_kind(self):
        g,_=build();self.assertEqual(g.activate(event(kind='BOSS')),(False,'INVALID_D08_ENVELOPE'))
    def test_invalid_phase(self):
        g,_=build();self.assertEqual(g.activate(event(phase='CLEANUP')),(False,'INVALID_D08_ENVELOPE'))
    def test_wrong_stage(self):
        g,_=build();self.assertEqual(g.activate(event(stage='S2')),(False,'ROUND_MISMATCH'))
    def test_unavailable_round_fails(self):
        g,_=build();g.read_round=lambda:None
        self.assertEqual(g.activate(event()),(False,'ROUND_INVALID'))
    def test_cancel_while_core_begin_is_yielding(self):
        g,_=build()
        orig=g.core.begin
        def reentrant_begin(args):
            ok,why=orig(args)
            g.cleanup(cleanup())
            return ok,why
        g.core.begin=reentrant_begin
        self.assertEqual(g.activate(event()),(False,'CANCELLED_DURING_CALLBACK'))
        self.assertIsNone(g.active)
        self.assertIsNone(g.core.active)
        self.assertEqual(g.core.close_count,1)
    def test_stop_while_core_begin_is_yielding(self):
        g,_=build()
        orig=g.core.begin
        def reentrant_begin(args):
            ok,why=orig(args)
            g.stop()
            return ok,why
        g.core.begin=reentrant_begin
        self.assertEqual(g.activate(event()),(False,'CANCELLED_DURING_CALLBACK'))
        self.assertIsNone(g.core.active)
        self.assertFalse(g.enabled)
    def test_failed_core_close_disables_gate(self):
        g,_=build();g.activate(event())
        g.core.close=lambda *args:(False,'INTENTIONAL_FAILURE')
        self.assertEqual(g.stop(),(False,'CORE_CLOSE_FAILED'))
        self.assertFalse(g.enabled)
        self.assertIsNone(g.active)
    def test_cleanup_when_round_callback_is_dead(self):
        g,_=build();g.activate(event())
        g.read_round=lambda: (_ for _ in ()).throw(RuntimeError('lost'))
        self.assertEqual(g.cleanup(cleanup()),(True,'CLOSED'))
        self.assertIsNone(g.core.active)
    def test_stale_id_rejected(self):
        g,_=build();self.assertFalse(g.activate(event(matchId='M*Bad'))[0])
    def test_round_clock_unchanged_allowed(self):
        g,state=build();self.assertTrue(g.activate(event())[0])
        self.assertEqual(g.snapshot()[1],'ACTIVE')
    def test_refuse_ambiguous_meteor_mapping_default(self):
        g,_=build()
        self.assertEqual(g.activate(event(subtype='WX01_METEOR')),(False,'UNAPPROVED_SUBTYPE'))
    def test_busy_is_released_on_cancel(self):
        g,_=build()
        g.choose_target=lambda r: (g.stop(),2)[1]
        self.assertFalse(g.activate(event())[0]);self.assertFalse(g.busy)
    def test_busy_denied(self):
        g,_=build()
        def cb(_):self.assertEqual(g.activate(event()),(False,'BUSY'));return 2
        g.choose_target=cb;self.assertTrue(g.activate(event())[0])

if __name__ == '__main__':unittest.main()
