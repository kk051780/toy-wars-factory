"""Offline regression for owner-only contents:write without PR creation.

Run inside exact PR163 repo with the corresponding prepared source patch.
No provider identity or GitHub writes are established by these mocks.
"""
from copy import deepcopy
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import system_actions_write_probe as p
from test_system_actions_write_probe import BASE_ENV, BASE_RUN, SHA
from test_system_actions_write_probe_claim_receipt import FakeHost

WORKFLOW=ROOT/'.github/workflows/twf-actions-branch-write-capability-probe.yml'

def setup_branch():
    env={**BASE_ENV,
         'PROBE_MODE':'BRANCH_ONLY',
         'PROBE_CONSENT':p.BRANCH_CONSENT,
         'GITHUB_WORKFLOW_REF':p.REPO+'/'+p.BRANCH_WORKFLOW+'@refs/heads/main'}
    run={**BASE_RUN,'path':p.BRANCH_WORKFLOW}
    return env,run

class TestBranchOnlyIdentity(unittest.TestCase):
    def test_current_owner_run_matches_only_exact_new_workflow_and_consent(self):
        env,run=setup_branch()
        state=p.checked_context(env,run,SHA)
        self.assertTrue(state['branch_only'])
        self.assertEqual(state['main'],SHA)
        self.assertEqual(state['run_id'],int(env['GITHUB_RUN_ID']))
        self.assertNotEqual(state['owner'],p.checked_context(BASE_ENV,BASE_RUN,SHA)['owner'])

    def test_wrong_path_is_rejected(self):
        env,run=setup_branch()
        with self.assertRaises(p.ProbeError): p.checked_context(env,BASE_RUN,SHA)
        with self.assertRaises(p.ProbeError): p.checked_context(BASE_ENV,run,SHA)

    def test_wrong_owner_phrase_is_rejected(self):
        env,run=setup_branch()
        for bad in ('',p.CONSENT,'I_AUTHORIZE_NOTHING'):
            with self.subTest(bad=bad),self.assertRaises(p.ProbeError):
                p.checked_context({**env,'PROBE_CONSENT':bad},run,SHA)

    def test_unknown_mode_is_rejected_even_with_legitimate_owner(self):
        env,run=setup_branch()
        with self.assertRaisesRegex(p.ProbeError,'PROBE_MODE_DENIED'):
            p.checked_context({**env,'PROBE_MODE':'AUTO_MERGE'},run,SHA)

class TestBranchOnlyWrite(unittest.TestCase):
    def test_branch_mode_only_performs_get_post_ref_and_put_file_no_pr(self):
        env,run=setup_branch()
        scope=p.checked_context(env,run,SHA)
        calls=[]
        class Fake:
            def call(self,method,path,body=None):
                calls.append((method,path,body))
                if (method,path)==('GET','/git/ref/heads/main'):
                    return {'object':{'sha':SHA}}
                if (method,path)==('POST','/git/refs'):
                    return {'ref':body['ref']}
                if method=='PUT' and path.startswith('/contents/ops/probes/'):
                    return {'commit':{'sha':'b'*40}}
                raise AssertionError('Unapproved call: '+method+' '+path)
        self.assertIsNone(p.create_branch_probe(Fake(),scope))
        self.assertEqual([x[0] for x in calls],['GET','POST','PUT'])
        self.assertTrue(all(x[1]!='/pulls' for x in calls))

    def test_branch_only_reports_no_pr_and_releases_exact_owner(self):
        x=FakeHost(claim_effect='own',claim_error=None)
        env,live=setup_branch()
        scope={**x.__dict__.get('scope',{}),
               'main':SHA,'branch':'controller/gha-write-probe-41199998877-a1',
               'run_id':41199998877,'attempt':1,
               'owner':'9da4af9c-0a89-49ea-a77e-8459eac6c65a',
               'branch_only':True}
        # FakeHost's CAS/release harness is proven in previous original tests.
        with patch.object(p,'checked_context',return_value=scope), \
             patch.object(p,'verify_staged_probe',return_value='b'*40), \
             patch.object(p,'create_branch_probe',return_value=None), \
             patch.object(p,'sha_ref',x.sha), \
             patch.object(p,'state_at',x.state), \
             patch.object(p,'acquire',x.acquire), \
             patch.object(p,'cas_state',x.cas), \
             patch.object(p,'owns',x.owns), \
             patch.object(p,'release',x.release), \
             patch.object(p,'now',lambda:'2026-10-31T03:11:00+00:00'):
            class API:
                def call(self,method,path,body=None): return {}
            result=p.run(API(),env)
        self.assertEqual(result,{'status':'BRANCH_VERIFIED_NO_PR_REQUEST',
                                 'pr':None,'wrote':True})
        self.assertEqual(len(x.cas_calls),2)
        self.assertIsNone(x.current['holder'])

class TestBranchOnlyWorkflow(unittest.TestCase):
    def test_workflow_manual_only_and_no_pull_request_write(self):
        src=WORKFLOW.read_text(encoding='utf-8')
        for value in ['  workflow_dispatch:', '  contents: read',
                      '      contents: write', '      actions: read',
                      '      github.actor == \'kk051780\'',
                      '      github.triggering_actor == \'kk051780\'',
                      '      github.ref == \'refs/heads/main\'',
                      'PROBE_MODE: BRANCH_ONLY', 'python3 tools/system_actions_write_probe.py',
                      'persist-credentials: false',p.BRANCH_CONSENT]:
            with self.subTest(value=value):self.assertIn(value,src)
        for bad in ['pull-requests: write','schedule:', '  push:',
                    '  pull_request:', 'id-token: write','secrets.', 'npm install',
                    'I_AUTHORIZE_ISOLATED_DRAFT_PR_ONLY']:
            with self.subTest(bad=bad):self.assertNotIn(bad,src)
        import re
        self.assertRegex(src,r'uses: actions/checkout@[0-9a-f]{40}')

if __name__=='__main__':unittest.main()
