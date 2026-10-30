"""Strict, non-authorizing evidence triage for Actions CI provenance."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from system_ci_chain_gate import assess, assess_with_payload

REPO='kk051780/toy-wars-factory'
HEAD='e220e85df6519ad5ec163042aba8b78564f3622f'
OTHER='f'*40
RUN=41145842751
WORKFLOW=394718989

def fixture():
    run={'id':RUN,'run_attempt':1,'event':'pull_request','workflow_id':WORKFLOW,
         'name':'Toy Wars bootstrap offline QA','head_sha':HEAD,
         'status':'completed','conclusion':'success',
         'repository':{'full_name':REPO},
         'html_url':f'https://github.com/{REPO}/actions/runs/{RUN}'}
    jobs=[{'id':124370626245,'run_id':RUN,'run_attempt':1,
           'head_sha':HEAD,'name':'compile_hold','status':'completed','conclusion':'success'},
          {'id':124370626516,'run_id':RUN,'run_attempt':1,
           'head_sha':HEAD,'name':'offline','status':'completed','conclusion':'success'}]
    return run,jobs

class ChainTriage(unittest.TestCase):
    def triage(self, alter=None, *, run=None, jobs=None, expected=HEAD):
        if run is None or jobs is None:
            x,y=fixture()
            run=run or x
            jobs=jobs or y
        run,jobs=copy.deepcopy(run),copy.deepcopy(jobs)
        if alter: alter(run,jobs)
        return assess(REPO,expected,WORKFLOW,run,jobs)

    def assertSafe(self, result):
        for name in ('dispatch_allowed','merge_allowed','publish_allowed',
                     'write_allowed','provider_attested','independent_review_complete'):
            self.assertIs(result[name],False)
        self.assertEqual(result['authority'],'READ_ONLY_UNTRUSTED_SNAPSHOT')

    def test_actual_pr152_green_snapshot_is_candidate_not_grant(self):
        q=self.triage();self.assertEqual(q['verdict'],'QA_CANDIDATE_GREEN');self.assertSafe(q)
        self.assertEqual(q['run_id'],RUN)

    def test_wrong_main_sha(self):
        self.assertEqual(self.triage(expected=OTHER)['verdict'],'BLOCK_SOURCE_MISMATCH')

    def test_wrong_run_repository(self):
        q=self.triage(lambda r,j:r['repository'].update(full_name='other/other'))
        self.assertEqual(q['verdict'],'BLOCK_REPO_MISMATCH')

    def test_wrong_run_event(self):
        self.assertEqual(self.triage(lambda r,j:r.update(event='push'))['verdict'],'BLOCK_EVENT_MISMATCH')

    def test_workflow_dispatch_not_pr_qa(self):
        self.assertEqual(self.triage(lambda r,j:r.update(event='workflow_dispatch'))['verdict'],'BLOCK_EVENT_MISMATCH')

    def test_wrong_workflow_id(self):
        self.assertEqual(self.triage(lambda r,j:r.update(workflow_id=WORKFLOW+1))['verdict'],'BLOCK_WORKFLOW_MISMATCH')

    def test_wrong_workflow_name(self):
        self.assertEqual(self.triage(lambda r,j:r.update(name='untrusted'))['verdict'],'BLOCK_WORKFLOW_MISMATCH')

    def test_action_required_run(self):
        q=self.triage(lambda r,j:r.update(status='completed',conclusion='action_required'))
        self.assertEqual(q['verdict'],'WAIT_WORKFLOW_APPROVAL');self.assertSafe(q)

    def test_waiting_run(self):
        self.assertEqual(self.triage(lambda r,j:r.update(status='waiting',conclusion=None))['verdict'],'WAIT_WORKFLOW_APPROVAL')

    def test_pending_run(self):
        self.assertEqual(self.triage(lambda r,j:r.update(status='pending',conclusion=None))['verdict'],'WAIT_WORKFLOW_APPROVAL')

    def test_queued_run(self):
        self.assertEqual(self.triage(lambda r,j:r.update(status='queued',conclusion=None))['verdict'],'WAIT_CI')

    def test_in_progress_run(self):
        self.assertEqual(self.triage(lambda r,j:r.update(status='in_progress',conclusion=None))['verdict'],'WAIT_CI')

    def test_run_failure(self):
        self.assertEqual(self.triage(lambda r,j:r.update(conclusion='failure'))['verdict'],'BLOCK_CI_FAILURE')

    def test_cancelled_run(self):
        self.assertEqual(self.triage(lambda r,j:r.update(conclusion='cancelled'))['verdict'],'BLOCK_CI_FAILURE')

    def test_unknown_run_status(self):
        self.assertEqual(self.triage(lambda r,j:r.update(status='bogus'))['verdict'],'BLOCK_MALFORMED')

    def test_bool_run_id(self):
        self.assertEqual(self.triage(lambda r,j:r.update(id=True))['verdict'],'BLOCK_MALFORMED')

    def test_float_attempt(self):
        self.assertEqual(self.triage(lambda r,j:r.update(run_attempt=1.0))['verdict'],'BLOCK_MALFORMED')

    def test_missing_run_attempt(self):
        self.assertEqual(self.triage(lambda r,j:r.pop('run_attempt'))['verdict'],'BLOCK_MALFORMED')

    def test_duplicate_job_name(self):
        self.assertEqual(self.triage(lambda r,j:j[1].update(name=j[0]['name']))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_extra_job(self):
        self.assertEqual(self.triage(lambda r,j:j.append(copy.deepcopy(j[0])))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_missing_job(self):
        self.assertEqual(self.triage(lambda r,j:j.pop())['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_job_recycled_from_other_run(self):
        self.assertEqual(self.triage(lambda r,j:j[0].update(run_id=1))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_job_from_previous_attempt(self):
        self.assertEqual(self.triage(lambda r,j:j[0].update(run_attempt=2))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_job_head_mismatch(self):
        self.assertEqual(self.triage(lambda r,j:j[0].update(head_sha=OTHER))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_job_status_pending(self):
        self.assertEqual(self.triage(lambda r,j:j[0].update(status='in_progress',conclusion=None))['verdict'],'WAIT_CI')

    def test_job_action_required(self):
        self.assertEqual(self.triage(lambda r,j:j[0].update(conclusion='action_required'))['verdict'],'WAIT_WORKFLOW_APPROVAL')

    def test_job_failure(self):
        self.assertEqual(self.triage(lambda r,j:j[0].update(conclusion='failure'))['verdict'],'BLOCK_CI_FAILURE')

    def test_job_bool_id(self):
        self.assertEqual(self.triage(lambda r,j:j[0].update(id=True))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_job_id_reuse(self):
        self.assertEqual(self.triage(lambda r,j:j[1].update(id=j[0]['id']))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_jobs_not_list(self):
        self.assertEqual(assess(REPO,HEAD,WORKFLOW,*((fixture()[0],{})))['verdict'],'BLOCK_JOBS_MISMATCH')

    def test_exact_input_repository_required(self):
        r,j=fixture();self.assertEqual(assess('different/repo',HEAD,WORKFLOW,r,j)['verdict'],'BLOCK_REPO_MISMATCH')

    def test_empty_head_rejected(self):
        self.assertEqual(self.triage(expected='')['verdict'],'BLOCK_MALFORMED')

    def test_invalid_workflow_type(self):
        r,j=fixture();self.assertEqual(assess(REPO,HEAD,True,r,j)['verdict'],'BLOCK_MALFORMED')

    def test_source_not_a_provider_receipt(self):
        q=self.triage();self.assertSafe(q)

    def test_json_duplicate_field_rejected(self):
        r,j=fixture()
        raw=json.dumps({'run':r,'jobs':j})
        malformed=raw.replace('"run_attempt": 1','"run_attempt": 1, "run_attempt": 2',1)
        self.assertEqual(assess_with_payload(REPO,HEAD,WORKFLOW,malformed)['verdict'],'BLOCK_MALFORMED')

    def test_json_oversized_rejected(self):
        self.assertEqual(assess_with_payload(REPO,HEAD,WORKFLOW,' '*100_001)['verdict'],'BLOCK_MALFORMED')

    def test_json_payload_green(self):
        r,j=fixture();q=assess_with_payload(REPO,HEAD,WORKFLOW,json.dumps({'run':r,'jobs':j}))
        self.assertEqual(q['verdict'],'QA_CANDIDATE_GREEN')

    def test_fixture_does_not_authorize_workflow_dispatch(self):
        r,j=fixture();r['event']='workflow_dispatch';q=assess(REPO,HEAD,WORKFLOW,r,j)
        self.assertFalse(q['dispatch_allowed'])

if __name__=='__main__':unittest.main()
