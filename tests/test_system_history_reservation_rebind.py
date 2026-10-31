"""Fail-closed tests for cross-owner, cross-epoch reservation replay."""
import copy
import unittest
from test_system_history_reservation import call, state, OWNER, SHA

OTHER = '6578f27c-635c-4c46-bd82-c706d1be3e3e'
NEXT_SHA = 'c' * 40

class RebindGuardTests(unittest.TestCase):
    def reserve(self):
        return call()['proposed_state']

    def assert_block(self, s, expected='WAIT_AUTHENTICATED_RESERVATION_REBIND'):
        before=copy.deepcopy(s)
        d=call(s, owner_id=s['holder']['owner_id'],main_sha=s['holder']['base_main_sha'])
        self.assertEqual(d['status'],expected)
        self.assertFalse(d['may_write'])
        self.assertFalse(d['may_claim'])
        self.assertFalse(d['cas_performed'])
        self.assertEqual(before,s)
        self.assertNotIn('proposed_state',d)

    def test_same_owner_same_epoch_same_main_joins_without_write(self):
        s=self.reserve()
        d=call(s)
        self.assertEqual(d['status'],'JOIN_RESERVED_NO_REISSUE')
        self.assertEqual(d['reserved_ids'],['C00173','C00174'])
        self.assertFalse(d['may_write'])

    def test_new_owner_cannot_join_prior_owner_claim(self):
        s=self.reserve()
        s['holder']['owner_id']=OTHER
        self.assert_block(s)

    def test_new_epoch_cannot_join_prior_epoch_claim(self):
        s=self.reserve()
        s['epoch']=303
        s['holder']['epoch']=303
        self.assert_block(s)

    def test_new_main_sha_cannot_join_prior_source_claim(self):
        s=self.reserve()
        s['holder']['base_main_sha']=NEXT_SHA
        self.assert_block(s)

    def test_changing_all_three_still_denied(self):
        s=self.reserve()
        s['holder']['owner_id']=OTHER
        s['epoch']=303
        s['holder']['epoch']=303
        s['holder']['base_main_sha']=NEXT_SHA
        self.assert_block(s)

    def test_mixed_migrated_ids_for_same_work_fail(self):
        s=self.reserve()
        rec=copy.deepcopy(s['history_id_reservations']['entries'][0])
        rec.update(id='C00175',owner_id=OTHER)
        s['history_id_reservations']['entries'].append(rec)
        s['history_id_reservations']['high_watermark']=175
        d=call(s,amount=3)
        self.assertEqual(d['status'],'BLOCK_MIXED_RESERVATION_ORIGINS')
        self.assertFalse(d['may_write'])

    def test_ledger_epoch_cannot_be_from_future(self):
        s=self.reserve()
        s['history_id_reservations']['entries'][0]['epoch']=303
        d=call(s)
        self.assertEqual(d['status'],'BLOCK_FUTURE_RESERVATION_EPOCH')
        self.assertFalse(d['may_write'])

    def test_new_work_still_allocates_above_old_ledger(self):
        s=self.reserve()
        d=call(s,work_id='NEXTWORKID',amount=1)
        self.assertEqual(d['status'],'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED')
        self.assertEqual(d['suggested_ids'],['C00175'])

    def test_old_work_new_owner_cannot_repurpose_ids_even_with_new_work(self):
        s=self.reserve()
        s['holder']['owner_id']=OTHER
        d=call(s,work_id='NEXTWORKID',amount=1,owner_id=OTHER)
        self.assertEqual(d['status'],'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED')
        self.assertEqual(d['suggested_ids'],['C00175'])
        self.assertFalse(d['may_write'])

if __name__=='__main__':unittest.main()
