import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_meta_diff import violations
from repair_queue import choose_system_action

RUN = "23e9ebe9-179c-8326-8fdd-ac241ec4ef53"


class SystemReviewScopeTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "config/autonomous_repair.json").read_text())

    def test_small_tool_fix_with_new_regression_is_allowed(self):
        self.assertEqual(violations([("M", "tools/repair_queue.py"), ("A", "tests/test_system_queue_regression.py")], self.policy), [])

    def test_protected_policy_and_game_edits_stay_blocked(self):
        for path in ("AGENTS.md", "config/quality_policy.json", "config/autonomous_repair.json", "src/ToyWarsServer.server.lua", ".github/workflows/bootstrap-quality.yml", "tools/check_meta_diff.py"):
            self.assertTrue(violations([("M", path), ("A", "tests/test_system_example.py")], self.policy))

    def test_existing_tests_cannot_be_weakened_or_deleted(self):
        for status in ("M", "D"):
            self.assertTrue(violations([(status, "tests/test_repair_control.py"), ("A", "tests/test_system_example.py")], self.policy))

    def test_research_alone_does_not_count_as_implementation(self):
        self.assertTrue(violations([("A", "docs/research/new_case.md")], self.policy))
        self.assertTrue(violations([("M", "tools/repair_queue.py")], self.policy))

    def test_full_game_queue_does_not_block_independent_system_review(self):
        pulls = [{"number": 35, "branch": self.policy["branch"], "repository": self.policy["repository"], "state": "open", "ci": "success"}]
        self.assertEqual(choose_system_action(self.policy, pulls, RUN)["action"], "START")

    def test_successful_meta_waits_for_approval_instead_of_stacking(self):
        pr = {"number": 41, "branch": self.policy["system_review"]["branch_prefix"] + RUN,
              "repository": self.policy["repository"], "state": "open", "ci": "success"}
        self.assertEqual(choose_system_action(self.policy, [pr], "039874ac-64a0-8323-bc57-5c35cf58ec90")["action"], "WAIT_REVIEW")
        pr["ci"] = "failure"
        self.assertEqual(choose_system_action(self.policy, [pr], RUN)["action"], "REPAIR_CI")


if __name__ == "__main__":
    unittest.main()
