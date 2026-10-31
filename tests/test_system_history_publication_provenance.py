"""Test-first safeguards for work_id consumption provenance and ledger schema.

The reducer has NO provider/GitHub authority. The only goal of these tests is
rejecting internally contradictory self-reported history and reservation state.
"""
import copy
import hashlib
import json
import unittest
from test_system_history_publication_bridge import sample
from system_history_publication_bridge import reconcile_publications

class ExactWorkIdentity(unittest.TestCase):
    def apply(self, st, claim):
        return reconcile_publications(st, ['C00172','C00173'], [claim])
    def rehash(self, claim, doc):
        changed=copy.deepcopy(claim)
        changed['body']=json.dumps(doc,sort_keys=True)+'\n'
        raw=changed['body'].encode('utf-8')
        changed['blob_sha']=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        return changed
    def assertDenied(self, st, claim, code):
        result=self.apply(st, claim)
        self.assertEqual(result['status'],code)
        for key in ('may_claim','may_write','may_merge','may_retry','github_authenticated','provider_attested','cas_performed'):
            self.assertIs(result[key],False)

    def test_matching_work_id_maintains_valid_consumption_advice(self):
        st,claim=sample()
        self.assertEqual(json.loads(claim['body'])['work_id'],'TWF_HISTORY_ID_REPAIR')
        r=self.apply(st,claim)
        self.assertEqual(r['status'],'MATCHED_CONSUMPTION_CANDIDATE_ONLY')
        self.assertEqual(r['matched_ids'],['C00173'])
    def test_missing_body_work_id_rejected_even_when_owner_epoch_main_match(self):
        st,claim=sample();body=json.loads(claim['body']);del body['work_id']
        self.assertDenied(st,self.rehash(claim,body),'BLOCK_PROVENANCE_MISMATCH')
    def test_unrelated_work_id_must_not_consume_reserved_id(self):
        st,claim=sample();body=json.loads(claim['body']);body['work_id']='OTHER_UNRELATED_JOB'
        self.assertDenied(st,self.rehash(claim,body),'BLOCK_PROVENANCE_MISMATCH')
    def test_boolean_work_id_is_not_a_string_identity(self):
        st,claim=sample();body=json.loads(claim['body']);body['work_id']=True
        self.assertDenied(st,self.rehash(claim,body),'BLOCK_PROVENANCE_MISMATCH')
    def test_work_id_is_not_a_collapsing_unicode_alias(self):
        st,claim=sample();body=json.loads(claim['body']);body['work_id']='TWF_\u212a_HISTORY'
        self.assertDenied(st,self.rehash(claim,body),'BLOCK_PROVENANCE_MISMATCH')
    def test_history_cannot_supply_second_work_id_key(self):
        st,claim=sample();body=claim['body'].replace('"work_id": "TWF_HISTORY_ID_REPAIR"','"work_id": "TWF_HISTORY_ID_REPAIR", "work_id": "OTHER_WORK"')
        # sorted JSON source ensures work_id appears close to final field.
        self.assertNotEqual(body,claim['body'])
        revised=copy.deepcopy(claim);revised['body']=body
        raw=body.encode('utf-8');revised['blob_sha']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()
        self.assertDenied(st,revised,'BLOCK_INVALID_HISTORY_BODY')

class LedgerIdentity(unittest.TestCase):
    def rejected(self, mutation, expected='BLOCK_INVALID_LEDGER'):
        st,claim=sample()
        mutation(st,claim)
        res=reconcile_publications(st,['C00172','C00173'],[claim])
        self.assertEqual(res['status'],expected)
        self.assertFalse(res['may_write'])
        self.assertFalse(res['cas_performed'])
    def test_missing_owner_ledger_uuid(self):
        self.rejected(lambda st,c: st['history_id_reservations']['entries'][0].update(owner_id='not-a-uuid'))
    def test_noncanonical_ledger_uuid(self):
        self.rejected(lambda st,c: st['history_id_reservations']['entries'][0].update(owner_id='D8A79F1E-8AA2-4C6C-96F0-147ECB423CEB'))
    def test_wrong_ledger_work_branch_namespace(self):
        self.rejected(lambda st,c: st['history_id_reservations']['entries'][0].update(work_branch='refs/heads/other'))
    def test_bad_ledger_work_id_cannot_claim_history(self):
        self.rejected(lambda st,c: st['history_id_reservations']['entries'][0].update(work_id='x'))
    def test_wrong_ledger_work_branch_type(self):
        self.rejected(lambda st,c: st['history_id_reservations']['entries'][0].update(work_branch=None))
    def test_bad_ledger_owner_type(self):
        self.rejected(lambda st,c: st['history_id_reservations']['entries'][0].update(owner_id=1))
    def test_bad_snapshot_source_branch_format(self):
        self.rejected(lambda st,c: c.update(source_branch='../../secret'),'BLOCK_BAD_SNAPSHOT')
    def test_ledger_bad_future_epoch(self):
        self.rejected(lambda st,c: st['history_id_reservations']['entries'][0].update(epoch=999999),'BLOCK_INVALID_LEDGER')
    def test_ledger_record_not_after_coordinator_generation(self):
        st,claim=sample();st['epoch']=1
        res=reconcile_publications(st,['C00172','C00173'],[claim])
        self.assertEqual(res['status'],'BLOCK_INVALID_LEDGER')
    def test_cross_epoch_provenance_never_grants_write(self):
        st,claim=sample();st['history_id_reservations']['entries'][0]['epoch']=300
        res=reconcile_publications(st,['C00172','C00173'],[claim])
        self.assertEqual(res['status'],'BLOCK_PROVENANCE_MISMATCH')
        self.assertFalse(res['may_write'])
if __name__=='__main__':unittest.main()
