"""Issue128 protected fail-first: declared META cadence matches hourly provider.

This checks SOURCE declarations only, never claims an authenticated provider
execution, task origin, automatic merge, or Roblox engine execution.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK = "6add445e4138819197d9cf2b1a02534d"

class MetaHourlyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "config/autonomous_repair.json").read_text())
        cls.state = json.loads((ROOT / "PROJECT_STATE.json").read_text())
        cls.builder = (ROOT / "tools/build_handoff.py").read_text()
        cls.agents = (ROOT / "AGENTS.md").read_text()
        cls.docs = (ROOT / "docs/SYSTEM_REVIEW.md").read_text()

    def test_config_hourly(self):
        self.assertEqual(type(self.config["system_review"]["cadence_hours"]), int)
        self.assertEqual(self.config["system_review"]["cadence_hours"], 1)

    def test_config_anchor(self):
        self.assertEqual(self.config["system_review"]["local_start"], "07:45")

    def test_state_hourly(self):
        self.assertEqual(type(self.state["system_review"]["cadence_hours"]), int)
        self.assertEqual(self.state["system_review"]["cadence_hours"], 1)

    def test_state_anchor(self):
        self.assertEqual(self.state["system_review"]["local_start"], "07:45")

    def test_state_hourly_status(self):
        self.assertEqual(self.state["system_review"]["status"],
                         "ENABLED_HOURLY_WITH_INDEPENDENT_INTEGRATION")

    def test_builder_not_hardcoded_daily(self):
        self.assertNotIn("## 体制とゲームの日次改善", self.builder)

    def test_builder_displays_hourly_anchor(self):
        self.assertIn("毎時45分を基準", self.builder)

    def test_agents_not_stale_daily(self):
        self.assertNotIn("The daily system/game review remains mandatory", self.agents)

    def test_docs_not_stale_morning(self):
        self.assertNotIn("ChatGPTの別タスクで毎朝", self.docs)

    def test_builder_checks_source_state_drift(self):
        self.assertIn("system review config/state cadence drift", self.builder)

    def test_builder_distinguishes_provider_observation(self):
        self.assertIn("接続先の実行時刻は別証拠", self.builder)

    def test_config_and_state_registered_task_same(self):
        self.assertEqual(self.config["system_review"]["task_id"], TASK)
        self.assertEqual(self.state["system_review"]["task_id"], TASK)

    def test_config_state_flexible_schedule_preserved(self):
        for data in (self.config, self.state):
            self.assertEqual(data["system_review"]["timezone"], "Asia/Tokyo")
            self.assertEqual(data["system_review"]["timing_mode"], "flexible_schedule")

    def test_source_does_not_expand_automatic_merge(self):
        self.assertIs(self.config["system_review"]["automatic_merge_authorized"], False)
        self.assertIs(self.config["integration"]["author_task_may_merge"], False)

    def test_worker_and_reviewer_schedules_not_modified(self):
        self.assertEqual(self.config["cadence_hours"], 1)
        self.assertEqual(self.config["integration"]["cadence_hours"], 1)

    def test_source_config_and_state_cadence_consistent(self):
        keys=("task_id","cadence_hours","local_start","timezone","timing_mode")
        self.assertEqual({k:self.config["system_review"][k] for k in keys},
                         {k:self.state["system_review"][k] for k in keys})

if __name__ == "__main__":
    unittest.main()
