"""Pure standard-library workflow syntax/permission regression guards.

Static source tests do not execute GitHub Actions or authenticate a workflow.
"""
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / '.github/workflows/twf-controller-claim-witness.yml'
RAW = P.read_text(encoding='utf-8')

class WorkflowContract(unittest.TestCase):
    def test_only_manually_triggered_event(self):
        self.assertIn("  workflow_dispatch:\n", RAW)
        self.assertNotIn("  schedule:\n", RAW)
        self.assertNotIn("  push:\n", RAW)
        self.assertNotIn("  pull_request:\n", RAW)
    def test_never_runs_from_untrusted_pr(self):
        self.assertIn("github.ref == 'refs/heads/main'", RAW)
        self.assertIn("github.repository == 'kk051780/toy-wars-factory'", RAW)
        self.assertIn("github.event_name == 'workflow_dispatch'", RAW)
        self.assertIn("github.run_attempt == 1", RAW)
    def test_content_read_only(self):
        self.assertIn("permissions:\n  contents: read\n", RAW)
        self.assertNotIn("contents: write", RAW)
        self.assertNotIn("pull-requests: write", RAW)
        self.assertNotIn("id-token: write", RAW)
    def test_no_external_inference_secret(self):
        self.assertNotIn("secrets.", RAW)
        self.assertNotIn("api.roblox.com", RAW)
    def test_persist_credentials_disabled(self):
        self.assertIn("persist-credentials: false", RAW)
    def test_exact_event_sha_checkout(self):
        self.assertIn("ref: ${{ github.sha }}", RAW)
    def test_pinned_checkout_action(self):
        self.assertIn("actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683", RAW)
        self.assertNotIn("uses: actions/checkout@v4", RAW)
    def test_no_user_string_interpolation_inside_bash_run(self):
        run = RAW.split("        run: |", 1)[1]
        for script in run.split("        run: |"):
            self.assertNotIn("${{ inputs.", script)
    def test_all_required_inputs(self):
        for name in ("claim_sha", "source_branch", "owner_id", "epoch", "main_sha"):
            self.assertIn(f"      {name}:\n", RAW)
        self.assertEqual(RAW.count("        required: true"), 5)
    def test_no_write_or_publish_command(self):
        for pattern in ('git push','curl -X POST','gh api -X POST','pip install','roblox upload','gh pr merge'):
            self.assertNotIn(pattern,RAW)
    def test_concurrency_not_cancel_in_progress(self):
        self.assertIn("cancel-in-progress: false",RAW)
    def test_run_bound(self):
        self.assertIn("timeout-minutes: 5",RAW)

if __name__ == '__main__': unittest.main()
