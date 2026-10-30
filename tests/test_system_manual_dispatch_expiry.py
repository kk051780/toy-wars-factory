"""Fail-first regressions for manual DISPATCH expiry in the accepted coordinator planner.

These are pure helper tests, NOT proof of authenticated provider-run admission,
service execution, GitHub CAS, task delivery, or live unattended coding.
"""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import acquire, initial_state, release

DISPATCHER = "4a26aba5-3470-43d2-a557-74dcc5eba181"
WORKER = "23e9ebe9-179c-8326-8fdd-ac241ec4ef53"
ANOTHER = "039874ac-64a0-8323-bc57-5c35cf58ec90"
START = "2026-10-30T07:00:00Z"
BEFORE_EXPIRY = "2026-10-30T07:01:59Z"
AT_EXPIRY = "2026-10-30T07:02:00Z"
AFTER_EXPIRY = "2026-10-30T07:04:00Z"


class ManualDispatchExpiryTests(unittest.TestCase):
    def ticket(self):
        r = acquire(initial_state(), "DISPATCH", DISPATCHER, START,
                    service_status="completed")
        self.assertEqual(r["action"], "ACQUIRE")
        self.assertTrue(r["write"])
        return r["state"]

    def worker(self, ticket, at=BEFORE_EXPIRY, owner=WORKER,
               task_id=None):
        return acquire(ticket, "WORKER", owner, at,
                       actor_task_id=task_id,
                       work_branch="auto/twf-game-repair-" + owner)

    def test_valid_ticket_still_adopted_by_registered_worker(self):
        t = self.ticket()
        r = self.worker(t)
        self.assertEqual(r["action"], "ACQUIRE")
        self.assertTrue(r["write"])
        self.assertEqual(r["state"]["epoch"], t["epoch"] + 1)
        self.assertEqual(r["state"]["holder"]["kind"], "WORKER")
        self.assertEqual(r["state"]["holder"]["origin"], "manual")
        self.assertEqual(r["state"]["holder"]["owner_id"], WORKER)
        self.assertIsNone(t["last_completed"])

    def test_exact_expiry_boundary_does_not_grant_writer(self):
        t = self.ticket()
        original = copy.deepcopy(t)
        r = self.worker(t, AT_EXPIRY)
        self.assertEqual(r["action"], "WAIT_DISPATCH_EXPIRED")
        self.assertFalse(r["write"])
        self.assertEqual(r["state"], original)
        self.assertEqual(t, original)

    def test_long_expired_ticket_never_becomes_worker_lease(self):
        t = self.ticket()
        r = self.worker(t, AFTER_EXPIRY)
        self.assertEqual(r["action"], "WAIT_DISPATCH_EXPIRED")
        self.assertFalse(r["write"])
        self.assertEqual(r["state"]["epoch"], t["epoch"])
        self.assertEqual(r["state"]["holder"]["kind"], "DISPATCH")

    def test_second_manual_go_joins_original_ticket(self):
        t = self.ticket()
        r = acquire(t, "DISPATCH", ANOTHER, BEFORE_EXPIRY,
                    service_status="completed")
        self.assertEqual(r["action"], "JOIN_EXISTING")
        self.assertFalse(r["write"])

    def test_unregistered_worker_still_rejected(self):
        with self.assertRaisesRegex(ValueError, "registered"):
            self.worker(self.ticket(), task_id="unregistered-task")

    def test_only_ticket_issuer_may_clean_up_expired_ticket(self):
        t = self.ticket()
        with self.assertRaisesRegex(ValueError, "only the current"):
            release(t, "DISPATCH", WORKER, t["epoch"], AFTER_EXPIRY)
        cleaned = release(t, "DISPATCH", DISPATCHER, t["epoch"], AFTER_EXPIRY)
        self.assertIsNone(cleaned["holder"])
        self.assertEqual(cleaned["epoch"], t["epoch"])

    def test_expired_controller_not_taken_over_as_dispatch(self):
        t = acquire(initial_state(), "CONTROLLER", DISPATCHER, START)["state"]
        r = self.worker(t, "2026-10-30T07:31:00Z")
        self.assertEqual(r["action"], "WAIT_RECOVERY")
        self.assertFalse(r["write"])


if __name__ == "__main__":
    unittest.main()
