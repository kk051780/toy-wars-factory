"""PR157 publication seam tests (untrusted fake source, no network or authority)."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from system_history_reservation import advise
from system_history_publication_bridge import reconcile_publications
from test_system_history_reservation import state,call,OWNER,SHA,BRANCH,REF,NOW


def sample():
    candidate=call()
    ledger=candidate['proposed_state']
    content={'id':'C00173','date':'2026-10-31','kind':'TEST',
             'base_main_sha':SHA, 'work_id':'TWF_HISTORY_ID_REPAIR',
             'coordination':{'branch':'twf-repair-coordinator','owner_run_id':OWNER,'epoch':302,'claim_commit':'f'*40}}
    body=json.dumps(content,sort_keys=True)+'\n'
    raw=body.encode('utf-8')
    blob=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
    claim={'id':'C00173','path':'history/C00173_sample.json','source_branch':BRANCH,
           'source_main_sha':SHA,'blob_sha':blob,'body':body}
    return ledger, claim


class PublicationBridgeTests(unittest.TestCase):
    def test_actual_pr157_gets_stuck_after_publication(self):
        ledger,_=sample()
        self.assertEqual(call(ledger,work_id='NEXT_TASK_00001',occupied_ids=['C00172','C00173'])['status'], 'WAIT_RECONCILE_EXISTING_IDS')

    def test_canonical_source_match_is_only_a_candidate(self):
        state_,claim=sample()
        r=reconcile_publications(state_,['C00172','C00173'],[claim])
        self.assertEqual(r['status'],'MATCHED_CONSUMPTION_CANDIDATE_ONLY')
        self.assertEqual(r['matched_ids'],['C00173'])
        self.assertEqual(r['remaining_occupied_ids'],['C00172'])
        self.assertFalse(r['github_authenticated'])
        self.assertFalse(r['may_write'])
        self.assertFalse(r['may_retry'])
        self.assertEqual(call(state_,work_id='NEXT_TASK_00001',occupied_ids=r['remaining_occupied_ids'])['suggested_ids'],['C00175','C00176'])

    def test_unpublished_reservations_are_not_implicitly_consumed(self):
        st,claim=sample()
        r=reconcile_publications(st,['C00172','C00173'],[claim])
        self.assertEqual(r['still_reserved_ids'],['C00174'])

    def test_missing_publication_evidence_blocks(self):
        st,claim=sample()
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[])['status'],'BLOCK_INCOMPLETE_CLAIM_SNAPSHOT')

    def test_missing_claim_from_occupied_blocks(self):
        st,claim=sample()
        self.assertEqual(reconcile_publications(st,['C00172'],[claim])['status'],'BLOCK_INCOMPLETE_CLAIM_SNAPSHOT')

    def test_false_blob_hash_blocks(self):
        st,claim=sample();claim['blob_sha']='f'*40
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_BLOB_MISMATCH')

    def test_wrong_source_branch_blocks(self):
        st,claim=sample();claim['source_branch']='controller/another'
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PROVENANCE_MISMATCH')

    def test_wrong_owner_blocks(self):
        st,claim=sample()
        body=json.loads(claim['body']);body['coordination']['owner_run_id']='0'*8+'-'+ '0'*4+'-'+'0'*4+'-'+'0'*4+'-'+'0'*12
        claim=self.rehash(claim,body)
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PROVENANCE_MISMATCH')

    def test_wrong_epoch_blocks(self):
        st,claim=sample();body=json.loads(claim['body']);body['coordination']['epoch']=303
        claim=self.rehash(claim,body)
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PROVENANCE_MISMATCH')

    def test_wrong_main_blocks(self):
        st,claim=sample();body=json.loads(claim['body']);body['base_main_sha']='a'*39+'f'
        claim=self.rehash(claim,body)
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PROVENANCE_MISMATCH')

    def test_mismatched_embedded_id_blocks(self):
        st,claim=sample();body=json.loads(claim['body']);body['id']='C00174'
        claim=self.rehash(claim,body)
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PATH_OR_ID_MISMATCH')

    def test_changed_path_id_blocks(self):
        st,claim=sample();claim['path']='history/C00174_sample.json'
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PATH_OR_ID_MISMATCH')

    def test_duplicate_claims_for_reserved_id_blocks(self):
        st,claim=sample();other=copy.deepcopy(claim);other['path']='history/C00173_second.json'
        self.assertEqual(reconcile_publications(st,['C00172','C00173','C00173'],[claim,other])['status'],'BLOCK_RESERVED_ID_DUPLICATED')

    def test_identical_snapshot_count_but_duplicate_claims_blocks(self):
        st,claim=sample()
        self.assertEqual(reconcile_publications(st,['C00172','C00173','C00173'],[claim,copy.deepcopy(claim)])['status'],'BLOCK_RESERVED_ID_DUPLICATED')

    def test_no_ledger_fails_closed(self):
        st,claim=sample();del st['history_id_reservations']
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'WAIT_VERIFIED_BOOTSTRAP')

    def test_untrusted_scan_never_authorizes(self):
        st,claim=sample()
        r=reconcile_publications(st,['C00172','C00173'],[claim])
        for key in ('may_claim','may_write','may_merge','may_retry','cas_performed','github_authenticated','provider_attested'):
            self.assertFalse(r[key])

    def test_bad_source_main_requires_recheck(self):
        st,claim=sample();claim['source_main_sha']='a'*39+'f'
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PROVENANCE_MISMATCH')

    def test_no_claim_for_any_reserved_is_safe_but_not_authorized(self):
        st,_=sample()
        r=reconcile_publications(st,['C00172'],[])
        self.assertEqual(r['status'],'NO_CONSUMED_RESERVATIONS_CANDIDATE_ONLY')
        self.assertEqual(r['still_reserved_ids'],['C00173','C00174'])
        self.assertFalse(r['may_write'])

    def test_never_mutates_original_state_or_source(self):
        st,claim=sample();before_st=copy.deepcopy(st);before_claim=copy.deepcopy(claim)
        reconcile_publications(st,['C00172','C00173'],[claim])
        self.assertEqual(st,before_st)
        self.assertEqual(claim,before_claim)

    def test_double_key_history_json_denied(self):
        st,claim=sample();claim['body']=claim['body'].replace('"id": "C00173"','"id": "C00173", "id": "C00173"')
        raw=claim['body'].encode();claim['blob_sha']=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_INVALID_HISTORY_BODY')

    def test_ledger_watermark_less_than_record_blocks(self):
        st,claim=sample();st['history_id_reservations']['high_watermark']=172
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_INVALID_LEDGER')

    def test_duplicate_ledger_ids_blocks(self):
        st,claim=sample();st['history_id_reservations']['entries'].append(copy.deepcopy(st['history_id_reservations']['entries'][0]))
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_DUPLICATE_LEDGER')

    def test_nonfinite_history_json_denied(self):
        st,claim=sample();claim['body']=claim['body'][:-2]+', "evil": NaN}\n'
        raw=claim['body'].encode();claim['blob_sha']=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_INVALID_HISTORY_BODY')

    def test_bool_epoch_metadata_denied(self):
        st,claim=sample();body=json.loads(claim['body']);body['coordination']['epoch']=True
        claim=self.rehash(claim,body)
        self.assertEqual(reconcile_publications(st,['C00172','C00173'],[claim])['status'],'BLOCK_PROVENANCE_MISMATCH')

    @staticmethod
    def rehash(claim,body):
        changed=copy.deepcopy(claim)
        changed['body']=json.dumps(body,sort_keys=True)+'\n'
        raw=changed['body'].encode('utf-8')
        changed['blob_sha']=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
        return changed

if __name__=='__main__': unittest.main()
