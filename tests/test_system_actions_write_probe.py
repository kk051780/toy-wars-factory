"""No network, no GitHub writes, fail-closed controls for manual capability probe."""
from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from urllib import error

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
try:
    import repair_control
except ImportError:
    # Local-only shim; GitHub CI exercises the genuine main repair_control import.
    shim=types.ModuleType('repair_control')
    def acq(state,kind,owner_id,now,**kwargs):
        if state['holder'] is not None: return {'action':'WAIT_LOCK','write':False}
        s=deepcopy(state);s['epoch']+=1;s['holder']={'kind':kind,'owner_id':owner_id,'epoch':s['epoch'],
            'acquired_at':now,'expires_at':'2099-01-01T00:00:00+00:00',**kwargs}
        return {'action':'ACQUIRE','write':True,'state':s}
    def own(state,kind,owner_id,epoch,now):
        h=state.get('holder');return bool(h and (h['kind'],h['owner_id'],h['epoch'])==(kind,owner_id,epoch))
    def rel(state,kind,owner_id,epoch,now):
        if not own(state,kind,owner_id,epoch,now):raise ValueError('not owner')
        s=deepcopy(state);s['holder']=None;s['last_completed']={'kind':kind,'owner_id':owner_id,'epoch':epoch,'released_at':now};return s
    shim.acquire=acq;shim.owns=own;shim.release=rel;shim.validate=lambda s:s
    sys.modules['repair_control']=shim
import system_actions_write_probe as p

SHA='a'*40
BASE_ENV={
    'GITHUB_REPOSITORY':p.REPO,'GITHUB_REPOSITORY_ID':str(p.REPO_ID),
    'GITHUB_ACTOR':p.ACTOR,'GITHUB_TRIGGERING_ACTOR':p.ACTOR,'GITHUB_EVENT_NAME':'workflow_dispatch',
    'GITHUB_REF':'refs/heads/main',
    'GITHUB_WORKFLOW_REF':p.REPO+'/'+p.WORKFLOW+'@refs/heads/main',
    'GITHUB_RUN_ID':'41199998877','GITHUB_RUN_ATTEMPT':'1',
    'GITHUB_SHA':SHA,'PROBE_CONSENT':p.CONSENT
}
BASE_RUN={'id':41199998877,'run_attempt':1,'event':'workflow_dispatch',
          'path':p.WORKFLOW,'head_repository':{'id':p.REPO_ID},
          'actor':{'login':p.ACTOR},'triggering_actor':{'login':p.ACTOR},'head_branch':'main','head_sha':SHA}

class ContextTests(unittest.TestCase):
    def test_positive_context(self):
        s=p.checked_context(BASE_ENV, BASE_RUN, SHA)
        self.assertTrue(s['owner'])
        self.assertEqual(s['branch'],'controller/gha-write-probe-41199998877-a1')
        self.assertEqual(s['main'],SHA)
        self.assertEqual(s['run_id'],41199998877)
        self.assertEqual(s['attempt'],1)
    def test_stable_separate_run_owner(self):
        x=p.checked_context(BASE_ENV,BASE_RUN,SHA)
        self.assertEqual(x['owner'],p.checked_context(BASE_ENV,BASE_RUN,SHA)['owner'])
        y={**BASE_ENV,'GITHUB_RUN_ID':'41199998878'};r={**BASE_RUN,'id':41199998878}
        self.assertNotEqual(x['owner'],p.checked_context(y,r,SHA)['owner'])
    def test_all_security_env_required(self):
        for key in BASE_ENV:
            with self.subTest(key=key),self.assertRaises(p.ProbeError):
                d=dict(BASE_ENV);d.pop(key);p.checked_context(d,BASE_RUN,SHA)
    def test_all_security_env_bad_type(self):
        for key in BASE_ENV:
            with self.subTest(key=key),self.assertRaises(p.ProbeError):
                d=dict(BASE_ENV);d[key]=None;p.checked_context(d,BASE_RUN,SHA)
    def test_all_security_env_mismatches(self):
        changes={'GITHUB_REPOSITORY':'foreign/foo','GITHUB_REPOSITORY_ID':'1',
            'GITHUB_ACTOR':'stranger','GITHUB_TRIGGERING_ACTOR':'stranger','GITHUB_EVENT_NAME':'schedule',
            'GITHUB_REF':'refs/heads/dev','GITHUB_WORKFLOW_REF':p.REPO+'/'+p.WORKFLOW+'@refs/heads/dev',
            'GITHUB_RUN_ID':'0','GITHUB_RUN_ATTEMPT':'0','GITHUB_SHA':'b'*40,
            'PROBE_CONSENT':'yes'}
        for key,value in changes.items():
            with self.subTest(key=key),self.assertRaises(p.ProbeError):
                p.checked_context({**BASE_ENV,key:value},BASE_RUN,SHA)
    def test_bad_main_ref(self):
        with self.assertRaises(p.ProbeError):p.checked_context(BASE_ENV,BASE_RUN,'b'*40)
    def test_live_run_required(self):
        for key,value in {'id':5,'run_attempt':2,'event':'push','path':'wrong',
            'head_repository':{'id':99},'actor':{'login':'foreign'},'triggering_actor':{'login':'foreign'},
            'head_branch':'different','head_sha':'b'*40}.items():
            with self.subTest(key=key),self.assertRaises(p.ProbeError):
                p.checked_context(BASE_ENV,{**BASE_RUN,key:value},SHA)
    def test_nonmapping_provider_denied(self):
        for row in [None,[],'hello']:
            with self.subTest(row=str(row)),self.assertRaises(p.ProbeError):
                p.checked_context(BASE_ENV,row,SHA)
    def test_negative_run_tokens(self):
        for key,value in [('GITHUB_RUN_ID','1e3'),('GITHUB_RUN_ID','-7'),('GITHUB_RUN_ID','12345678901234567890'),
                         ('GITHUB_RUN_ATTEMPT','2'),('GITHUB_SHA','0xabc')]:
            with self.subTest(key=key,value=value),self.assertRaises(p.ProbeError):
                p.checked_context({**BASE_ENV,key:value},BASE_RUN,SHA)

class FakeResponse:
    def __init__(self, body):self.body=json.dumps(body).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return None
    def read(self,n):return self.body[:n]

class ApiTests(unittest.TestCase):
    def test_api_rejects_untrusted_url_and_method(self):
        a=p.GitHubAPI('secret-token',lambda *a,**k:FakeResponse({}))
        for method,suffix in [('DELETE','/git/refs/heads/main'),('GET','https://evil.com'),('GET','/git/../refs'),
                              ('GET','/git/refs/%0A'),('GET','/git/refs/../../issues'),('GET','/git/refs/ a')]:
            with self.subTest(method=method,suffix=suffix),self.assertRaises(p.ProbeError):
                a.call(method,suffix)
    def test_api_token_does_not_appear_in_error(self):
        def reject(*args,**kwargs):raise error.HTTPError('x',403,'token_is_abc',None,None)
        a=p.GitHubAPI('token_is_abc',reject)
        with self.assertRaises(p.ProbeError) as ex:a.call('GET','/git/ref/heads/main')
        self.assertEqual(str(ex.exception),'GITHUB_HTTP_403')
    def test_api_valid_result(self):
        captured=[]
        def reply(req,timeout):captured.append(req);return FakeResponse({'ok':1})
        a=p.GitHubAPI('secret',reply)
        self.assertEqual(a.call('PUT','/contents/ops/probes/file.json',{'content':'YWJj'}),{'ok':1})
        self.assertEqual(captured[0].get_method(),'PUT')
        self.assertEqual(captured[0].get_header('Authorization'),'Bearer secret')
        self.assertEqual(captured[0].full_url,'https://api.github.com/repos/'+p.REPO+'/contents/ops/probes/file.json')
    def test_api_no_empty_token(self):
        with self.assertRaises(p.ProbeError):p.GitHubAPI('')
    def test_api_blocks_json_list(self):
        a=p.GitHubAPI('token',lambda *a,**k:FakeResponse([]))
        with self.assertRaises(p.ProbeError):a.call('GET','/git/ref/heads/main')

class FakeAPI:
    def __init__(self):self.calls=[];self.main=SHA
    def call(self,method,path,body=None):
        self.calls.append((method,path,deepcopy(body)))
        if method=='GET' and path=='/git/ref/heads/main':return {'object':{'sha':self.main}}
        if method=='GET' and path=='/git/ref/heads/'+p.CONTROL_REF:return {'object':{'sha':'b'*40}}
        if method=='POST' and path=='/git/refs':return {'ref':body['ref']}
        if method=='PUT' and path.startswith('/contents/ops/probes/'):return {'commit':{'sha':'c'*40}}
        if method=='POST' and path=='/pulls':return {'number':123}
        raise AssertionError((method,path))

class BranchTests(unittest.TestCase):
    def setUp(self):self.api=FakeAPI();self.scope=p.checked_context(BASE_ENV,BASE_RUN,SHA)
    def test_exact_immutable_probe_scope(self):
        no=p.create_branch_probe(self.api,self.scope)
        self.assertEqual(no,123)
        self.assertEqual([x[0] for x in self.api.calls],['GET','POST','PUT','POST'])
        write=self.api.calls[2]
        self.assertIn('/contents/ops/probes/',write[1]);self.assertEqual(write[2]['branch'],self.scope['branch'])
        decoded=json.loads(base64.b64decode(write[2]['content']))
        self.assertEqual(decoded['status'],'NO_AI_NO_GAME_CHANGE')
        self.assertEqual(decoded['source_main_sha'],SHA)
        self.assertNotIn('token',json.dumps(decoded).lower())
        self.assertTrue(self.api.calls[3][2]['draft'])
        self.assertEqual(self.api.calls[3][2]['base'],'main')
        self.assertEqual(self.api.calls[3][2]['head'],self.scope['branch'])
    def test_stale_main_no_write(self):
        self.api.main='f'*40
        with self.assertRaisesRegex(p.ProbeError,'MAIN_CHANGED'):
            p.create_branch_probe(self.api,self.scope)
        self.assertEqual([x[0] for x in self.api.calls],['GET'])
    def test_failed_create_branch_no_file(self):
        def bad(method,path,body=None):
            self.api.calls.append((method,path,body))
            if method=='GET':return {'object':{'sha':SHA}}
            raise p.ProbeError('GITHUB_HTTP_403')
        self.api.call=bad
        with self.assertRaises(p.ProbeError):p.create_branch_probe(self.api,self.scope)
        self.assertEqual(len(self.api.calls),2)
    def test_malformed_pr_no_approval(self):
        old=self.api.call
        def bad(method,path,body=None):
            if method=='POST' and path=='/pulls':self.api.calls.append((method,path,body));return {'number':'123'}
            return old(method,path,body)
        self.api.call=bad
        with self.assertRaisesRegex(p.ProbeError,'PR_RESPONSE_UNVERIFIED'):
            p.create_branch_probe(self.api,self.scope)

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow=(ROOT/'.github/workflows/twf-actions-write-capability-probe.yml').read_text()
    def test_manual_only_no_schedule_or_pull_request(self):
        self.assertIn('  workflow_dispatch:',self.workflow)
        self.assertNotIn('  schedule:',self.workflow)
        self.assertNotIn('  pull_request:',self.workflow)
        self.assertNotIn('  push:',self.workflow)
    def test_permissions_are_explicit_and_scoped(self):
        self.assertIn('  contents: write',self.workflow)
        self.assertIn('  pull-requests: write',self.workflow)
        self.assertIn('  actions: read',self.workflow)
        self.assertNotIn('  id-token: write',self.workflow)
    def test_operator_actor_main_and_phrase_gates(self):
        for piece in ["github.actor == 'kk051780'","github.triggering_actor == 'kk051780'","github.ref == 'refs/heads/main'",
            "github.event_name == 'workflow_dispatch'",p.CONSENT,
            "github.repository == 'kk051780/toy-wars-factory'"]:
            self.assertIn(piece,self.workflow)
    def test_no_autonomous_expensive_actions(self):
        for piece in ['gemini ', 'openai ', 'gh aw run', 'npm run publish', 'roblox publish']:
            self.assertNotIn(piece,self.workflow.lower())
    def test_checkout_does_not_persist_token(self):
        self.assertIn('persist-credentials: false',self.workflow)
    def test_reviewed_source_only(self):
        self.assertIn('python3 tools/system_actions_write_probe.py',self.workflow)
        self.assertNotIn('curl ',self.workflow)

class CoordinatorTests(unittest.TestCase):
    def test_claim_immutable_parent_and_force_false(self):
        old='b'*40;new='d'*40;seen=[];pinned={'schema':1,'task_id':'6adbf0d6a7d881918ce181dff2468867',
          'epoch':22,'holder':None,'authorized_tasks':{'CONTROLLER':'none'}}
        class API:
            def call(self,method,path,body=None):
                seen.append((method,path,deepcopy(body)))
                if (method,path)==('GET','/git/commits/'+old):return {'tree':{'sha':'e'*40}}
                if (method,path)==('POST','/git/blobs'):return {'sha':'f'*40}
                if (method,path)==('POST','/git/trees'):return {'sha':'a'*40}
                if (method,path)==('POST','/git/commits'):return {'sha':new}
                if (method,path)==('PATCH','/git/refs/heads/'+p.CONTROL_REF):return {'object':{'sha':new}}
                if (method,path)==('GET','/git/ref/heads/'+p.CONTROL_REF):return {'object':{'sha':new}}
                if (method,path)==('GET','/contents/'+p.CONTROL_PATH+'?ref='+new):
                    return {'encoding':'base64','type':'file',
                        'content':base64.b64encode((json.dumps(pinned,indent=2)+'\n').encode()).decode()}
                raise AssertionError((method,path))
        self.assertEqual(p.cas_state(API(),old,pinned),new)
        self.assertEqual([x[0] for x in seen],['GET','POST','POST','POST','PATCH','GET','GET'])
        self.assertEqual(seen[3][2]['parents'],[old])
        self.assertEqual(seen[4][2],{'sha':new,'force':False})
        self.assertEqual(seen[2][2]['base_tree'],'e'*40)
    def test_postread_not_matching_fails(self):
        old='b'*40
        class API:
            def call(self,method,path,body=None):
                if method=='GET' and path=='/git/commits/'+old:return {'tree':{'sha':'e'*40}}
                if method=='POST':return {'sha':'c'*40}
                if method=='PATCH':return {}
                if method=='GET' and path.startswith('/git/ref/'):return {'object':{'sha':'f'*40}}
                raise AssertionError((method,path))
        with self.assertRaisesRegex(p.ProbeError,'CONTROL_CAS_READBACK_UNCONFIRMED'):
            p.cas_state(API(),old,{})
    def test_no_invalid_ref_sha(self):
        class API:
            def call(self,*a,**kw):return {'object':{'sha':'notasha'}}
        with self.assertRaisesRegex(p.ProbeError,'REF_INVALID'):p.sha_ref(API(),'main')
    def test_malformed_state_file_denied(self):
        class API:
            def call(self,*a,**kw):return {'encoding':'base64','type':'file','content':'@@@'}
        with self.assertRaisesRegex(p.ProbeError,'STATE_INVALID'):p.state_at(API(),'b'*40)
    def test_untrusted_json_state_role_denied(self):
        class API:
            def call(self,*a,**kw):return {'encoding':'base64','type':'file',
                'content':base64.b64encode(b'[]').decode()}
        with self.assertRaises(p.ProbeError):p.state_at(API(),'b'*40)
    def test_no_claim_if_invalid_consent_no_api(self):
        class API:
            def call(self,*args):raise AssertionError('unexpected network call')
        with self.assertRaisesRegex(p.ProbeError,'CONSENT_MISSING'):
            p.run(API(),{**BASE_ENV,'PROBE_CONSENT':'wrong'})
    def test_busy_coordinator_never_attempts_source_write(self):
        class API:
            def __init__(self):self.calls=[]
            def call(self,method,path,body=None):
                self.calls.append((method,path))
                if path.startswith('/actions/runs/'):return BASE_RUN
                if path=='/git/ref/heads/main':return {'object':{'sha':SHA}}
                if path=='/git/ref/heads/'+p.CONTROL_REF:return {'object':{'sha':'b'*40}}
                if path.startswith('/contents/'):
                    data={'schema':1,'task_id':p.__dict__.get('TASK_ID','6adbf0d6a7d881918ce181dff2468867'),
                          'epoch':2,'holder':{'kind':'CONTROLLER','owner_id':'c'*36,'epoch':2,
                            'acquired_at':'2026-10-31T00:00:00+00:00','expires_at':'2099-01-01T00:00:00+00:00'},
                          'authorized_tasks':{'CONTROLLER':'none'}}
                    return {'encoding':'base64','type':'file',
                        'content':base64.b64encode(json.dumps(data).encode()).decode()}
                raise AssertionError((method,path))
        a=API()
        with patch.object(p,'acquire',return_value={'action':'WAIT_LOCK','write':False}):
            self.assertEqual(p.run(a,BASE_ENV),{'status':'WAIT_COORDINATOR','pr':None,'wrote':False})
        self.assertEqual([m for m,_ in a.calls],['GET','GET','GET','GET'])

if __name__=='__main__':unittest.main()