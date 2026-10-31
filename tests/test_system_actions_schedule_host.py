"""Strict manual-only GitHub host proof: offline fixtures are NOT live run evidence."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib import error
from tools import system_actions_schedule_host as h
from tools import system_actions_schedule_cadence as c

ROOT=Path(__file__).resolve().parents[1]
VALID={"GITHUB_REPOSITORY":h.REPO,"GITHUB_REPOSITORY_ID":str(h.REPO_ID),
       "GITHUB_ACTOR":h.ACTOR,"GITHUB_TRIGGERING_ACTOR":h.ACTOR,
       "GITHUB_EVENT_NAME":"workflow_dispatch","GITHUB_REF":"refs/heads/main",
       "GITHUB_WORKFLOW_REF":f"{h.REPO}/{h.WORKFLOW}@refs/heads/main",
       "GITHUB_SHA":"e"*40,"GITHUB_RUN_ID":"41188887777",
       "GITHUB_RUN_ATTEMPT":"1","PROBE_CONSENT":h.CONSENT}

RUN={"id":41188887777,"event":"workflow_dispatch","path":h.WORKFLOW,
     "run_attempt":1,"head_branch":"main","head_sha":"e"*40,
     "repository":{"id":h.REPO_ID},"head_repository":{"id":h.REPO_ID},
     "actor":{"login":h.ACTOR},"triggering_actor":{"login":h.ACTOR}}

class MockLive:
    def __init__(self,rows=None,broken=None):
        self.calls=[];self.bad=broken;self.rows=[] if rows is None else rows
    def __call__(self,url):
        self.calls.append(url)
        if self.bad:return self.bad(url)
        if url==h.API_ROOT+'/git/ref/heads/main':return {'object':{'sha':'e'*40}}
        if url==h.API_ROOT+'/actions/runs/41188887777':return deepcopy(RUN)
        if url==h.API_ROOT+'/actions/runs?event=schedule&per_page=100&page=1':
            return {'total_count':len(self.rows),'workflow_runs':deepcopy(self.rows)}
        raise AssertionError(url)

def make_root():
    d=tempfile.TemporaryDirectory();root=Path(d.name)
    for file,minute in [(h.BINDING['workflows'][0]['path'],'13,33,53'),
                        (h.BINDING['workflows'][1]['path'],'7,27,47')]:
        p=root/file;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('name: test\non:\n  schedule:\n    - cron: '+
                     (f'"{minute} * * * *"' if 'watchdog' in file else f"'{minute} * * * *'")+'\n')
    return d,root

def act(reader=None,env=None,root=None,clock=None):
    own,source=make_root() if root is None else (None,root)
    try:
        return h.execute(reader or MockLive(),VALID if env is None else env,root=source,
                         clock=clock or (lambda:datetime(2026,10,31,12,0,tzinfo=timezone.utc)))
    finally:
        if own:own.cleanup()

class HostTests(unittest.TestCase):
    def test_positive_owner_only_zero_rows(self):
        r=act();self.assertEqual(r['status'],'OWNER_MANUAL_READ_ONLY_PROBE_NOT_AUTOMATED_SCHEDULER')
        self.assertEqual(r['run_id'],int(VALID['GITHUB_RUN_ID']))
        self.assertTrue(r['host_gets_executed']);self.assertFalse(r['historical_cron_source_authenticated'])
        self.assertFalse(r['automatic_ai_coding_verified'])
        self.assertTrue(all(x is False for x in r['authority'].values()))

    def test_injected_get_callback_never_becomes_provider_evidence(self):
        injected=MockLive()
        result=act(injected)
        self.assertGreaterEqual(len(injected.calls),4)
        self.assertTrue(result['get_callback_invoked'])
        self.assertEqual(result['callback_provenance'],'INJECTED_READER_NOT_PROVIDER_ATTESTATION')
        self.assertNotIn('host_gets_executed', result)
        self.assertFalse(result['current_cron_source_authenticated'])
        self.assertFalse(result['provider_authenticated_outside_job'])

    def test_replayed_original_shaped_run_is_still_not_live_proof(self):
        fake=MockLive()
        result=act(fake)
        self.assertEqual(result['source_verification'],'UNTRUSTED_INPUT_ONLY')
        self.assertNotIn('host_gets_executed',result)
        self.assertFalse(result['historical_cron_source_authenticated'])
        self.assertFalse(result['current_cron_source_authenticated'])
        self.assertFalse(result['authority']['provider_authenticated'])

    def test_scope_ids_accepted(self):
        self.assertEqual(h.validated_context(VALID),{'main_sha':'e'*40,'run_id':41188887777})
    def test_required_context_keys(self):
        for key in VALID:
            with self.subTest(key=key),self.assertRaises(h.HostError):
                a=VALID.copy();a.pop(key);h.validated_context(a)
    def test_every_context_denial(self):
        mutations={'GITHUB_REPOSITORY':'evil/a','GITHUB_REPOSITORY_ID':'1',
           'GITHUB_ACTOR':'foreign','GITHUB_TRIGGERING_ACTOR':'foreign',
           'GITHUB_EVENT_NAME':'schedule','GITHUB_REF':'refs/heads/dev',
           'GITHUB_WORKFLOW_REF':'foreign/a/.github/workflows/twf-readonly-cadence-audit.yml@refs/heads/main',
           'GITHUB_SHA':'not_sha','GITHUB_RUN_ID':'0','GITHUB_RUN_ATTEMPT':'2',
           'PROBE_CONSENT':'not-approved'}
        for key,value in mutations.items():
            with self.subTest(key=key),self.assertRaises(h.HostError):
                h.validated_context({**VALID,key:value})
    def test_wrong_context_no_network(self):
        rr=MockLive();
        with self.assertRaises(h.HostError):act(rr,{**VALID,'GITHUB_ACTOR':'other'})
        self.assertEqual(rr.calls,[])
    def test_main_shas_must_match(self):
        rr=MockLive(broken=lambda url: {'object':{'sha':'a'*40}})
        with self.assertRaisesRegex(h.HostError,'MAIN_SHA_CHANGED'):act(rr)
        self.assertEqual(len(rr.calls),1)
    def test_live_actor_and_head_repository_originals(self):
        for field,value in [('actor',{'login':'other'}),('triggering_actor',{'login':'other'}),
                ('head_repository',{'id':42}),('repository',{'id':42}),('run_attempt',2),
                ('event','schedule'),('head_branch','feature'),('head_sha','a'*40),
                ('path','/bad'),('id',1)]:
            def bad(url):
                if url.endswith('/git/ref/heads/main'):return {'object':{'sha':'e'*40}}
                o=deepcopy(RUN);o[field]=value;return o
            with self.subTest(field=field),self.assertRaisesRegex(h.HostError,'MANUAL_RUN_LINEAGE_UNVERIFIED'):
                act(MockLive(broken=bad))
    def test_source_cron_drift_fails_before_any_get(self):
        d,root=make_root();r=MockLive()
        try:
            path=root/h.BINDING['workflows'][0]['path'];path.write_text(path.read_text().replace('13,33,53','13,33,54'))
            with self.assertRaisesRegex(h.HostError,'CURRENT_CRON_SOURCE_DRIFT'):act(r,root=root)
            self.assertEqual(r.calls,[])
        finally:d.cleanup()
    def test_source_more_than_one_cron_denied(self):
        d,root=make_root()
        try:
            p=root/h.BINDING['workflows'][1]['path'];p.write_text(p.read_text()+"    - cron: '10 * * * *'\n")
            with self.assertRaises(h.HostError):act(root=root)
        finally:d.cleanup()
    def test_symlink_denied(self):
        d,root=make_root()
        try:
            p=root/h.BINDING['workflows'][0]['path'];p.unlink();p.symlink_to(root/h.BINDING['workflows'][1]['path'])
            with self.assertRaisesRegex(h.HostError,'CRON_SOURCE_UNAVAILABLE'):act(root=root)
        finally:d.cleanup()
    def test_bounded_window_exact_48_hours(self):
        r=act();q=r['workflows'][h.BINDING['workflows'][0]['path']]
        self.assertEqual(q['configured_cron_slots'],144)
    def test_wrong_clock_denied(self):
        for clock in [lambda:None,lambda:datetime(2026,10,31,12)]:
            with self.subTest(clock=clock),self.assertRaisesRegex(h.HostError,'INVALID_CLOCK'):
                act(clock=clock)
    def test_injected_reader_error_sanitized(self):
        def fail(url):raise ValueError('PRIVATE_KEY=should_not_appear')
        with self.assertRaisesRegex(ValueError,'PRIVATE_KEY'):act(MockLive(broken=fail))
        # Host main() sanitizer is intentionally separate from the pure adapter.
    def test_transport_no_token(self):
        with self.assertRaisesRegex(h.HostError,'TOKEN_UNAVAILABLE'):h.GitHubReader('')
    def test_transport_url_strict(self):
        calls=[]
        def opener(req,timeout):calls.append(req);raise error.URLError('NO_NETWORK')
        reader=h.GitHubReader('token',opener)
        for url in ['https://evil.example/actions/runs?event=schedule&per_page=100&page=1',
                    h.API_ROOT+'/pulls',h.API_ROOT+'/actions/runs?event=workflow_dispatch&per_page=100&page=1',
                    h.API_ROOT+'/actions/runs?event=schedule&per_page=100&page=11',
                    h.API_ROOT+'/git/ref/heads/dev']:
            with self.subTest(url=url),self.assertRaisesRegex(h.HostError,'URL_NOT_ALLOWLISTED'):reader(url)
        self.assertEqual(calls,[])
    def test_get_only_no_redirect(self):
        class FakeResponse:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def getcode(self):return 200
            def read(self,n):return b'{}'
        reqs=[]
        def op(req,timeout):reqs.append(req);return FakeResponse()
        reader=h.GitHubReader('token_X',op)
        reader(h.API_ROOT+'/git/ref/heads/main')
        self.assertEqual(reqs[0].get_method(),'GET')
        self.assertEqual(reqs[0].get_header('Authorization'),'Bearer token_X')
        self.assertEqual(reqs[0].full_url,h.API_ROOT+'/git/ref/heads/main')
        self.assertIsNone(h.NoRedirect().redirect_request(None,None,None,302,None,None))
    def test_http_failure_sanitized(self):
        def bad(req,timeout):raise error.HTTPError(req.full_url,403,'TOKENSECRET',{},None)
        with self.assertRaisesRegex(h.HostError,'READ_ONLY_GITHUB_GET_FAILED') as ctx:
            h.GitHubReader('TOKENSECRET',bad)(h.API_ROOT+'/git/ref/heads/main')
        self.assertNotIn('TOKENSECRET',str(ctx.exception))
    def test_invalid_json_and_oversize_rejected(self):
        class Response:
            def __init__(self,b):self.b=b
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def getcode(self):return 200
            def read(self,n):return self.b[:n]
        for raw in [b'[]',b'foo',b'0'*2000001]:
            with self.subTest(size=len(raw)),self.assertRaises(h.HostError):
                h.GitHubReader('TOKEN',lambda req,timeout:Response(raw))(h.API_ROOT+'/git/ref/heads/main')
    def test_manual_yaml_no_scheduler(self):
        wf=(ROOT/h.WORKFLOW).read_text()
        for piece in ['  workflow_dispatch:',"github.actor == 'kk051780'", "github.triggering_actor == 'kk051780'",
             "github.ref == 'refs/heads/main'", "github.run_attempt == 1",h.CONSENT,
             '  actions: read','  contents: read','persist-credentials: false','timeout-minutes: 4']:
            self.assertIn(piece,wf)
        for phrase in ('  push:', '  schedule:', '  pull_request:', 'pull-requests: write', 'contents: write', 'id-token: write','npm install'):
            self.assertNotIn(phrase,wf)
    def test_workflow_manual_not_actual_hosted_write_proof(self):
        self.assertNotIn('GITHUB_TOKEN: ${{ secrets.',(ROOT/h.WORKFLOW).read_text())
        self.assertNotIn('gh aw run',(ROOT/h.WORKFLOW).read_text().lower())
        self.assertFalse(hasattr(h,'create_pull_request'))
        self.assertFalse(hasattr(h,'mutate_repo'))

if __name__=='__main__':unittest.main()