"""Gemini static audit regressions for manual Actions probe; no real GitHub writes.

Only synthetic API callbacks and source files are inspected.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import system_actions_write_probe as p
from test_system_actions_write_probe_claim_receipt import FakeHost


class GeminiAuditRegression(unittest.TestCase):
    def test_primary_failure_and_cleanup_transport_error_both_reported(self):
        x = FakeHost(claim_effect="own", claim_error=None, source_error="BRANCH_DENIED")
        original = x.state
        def state(api, sha):
            if x.source_calls:
                raise p.ProbeError("CURRENT_READ_UNAVAILABLE")
            return original(api, sha)
        x.state = state
        with self.assertRaisesRegex(p.ProbeError,
                                    "^BRANCH_DENIED__RELEASE_UNCONFIRMED$"):
            x.run()
        self.assertEqual(x.source_calls, 1)
        self.assertEqual(len(x.cas_calls), 1)

    def test_lease_loss_does_not_get_disguised_as_transport_failure(self):
        x = FakeHost(claim_effect="own", claim_error=None, source_error="BRANCH_DENIED")
        original = x.owns
        def owns(*args, **kwargs):
            return False if x.source_calls else original(*args, **kwargs)
        x.owns = owns
        with self.assertRaisesRegex(p.ProbeError,
                                    "^BRANCH_DENIED__RELEASE_NOT_OWNED$"):
            x.run()
        self.assertEqual(len(x.cas_calls), 1)

    def test_invalid_blob_sha_blocks_tree_write(self):
        class API:
            def __init__(self): self.calls = []
            def call(self, method, path, body=None):
                self.calls.append((method, path))
                if path.startswith("/git/commits/"): return {"tree": {"sha": "b"*40}}
                if path == "/git/blobs": return {"sha": None}
                raise AssertionError("unexpected mutation " + path)
        api = API()
        with self.assertRaisesRegex(p.ProbeError, "^CONTROL_BLOB_INVALID$"):
            p.cas_state(api, "a"*40, {"schema":1})
        self.assertEqual(len(api.calls), 2)

    def test_invalid_tree_sha_blocks_commit_write(self):
        class API:
            def __init__(self): self.calls = []
            def call(self, method, path, body=None):
                self.calls.append((method, path))
                if path.startswith("/git/commits/"): return {"tree": {"sha": "b"*40}}
                if path == "/git/blobs": return {"sha": "c"*40}
                if path == "/git/trees": return {"sha": None}
                raise AssertionError("unexpected mutation " + path)
        api = API()
        with self.assertRaisesRegex(p.ProbeError, "^CONTROL_TREE_CREATE_INVALID$"):
            p.cas_state(api, "a"*40, {"schema":1})
        self.assertEqual(len(api.calls), 3)

    def test_workflow_writes_only_from_isolated_job_with_pinned_checkout(self):
        workflow = ROOT / ".github" / "workflows" / "twf-actions-write-capability-probe.yml"
        raw = workflow.read_text()
        top, jobs = raw.split("jobs:", 1)
        self.assertIn("permissions:\n  contents: read\n", top)
        self.assertNotIn("contents: write", top)
        self.assertIn("    permissions:\n      contents: write\n      pull-requests: write\n      actions: read\n", jobs)
        self.assertIn("ref: $" + "{{ github.sha }}", jobs)
        self.assertIn("persist-credentials: false", jobs)
        self.assertIn("workflow_dispatch:", top)
        self.assertNotIn("schedule:", top)


if __name__ == "__main__":
    unittest.main()
