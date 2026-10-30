"""RED->GREEN recovery provenance regressions; local JSON never authenticates provider."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from repair_control import initial_state, acquire, recover_finished_worker

RUN = "49a54157-e358-8325-abf9-b6f21d5faf35"
TASK = "6add445e4138819197d9cf2b1a02534d"
CLAIM = "2026-10-30T07:53:37Z"
START = "2026-10-30T07:45:52.992741Z"
SHIFT = "2026-10-30T08:04:45.167629Z"
END = "2026-10-30T08:08:46.660817Z"
NOW = "2026-10-30T08:40:00Z"

def lease():
    s = initial_state()
    s["authorized_tasks"]["META"] = TASK
    r = acquire(s, "META", RUN, CLAIM, actor_task_id=TASK,
                work_branch="auto/twf-system-review-" + RUN)
    assert r["action"] == "ACQUIRE"
    return r["state"]

def ended(**kw):
    r = {"id": RUN, "recorded_status": "completed",
         "started_at": START, "completed_at": END}
    r.update(kw)
    return r

class StartTimeRecoveryRegression(unittest.TestCase):
    def blocked(self, **changes):
        s = lease()
        before = copy.deepcopy(s)
        with self.assertRaises(ValueError):
            recover_finished_worker(s, ended(**changes), NOW)
        self.assertEqual(s, before)

    def test_same_run_changed_start_after_claim_must_block(self):
        self.blocked(started_at=SHIFT)

    def test_missing_start_must_block(self):
        s = lease()
        row = ended()
        del row["started_at"]
        with self.assertRaises(ValueError):
            recover_finished_worker(s, row, NOW)

    def test_none_start_must_block(self):
        self.blocked(started_at=None)

    def test_naive_start_must_block(self):
        self.blocked(started_at="2026-10-30T07:45:52")

    def test_start_after_completion_must_block(self):
        self.blocked(started_at="2026-10-30T08:08:47Z")

    def test_wrong_run_must_block(self):
        self.blocked(id="23e9ebe9-179c-8326-8fdd-ac241ec4ef53")

    def test_nonterminal_must_block(self):
        self.blocked(recorded_status="in_progress", completed_at=None)

    def test_completion_before_claim_must_block(self):
        self.blocked(completed_at="2026-10-30T07:53:36Z")

    def test_completion_in_future_must_block(self):
        self.blocked(completed_at="2026-10-30T08:41:00Z")

    def test_original_consistent_sequence_passes_helper_only(self):
        r = recover_finished_worker(lease(), ended(), NOW)
        self.assertIsNone(r["holder"])
        self.assertTrue(r["last_completed"]["recovered_from_service_evidence"])

    def test_start_equal_claim_passes_helper_only(self):
        r = recover_finished_worker(lease(), ended(started_at=CLAIM), NOW)
        self.assertIsNone(r["holder"])

if __name__ == "__main__":
    unittest.main()
