"""Additional regressions specifically arising from live 2026-10-31 GitHub PR ID collision evidence.

All inputs are fixtures. No provider connection or GitHub CAS is made by these tests.
"""
from test_system_history_reservation import call, state, SHA, OWNER, BRANCH
import copy
import unittest

LIVE_IDS = [
    'C00159', 'C00159',                    # #142 / #152
    'C00160', 'C00160', 'C00160',          # #142 / #152 / #153
    'C00161', 'C00161', 'C00161',          # #144 / #154 / #155
    'C00162', 'C00162',                    # #144 / #154
    'C00171', 'C00172',                    # later A14 candidates
]

class ActualCollisionSafety(unittest.TestCase):
    def test_current_four_collisions_do_not_reissue_them(self):
        p=call(occupied_ids=LIVE_IDS)
        self.assertEqual(p['status'], 'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED')
        self.assertEqual(p['legacy_collision_ids'], ['C00159', 'C00160', 'C00161', 'C00162'])
        self.assertTrue(p['legacy_collisions_unresolved'])
        self.assertEqual(p['suggested_ids'], ['C00173', 'C00174'])
        for key in ('may_claim','may_write','may_create_pr','may_merge','cas_performed','provider_attested','may_retry'):
            self.assertIs(p[key], False)
    def test_occupied_claims_order_independent(self):
        a=call(occupied_ids=LIVE_IDS)
        b=call(occupied_ids=list(reversed(LIVE_IDS)))
        self.assertEqual(a['legacy_collision_ids'], b['legacy_collision_ids'])
        self.assertEqual(a['suggested_ids'], b['suggested_ids'])
    def test_high_watermark_above_unresolved_claims_used(self):
        s=state();s['history_id_reservations']['high_watermark']=220
        p=call(s,occupied_ids=LIVE_IDS)
        self.assertEqual(p['suggested_ids'],['C00221','C00222'])
    def test_no_mutation_under_collisions(self):
        s=state();pre=copy.deepcopy(s)
        call(s,occupied_ids=LIVE_IDS)
        self.assertEqual(s,pre)
    def test_missing_ledger_still_fails_with_live_collisions(self):
        s=state();s.pop('history_id_reservations')
        self.assertEqual(call(s,occupied_ids=LIVE_IDS)['status'],'WAIT_VERIFIED_BOOTSTRAP')
    def test_truncated_or_malformed_claim_fails(self):
        self.assertEqual(call(occupied_ids=LIVE_IDS+['C0016X'])['status'],'BLOCK_OCCUPIED_SET')
    def test_replay_amount_drift_is_not_silent(self):
        s=call()['proposed_state']
        self.assertEqual(call(s,occupied_ids=['C00172'],amount=1)['status'], 'BLOCK_REPLAY_AMOUNT_DRIFT')
    def test_same_amount_replay_preserves_original_ids(self):
        s=call()['proposed_state']
        self.assertEqual(call(s,occupied_ids=['C00172'])['reserved_ids'], ['C00173','C00174'])
    def test_worker_missing_registry_cannot_plan(self):
        s=state();s['holder']['kind']='WORKER';s['holder']['task_id']=None;s['authorized_tasks'].pop('WORKER')
        self.assertEqual(call(s)['status'],'BLOCK_UNREGISTERED_AUTHOR')
    def test_worker_registered_but_wrong_branch_cannot_plan(self):
        s=state();s['holder']['kind']='WORKER';s['holder']['task_id']=s['authorized_tasks']['WORKER']
        self.assertEqual(call(s)['status'],'BLOCK_WRONG_ROLE_BRANCH')
    def test_meta_wrong_branch_cannot_plan(self):
        s=state();s['holder']['kind']='META';s['authorized_tasks']['META']='6add445e4138819197d9cf2b1a02534d';s['holder']['task_id']=s['authorized_tasks']['META']
        self.assertEqual(call(s)['status'],'BLOCK_WRONG_ROLE_BRANCH')
    def test_empty_source_claims_are_not_proof(self):
        p=call(occupied_ids=[])
        self.assertEqual(p['status'],'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED')
        self.assertFalse(p['provider_attested'])
        self.assertFalse(p['cas_performed'])
    def test_remaining_legacy_collision_not_misreported_as_clear(self):
        p=call(occupied_ids=['C00160','C00160'])
        self.assertEqual(p['legacy_collision_ids'],['C00160'])
        self.assertTrue(p['legacy_collisions_unresolved'])
    def test_ledger_vs_live_overlap_still_needs_reconcile(self):
        s=call()['proposed_state']
        p=call(s,occupied_ids=['C00160','C00160','C00173'])
        self.assertEqual(p['status'],'WAIT_RECONCILE_EXISTING_IDS')
        self.assertNotIn('proposed_state',p)
    def test_fake_occupied_ids_cannot_grant_write(self):
        for occ in ([],['C00999'],LIVE_IDS):
            p=call(occupied_ids=occ)
            self.assertFalse(p['may_write'])
            self.assertFalse(p['may_claim'])

if __name__=='__main__': unittest.main()
