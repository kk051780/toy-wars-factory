import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle import Harness, OracleGate, OriginalCore


class OriginalAdapterContractTests(unittest.TestCase):
    def setUp(self):
        self.h = Harness()

    def test_original_core_exact_api_six_methods(self):
        self.assertTrue(all(hasattr(self.h.core, fn) for fn in (
            'new', 'begin', 'advance', 'leave', 'close', 'snapshot')))

    def test_default_disabled(self):
        h = Harness(enabled=False)
        self.assertEqual(h.gate.activate(h.envelope()), (False, 'DISABLED_DEFAULT'))
        self.assertEqual(h.core.calls, [])

    def test_owner_approval_missing(self):
        h = Harness(approved=False)
        self.assertFalse(h.gate.activate(h.envelope())[0])
        self.assertFalse(h.gate.enabled)

    def test_empty_mapping_denied(self):
        h = Harness(mapping={})
        self.assertEqual(h.gate.activate(h.envelope()), (False, 'OWNER_MAPPING_NOT_APPROVED'))

    def test_unreviewed_weather_rejected(self):
        for k in ('WX99_FAKE', 'GIANT_ONE', 'WX03_CROWN_'):
            with self.subTest(k=k):
                with self.assertRaises(ValueError):
                    Harness(mapping={k: 'GIANT_ONE'})

    def test_bad_kind_mapping_rejected(self):
        for v in ('giant', 'MIXED', 'MINI_ALL_PLUS', 1600):
            with self.subTest(v=v):
                with self.assertRaises(ValueError):
                    Harness(mapping={'WX02_SMALL': v})

    def test_mini_all_exact_core_signature(self):
        self.assertEqual(self.h.gate.activate(self.h.envelope()), (True, 'STARTED'))
        calls = self.h.core.calls
        self.assertEqual(calls[:2], [('new', 'm1'),
            ('begin', 'm1', 'serverEvent1', 'MINI_ALL', None, ('alice', 'bob'), 100.)])

    def test_giant_one_exact_core_signature(self):
        h = Harness(mapping={'WX03_CROWN': 'GIANT_ONE'})
        self.assertEqual(h.gate.activate(h.envelope('WX03_CROWN')), (True, 'STARTED'))
        self.assertEqual(h.core.calls[1],
                         ('begin', 'm1', 'serverEvent1', 'GIANT_ONE', 'alice', ('alice', 'bob'), 100.))

    def test_original_uses_seconds_not_milliseconds(self):
        self.h.gate.activate(self.h.envelope())
        v, _ = self.h.gate.snapshot()
        self.assertEqual(v['expiresAt'], 108.)
        self.assertEqual(v['scaleMilli'], 700)

    def test_giant_milli_scale(self):
        h = Harness(mapping={'WX03_CROWN': 'GIANT_ONE'})
        h.gate.activate(h.envelope('WX03_CROWN'))
        self.assertEqual(h.gate.snapshot()[0]['scaleMilli'], 1600)

    def test_invalid_phase_rejected(self):
        e=self.h.envelope(); e['phase']='WARNING'
        self.assertEqual(self.h.gate.activate(e)[1], 'INVALID_D08_ENVELOPE')

    def test_invalid_event_kind_rejected(self):
        e=self.h.envelope(); e['kind']='BOSS'
        self.assertEqual(self.h.gate.activate(e)[1], 'INVALID_D08_ENVELOPE')

    def test_bad_subtype_rejected(self):
        e=self.h.envelope(); e['subtype']='GIANT_ONE'
        self.assertEqual(self.h.gate.activate(e)[1], 'INVALID_D08_ENVELOPE')

    def test_fake_envelope_provenance_rejected(self):
        self.h.authentic=False
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'NOT_AUTHENTIC_D08_ENVELOPE')
        self.assertFalse(any(c[0]=='begin' for c in self.h.core.calls))

    def test_duplicate_event_refused(self):
        e=self.h.envelope(); self.h.gate.activate(e)
        self.assertEqual(self.h.gate.activate(e)[1], 'ALREADY_ACTIVE')
        self.h.gate.cleanup(self.h.cleanup())
        self.assertEqual(self.h.gate.activate(e)[1], 'DUPLICATE_OR_ROUND_LIMIT')

    def test_expired_event_denied(self):
        e=self.h.envelope(); e['validUntil']=99.0
        self.assertEqual(self.h.gate.activate(e)[1], 'STALE_OR_INACTIVE_ROUND')

    def test_wrong_epoch_denied(self):
        e=self.h.envelope();e['epoch']=2
        self.assertEqual(self.h.gate.activate(e)[1], 'STALE_OR_INACTIVE_ROUND')

    def test_wrong_stage_denied(self):
        e=self.h.envelope();e['stage']='S2'
        self.assertEqual(self.h.gate.activate(e)[1], 'STALE_OR_INACTIVE_ROUND')

    def test_wrong_match_denied(self):
        e=self.h.envelope();e['matchId']='other'
        self.assertEqual(self.h.gate.activate(e)[1], 'STALE_OR_INACTIVE_ROUND')

    def test_inactive_round_denied(self):
        self.h.state['active']=False
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'STALE_OR_INACTIVE_ROUND')

    def test_clock_reversal_denied(self):
        self.h.gate.last_now=110
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'STALE_OR_INACTIVE_ROUND')

    def test_invalid_roster_empty(self):
        self.h.roster=[]
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'INVALID_TRUSTED_ROSTER')

    def test_invalid_roster_duplicate(self):
        self.h.roster=['alice','alice']
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'INVALID_TRUSTED_ROSTER')

    def test_roster_overflow(self):
        self.h.roster=[f'p{x}' for x in range(17)]
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'INVALID_TRUSTED_ROSTER')

    def test_actor_not_in_roster_denied(self):
        h=Harness(mapping={'WX03_CROWN':'GIANT_ONE'});h.actor='charlie'
        self.assertEqual(h.gate.activate(h.envelope('WX03_CROWN'))[1], 'INVALID_SERVER_ACTOR')

    def test_actor_callback_none_denied(self):
        h=Harness(mapping={'WX03_CROWN':'GIANT_ONE'});h.actor=None
        self.assertEqual(h.gate.activate(h.envelope('WX03_CROWN'))[1], 'INVALID_SERVER_ACTOR')

    def test_bad_minted_event_id_denied(self):
        self.h.id='bad event'
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'INVALID_SERVER_EVENT_ID')

    def test_round_change_during_roster_callback(self):
        self.h.hooks['roster']=lambda:self.h.state.update(matchId='m2')
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'REVOKED_OR_CHANGED_DURING_CALLBACK')
        self.assertFalse(any(c[0]=='begin' for c in self.h.core.calls))

    def test_epoch_change_during_actor_callback(self):
        h=Harness(mapping={'WX03_CROWN':'GIANT_ONE'})
        h.hooks['actor']=lambda:h.state.update(epoch=2)
        self.assertEqual(h.gate.activate(h.envelope('WX03_CROWN'))[1], 'REVOKED_OR_CHANGED_DURING_CALLBACK')

    def test_deadline_reached_during_callback(self):
        self.h.hooks['event_id']=lambda:setattr(self.h,'clock',141.)
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'REVOKED_OR_CHANGED_DURING_CALLBACK')

    def test_subtype_mutated_during_callback(self):
        e=self.h.envelope()
        self.h.hooks['roster']=lambda:e.update(subtype='WX03_CROWN')
        self.assertEqual(self.h.gate.activate(e)[1], 'REVOKED_OR_CHANGED_DURING_CALLBACK')

    def test_cleanup_during_roster_callback_revokes_inflight(self):
        self.h.hooks['roster']=lambda:self.h.gate.cleanup(self.h.cleanup())
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'REVOKED_OR_CHANGED_DURING_CALLBACK')
        self.assertFalse(any(c[0]=='begin' for c in self.h.core.calls))

    def test_stop_during_roster_callback_revokes_inflight(self):
        self.h.hooks['roster']=lambda:self.h.gate.stop()
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'REVOKED_OR_CHANGED_DURING_CALLBACK')
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'DISABLED_DEFAULT')

    def test_cleanup_during_second_auth_revokes_inflight(self):
        self.h.hooks['auth2']=lambda:self.h.gate.cleanup(self.h.cleanup())
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'REVOKED_AFTER_PROVENANCE_RECHECK')
        self.assertFalse(any(c[0]=='begin' for c in self.h.core.calls))

    def test_stop_during_second_auth_revokes_inflight(self):
        self.h.hooks['auth2']=lambda:self.h.gate.stop()
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'REVOKED_AFTER_PROVENANCE_RECHECK')

    def test_clock_expires_during_second_auth(self):
        self.h.hooks['auth2']=lambda:setattr(self.h,'clock',136.)
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'REVOKED_AFTER_PROVENANCE_RECHECK')

    def test_forged_cleanup_rejected(self):
        self.h.gate.activate(self.h.envelope()); self.h.authentic_cleanup=False
        self.assertEqual(self.h.gate.cleanup(self.h.cleanup())[1], 'UNTRUSTED_CLEANUP')
        self.assertIsNotNone(self.h.gate.active)

    def test_stale_cleanup_rejected(self):
        self.h.gate.activate(self.h.envelope());c=self.h.cleanup();c['epoch']=2
        self.assertEqual(self.h.gate.cleanup(c)[1], 'STALE_CLEANUP')
        self.assertIsNotNone(self.h.gate.active)

    def test_valid_cleanup_closes_original(self):
        self.h.gate.activate(self.h.envelope())
        self.assertEqual(self.h.gate.cleanup(self.h.cleanup()), (True,'CLOSED'))
        self.assertIsNone(self.h.gate.active)
        self.assertTrue(any(x[0]=='close' for x in self.h.core.calls))

    def test_effect_advance_before_expiry(self):
        self.h.gate.activate(self.h.envelope());self.h.clock=105
        self.assertEqual(self.h.gate.tick(), (True,'ACTIVE'))

    def test_effect_expiry_8_seconds(self):
        self.h.gate.activate(self.h.envelope());self.h.clock=108
        self.assertEqual(self.h.gate.tick(), (True,'EFFECT_ENDED'))
        self.assertIsNone(self.h.gate.active)

    def test_round_stop_cleanup_on_tick(self):
        self.h.gate.activate(self.h.envelope());self.h.state['active']=False
        self.assertEqual(self.h.gate.tick()[1], 'ROUND_INVALID_OR_EXPIRED')
        self.assertIsNone(self.h.gate.active)

    def test_round_swap_cleanup_on_tick(self):
        self.h.gate.activate(self.h.envelope());self.h.state['matchId']='m2'
        self.assertEqual(self.h.gate.tick()[1], 'ROUND_INVALID_OR_EXPIRED')

    def test_clock_regression_cleanup_on_tick(self):
        self.h.gate.activate(self.h.envelope());self.h.clock=99
        self.assertEqual(self.h.gate.tick()[1], 'ROUND_INVALID_OR_EXPIRED')

    def test_stop_during_tick_round_callback_prevents_core_advance(self):
        self.h.gate.activate(self.h.envelope());self.h.hooks['round']=lambda:self.h.gate.stop()
        self.assertEqual(self.h.gate.tick()[1], 'ROUND_INVALID_OR_EXPIRED')
        self.assertFalse(any(x[0]=='advance' for x in self.h.core.calls))

    def test_stop_during_snapshot_round_callback(self):
        self.h.gate.activate(self.h.envelope());self.h.hooks['round']=lambda:self.h.gate.stop()
        self.assertEqual(self.h.gate.snapshot()[1], 'ROUND_INVALID_OR_EXPIRED')
        self.assertIsNone(self.h.gate.active)

    def test_leave_player_from_giant_closes(self):
        h=Harness(mapping={'WX03_CROWN':'GIANT_ONE'});h.gate.activate(h.envelope('WX03_CROWN'))
        self.assertEqual(h.gate.leave('alice')[1], 'EXPIRED')
        self.assertIsNone(h.gate.active)

    def test_leave_one_from_mini_preserves_other(self):
        self.h.gate.activate(self.h.envelope())
        self.assertEqual(self.h.gate.leave('alice')[1], 'ACTIVE')
        v,_=self.h.gate.snapshot();self.assertEqual(v['targets'],['bob'])

    def test_snapshot_is_defensive_copy(self):
        self.h.gate.activate(self.h.envelope())
        v,_=self.h.gate.snapshot();v['targets'].clear()
        self.assertEqual(self.h.gate.snapshot()[0]['targets'],['alice','bob'])

    def test_stop_idempotent_and_disables(self):
        self.h.gate.activate(self.h.envelope())
        self.assertEqual(self.h.gate.stop(), (True,'STOPPED'))
        self.assertEqual(self.h.gate.stop(), (True,'STOPPED'))
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'DISABLED_DEFAULT')

    def test_multiple_round_budget_fail_closed(self):
        self.h.gate.seen={(f'm{i}',i) for i in range(128)}
        self.assertEqual(self.h.gate.activate(self.h.envelope())[1], 'DUPLICATE_OR_ROUND_LIMIT')

    def test_issuer_stops_after_first_attempt_even_if_fails_auth(self):
        self.h.authentic=False
        e=self.h.envelope()
        self.h.gate.activate(e)
        self.h.authentic=True
        self.assertEqual(self.h.gate.activate(e)[1], 'DUPLICATE_OR_ROUND_LIMIT')

    def test_snapshot_expires_without_tick(self):
        self.h.gate.activate(self.h.envelope())
        self.h.clock=108
        self.assertEqual(self.h.gate.snapshot()[1], 'EFFECT_EXPIRED_OR_INACTIVE')
        self.assertIsNone(self.h.gate.active)

    def test_snapshot_one_moment_before_expiry_valid(self):
        self.h.gate.activate(self.h.envelope());self.h.clock=107.999
        self.assertEqual(self.h.gate.snapshot()[0]['scaleMilli'],700)

    def test_leave_after_expiry_rejects_and_closes(self):
        self.h.gate.activate(self.h.envelope());self.h.clock=108
        self.assertEqual(self.h.gate.leave('alice')[1], 'ROUND_OR_EFFECT_NOT_ACTIVE')
        self.assertIsNone(self.h.gate.active)

    def test_shorter_d08_event_cutoff_closes_early_on_tick(self):
        e=self.h.envelope();e['validUntil']=103
        self.h.gate.activate(e);self.h.clock=103
        self.assertEqual(self.h.gate.tick()[1], 'ROUND_INVALID_OR_EXPIRED')
        self.assertIsNone(self.h.gate.active)

    def test_shorter_d08_event_cutoff_closes_early_on_snapshot(self):
        e=self.h.envelope();e['validUntil']=103
        self.h.gate.activate(e);self.h.clock=103
        self.assertEqual(self.h.gate.snapshot()[1], 'ROUND_INVALID_OR_EXPIRED')
        self.assertIsNone(self.h.gate.active)

    def test_static_luau_guards(self):
        p=Path(__file__).resolve().parents[1]/'luau'/'OriginalScaleD08AuthorityGate.luau'
        s=p.read_text()
        for exact in ('pcall(self.core.new,initial.matchId)',
                      'pcall(self.core.begin,state,initial.matchId,eventId,kind,',
                      'pcall(self.core.advance,a.state,a.round.matchId,s.now)',
                      'pcall(self.core.leave,a.state,a.round.matchId,trustedPlayerId)',
                      'pcall(self.core.close,active.state,active.round.matchId)',
                      'pcall(self.core.snapshot,a.state,a.round.matchId)',
                      'ownerApproved==true', 'OWNER_MAPPING_NOT_APPROVED',
                      'REVOKED_AFTER_PROVENANCE_RECHECK'):
            with self.subTest(signature=exact):
                self.assertIn(exact,s)
        for banned in ('Instance.new(', '.FireServer(', '.OnServerEvent:', 'RemoteEvent.new(',
                       'Humanoid:TakeDamage', 'math.random(', 'DataStoreService',
                       'workspace:Raycast(', 'RenderStepped:Connect(', 'Heartbeat:Connect('):
            with self.subTest(ban=banned):
                self.assertNotIn(banned,s)

    def test_original_not_cleanroom_contract(self):
        lua=(Path(__file__).resolve().parents[1]/'luau'/'OriginalScaleD08AuthorityGate.luau').read_text()
        self.assertIn('pcall(self.core.begin,state,initial.matchId,eventId,kind,',lua)
        self.assertNotIn('visualScale',lua)
        self.assertNotIn('nowMs',lua)


if __name__=='__main__':
    unittest.main()
