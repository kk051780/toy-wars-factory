#!/usr/bin/env python3
"""Offline falsification tests; network used only by explicit live CI step."""
import copy
import json
import unittest

from check_trace import MATRIX, TraceFailure
from check_rc_freshness import BRANCH, REPO, verify_live_identity


class LiveOfficialIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        obs = cls.matrix["official_rc_observation"]
        cls.sha = obs["head"]
        cls.run_id = int(obs["verified_source_build_run"].rsplit("/", 1)[-1])

    def setUp(self):
        self.record = copy.deepcopy(self.matrix)
        self.branch = {"name": BRANCH, "commit": {"sha": self.sha}}
        self.run = {
            "id": self.run_id,
            "html_url": self.matrix["official_rc_observation"]["verified_source_build_run"],
            "repository": {"full_name": REPO},
            "head_branch": BRANCH,
            "head_sha": self.sha,
            "status": "completed",
            "conclusion": "success",
        }

    def check_reject(self):
        with self.assertRaises(TraceFailure):
            verify_live_identity(self.record, self.branch, self.run)

    def test_genuine_same_head_metadata(self):
        report = verify_live_identity(self.record, self.branch, self.run)
        self.assertEqual(report["verified_same_head"], self.sha)
        self.assertEqual(report["source_identity"], "LIVE_SAME_HEAD_VERIFIED")
        self.assertTrue(report["official_rc_zip_bytes"].startswith("UNKNOWN"))

    def test_rc_head_advanced_but_snapshot_stale(self):
        self.branch["commit"]["sha"] = "a" * 40
        self.check_reject()

    def test_actions_good_but_for_another_commit(self):
        self.run["head_sha"] = "b" * 40
        self.check_reject()

    def test_actions_run_different_from_claimed_run(self):
        self.run["id"] += 1
        self.check_reject()

    def test_actions_url_other_repo(self):
        self.record["official_rc_observation"]["verified_source_build_run"] = (
            "https://github.com/other/repo/actions/runs/" + str(self.run_id)
        )
        self.check_reject()

    def test_actions_wrong_branch(self):
        self.run["head_branch"] = "main"
        self.check_reject()

    def test_actions_other_repository(self):
        self.run["repository"]["full_name"] = "someone/other"
        self.check_reject()

    def test_in_progress_or_failure_is_not_success(self):
        self.run["conclusion"] = "failure"
        self.check_reject()
        self.run["conclusion"] = "success"
        self.run["status"] = "in_progress"
        self.check_reject()

    def test_branch_name_cannot_be_spoofed(self):
        self.branch["name"] = "main"
        self.check_reject()

    def test_old_success_without_exact_actions_url(self):
        self.run["html_url"] = "https://github.com/" + REPO + "/actions/runs/1"
        self.check_reject()


if __name__ == "__main__":
    unittest.main()
