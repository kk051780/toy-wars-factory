"""Prevent a full draft PR from disabling or blocking all autonomous repair work."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_auto_diff import is_worker_branch
from repair_queue import choose_action

RUN = "9fd5c391-5054-832e-b21b-9527e78d6733"
OTHER = "c7058bdc-64e4-8332-95ba-06037acb5d28"
THIRD = "00000000-0000-0000-0000-000000000001"


class RepairQueueTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "config/autonomous_repair.json").read_text())

    def pr(self, number, ci="success", branch=None, state="open", repository=None):
        return {"number": number, "ci": ci, "branch": branch or self.policy["branch"],
                "state": state, "repository": repository or self.policy["repository"]}

    def decide(self, pulls):
        decision = choose_action(self.policy, pulls, RUN)
        self.assertFalse(decision["change_scheduler"])
        return decision

    def test_passed_pr35_does_not_block_next_independent_fix(self):
        decision = self.decide([self.pr(35)])
        self.assertEqual(decision["action"], "START")
        self.assertEqual(decision["base"], "main")
        self.assertEqual(decision["branch"], self.policy["branch_prefix"] + RUN)

    def test_failed_ci_is_repaired_before_starting_work_even_at_capacity(self):
        pulls = [self.pr(35), self.pr(38, "failure", self.policy["branch_prefix"] + OTHER),
                 self.pr(39, branch=self.policy["branch_prefix"] + THIRD)]
        decision = self.decide(pulls)
        self.assertEqual((decision["action"], decision["pr"]), ("REPAIR_CI", 38))

    def test_pending_or_absent_ci_waits_without_disabling(self):
        for status in ("pending", "in_progress", None):
            with self.subTest(status=status):
                self.assertEqual(self.decide([self.pr(35, status)])["action"], "WAIT_CI")

    def test_full_queue_waits_for_review_without_disabling(self):
        decision = self.decide([self.pr(35), self.pr(38, branch=self.policy["branch_prefix"] + OTHER),
                                self.pr(39, branch=self.policy["branch_prefix"] + THIRD)])
        self.assertEqual(decision["action"], "WAIT_REVIEW")

    def test_merge_or_close_frees_capacity_without_user_restart(self):
        pulls = [self.pr(35, state="closed"), self.pr(38, branch=self.policy["branch_prefix"] + OTHER),
                 self.pr(39, branch=self.policy["branch_prefix"] + THIRD)]
        self.assertEqual(self.decide(pulls)["action"], "START")

    def test_other_branches_and_foreign_forks_do_not_consume_slots(self):
        pulls = [self.pr(35, branch="fix/unrelated"), self.pr(38, repository="other/fork")]
        self.assertEqual(self.decide(pulls)["open_prs"], [])

    def test_retry_reuses_observed_pr_without_creating_duplicate(self):
        pr = self.pr(38, branch=self.policy["branch_prefix"] + RUN)
        self.assertEqual(self.decide([pr])["action"], "ALREADY_RECORDED")

    def test_missing_or_duplicated_metadata_cannot_invent_capacity(self):
        pr = self.pr(35)
        pr.pop("repository")
        self.assertEqual(self.decide([pr])["action"], "WAIT_METADATA")
        self.assertEqual(self.decide([self.pr(35), self.pr(35)])["action"], "WAIT_METADATA")
        pr = self.pr(35)
        pr.pop("state")
        self.assertEqual(self.decide([pr])["action"], "WAIT_METADATA")

    def test_owner_config_disable_stops_edits_without_scheduler_mutation(self):
        self.policy["enabled"] = False
        self.assertEqual(self.decide([])["action"], "DISABLED")

    def test_non_draft_mode_cannot_start_automatic_edits(self):
        self.policy["mode"] = "AUTO_MERGE"
        self.assertEqual(self.decide([])["action"], "DISABLED")

    def test_closed_run_branch_is_not_recreated_by_retry(self):
        pr = self.pr(38, branch=self.policy["branch_prefix"] + RUN, state="closed")
        self.assertEqual(self.decide([pr])["action"], "ALREADY_RECORDED")

    def test_legacy_and_uuid_lanes_are_the_only_accepted_branches(self):
        self.assertTrue(is_worker_branch(self.policy["branch"], self.policy))
        self.assertTrue(is_worker_branch(self.policy["branch_prefix"] + RUN, self.policy))
        for branch in ("auto/twf-game-repair-evil", "auto/twf-game-repair/other", "auto/twf-game-repair-" + RUN.upper(), "main"):
            with self.subTest(branch=branch):
                self.assertFalse(is_worker_branch(branch, self.policy))

    def test_noncanonical_run_identity_cannot_choose_new_branch(self):
        with self.assertRaises(ValueError):
            choose_action(self.policy, [], "unknown")


if __name__ == "__main__":
    unittest.main()
