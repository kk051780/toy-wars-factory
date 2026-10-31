"""Protected pure-state Open Cloud reservation regressions; no Roblox/GitHub writes."""
import copy,importlib.util,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'tools'/'cloud_global_intent_fence.py'
spec=importlib.util.spec_from_file_location('cloud_global_intent_fence',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
OWNER='4c8d111d-2456-4959-aa5b-219fc7d43546'; MAIN='e5deff4d5681bca4823a3da0f848e01bc089ae6e'; REF='1'*40
AT='2026-10-31T01:30:00Z'
def state():
 return {'schema':1,'task_id':m.TASK_ID,'epoch':306,'holder':{'kind':'CONTROLLER','owner_id':OWNER,'task_id':None,'epoch':306,'acquired_at':'2026-10-31T01:23:55Z','expires_at':'2026-10-31T01:48:55Z','base_main_sha':MAIN,'work_branch':'controller/roblox-cloud-cas-4c8d111d','origin':'controller'},'last_completed':{'epoch':305},'administrative_revocations':[{'do_not_touch':True}]}
def request(**kwargs):
 r={'repository':m.REPO,'source_main_sha':MAIN,'artifact_zip_sha256':'2'*64,'rbxlx_sha256':'3'*64,'luau_sha256':'4'*64,'universe_id':123,'place_id':456,'version_id':7,'intent_type':'HEADLESS_SERVER_SMOKE_V1'};r.update(kwargs);return r
def propose(s=None,r=None):
 return m.propose(s if s is not None else state(),r if r is not None else request(),owner_id=OWNER,epoch=306,now=AT,expected_ref=REF)
class SourceContract(unittest.TestCase):
 def assertBlock(self,fn):
  with self.assertRaises(m.Blocked):fn()
 def test_candidate_has_no_authority(self):
  p=propose();self.assertFalse(p['post_authorized']);self.assertFalse(p['provider_attested']);self.assertFalse(p['main_merge_authorized'])
 def test_preserve_unrelated(self):
  s=state();p=propose(s);self.assertEqual(p['next_state']['last_completed'],s['last_completed']);self.assertEqual(p['next_state']['administrative_revocations'],s['administrative_revocations'])
 def test_dedup_exact(self):
  s=propose()['next_state'];self.assertBlock(lambda:propose(s))
 def test_dedup_new_script_same_version(self):
  s=propose()['next_state'];self.assertBlock(lambda:propose(s,request(luau_sha256='5'*64)))
 def test_distinct_version(self):
  s=propose()['next_state'];self.assertEqual(len(propose(s,request(version_id=8))['next_state'][m.FIELD]),2)
 def test_bad_role(self):
  s=state();s['holder']['kind']='WORKER';self.assertBlock(lambda:propose(s))
 def test_bad_main(self):self.assertBlock(lambda:propose(r=request(source_main_sha='a'*40)))
 def test_bad_destination(self):self.assertBlock(lambda:propose(r=request(universe_id=True)))
 def test_expired(self):
  s=state();s['holder']['expires_at']='2026-10-31T01:29:00Z';self.assertBlock(lambda:propose(s))
 def test_bad_owner(self):
  s=state();s['holder']['owner_id']='00000000-0000-4000-8000-000000000000';self.assertBlock(lambda:propose(s))
 def test_bad_epoch(self):
  s=state();s['epoch']=307;self.assertBlock(lambda:propose(s))
 def test_bad_branch(self):
  s=state();s['holder']['work_branch']='controller/other';self.assertBlock(lambda:propose(s))
 def test_bad_schema(self):
  s=state();s['schema']=True;self.assertBlock(lambda:propose(s))
 def test_bad_ledger(self):
  s=propose()['next_state'];s[m.FIELD][0]['phase']='REPLAY_ALLOWED';self.assertBlock(lambda:propose(s))
 def test_readback_with_matching_commit_is_still_no_authority(self):
  p=propose();r=m.confirm_readback(p,actual_ref='6'*40,cas_ack_ref='6'*40,actual_state=copy.deepcopy(p['next_state']),current_holder_state=copy.deepcopy(p['next_state']),owner_id=OWNER,epoch=306,now=AT);self.assertFalse(r['post_authorized']);self.assertFalse(r['github_provider_authenticated'])
 def test_lost_cas_ack(self):
  p=propose();self.assertBlock(lambda:m.confirm_readback(p,actual_ref='6'*40,cas_ack_ref='7'*40,actual_state=p['next_state'],current_holder_state=p['next_state'],owner_id=OWNER,epoch=306,now=AT))
 def test_forged_readback(self):
  p=propose();self.assertBlock(lambda:m.confirm_readback(p,actual_ref='6'*40,cas_ack_ref='6'*40,actual_state=state(),current_holder_state=p['next_state'],owner_id=OWNER,epoch=306,now=AT))
if __name__=='__main__':unittest.main()
