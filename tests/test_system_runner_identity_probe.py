"""Negative controls for the read-only GitHub Actions identity probe."""
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "system_runner_identity_probe.py"
spec = importlib.util.spec_from_file_location("twf_runner_identity_probe", MODULE)
probe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = probe
spec.loader.exec_module(probe)

SHA = "a" * 40
REPO = "kk051780/toy-wars-factory"
WORKFLOW = ".github/workflows/twf-runner-identity-probe.yml"

def valid():
    c = dict(repository=REPO, run_id="12345", run_attempt="2", ref="refs/heads/main",
             sha=SHA, event_name="workflow_dispatch",
             workflow_ref=f"{REPO}/{WORKFLOW}@refs/heads/main")
    r = dict(id=12345, run_attempt=2, repository={"full_name": REPO},
             event="workflow_dispatch", head_branch="main", path=WORKFLOW,
             head_sha=SHA, status="in_progress", workflow_id=65432)
    m = {"name": "main", "commit": {"sha": SHA}}
    return c, r, m

class RunnerIdentityTests(unittest.TestCase):
    def test_positive_is_diagnostic_not_authority(self):
        out = probe.check(*valid())
        self.assertTrue(out["github_api_consistent"])
        self.assertEqual(out["status"], "CONSISTENT_LOCAL_GITHUB_ACTIONS_VIEW_NOT_PORTABLE_ATTESTATION")
        for key in ("current_chatgpt_run_attested", "external_verifier_attested",
                    "cas_performed", "may_write", "may_dispatch", "may_merge",
                    "may_publish", "may_spend", "may_retry"):
            self.assertFalse(out[key], key)

    def denied(self, which, key, value, reason):
        c, r, m = valid()
        [c, r, m][which][key] = value
        with self.assertRaises(probe.NotVerified) as caught:
            probe.check(c, r, m)
        self.assertEqual(str(caught.exception), reason)

    def test_foreign_context_repo(self): self.denied(0, "repository", "bad/other", "FOREIGN_REPO")
    def test_foreign_context_event(self): self.denied(0, "event_name", "pull_request", "FOREIGN_EVENT")
    def test_foreign_context_ref(self): self.denied(0, "ref", "refs/heads/other", "FOREIGN_REF")
    def test_wrong_workflow_ref(self): self.denied(0, "workflow_ref", f"{REPO}/{WORKFLOW}@refs/heads/feature", "FOREIGN_WORKFLOW")
    def test_missing_workflow_ref(self): self.denied(0, "workflow_ref", "", "FOREIGN_WORKFLOW")
    def test_short_context_sha(self): self.denied(0, "sha", "a" * 39, "INVALID_HEAD")
    def test_uppercase_context_sha(self): self.denied(0, "sha", "A" * 40, "INVALID_HEAD")
    def test_zero_run_id(self): self.denied(0, "run_id", "0", "INVALID_RUN_ID")
    def test_float_run_id(self): self.denied(0, "run_id", "12.3", "INVALID_RUN_ID")
    def test_boolean_run_id(self): self.denied(0, "run_id", True, "INVALID_CONTEXT")
    def test_extra_context_key(self): self.denied(0, "added", "x", "INVALID_CONTEXT")
    def test_foreign_run_repo(self): self.denied(1, "repository", {"full_name": "bad/other"}, "FOREIGN_RUN_REPO")
    def test_wrong_run(self): self.denied(1, "id", 12346, "WRONG_RUN")
    def test_boolean_as_run_id(self): self.denied(1, "id", True, "WRONG_RUN")
    def test_wrong_attempt(self): self.denied(1, "run_attempt", 1, "WRONG_ATTEMPT")
    def test_boolean_attempt(self): self.denied(1, "run_attempt", True, "WRONG_ATTEMPT")
    def test_wrong_run_event(self): self.denied(1, "event", "schedule", "WRONG_RUN_EVENT")
    def test_wrong_run_branch(self): self.denied(1, "head_branch", "feature", "WRONG_RUN_BRANCH")
    def test_wrong_run_workflow(self): self.denied(1, "path", ".github/workflows/push.yml", "WRONG_RUN_WORKFLOW")
    def test_wrong_run_sha(self): self.denied(1, "head_sha", "b" * 40, "WRONG_RUN_HEAD")
    def test_run_complete_not_running(self): self.denied(1, "status", "completed", "RUN_NOT_IN_PROGRESS")
    def test_missing_workflow_id(self): self.denied(1, "workflow_id", None, "INVALID_WORKFLOW_ID")
    def test_bool_workflow_id(self): self.denied(1, "workflow_id", True, "INVALID_WORKFLOW_ID")
    def test_wrong_main_ref(self): self.denied(2, "name", "old-main", "WRONG_MAIN_BRANCH")
    def test_main_moved(self): self.denied(2, "commit", {"sha": "b" * 40}, "MAIN_MOVED")
    def test_main_missing_commit(self): self.denied(2, "commit", None, "MISSING_MAIN")
    def test_run_missing_repo(self): self.denied(1, "repository", None, "MISSING_RUN")
    def test_invalid_context_type(self):
        with self.assertRaisesRegex(probe.NotVerified, "INVALID_CONTEXT"):
            probe.check(None, valid()[1], valid()[2])
    def test_strict_dup_json(self):
        with self.assertRaisesRegex(probe.NotVerified, "DUPLICATE_JSON_KEY"):
            probe.parse_json('{"id":1,"id":2}')
    def test_nonfinite_json(self):
        with self.assertRaises(probe.NotVerified):
            probe.parse_json('{"x":NaN}')
    def test_oversized_json(self):
        with self.assertRaisesRegex(probe.NotVerified, "INVALID_RESPONSE"):
            probe.parse_json(" " * 262145)
    def test_replay_of_old_attempt(self):
        c, r, m = valid()
        c["run_attempt"] = "3"
        with self.assertRaisesRegex(probe.NotVerified, "WRONG_ATTEMPT"):
            probe.check(c, r, m)
    def test_emulated_context_and_api_can_be_forged_without_dispatch_authority(self):
        c, r, m = valid()
        c["run_id"] = "54321"
        r["id"] = 54321
        self.assertFalse(probe.check(c, r, m)["may_dispatch"])

class RunnerWorkflowTokenIsolationTests(unittest.TestCase):
    """The read-only probe must not give its test suite the run-inspection token."""
    def setUp(self):
        self.workflow = (MODULE.parents[1] / ".github/workflows/twf-runner-identity-probe.yml").read_text()

    def test_offline_identity_and_redirect_fixtures_are_tokenless(self):
        first = "      - name: Verify read-only identity and redirect regressions without GitHub token"
        second = "      - name: Inspect matching GitHub run with read-only token"
        self.assertEqual(self.workflow.count(first), 1)
        self.assertEqual(self.workflow.count(second), 1)
        fixture = self.workflow.split(first, 1)[1].split(second, 1)[0]
        self.assertIn("test_system_runner_identity_*.py", fixture)
        self.assertNotIn("GH_TOKEN:", fixture)
        self.assertNotIn("github.token", fixture)
        self.assertNotIn("system_runner_identity_probe.py", fixture.replace("test_system_runner_identity_*.py", ""))

    def test_token_available_only_to_read_only_live_probe(self):
        self.assertEqual(self.workflow.count("GH_TOKEN: ${{ github.token }}"), 1)
        step = self.workflow.split("      - name: Inspect matching GitHub run with read-only token", 1)[1]
        self.assertIn("GH_TOKEN: ${{ github.token }}", step)
        self.assertIn("python3 tools/system_runner_identity_probe.py", step)
        self.assertNotIn("python3 -m unittest", step)
        self.assertIn("  contents: read", self.workflow)
        self.assertIn("  actions: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertNotIn("pull-requests: write", self.workflow)

    def test_tokenless_checkout_pinned_to_immutable_source(self):
        self.assertIn("actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2", self.workflow)
        self.assertNotIn("actions/checkout@v4", self.workflow)
        self.assertIn("persist-credentials: false", self.workflow)


if __name__ == "__main__":
    unittest.main()
