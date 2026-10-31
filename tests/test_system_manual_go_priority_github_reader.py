"""Offline mock-only tests; NOT live original GitHub GET attestation."""
from __future__ import annotations
import base64
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from urllib import error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import system_manual_go_priority_github_reader as r
from tools import system_manual_go_priority_preflight as p

MAIN='e'*40
COORD='d'*40
STALE='a'*40
ID1='main_shutdown_sequential_save_deadline_20261028'
ID2='main_expired_lease_refresh_failure_unsavable_play_20261028'


def state():
    return {'schema':1,'task_id':p.WORKER_TASK,'epoch':326,'holder':None,
        'authorized_tasks':{'WORKER':p.WORKER_TASK},
        'manual_go_context':{'mode':'FENCED_DISPATCH_EXISTING_WORKER_ONLY',
            'next_actor':'REGISTERED_WORKER','source_main_sha':STALE,
            'priority_request_ids':[ID1,ID2]}}


def requests():
    return {'schema':1,'requests':[
        {'id':ID1,'status':'RESOLVED_MERGED_MAIN_QA_AND_HANDOFF_PASSED','assigned_role':'WORKER'},
        {'id':ID2,'status':'RESOLVED_MERGED_MAIN_QA_AND_HANDOFF_PASSED','assigned_role':'WORKER'}]}


def packed(path,value):
    raw=json.dumps(value,sort_keys=True).encode()
    return {'type':'file','path':path,'encoding':'base64','content':base64.b64encode(raw).decode(),
        'size':len(raw),'sha':r.gitsha(raw)}


class Fake:
    def __init__(self,*,changes=None):
        self.calls=[];self.changes=changes or {}
    def __call__(self,url):
        self.calls.append(url)
        n=len(self.calls)
        if n in self.changes:return self.changes[n]
        if url==r.ROOT:return {'id':r.REPO_ID,'full_name':r.REPO,'private':True}
        if url==f'{r.ROOT}/git/ref/heads/main':
            return {'ref':'refs/heads/main','object':{'sha':MAIN,'type':'commit'}}
        if url==f'{r.ROOT}/git/ref/heads/{r.CONTROL}':
            return {'ref':f'refs/heads/{r.CONTROL}','object':{'sha':COORD,'type':'commit'}}
        if url==f'{r.ROOT}/contents/{r.COORD_PATH}?ref={COORD}':return packed(r.COORD_PATH,state())
        if url==f'{r.ROOT}/contents/{r.REQUEST_PATH}?ref={COORD}':return packed(r.REQUEST_PATH,requests())
        raise AssertionError(url)

class ReadTests(unittest.TestCase):
    def test_original_shape_mock_detects_two_resolved_priorities(self):
        fake=Fake();res=r.collect_preflight(fake)
        self.assertEqual(len(fake.calls),7)
        self.assertEqual(res['status'],'WAIT_RESELECT_CURRENT_WORK')
        self.assertEqual(res['resolved_ids'],[ID2,ID1] if ID2<ID1 else [ID1,ID2])
        self.assertTrue(res['stale_main'])
        self.assertFalse(res['authority']['provider_authenticated'])
        self.assertFalse(res['authority']['may_dispatch'])
        self.assertFalse(res['allow_worker_run_now'])
        self.assertEqual(res['reader_input_class'],'CALLBACK_INPUT_NOT_PROVIDER_ATTESTED')
    def test_true_fresh_context_still_not_authority(self):
        s=state();s['manual_go_context']['source_main_sha']=MAIN;s['manual_go_context']['priority_request_ids']=[]
        class Fresh(Fake):
            def __call__(self,url):
                if url==f'{r.ROOT}/contents/{r.COORD_PATH}?ref={COORD}':
                    self.calls.append(url);return packed(r.COORD_PATH,s)
                return super().__call__(url)
        obj=r.collect_preflight(Fresh());self.assertEqual(obj['status'],'WAIT_SELECT_NEW_WORK');self.assertFalse(obj['authority']['may_write'])
    def test_repo_mismatch_denied_before_ref(self):
        fake=Fake(changes={1:{'id':1,'full_name':r.REPO,'private':True}})
        with self.assertRaisesRegex(r.ReadError,'REPOSITORY_ID_MISMATCH'):r.collect_preflight(fake)
        self.assertEqual(len(fake.calls),1)
    def test_malformed_ref_denied(self):
        with self.assertRaisesRegex(r.ReadError,'INVALID_GIT_REF'):r.collect_preflight(Fake(changes={2:{'object':{'sha':MAIN}}}))
    def test_ref_drift_denied(self):
        fake=Fake(changes={6:{'ref':'refs/heads/main','object':{'sha':'f'*40,'type':'commit'}}})
        with self.assertRaisesRegex(r.ReadError,'GIT_REF_DRIFT'):r.collect_preflight(fake)
        self.assertEqual(len(fake.calls),6)
    def test_ref_drift_coordinator_denied(self):
        fake=Fake(changes={7:{'ref':f'refs/heads/{r.CONTROL}','object':{'sha':'f'*40,'type':'commit'}}})
        with self.assertRaisesRegex(r.ReadError,'GIT_REF_DRIFT'):r.collect_preflight(fake)
    def test_wrong_file_hash_denied(self):
        broken=packed(r.COORD_PATH,state());broken['sha']='0'*40
        with self.assertRaisesRegex(r.ReadError,'GIT_FILE_HASH_MISMATCH'):r.collect_preflight(Fake(changes={4:broken}))
    def test_wrong_file_path_denied(self):
        broken=packed('ops/OTHER.json',state())
        with self.assertRaisesRegex(r.ReadError,'INVALID_GIT_FILE'):r.collect_preflight(Fake(changes={4:broken}))
    def test_malformed_base64_denied(self):
        broken=packed(r.COORD_PATH,state());broken['content']='!bad!'
        with self.assertRaises(r.ReadError):r.collect_preflight(Fake(changes={4:broken}))
    def test_base64_non_linebreak_injection_denied(self):
        broken=packed(r.COORD_PATH,state());broken['content']='!' + broken['content']
        with self.assertRaisesRegex(r.ReadError,'INVALID_GIT_FILE'):
            r.collect_preflight(Fake(changes={4:broken}))
    def test_real_rest_newline_wrapped_base64_allowed(self):
        correct=packed(r.COORD_PATH,state())
        text=correct['content']
        correct['content']='\n'.join(text[i:i+60] for i in range(0,len(text),60))
        result=r.collect_preflight(Fake(changes={4:correct}))
        self.assertEqual(result['status'],'WAIT_RESELECT_CURRENT_WORK')
    def test_wrong_size_denied(self):
        broken=packed(r.COORD_PATH,state());broken['size']+=1
        with self.assertRaisesRegex(r.ReadError,'GIT_FILE_HASH_MISMATCH'):r.collect_preflight(Fake(changes={4:broken}))
    def test_missing_token_denied(self):
        with self.assertRaisesRegex(r.ReadError,'TOKEN_NOT_AVAILABLE'):r.GitHubGet('')
    def test_url_allowlist(self):
        for bad in ['https://evil.example/','http://api.github.com/',r.ROOT+'/pulls',r.ROOT+'/git/ref/heads/test',
                    r.ROOT+'/contents/ops/REPAIR_COORDINATOR.json?ref=main',
                    r.ROOT+'/contents/ops/WORK_REQUESTS.json?ref='+'f'*40+'&secret=1',r.ROOT+'/actions/runs?per_page=100']:
            with self.subTest(url=bad):self.assertFalse(r.GitHubGet.allowed_url(bad))
        self.assertTrue(r.GitHubGet.allowed_url(r.ROOT))
        self.assertTrue(r.GitHubGet.allowed_url(f'{r.ROOT}/contents/{r.COORD_PATH}?ref={COORD}'))
    def test_transport_GET_no_redirect_or_secret_in_exception(self):
        seen=[]
        def bad(req,timeout):seen.append(req);raise error.HTTPError(req.full_url,302,'TOKEN_SECRET',{},None)
        client=r.GitHubGet('TOKEN_SECRET',opener=bad)
        with self.assertRaisesRegex(r.ReadError,'GITHUB_GET_FAILED') as e:client(r.ROOT)
        self.assertNotIn('TOKEN_SECRET',str(e.exception))
        self.assertEqual(seen[0].get_method(),'GET')
        self.assertEqual(seen[0].get_header('Authorization'),'Bearer TOKEN_SECRET')
        self.assertIsNone(r.NoRedirect().redirect_request(None,None,None,302,None,None))
    def test_duplicate_json_key_denied(self):
        with self.assertRaisesRegex(r.ReadError,'DUPLICATE_JSON_FIELD'):r.parse_json(b'{"id":1,"id":2}')
    def test_nonfinite_json_denied(self):
        with self.assertRaisesRegex(r.ReadError,'NONFINITE_JSON'):r.parse_json(b'{"id": NaN}')
    def test_no_github_write_or_dispatch_symbols(self):
        text=(ROOT/'tools/system_manual_go_priority_github_reader.py').read_text()
        for fragment in ('request.Request(url, method=\'POST\'', 'create_pull_request(', 'update_ref(', 'run_now(', 'merge_pull_request('):
            self.assertNotIn(fragment,text)
    def test_reader_exception_fail_closed(self):
        with self.assertRaisesRegex(r.ReadError,'READER_NOT_AVAILABLE'):r.collect_preflight(None)
    def test_host_main_never_displays_token(self):
        import io
        from contextlib import redirect_stdout
        from unittest.mock import patch
        output=io.StringIO()
        with patch.dict('os.environ',{'GITHUB_TOKEN':'SECRET_TOKEN'}) as _:
            with patch.object(r,'GitHubGet',side_effect=r.ReadError('TOKEN_NOT_AVAILABLE')):
                with redirect_stdout(output):status=r.main()
        self.assertEqual(status,2);self.assertNotIn('SECRET_TOKEN',output.getvalue())

if __name__=='__main__': unittest.main()
