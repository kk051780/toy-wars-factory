"""P0 GitHub Actions host-readonly provenance validation: no write privileges."""
import copy
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import p0_actions_host_evidence as probe

RUN, PR, ACTOR = 42439033749, 203, 233213370
HEAD, BASE = "a"*40, "b"*40
BRANCH = "controller/p0-legacy-shadow-compat-20261108-76116caf"

def fixtures():
    context = {"TWF_RUN_ID": str(RUN), "TWF_RUN_ATTEMPT": "1",
               "TWF_PR_NUMBER": str(PR), "TWF_HEAD_SHA": HEAD,
               "TWF_BASE_SHA": BASE, "TWF_HEAD_BRANCH": BRANCH,
               "TWF_ACTOR_ID": str(ACTOR), "TWF_EVENT_NAME": "pull_request",
               "TWF_REPOSITORY": probe.REPO}
    run = {"id": RUN, "run_attempt": 1, "event": "pull_request",
           "path": probe.PATH, "repository": {"full_name": probe.REPO},
           "head_repository": {"full_name": probe.REPO},
           "head_sha": HEAD, "head_branch": BRANCH,
           "actor": {"id": ACTOR},
           "pull_requests": [{"number": PR}]}
    pr = {"number": PR, "state": "open", "draft": True,
          "head": {"sha": HEAD, "ref": BRANCH,
                   "repo": {"full_name": probe.REPO}},
          "base": {"sha": BASE, "ref": "main"}}
    return context, run, pr


class HostProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.c, self.r, self.p = fixtures()

    def assertRefused(self):
        with self.assertRaises(ValueError):
            probe.verify(self.c, self.r, self.p)

    def test_matched_run_pr_metadata_never_grants_write(self):
        result = probe.verify(self.c, self.r, self.p)
        self.assertEqual(result["kind"], "P0_ACTIONS_RUN_PR_READONLY_MATCH")
        self.assertEqual(result["run_id"], RUN)
        for item in ("may_write", "may_merge", "may_release",
                     "openai_chatgpt_task_authenticated",
                     "old_runner_fleet_drained",
                     "source_branch_action_cas_verified",
                     "real_two_gpt_writers_verified",
                     "scoped_parallel_activation_authorized"):
            self.assertFalse(result[item], item)
        self.assertNotIn("actor_token", result)

    def test_wrong_event_refused(self):
        self.r["event"] = "workflow_dispatch"
        self.assertRefused()

    def test_wrong_run_id_refused(self):
        self.r["id"] += 1
        self.assertRefused()

    def test_wrong_run_attempt_refused(self):
        self.r["run_attempt"] += 1
        self.assertRefused()

    def test_wrong_actor_refused(self):
        self.r["actor"]["id"] += 1
        self.assertRefused()

    def test_missing_pr_assoc_refused(self):
        self.r["pull_requests"] = []
        self.assertRefused()

    def test_changed_workflow_refused(self):
        self.r["path"] = ".github/workflows/foreign.yml"
        self.assertRefused()

    def test_changed_run_head_refused(self):
        self.r["head_sha"] = "f"*40
        self.assertRefused()

    def test_changed_pr_head_refused(self):
        self.p["head"]["sha"] = "f"*40
        self.assertRefused()

    def test_changed_pr_base_refused(self):
        self.p["base"]["sha"] = "f"*40
        self.assertRefused()

    def test_fork_repo_refused(self):
        self.p["head"]["repo"]["full_name"] = "other/fork"
        self.assertRefused()

    def test_non_draft_pr_refused(self):
        self.p["draft"] = False
        self.assertRefused()

    def test_foreign_run_repo_refused(self):
        self.r["repository"]["full_name"] = "other/repo"
        self.assertRefused()

    def test_unexpected_pr_number_refused(self):
        self.c["TWF_PR_NUMBER"] = "204"
        self.assertRefused()

    def test_untrusted_branch_refused(self):
        self.c["TWF_HEAD_BRANCH"] = "main"
        self.assertRefused()

    def test_missing_run_context_refused(self):
        del self.c["TWF_RUN_ID"]
        self.assertRefused()

    def test_api_requires_fixed_https_path(self):
        with self.assertRaises(ValueError):
            probe.github_get("https://other.invalid/unsafe", "redacted")

    def test_only_deterministic_readonly_verification(self):
        first = probe.verify(self.c, self.r, self.p)
        second = probe.verify(copy.deepcopy(self.c),
                              copy.deepcopy(self.r), copy.deepcopy(self.p))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
