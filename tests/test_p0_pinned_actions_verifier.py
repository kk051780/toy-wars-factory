"""P0 immutable Git blob read-only runner verifier regressions."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WF = (ROOT / ".github/workflows/bootstrap-quality.yml").read_text()

class PinnedActionsVerifierTests(unittest.TestCase):
    def test_immutable_commit_literal(self):
        self.assertIn("pinned=adec1e1a642371256fe6b8bd790ccb711bc99251", WF)

    def test_pinned_blob_literal(self):
        self.assertIn("expected_blob=861b3511955e933707538a7dc5ea874caa9bda65", WF)

    def test_pr_head_copy_not_executed(self):
        self.assertNotIn("run: python3 tools/p0_actions_host_evidence.py", WF)
        self.assertIn('git show "${pinned}:tools/p0_actions_host_evidence.py"', WF)

    def test_blob_gate_precedes_execution(self):
        self.assertLess(WF.index('test "$actual_blob" = "$expected_blob"'),
                        WF.index('python3 -I "$tmpdir/verified_host_probe.py"'))

    def test_permissions_remain_read_only(self):
        header = WF.split("jobs:", 1)[0]
        for p in ("contents: read", "actions: read", "pull-requests: read"):
            self.assertIn(p, header)
        self.assertNotIn("contents: write", header)

    def test_pr203_only_no_elevated_trigger(self):
        self.assertIn("github.event.pull_request.number == 203", WF)
        self.assertNotIn("pull_request_target:", WF)
        self.assertIn("set -euo pipefail", WF)

if __name__ == "__main__":
    unittest.main()
