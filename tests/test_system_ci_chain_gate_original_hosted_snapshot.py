"""Pinned original GitHub Actions PR154 run #41146767732 (read-only evidence).

Captured 2026-11-01 from GitHub's run + jobs REST endpoints. This is a
historical snapshot, not a provider-signed receipt, fresh CI, or write grant.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from system_ci_chain_gate import assess_with_payload

REPO = 'kk051780/toy-wars-factory'
HEAD = '4780806fbae5af6f84705478070120a1c6fd7134'
WORKFLOW = 394718989
RUN = {
    'id': 41146767732, 'run_attempt': 1, 'event': 'pull_request',
    'workflow_id': WORKFLOW, 'name': 'Toy Wars bootstrap offline QA',
    'head_sha': HEAD, 'status': 'completed', 'conclusion': 'success',
    'repository': {'full_name': REPO}
}
JOBS = [
    {'id': 124373589205, 'run_id': 41146767732, 'run_attempt': 1,
     'head_sha': HEAD, 'name': 'offline', 'status': 'completed',
     'conclusion': 'success'},
    {'id': 124373589500, 'run_id': 41146767732, 'run_attempt': 1,
     'head_sha': HEAD, 'name': 'compile_hold', 'status': 'completed',
     'conclusion': 'success'}
]


class OriginalHostedSnapshotReplay(unittest.TestCase):
    def verdict(self, run=None, jobs=None, expected_head=HEAD, workflow=WORKFLOW):
        packet = {'run': copy.deepcopy(RUN if run is None else run),
                  'jobs': copy.deepcopy(JOBS if jobs is None else jobs)}
        return assess_with_payload(REPO, expected_head, workflow,
                                   json.dumps(packet, separators=(',', ':')))

    def assertNeverAuthorizes(self, result):
        for key in ('write_allowed', 'dispatch_allowed', 'merge_allowed',
                    'publish_allowed', 'provider_attested',
                    'independent_review_complete'):
            self.assertIs(result[key], False, key)
        self.assertEqual(result['authority'], 'READ_ONLY_UNTRUSTED_SNAPSHOT')

    def test_actual_original_github_two_job_green_is_candidate_only(self):
        out = self.verdict()
        self.assertEqual(out['verdict'], 'QA_CANDIDATE_GREEN')
        self.assertEqual(out['run_id'], RUN['id'])
        self.assertNeverAuthorizes(out)

    def test_real_green_snapshot_cannot_be_reused_for_new_head(self):
        out = self.verdict(expected_head='a' * 40)
        self.assertEqual(out['verdict'], 'BLOCK_SOURCE_MISMATCH')
        self.assertNeverAuthorizes(out)

    def test_original_job_replaced_by_other_attempt(self):
        jobs = copy.deepcopy(JOBS)
        jobs[0]['run_attempt'] = 2
        out = self.verdict(jobs=jobs)
        self.assertEqual(out['verdict'], 'BLOCK_JOBS_MISMATCH')
        self.assertNeverAuthorizes(out)

    def test_original_job_replaced_by_other_source(self):
        jobs = copy.deepcopy(JOBS)
        jobs[1]['head_sha'] = 'a' * 40
        out = self.verdict(jobs=jobs)
        self.assertEqual(out['verdict'], 'BLOCK_JOBS_MISMATCH')
        self.assertNeverAuthorizes(out)

    def test_original_pull_request_event_cannot_masquerade_as_dispatch(self):
        run = copy.deepcopy(RUN)
        run['event'] = 'workflow_dispatch'
        out = self.verdict(run=run)
        self.assertEqual(out['verdict'], 'BLOCK_EVENT_MISMATCH')
        self.assertNeverAuthorizes(out)

    def test_original_green_snapshot_fails_closed_without_offline(self):
        out = self.verdict(jobs=JOBS[1:])
        self.assertEqual(out['verdict'], 'BLOCK_JOBS_MISMATCH')
        self.assertNeverAuthorizes(out)

    def test_original_green_snapshot_fails_closed_if_workflow_is_unpinned(self):
        out = self.verdict(workflow=WORKFLOW + 1)
        self.assertEqual(out['verdict'], 'BLOCK_WORKFLOW_MISMATCH')
        self.assertNeverAuthorizes(out)


if __name__ == '__main__':
    unittest.main()
