"""Dedicated Actions run/job join key; synthetic, not provider-authenticated."""
import unittest
from unittest.mock import patch
from copy import deepcopy
from test_manual_claim_witness import check, m, CLAIM, SRC, MAIN
from test_actions_host_context import BASE

REAL = {**BASE, "GITHUB_SHA": MAIN, "GITHUB_WORKFLOW_SHA": MAIN}

class RunJoinKeyTests(unittest.TestCase):
    def result(self):
        return m.bind_actions_run_observation(check(), dict(REAL))

    def test_host_success_stays_non_authorizing(self):
        out=self.result()
        self.assertFalse(out['provider_authenticated'])
        self.assertFalse(out['merge_authorized'])
        self.assertFalse(out['roblox_post_authorized'])
        x=out['reported_actions_origin_untrusted']
        self.assertEqual(x['repository'],m.REPO)
        self.assertEqual(x['repository_id'],m.REPO_ID)
        self.assertEqual(x['workflow_ref'],m.WORKFLOW_REF)
        self.assertEqual(x['workflow_sha'],REAL['GITHUB_SHA'])
        self.assertEqual(x['run_id'],int(BASE['GITHUB_RUN_ID']))
        self.assertEqual(x['run_attempt'],1)
        self.assertEqual(x['job_id'],'witness')
        self.assertEqual(x['claim_sha'],CLAIM)
        self.assertEqual(x['source_branch'],SRC)
        for flag in ('provider_authenticated','job_log_attested','may_review_or_merge','may_write_or_publish'):
            self.assertIs(x[flag],False)

    def test_extra_host_identity_is_mandatory(self):
        for key in ('GITHUB_ACTIONS','GITHUB_JOB','GITHUB_WORKFLOW_SHA'):
            with self.subTest(key=key), self.assertRaises(m.WitnessHold):
                e=dict(REAL);del e[key];m.validate_host_context(e)

    def test_wrong_job_and_workflow_sha_rejected(self):
        for change in ({'GITHUB_JOB':'foreign-job'},{'GITHUB_ACTIONS':'false'},
                       {'GITHUB_WORKFLOW_SHA':'f'*40}, {'GITHUB_WORKFLOW_SHA':'bad'}):
            with self.subTest(change=change), self.assertRaises(m.WitnessHold):
                m.validate_host_context({**REAL,**change})

    def test_wrong_main_and_missing_claim_cannot_report_run(self):
        for change in ({'main_sha':'f'*40},{'claim_sha':'not-a-sha'},{'epoch':True},
                       {'source_branch':'other/branch'},{'status':'FAILED'}):
            x=check();x.update(change)
            with self.subTest(change=change), self.assertRaises(m.WitnessHold):
                m.bind_actions_run_observation(x,dict(REAL))

    def test_self_claimed_approval_is_denied(self):
        for key in ('provider_authenticated','independent_review_authorized',
                    'merge_authorized','roblox_post_authorized'):
            x=check();x[key]=True
            with self.subTest(key=key), self.assertRaises(m.WitnessHold):
                m.bind_actions_run_observation(x,dict(REAL))

    def test_missing_status_or_invalid_observation_denied(self):
        for bad in (None,[],{},'passed',{'status':'HOLD'},True):
            with self.subTest(value=bad), self.assertRaises(m.WitnessHold):
                m.bind_actions_run_observation(bad,dict(REAL))

    def test_real_entrypoint_joins_labels_without_network_in_stub(self):
        fake = check()
        with patch.dict('os.environ', {**REAL,'GH_TOKEN':'TEST_TOKEN_FAKE_123456789'}, clear=True), \
             patch.object(m, 'first_party_witness', return_value=fake), \
             patch.object(m, 'ProviderReadOnly'):
            out=m.from_actions_env()
        self.assertEqual(out['reported_actions_origin_untrusted']['run_id'],int(REAL['GITHUB_RUN_ID']))
        self.assertIs(out['provider_authenticated'],False)
        self.assertIs(out['reported_actions_origin_untrusted']['job_log_attested'],False)

    def test_entrypoint_rejects_foreign_job_before_provider_or_token(self):
        with patch.dict('os.environ', {**REAL,'GITHUB_JOB':'evil'}, clear=True), \
             patch.object(m, 'ProviderReadOnly') as provider:
            with self.assertRaises(m.WitnessHold):m.from_actions_env()
            provider.assert_not_called()

    def test_good_join_key_does_not_claim_completed_hosted_work(self):
        out=self.result()
        self.assertEqual(out['provider_witness_id'],'MUST_BIND_TO_AUTHENTICATED_WORKFLOW_RUN_AND_JOB')
        self.assertNotIn('original_github_job_authenticated',out)
        self.assertNotIn('merge_authorized',out['reported_actions_origin_untrusted'])
        self.assertIs(out['reported_actions_origin_untrusted']['may_review_or_merge'],False)

    def test_noncanonical_run_id_rejected(self):
        for bad in ('0','-1','1.0','00001','a'*30):
            with self.subTest(bad=bad), self.assertRaises(m.WitnessHold):
                m.bind_actions_run_observation(check(),{**REAL,'GITHUB_RUN_ID':bad})

if __name__ == '__main__': unittest.main()
