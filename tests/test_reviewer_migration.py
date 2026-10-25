"""Guard exact-scheduled reviewer registration and immutable safety controls."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NEW = "6add6aaceb4c8191b1666fe15f97cd88"
OLD = "6add4ea80d3881919da4ea2c1d5def88"

class ReviewerMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "config/autonomous_repair.json").read_text(encoding="utf-8"))
        cls.state = json.loads((ROOT / "PROJECT_STATE.json").read_text(encoding="utf-8"))
        cls.prompt = (ROOT / "ops/CHATGPT_INTEGRATION_REVIEW_PROMPT.md").read_text(encoding="utf-8")
    def test_current_registration_consistent(self):
        self.assertEqual(self.config["integration"]["task_id"], NEW)
        self.assertEqual(self.state["independent_integration"]["task_id"], NEW)
        self.assertEqual(self.state["cloud_game_repair"]["independent_reviewer_task"], NEW)
        self.assertEqual(self.state["system_review"]["independent_reviewer_task"], NEW)
        self.assertIn(NEW, self.prompt)
        self.assertNotIn(OLD, self.prompt)
    def test_existing_workers_unchanged(self):
        self.assertEqual(self.config["task_id"], "6adbf0d6a7d881918ce181dff2468867")
        self.assertEqual(self.config["system_review"]["task_id"], "6add445e4138819197d9cf2b1a02534d")
        self.assertEqual(self.config["coordination"]["branch"], "twf-repair-coordinator")
        self.assertEqual(self.config["queue_version"], 4)
    def test_anti_self_review_and_release_hold(self):
        c = self.config
        i = c["integration"]
        self.assertTrue(i["enabled"] and c["automatic_merge_authorized"])
        self.assertTrue(i["require_independent_task_and_run"] and i["require_exact_head_ci"] and i["require_current_main_qa"])
        self.assertTrue(i["require_shared_reviewer_lease"] and i["require_post_merge_qa"])
        self.assertFalse(i["author_may_approve_own_work"] or i["author_task_may_merge"] or i["roblox_publish_authorized"])
        self.assertFalse(c["external_provider_inference_authorized"])
        self.assertEqual(self.state["release_decision"], "HOLD_ENGINE_UNVERIFIED")
    def test_new_candidate_not_falsely_marked_live(self):
        i = self.state["independent_integration"]
        self.assertEqual(i["status"], "PENDING_EXACT_REVIEWER_CUTOVER")
        self.assertIs(i["is_enabled_confirmed"], False)
        self.assertIs(i["runtime_verified"], False)
        self.assertEqual(self.state["cloud_game_repair"]["status"], "ENABLED_AUTHOR_REVIEWER_CUTOVER_PENDING")
        self.assertEqual(i["new_candidate_bootstrap"]["mode"], "READ_ONLY_SUCCESS_NOT_LIVE_INTEGRATION")
    def test_historical_task_provenance_retained(self):
        self.assertTrue(any(OLD in str(item) for item in self.state["resume_checkpoint"]["completed"]))

if __name__ == "__main__":
    unittest.main()
