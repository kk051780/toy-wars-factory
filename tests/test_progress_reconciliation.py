"""First real separate-review merge proof cannot weaken engine/release holds."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
class EvidenceSyncTests(unittest.TestCase):
    def test_pr45_first_live_cycle(self):
        state = json.loads((ROOT / "PROJECT_STATE.json").read_text(encoding="utf-8"))
        integration = state["independent_integration"]
        self.assertTrue(integration["runtime_verified"])
        self.assertTrue(integration["is_enabled_confirmed"])
        self.assertEqual(integration["first_full_cycle"]["pr"],45)
        self.assertEqual(integration["first_full_cycle"]["reviewer_task_id"], integration["task_id"])
        self.assertEqual(integration["first_full_cycle"]["shared_lease_epoch"],18)
        self.assertEqual(integration["first_full_cycle"]["merge_commit"],"8f3312ba7b61095f839b7121e2776bfca6245aee")
        self.assertIn("40157791404",integration["first_full_cycle"]["post_merge_qa"])
    def test_game_and_provider_hold_unchanged(self):
        state = json.loads((ROOT / "PROJECT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["release_decision"],"HOLD_ENGINE_UNVERIFIED")
        self.assertEqual(state["verification"]["roblox_studio"],"NOT_RUN")
        self.assertEqual(state["verification"]["two_client_multiplayer"],"NOT_RUN")
        self.assertEqual(state["verification"]["mobile_visual"],"NOT_RUN")
        self.assertFalse(state["independent_integration"]["roblox_publish_authorized"])
        self.assertFalse(state["autonomous_coding"]["proposed_migration"]["next_reexecution_authorized"])
if __name__ == "__main__": unittest.main()
