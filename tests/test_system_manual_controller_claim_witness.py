"""Future-only protected controller claim witness: fail-first native tests.

These assertions do not create a review, merge, GitHub write, or Roblox action.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from manual_controller_claim_witness import (
    REPO, REPO_ID, WORKFLOW_REF, WitnessHold,
    ProviderReadOnly, validate_host_context,
)

def good_env():
    return {
        'GITHUB_REPOSITORY': REPO,
        'GITHUB_REPOSITORY_ID': REPO_ID,
        'GITHUB_WORKFLOW_REF': WORKFLOW_REF,
        'GITHUB_WORKFLOW_SHA': 'a' * 40,
        'GITHUB_ACTIONS': 'true',
        'GITHUB_JOB': 'witness',
        'GITHUB_EVENT_NAME': 'workflow_dispatch',
        'GITHUB_REF': 'refs/heads/main',
        'GITHUB_SHA': 'a' * 40,
        'GITHUB_RUN_ID': '123456789',
        'GITHUB_RUN_ATTEMPT': '1',
    }

class ProtectedMainHostTests(unittest.TestCase):
    def test_correct_shape_only_never_provider_attestation(self):
        self.assertTrue(validate_host_context(good_env()))

    def test_foreign_repository_rejected(self):
        with self.assertRaises(WitnessHold):
            validate_host_context({**good_env(),'GITHUB_REPOSITORY': 'other/repo'})

    def test_wrong_workflow_ref_rejected(self):
        with self.assertRaises(WitnessHold):
            validate_host_context({**good_env(),'GITHUB_WORKFLOW_REF': WORKFLOW_REF + '-unreviewed'})

    def test_wrong_attempt_rejected(self):
        with self.assertRaises(WitnessHold):
            validate_host_context({**good_env(),'GITHUB_RUN_ATTEMPT': '2'})

    def test_non_github_route_rejected_before_network(self):
        reader = ProviderReadOnly('PLACEHOLDER_TEST_ONLY_123456789', opener=lambda *a,**k: self.fail('network call'))
        with self.assertRaises(WitnessHold):
            reader.get('https://attacker.test/evil')
        self.assertEqual(reader.queries, 0)

    def test_unbounded_github_route_rejected_before_network(self):
        reader = ProviderReadOnly('PLACEHOLDER_TEST_ONLY_123456789', opener=lambda *a,**k: self.fail('network call'))
        with self.assertRaises(WitnessHold):
            reader.get('/actions/runs?per_page=100')
        self.assertEqual(reader.queries, 0)

if __name__ == '__main__':
    unittest.main()
