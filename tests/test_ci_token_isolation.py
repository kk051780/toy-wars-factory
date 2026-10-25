"""Security invariants: untrusted PR QA no secret; trusted coordination base only."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
QA = (ROOT / '.github/workflows/bootstrap-quality.yml').read_text(encoding='utf-8')
TRUSTED = (ROOT / '.github/workflows/trusted-coordinator-claim.yml').read_text(encoding='utf-8')

class WorkflowIsolationTests(unittest.TestCase):
    def test_pull_request_qa_has_no_explicit_github_token_use(self):
        self.assertIn('  pull_request:', QA)
        self.assertNotIn('GH_TOKEN:', QA)
        self.assertNotIn('GITHUB_TOKEN:', QA)
        self.assertNotIn('github.token', QA)
        self.assertNotIn('gh extension install', QA)

    def test_compiler_binary_is_unauthenticated_and_checksum_pinned(self):
        self.assertIn('v0.93.2/linux-amd64', QA)
        self.assertIn('364b98de9a8b8948792289128bbf3907d152284804e02b70804fc123e09ca6fd', QA)
        self.assertIn('sha256sum --check', QA)
        self.assertIn('/tmp/twf-gh-aw compile .github/workflows/twf-gemini-free-trial.md', QA)
        self.assertNotIn('GH_TOKEN', QA)

    def test_checkouts_all_disable_persisted_credentials(self):
        named = len(re.findall(r'persist-credentials: false', QA))
        self.assertEqual(named, 3)

    def test_pr_qa_preserves_scope_and_compilation_regressions(self):
        self.assertIn('tools/check_auto_diff.py', QA)
        self.assertIn('check_meta_diff.py', QA)
        self.assertIn('tools/verify_gemini_hold.py', QA)
        self.assertIn('git diff --exit-code -- .github/workflows/twf-gemini-free-trial.lock.yml', QA)

    def test_trusted_claim_workflow_is_base_scoped_and_not_pr_checkout(self):
        self.assertIn('  pull_request_target:', TRUSTED)
        self.assertNotIn('  pull_request:', TRUSTED)
        self.assertIn('ref: ${{ github.event.pull_request.base.sha }}', TRUSTED)
        self.assertNotIn('ref: ${{ github.event.pull_request.head.sha }}', TRUSTED)
        self.assertIn('persist-credentials: false', TRUSTED)
        self.assertIn('TWF_HEAD_REPO:', TRUSTED)
        self.assertIn('test "$TWF_HEAD_REPO" = "$TWF_BASE_REPO"', TRUSTED)

    def test_trusted_claim_is_data_only_and_uses_base_verifier(self):
        self.assertIn('GH_TOKEN: ${{ github.token }}', TRUSTED)
        self.assertIn('contents: read', TRUSTED)
        self.assertNotIn('contents: write', TRUSTED)
        self.assertIn('python3 tools/repair_control.py verify-pr', TRUSTED)
        self.assertIn('refs/remotes/origin/twf-repair-coordinator', TRUSTED)
        self.assertIn('test "$(git rev-parse refs/remotes/origin/trusted-pr-head)" = "$TWF_HEAD_SHA"', TRUSTED)
        self.assertNotIn('python3 -m unittest discover', TRUSTED)
        self.assertNotIn('lua5.4', TRUSTED)
        self.assertNotIn('gh aw compile', TRUSTED)

    def test_no_released_workflow_runs_untrusted_code_with_credential(self):
        self.assertNotIn('GH_TOKEN', QA)
        for line in TRUSTED.splitlines():
            self.assertNotIn('sudo ', line)
            self.assertNotIn('npm ', line)
            self.assertNotIn('lua5.4', line)

if __name__ == '__main__':
    unittest.main()
