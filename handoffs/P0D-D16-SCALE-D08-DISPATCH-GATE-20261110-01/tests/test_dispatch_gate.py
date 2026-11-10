import unittest
from copy import deepcopy
from reference_gate import Gate, WEATHER, STAGES


def round_state(**updates):
    d={'matchId':'M1','stage':'S1','epoch':1,'now':21.0,'startedAt':0.0,'deadline':80.0,'active':True}
    d.update(updates);return d

def envelope(**updates):
    e={'matchId':'M1','stage':'S1','epoch':1,'kind':'WEATHER','subtype':'WX02_SMALL','phase':'ACTIVATE','validUntil':27.0}
    e.update(updates);return e

class Fixture:
    def __init__(self):
        self.round=round_state();self.players=[1,2,3];self.mapping={'WX02_SMALL':'MINI_ALL'}
        self.calls=0;self.roster_calls=0
    def read_round(self):self.calls+=1;return deepcopy(self.round)
    def read_roster(self):self.roster_calls+=1;return list(self.players)
    def gate(self, **overrides):
        kw={'read_round':self.read_round,'read_roster':self.read_roster,
            'mapping':self.mapping,'choose_target':lambda roster:roster[0],
            'enabled':True,'owner_approved':True,'renderer_ready':True}
        kw.update(overrides)
        return Gate(**kw)

class GateTests(unittest.TestCase):
    def setUp(self):
        self.f=Fixture();self.g=self.f.gate()

    def test_starts_explicit_mini(self):
        self.assertEqual(self.g.activate(envelope()),(True,'STARTED'))
        snap,status=self.g.snapshot()
        self.assertEqual(status,'ACTIVE')
        self.assertEqual(snap['userIds'],[1,2,3])
        self.assertEqual(snap['visualScale'],.7)
    def test_starts_explicit_giant_after_owner_mapping(self):
        self.f.mapping['WX02_SMALL']='GIANT_ONE'
        self.assertEqual(self.g.activate(envelope()),(True,'STARTED'))
        self.assertEqual(self.g.snapshot()[0]['userIds'],[1])
        self.assertEqual(self.g.snapshot()[0]['visualScale'],1.6)
    def test_no_mapping_default(self):
        g=self.f.gate(mapping=None)
        self.assertEqual(g.activate(envelope()),(False,'NO_EXPLICIT_MAPPING'))
    def test_empty_mapping(self):
        g=self.f.gate(mapping={})
        self.assertEqual(g.activate(envelope()),(False,'UNAPPROVED_SUBTYPE'))
    def test_invalid_effect_mapping(self):
        self.f.mapping['WX02_SMALL']='METEOR'
        self.assertEqual(self.g.activate(envelope()),(False,'UNAPPROVED_SUBTYPE'))
    def test_owner_approval_missing(self):
        g=self.f.gate(owner_approved=False)
        self.assertEqual(g.activate(envelope()),(False,'DISABLED_DEFAULT'))
    def test_renderer_not_ready(self):
        g=self.f.gate(renderer_ready=False)
        self.assertEqual(g.activate(envelope()),(False,'DISABLED_DEFAULT'))
    def test_enabled_missing(self):
        g=self.f.gate(enabled=False)
        self.assertEqual(g.activate(envelope()),(False,'DISABLED_DEFAULT'))
    def test_duplicate_activate(self):
        self.assertTrue(self.g.activate(envelope())[0])
        self.assertEqual(self.g.activate(envelope()),(False,'DUPLICATE_OR_ACTIVE'))
    def test_replay_after_cleanup(self):
        self.assertTrue(self.g.activate(envelope())[0])
        self.assertTrue(self.g.cleanup(dict(envelope(),phase=None))[0])
        self.assertEqual(self.g.activate(envelope()),(False,'DUPLICATE_OR_ACTIVE'))
    def test_valid_cleanup(self):
        self.assertTrue(self.g.activate(envelope())[0])
        self.assertEqual(self.g.cleanup(dict(envelope(),phase=None)),(True,'CLOSED'))
        self.assertEqual(self.g.snapshot(),(None,'INACTIVE'))
    def test_cleanup_wrong_subtype(self):
        self.g.activate(envelope())
        self.assertEqual(self.g.cleanup(dict(envelope(subtype='WX04_GLIDE'),phase=None)),(False,'CLEANUP_MISMATCH'))
        self.assertEqual(self.g.snapshot()[1],'ACTIVE')
    def test_cleanup_activate_phase_rejected(self):
        self.g.activate(envelope())
        self.assertEqual(self.g.cleanup(envelope()),(False,'CLEANUP_MISMATCH'))
    def test_expiry_deadline_not_fixed_core_ttl(self):
        self.g.activate(envelope())
        self.f.round['now']=26.999
        self.assertEqual(self.g.snapshot()[1],'ACTIVE')
        self.f.round['now']=27.0
        self.assertEqual(self.g.snapshot(),(None,'ROUND_CLOSED_OR_EXPIRED'))
    def test_match_change_closes(self):
        self.g.activate(envelope())
        self.f.round.update({'matchId':'M2','epoch':2,'now':22})
        self.assertEqual(self.g.snapshot(),(None,'ROUND_CLOSED_OR_EXPIRED'))
    def test_closed_round_clears(self):
        self.g.activate(envelope())
        self.f.round['active']=False
        self.assertEqual(self.g.snapshot(),(None,'ROUND_CLOSED_OR_EXPIRED'))
    def test_stage_change_closes(self):
        self.g.activate(envelope())
        self.f.round['stage']='S2'
        self.assertEqual(self.g.snapshot(),(None,'ROUND_CLOSED_OR_EXPIRED'))
    def test_clock_backwards_disables_gate(self):
        self.g.activate(envelope())
        self.f.round['now']=20.0
        self.assertEqual(self.g.snapshot(),(None,'CLOCK_BACKWARDS'))
        self.assertFalse(self.g.enabled)
    def test_stop_disables(self):
        self.g.activate(envelope());self.g.stop()
        self.assertEqual(self.g.activate(envelope()),(False,'OWNER_STOP'))
        self.assertIsNone(self.g.snapshot()[0])
    def test_zero_events_for_disabled(self):
        g=self.f.gate(enabled=False)
        self.assertFalse(g.activate(envelope())[0]);self.assertEqual(self.f.calls,0)
    def test_reject_boss_event(self):
        self.assertEqual(self.g.activate(envelope(kind='BOSS')),(False,'INVALID_D08_ENVELOPE'))
    def test_reject_warning(self):
        self.assertEqual(self.g.activate(envelope(phase='WARNING')),(False,'INVALID_D08_ENVELOPE'))
    def test_reject_client_like_arbitrary_subtype(self):
        self.assertEqual(self.g.activate(envelope(subtype='GIANT_ONE')),(False,'INVALID_D08_ENVELOPE'))
    def test_reject_wrong_match(self):
        self.assertEqual(self.g.activate(envelope(matchId='M999')),(False,'ROUND_MISMATCH'))
    def test_reject_wrong_epoch(self):
        self.assertEqual(self.g.activate(envelope(epoch=2)),(False,'ROUND_MISMATCH'))
    def test_reject_wrong_stage(self):
        self.assertEqual(self.g.activate(envelope(stage='S4')),(False,'ROUND_MISMATCH'))
    def test_reject_expired(self):
        self.assertEqual(self.g.activate(envelope(validUntil=21.0)),(False,'INVALID_EVENT_DEADLINE'))
    def test_reject_overlong_weather(self):
        self.assertEqual(self.g.activate(envelope(validUntil=31.0)),(False,'INVALID_EVENT_DEADLINE'))
    def test_reject_nan_deadline(self):
        self.assertEqual(self.g.activate(envelope(validUntil=float('nan'))),(False,'INVALID_D08_ENVELOPE'))
    def test_reject_boolean_epoch(self):
        self.assertEqual(self.g.activate(envelope(epoch=True)),(False,'INVALID_D08_ENVELOPE'))
    def test_invalid_round(self):
        self.f.round['now']=-1
        self.assertEqual(self.g.activate(envelope()),(False,'ROUND_INVALID'))
    def test_missing_server_roster(self):
        self.f.players=[]
        self.assertEqual(self.g.activate(envelope()),(False,'ROSTER_UNAVAILABLE'))
    def test_reject_duplicate_roster(self):
        self.f.players=[1,1]
        self.assertEqual(self.g.activate(envelope()),(False,'ROSTER_UNAVAILABLE'))
    def test_reject_bad_roster_bool(self):
        self.f.players=[True,2]
        self.assertEqual(self.g.activate(envelope()),(False,'ROSTER_UNAVAILABLE'))
    def test_giant_target_not_in_roster(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        g=self.f.gate(choose_target=lambda users:999)
        self.assertEqual(g.activate(envelope()),(False,'TARGET_NOT_IN_ROSTER'))
    def test_giant_bool_target_not_accepted(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        g=self.f.gate(choose_target=lambda users:True)
        self.assertEqual(g.activate(envelope()),(False,'TARGET_NOT_IN_ROSTER'))
    def test_giant_missing_target_callback(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        g=self.f.gate(choose_target=None)
        self.assertEqual(g.activate(envelope()),(False,'TARGET_CALLBACK_MISSING'))
    def test_callback_throws(self):
        def err(_):raise ValueError('boom')
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        g=self.f.gate(choose_target=err)
        self.assertEqual(g.activate(envelope()),(False,'TARGET_CALLBACK_FAILED'))
    def test_read_round_throws(self):
        def err():raise RuntimeError('boom')
        g=self.f.gate(read_round=err)
        self.assertEqual(g.activate(envelope()),(False,'READ_ROUND_FAILED'))
    def test_round_replaced_mid_callback(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        def change(_):self.f.round.update({'matchId':'M2','epoch':2});return 1
        g=self.f.gate(choose_target=change)
        self.assertEqual(g.activate(envelope()),(False,'ROUND_CHANGED_DURING_CALLBACK'))
    def test_round_clock_regression_mid_callback(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        def change(_):self.f.round['now']=20.0;return 1
        g=self.f.gate(choose_target=change)
        self.assertEqual(g.activate(envelope()),(False,'ROUND_CHANGED_DURING_CALLBACK'))
    def test_deadline_change_mid_callback(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        def change(_):self.f.round['deadline']=100.;return 1
        g=self.f.gate(choose_target=change)
        self.assertEqual(g.activate(envelope()),(False,'ROUND_CHANGED_DURING_CALLBACK'))
    def test_roster_changed_mid_callback(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        def change(_):self.f.players.append(4);return 1
        g=self.f.gate(choose_target=change)
        self.assertEqual(g.activate(envelope()),(False,'ROSTER_CHANGED'))
    def test_roster_order_change_ok(self):
        self.f.mapping={'WX02_SMALL':'GIANT_ONE'}
        def change(_):self.f.players.reverse();return 1
        g=self.f.gate(choose_target=change)
        self.assertEqual(g.activate(envelope()),(True,'STARTED'))
    def test_second_activate_without_cleanup_denied(self):
        self.g.activate(envelope())
        self.f.round.update({'matchId':'M2','epoch':2,'now':22.})
        self.assertEqual(self.g.activate(envelope(matchId='M2',epoch=2,validUntil=28.)),(False,'DUPLICATE_OR_ACTIVE'))
    def test_different_round_after_cleanup(self):
        self.g.activate(envelope())
        self.g.cleanup(dict(envelope(),phase=None))
        self.f.round.update({'matchId':'M2','epoch':2,'now':22.,'startedAt':19.})
        self.assertEqual(self.g.activate(envelope(matchId='M2',epoch=2,validUntil=28.)),(True,'STARTED'))
    def test_no_roster_data_from_external_event(self):
        e=envelope(serverRoster=[999],targetUserId=999)
        self.assertTrue(self.g.activate(e)[0]);self.assertEqual(self.g.snapshot()[0]['userIds'],[1,2,3])
    def test_all_weather_names_are_finite_contract(self):
        self.assertEqual(len(WEATHER),5)
        self.assertEqual(STAGES,{'S1','S2','S3','S4'})

if __name__=='__main__':unittest.main()
