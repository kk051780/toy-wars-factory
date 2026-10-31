import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'tools'))
from system_history_reservation import advise
SHA='a'*40;REF='b'*40;OWNER='d8a79f1e-8aa2-4c6c-96f0-147ecb423ceb';BRANCH='controller/history-allocator-d8a79f1e';NOW='2026-10-31T00:03:00Z'
def state():
 return {'schema':1,'epoch':302,'authorized_tasks':{'WORKER':'6adbf0d6a7d881918ce181dff2468867'}, 'holder':{'kind':'CONTROLLER','owner_id':OWNER,'task_id':None,'origin':'controller','work_branch':BRANCH,'epoch':302,'base_main_sha':SHA,'acquired_at':'2026-10-31T00:00:00Z','expires_at':'2026-10-31T00:10:00Z'},'history_id_reservations':{'schema':1,'high_watermark':172,'entries':[]}}
def call(s=None,**kw):
 a=dict(expected_ref=REF,owner_id=OWNER,work_branch=BRANCH,work_id='TWF_HISTORY_ID_REPAIR',occupied_ids=['C00171','C00172'],main_sha=SHA,amount=2,now=NOW);a.update(kw);return advise(state() if s is None else s,**a)
class Cases(unittest.TestCase):
 def denied(self,code,mutate=None,kwargs=None):
  s=state()
  if mutate:mutate(s)
  self.assertEqual(call(s,**(kwargs or {}))['status'],code)
 def test_valid_is_advice_not_grant(self):
  r=call();self.assertEqual(r['suggested_ids'],['C00173','C00174'])
  for k in ('may_claim','may_write','may_merge','may_create_pr','provider_attested','cas_performed','may_retry'):self.assertFalse(r[k])
 def test_pure_no_mutate(self):
  s=state();z=copy.deepcopy(s);call(s);self.assertEqual(s,z)
 def test_atomic_receipt_proposal(self):
  r=call();s=r['proposed_state'];self.assertEqual(s['history_id_reservations']['high_watermark'],174);self.assertEqual(len(s['history_id_reservations']['entries']),2)
 def test_reservation_replay_no_reissue(self):
  s=call()['proposed_state'];r=call(s,occupied_ids=['C00172']);self.assertEqual(r['status'],'JOIN_RESERVED_NO_REISSUE');self.assertEqual(r['reserved_ids'],['C00173','C00174']);self.assertFalse(r['may_write'])
 def test_high_external_id_advances_monotonic(self): self.assertEqual(call(occupied_ids=['C00205'])['suggested_ids'],['C00206','C00207'])
 def test_broken_ref(self): self.denied('BLOCK_BAD_SHA',kwargs={'expected_ref':'f'*39})
 def test_bad_main(self): self.denied('BLOCK_BAD_SHA',kwargs={'main_sha':'bad'})
 def test_wrong_owner(self): self.denied('BLOCK_OWNER_OR_MAIN_CHANGED',kwargs={'owner_id':'31a79f1e-8aa2-4c6c-96f0-147ecb423ceb'})
 def test_wrong_branch(self): self.denied('BLOCK_OWNER_OR_MAIN_CHANGED',kwargs={'work_branch':'controller/another'})
 def test_wrong_epoch(self): self.denied('BLOCK_OWNER_OR_MAIN_CHANGED',mutate=lambda s:s.update(epoch=303))
 def test_bool_epoch(self): self.denied('BLOCK_BAD_COORD',mutate=lambda s:s.update(epoch=True))
 def test_wrong_main_holder(self): self.denied('BLOCK_OWNER_OR_MAIN_CHANGED',mutate=lambda s:s['holder'].update(base_main_sha='f'*40))
 def test_expired(self): self.denied('BLOCK_EXPIRED_OR_TIME_TRAVEL',kwargs={'now':'2026-10-31T00:10:00Z'})
 def test_before_acquired(self): self.denied('BLOCK_EXPIRED_OR_TIME_TRAVEL',kwargs={'now':'2026-10-30T23:59:59Z'})
 def test_naive_time(self): self.denied('BLOCK_TIME',kwargs={'now':'2026-10-31T00:03:00'})
 def test_no_holder(self): self.denied('BLOCK_NO_AUTHOR_LEASE',mutate=lambda s:s.update(holder=None))
 def test_dispatch_cannot_author(self): self.denied('BLOCK_NO_AUTHOR_LEASE',mutate=lambda s:s['holder'].update(kind='DISPATCH'))
 def test_reviewer_cannot_author(self): self.denied('BLOCK_NO_AUTHOR_LEASE',mutate=lambda s:s['holder'].update(kind='REVIEWER'))
 def test_no_ledger_needs_bootstrap(self): self.denied('WAIT_VERIFIED_BOOTSTRAP',mutate=lambda s:s.pop('history_id_reservations'))
 def test_duplicate_external_is_reported_but_new_unique_reservation_can_be_planned(self):
  x=call(occupied_ids=['C00159','C00160','C00160','C00161','C00161','C00162','C00172']);self.assertEqual(x['status'],'PREPARE_SINGLE_PARENT_CAS_ONLY_NOT_AUTHORIZED');self.assertEqual(x['legacy_collision_ids'],['C00160','C00161']);self.assertTrue(x['legacy_collisions_unresolved']);self.assertEqual(x['suggested_ids'],['C00173','C00174']);self.assertFalse(x['may_write'])
 def test_bad_external(self): self.denied('BLOCK_OCCUPIED_SET',kwargs={'occupied_ids':['C0017X']})
 def test_duplicate_ledger_entry(self):
  s=call()['proposed_state'];s['history_id_reservations']['entries'].append(copy.deepcopy(s['history_id_reservations']['entries'][0]))
  self.assertEqual(call(s,occupied_ids=['C00172'])['status'],'BLOCK_DUPLICATE_LEDGER_ID')
 def test_existing_ledger_and_source_overlap_needs_reconcile(self):
  s=call()['proposed_state'];self.assertEqual(call(s,occupied_ids=['C00173'])['status'],'WAIT_RECONCILE_EXISTING_IDS')
 def test_cross_branch_work_reuse_blocked(self):
  s=call()['proposed_state'];s['history_id_reservations']['entries'][0]['work_branch']='controller/foreign'
  self.assertEqual(call(s,occupied_ids=['C00172'])['status'],'BLOCK_CROSS_BRANCH_WORK_ID')
 def test_missing_work_id(self): self.denied('BLOCK_BAD_WORK',kwargs={'work_id':''})
 def test_bad_branch(self): self.denied('BLOCK_BAD_WORK',kwargs={'work_branch':'../../escape'})
 def test_boolean_amount(self): self.denied('BLOCK_BAD_AMOUNT',kwargs={'amount':True})
 def test_zero_amount(self): self.denied('BLOCK_BAD_AMOUNT',kwargs={'amount':0})
 def test_five_amount(self): self.denied('BLOCK_BAD_AMOUNT',kwargs={'amount':5})
 def test_exhausted(self): self.denied('BLOCK_EXHAUSTED',kwargs={'occupied_ids':['C99999']})
 def test_wrong_ledger_counter(self): self.denied('BLOCK_LEDGER_SCHEMA',mutate=lambda s:s['history_id_reservations'].update(high_watermark='172'))
 def test_watermark_below_entry_block(self):
  s=call()['proposed_state'];s['history_id_reservations']['high_watermark']=172
  self.assertEqual(call(s,occupied_ids=['C00172'])['status'],'BLOCK_LEDGER_WATERMARK')
 def test_worker_must_registered(self): self.denied('BLOCK_UNREGISTERED_AUTHOR',mutate=lambda s:s['holder'].update(kind='WORKER',task_id='bad'))
if __name__=='__main__':unittest.main()
