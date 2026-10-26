"""Regression for PR69's accepted source; reuse its canonical evidence fixtures."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from system_host_write_triage import classify
from test_system_host_write_triage import fixtures, holder, NOW


class TriageTerminalOutcomeTests(unittest.TestCase):
    def assert_not_safe(self, value):
        self.assertEqual(value["state"], "INDETERMINATE", value)
        self.assertEqual(value["reason"], "SERVICE_NOT_SUCCESSFULLY_COMPLETED")
        self.assertFalse(value["safe_to_next_schedule"])
        self.assertFalse(value["claim_verified"])
        for flag in ("write_authorized", "start_now_allowed", "takeover_allowed"):
            self.assertIs(value[flag], False)

    def test_failed_service_is_not_safe_even_with_exact_run_head_green_qa(self):
        evidence, config = fixtures()
        evidence["service"]["data"]["last_run"]["recorded_status"] = "failed"
        self.assert_not_safe(classify(evidence, config, NOW))

    def test_no_update_service_is_not_safe_even_with_exact_run_head_green_qa(self):
        evidence, config = fixtures()
        evidence["service"]["data"]["last_run"]["recorded_status"] = "no_update"
        self.assert_not_safe(classify(evidence, config, NOW))

    def test_completed_service_keeps_existing_safe_wait_behavior(self):
        evidence, config = fixtures()
        value = classify(evidence, config, NOW)
        self.assertEqual(value["state"], "SAFE_TO_NEXT_SCHEDULE")
        self.assertTrue(value["safe_to_next_schedule"])
        self.assertFalse(value["write_authorized"])
        self.assertFalse(value["start_now_allowed"])
        self.assertFalse(value["takeover_allowed"])

    def test_failed_or_suppressed_owner_can_still_be_diagnosed_as_orphan(self):
        # These are usable terminal observations for orphan diagnosis, not
        # evidence of a healthy completed task. Do not ban them in service().
        from copy import deepcopy
        for state in ("failed", "no_update"):
            with self.subTest(recorded_status=state):
                evidence, config = fixtures()
                holder(evidence, expired=True)
                evidence["service"]["data"]["last_run"]["recorded_status"] = state
                evidence["holder_service"] = deepcopy(evidence["service"])
                value = classify(evidence, config, NOW)
                self.assertEqual(value["state"], "WRITER_EXITED_WITHOUT_RELEASE")
                self.assertFalse(value["safe_to_next_schedule"])
                self.assertFalse(value["takeover_allowed"])
                self.assertFalse(value["write_authorized"])


if __name__ == "__main__":
    unittest.main()
