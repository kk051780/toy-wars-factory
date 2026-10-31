import base64
from copy import deepcopy
import importlib.util
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import unittest
from urllib.error import HTTPError
from urllib.request import Request

M = Path(__file__).resolve().parents[1] / 'tools/manual_controller_claim_witness.py'
spec = importlib.util.spec_from_file_location('manual_controller_claim_witness', M)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

OWNER='173516b8-1a60-42e5-b93b-76eb5f63f912'
SRC='controller/protected-system-'+OWNER
CLAIM='a'*40
PARENT='b'*40
MAIN='c'*40
REF='refs/heads/twf-repair-coordinator'


def fixture():
    before={'schema':1,'epoch':19,'holder':None,'last_completed':{'previous':'preserve'},'authorized_tasks':{'REVIEWER':'do_not_modify'}}
    after=deepcopy(before)
    after['epoch']=20
    after['holder']={
        'kind':'CONTROLLER','owner_id':OWNER,'task_id':None,'epoch':20,
        'acquired_at':'2026-10-31T01:15:00Z','expires_at':'2026-10-31T01:38:00Z',
        'base_main_sha':MAIN,'work_branch':SRC,'origin':'controller'}
    return before,after


def encoded(state):
    raw=json.dumps(state).encode()
    git_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    return {'type':'file','encoding':'base64','size':len(raw),'sha':git_sha,
            'content':base64.b64encode(raw).decode()}


class Fake:
    def __init__(self):
        before,after=fixture()
        parent_file, child_file = encoded(before), encoded(after)
        parent_tree_sha, claim_tree_sha = 'd'*40, 'e'*40
        shared = [
            {'path':'.github','type':'tree','mode':'040000','sha':'1'*40},
            {'path':'README.md','type':'blob','mode':'100644','sha':'2'*40},
        ]
        def tree(tree_sha, ops_sha, blob_sha):
            return {'sha':tree_sha,'truncated':False,'tree':deepcopy(shared) + [
                {'path':'ops','type':'tree','mode':'040000','sha':ops_sha},
                {'path':'ops/REPAIR_COORDINATOR.json','type':'blob','mode':'100644','sha':blob_sha},
            ]}
        self.items={
            '/git/ref/heads/twf-repair-coordinator':{'ref':REF,'object':{'sha':CLAIM}},
            '/git/ref/heads/main':{'ref':'refs/heads/main','object':{'sha':MAIN}},
            '/git/commits/'+CLAIM:{'sha':CLAIM,'parents':[{'sha':PARENT}],'tree':{'sha':claim_tree_sha}},
            '/git/commits/'+PARENT:{'sha':PARENT,'parents':[{'sha':'f'*40}],'tree':{'sha':parent_tree_sha}},
            '/contents/ops/REPAIR_COORDINATOR.json?ref='+PARENT:parent_file,
            '/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM:child_file,
            '/git/trees/'+parent_tree_sha+'?recursive=1':tree(parent_tree_sha,'3'*40,parent_file['sha']),
            '/git/trees/'+claim_tree_sha+'?recursive=1':tree(claim_tree_sha,'4'*40,child_file['sha']),
            '/git/ref/heads/'+SRC:None
        }
        self.calls=[]
        self.bad_status={}

    def get(self,path,*,allow_missing=False):
        self.calls.append((path,allow_missing))
        if path in self.bad_status:
            raise m.WitnessHold(self.bad_status[path])
        if path not in self.items:
            raise m.WitnessHold('UNEXPECTED_QUERY')
        value=self.items[path]
        if value is None and not allow_missing:
            raise m.WitnessHold('MISSING_DENIED')
        return deepcopy(value)


def check(provider=None,**kwargs):
    args={'claim_sha':CLAIM,'owner_id':OWNER,'epoch':20,
          'source_branch':SRC,'main_sha':MAIN,
          'event_name':'workflow_dispatch','event_ref':'refs/heads/main','event_sha':MAIN,
          'observed_at':datetime(2026,10,31,1,20,tzinfo=timezone.utc)}
    args.update(kwargs)
    return m.first_party_witness(provider or Fake(),**args)


class WitnessContract(unittest.TestCase):
    def blocked(self, callback,code=None):
        with self.assertRaises(m.WitnessHold) as r:callback()
        if code:self.assertEqual(str(r.exception),code)

    def test_positive_is_never_permission(self):
        r=check()
        self.assertEqual(r['status'],'CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY')
        for k in ['provider_authenticated','independent_review_authorized','merge_authorized','roblox_post_authorized']:
            self.assertIs(r[k],False)

    def test_read_last_is_branch_absence(self):
        f=Fake();check(f)
        self.assertEqual(f.calls[-1],('/git/ref/heads/'+SRC,True))
        self.assertEqual(len(f.calls),11)
        self.assertEqual([p for p,_ in f.calls].count('/git/ref/heads/twf-repair-coordinator'),2)
        self.assertEqual([p for p,_ in f.calls].count('/git/ref/heads/main'),2)

    def test_missing_claim_ref(self):
        f=Fake();f.items['/git/ref/heads/twf-repair-coordinator']={'ref':REF,'object':None}
        self.blocked(lambda:check(f),'CLAIM_NOT_LIVE_CURRENT_REF')

    def test_wrong_claim_sha(self):
        f=Fake();f.items['/git/ref/heads/twf-repair-coordinator']['object']['sha']='f'*40
        self.blocked(lambda:check(f),'CLAIM_NOT_LIVE_CURRENT_REF')

    def test_claim_missing_one_parent(self):
        f=Fake();f.items['/git/commits/'+CLAIM]['parents']=[]
        self.blocked(lambda:check(f),'CLAIM_PARENT_UNPROVEN')

    def test_claim_two_parents(self):
        f=Fake();f.items['/git/commits/'+CLAIM]['parents']=[{'sha':PARENT},{'sha':MAIN}]
        self.blocked(lambda:check(f),'CLAIM_PARENT_UNPROVEN')

    def test_wrong_commit_identity(self):
        f=Fake();f.items['/git/commits/'+CLAIM]['sha']='d'*40
        self.blocked(lambda:check(f),'CLAIM_PARENT_UNPROVEN')

    def test_before_busy(self):
        f=Fake();prior,_=fixture();prior['holder']={'kind':'WORKER'}
        f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+PARENT]=encoded(prior)
        self.blocked(lambda:check(f),'CLAIM_PARENT_BUSY')

    def test_old_epoch(self):
        f=Fake();a,b=fixture();a['epoch']=18
        f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+PARENT]=encoded(a)
        self.blocked(lambda:check(f),'CLAIM_PARENT_BUSY')

    def test_claim_additional_policy_change(self):
        f=Fake();a,b=fixture();b['authorized_tasks']['REVIEWER']='OVERRIDDEN'
        f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]=encoded(b)
        self.blocked(lambda:check(f),'CLAIM_MUTATED_UNRELATED_STATE')

    def test_claim_historical_audit_rewrite(self):
        f=Fake();a,b=fixture();b['last_completed']['previous']='spoofed'
        f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]=encoded(b)
        self.blocked(lambda:check(f),'CLAIM_MUTATED_UNRELATED_STATE')

    def test_wrong_owner(self):self.blocked(lambda:check(owner_id='00000000-0000-4000-8000-000000000001'),'UNIQUE_SOURCE_BRANCH_REQUIRED')
    def test_wrong_holder_owner(self):
        f=Fake();a,b=fixture();b['holder']['owner_id']='00000000-0000-4000-8000-000000000001';f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]=encoded(b)
        self.blocked(lambda:check(f),'CLAIM_OWNER_BINDING_FAIL')

    def test_wrong_epoch(self):self.blocked(lambda:check(epoch=21),'CLAIM_PARENT_BUSY')
    def test_bool_epoch(self):self.blocked(lambda:check(epoch=True),'INVALID_ACTOR')
    def test_wrong_main(self):self.blocked(lambda:check(main_sha='f'*40),'NOT_TRUSTED_MAIN_WORKFLOW')
    def test_wrong_workflow_event(self):self.blocked(lambda:check(event_name='pull_request'),'NOT_TRUSTED_MAIN_WORKFLOW')
    def test_workflow_running_on_pr_ref(self):self.blocked(lambda:check(event_ref='refs/pull/1/merge'),'NOT_TRUSTED_MAIN_WORKFLOW')
    def test_dispatch_wrong_sha(self):self.blocked(lambda:check(event_sha='e'*40),'NOT_TRUSTED_MAIN_WORKFLOW')
    def test_source_branch_exists(self):
        f=Fake();f.items['/git/ref/heads/'+SRC]={'ref':'refs/heads/'+SRC,'object':{'sha':MAIN}}
        self.blocked(lambda:check(f),'SOURCE_BRANCH_ALREADY_EXISTS')
    def test_wrong_source_branch(self):self.blocked(lambda:check(source_branch='controller/other'),'UNIQUE_SOURCE_BRANCH_REQUIRED')
    def test_claim_expiry_excessive(self):
        f=Fake();a,b=fixture();b['holder']['expires_at']='2026-10-31T04:38:00Z';f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]=encoded(b)
        self.blocked(lambda:check(f),'CLAIM_LEASE_INVALID')
    def test_claim_expiry_before_start(self):
        f=Fake();a,b=fixture();b['holder']['expires_at']='2026-10-31T00:38:00Z';f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]=encoded(b)
        self.blocked(lambda:check(f),'CLAIM_LEASE_INVALID')
    def test_main_changed_after_lease(self):
        f=Fake();f.items['/git/ref/heads/main']['object']['sha']='f'*40
        self.blocked(lambda:check(f),'BASE_MAIN_MOVED')
    def test_wrong_token_route(self):
        self.blocked(lambda:m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE').get('https://attacker.test/data'),'INVALID_API_ROUTE')
    def test_token_missing(self):self.blocked(lambda:m.ProviderReadOnly('bad'),'CREDENTIAL_MISSING')
    def test_redirect_blocked(self):
        handler=m.NoRedirect()
        self.blocked(lambda:handler.redirect_request(None,None,302,'redirect',{},'https://attacker.test/'),'REDIRECT_REFUSED')
    def test_github_absent_ref_404(self):
        def opener(req,timeout):raise HTTPError(req.full_url,404,'Not Found',{},None)
        t=m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE',opener=opener)
        self.assertIsNone(t.get('/git/ref/heads/'+SRC,allow_missing=True))
    def test_unrelated_404_is_denied(self):
        def opener(req,timeout):raise HTTPError(req.full_url,404,'Not Found',{},None)
        t=m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE',opener=opener)
        self.blocked(lambda:t.get('/git/commits/'+CLAIM),'PROVIDER_API_UNAVAILABLE_HOLD')
    def test_provider_403_not_absence(self):
        def opener(req,timeout):raise HTTPError(req.full_url,403,'Forbidden',{},None)
        t=m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE',opener=opener)
        self.blocked(lambda:t.get('/git/ref/heads/'+SRC,allow_missing=True),'PROVIDER_API_UNAVAILABLE_HOLD')
    def test_provider_429_not_absence(self):
        def opener(req,timeout):raise HTTPError(req.full_url,429,'Quota',{},None)
        t=m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE',opener=opener)
        self.blocked(lambda:t.get('/git/ref/heads/'+SRC,allow_missing=True),'PROVIDER_API_UNAVAILABLE_HOLD')
    def test_nan_provider_json_refused(self):
        self.blocked(lambda:m.parse_json(b'{"result":NaN}'),'INVALID_PROVIDER_JSON')
    def test_missing_flag_on_claim_ref_is_refused(self):
        t=m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE',opener=lambda *args,**kw:None)
        self.blocked(lambda:t.get('/git/ref/heads/twf-repair-coordinator',allow_missing=True),
                     'MISSING_ONLY_ALLOWED_FOR_UNCREATED_SOURCE_REF')
    def test_missing_flag_on_claim_commit_is_refused(self):
        t=m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE',opener=lambda *args,**kw:None)
        self.blocked(lambda:t.get('/git/commits/'+CLAIM,allow_missing=True),
                     'MISSING_ONLY_ALLOWED_FOR_UNCREATED_SOURCE_REF')
    def test_json_duplicate_key_denied(self):self.blocked(lambda:m.parse_json(b'{"epoch":1,"epoch":2}'))
    def test_bad_json_utf8_denied(self):self.blocked(lambda:m.parse_json(b'\xff'),'INVALID_PROVIDER_JSON')
    def test_oversized_response_denied(self):self.blocked(lambda:m.parse_json(b'a'*(m.MAX_BODY+1)),'INVALID_PROVIDER_PAYLOAD')
    def test_non_utf8_base64_denied(self):
        self.blocked(lambda:m.decode_file({'type':'file','encoding':'base64','content':'_not_valid'}))
    def test_not_dict_state_denied(self):
        self.blocked(lambda:m.decode_file(encoded(['wrong'])),'STATE_NOT_DICT')
    def test_timestamp_naive_denied(self):self.blocked(lambda:m.date('2026-10-31T12:00:00'),'INVALID_TIME')
    def test_invalid_sha_denied(self):self.blocked(lambda:check(claim_sha='NO_SHA'),'INVALID_SHA')
    def test_invalid_uuid_denied(self):self.blocked(lambda:check(owner_id='z'*36),'INVALID_ACTOR')
    def test_same_epoch_wrong_ref_is_hold(self):
        f=Fake();f.items['/git/ref/heads/twf-repair-coordinator']['object']['sha']='e'*40
        self.blocked(lambda:check(f),'CLAIM_NOT_LIVE_CURRENT_REF')
    def test_expired_at_witness_observation(self):
        self.blocked(lambda:check(observed_at=datetime(2026,10,31,1,39,tzinfo=timezone.utc)),
                     'LEASE_NOT_LIVE_AT_OBSERVATION')
    def test_naive_observation_time(self):
        self.blocked(lambda:check(observed_at=datetime(2026,10,31,1,20)),
                     'INVALID_OBSERVATION_TIME')
    def test_file_content_changed_after_sha(self):
        f=Fake();r=f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]
        r['content']=base64.b64encode(b'{"tampered":true}').decode()
        self.blocked(lambda:check(f),'FILE_BLOB_HASH_MISMATCH')
    def test_file_content_size_wrong(self):
        f=Fake();f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]['size']+=1
        self.blocked(lambda:check(f),'FILE_BLOB_HASH_MISMATCH')
    def test_invalid_base64_rejected(self):
        f=Fake();f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]['content']='NOT!VALID!BASE64'
        self.blocked(lambda:check(f),'FILE_ENVELOPE_MISMATCH')
    def test_repo_file_base64_newlines_accepted(self):
        f=Fake();r=f.items['/contents/ops/REPAIR_COORDINATOR.json?ref='+CLAIM]
        r['content']='\n'.join(r['content'][i:i+44] for i in range(0,len(r['content']),44))
        self.assertEqual(check(f)['status'],'CLAIM_OBSERVED_BRANCH_ABSENT_CANDIDATE_ONLY')
    def test_status_200_and_bounded_json(self):
        class Resp:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,n):return b'{"safe":true}'
        def opener(req,timeout):
            self.assertEqual(req.get_method(),'GET')
            self.assertEqual(req.full_url,m.API+'/git/commits/'+CLAIM)
            self.assertEqual(timeout,9)
            return Resp()
        t=m.ProviderReadOnly('TEST_TOKEN_ONLY_DONT_USE',opener=opener)
        self.assertEqual(t.get('/git/commits/'+CLAIM),{'safe':True})
        self.assertEqual(t.queries,1)

if __name__=='__main__':unittest.main()
