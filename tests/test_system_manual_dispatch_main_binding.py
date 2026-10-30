"""Fail-first tests: DISPATCH admission must retain its exact main SHA source pin.

The accepted PR139 checks expiration; these tests intentionally demonstrate that
live tickets with changed/missing source references are currently adoptable.
Pure coordinator helper tests. Never evidence of service execution or GitHub CAS.
"""
import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from repair_control import acquire, initial_state, TASK_ID

ISSUER = "4a26aba5-3470-43d2-a557-74dcc5eba181"
WORKER = "23e9ebe9-179c-8326-8fdd-ac241ec4ef53"
FOREIGN = "039874ac-64a0-8323-bc57-5c35cf58ec90"
SOURCE = "a" * 40
CHANGED = "b" * 40
ISSUED = "2026-10-30T07:00:00Z"
LIVE = "2026-10-30T07:01:00Z"
EXPIRED = "2026-10-30T07:02:00Z"
BEFORE_ISSUE = "2026-10-30T06:59:59Z"


class DispatchMainBindingTests(unittest.TestCase):
    def ticket(self, sha=SOURCE):
        packet = acquire(initial_state(), "DISPATCH", ISSUER, ISSUED,
                         service_status="completed", base_main_sha=sha)
        self.assertEqual(packet["action"], "ACQUIRE")
        self.assertTrue(packet["write"])
        return packet["state"]

    def worker(self, ticket, *, sha=SOURCE, at=LIVE, owner=WORKER):
        return acquire(ticket, "WORKER", owner, at,
                       base_main_sha=sha, actor_task_id=TASK_ID,
                       work_branch="auto/twf-game-repair-" + owner)

    def assert_denied(self, result, ticket, action):
        self.assertEqual(result["action"], action)
        self.assertFalse(result["write"])
        self.assertEqual(result["state"], ticket)
        self.assertEqual(result["state"]["epoch"], ticket["epoch"])
        self.assertEqual(result["state"]["holder"]["kind"], "DISPATCH")

    def test_matching_main_still_allows_live_registered_adoption(self):
        ticket = self.ticket()
        r = self.worker(ticket)
        self.assertEqual(r["action"], "ACQUIRE")
        self.assertTrue(r["write"])
        self.assertEqual(r["state"]["holder"]["kind"], "WORKER")
        self.assertEqual(r["state"]["holder"]["base_main_sha"], SOURCE)
        self.assertEqual(r["state"]["epoch"], ticket["epoch"] + 1)

    def test_changed_main_rejected_without_consume(self):
        ticket = self.ticket()
        self.assert_denied(self.worker(ticket, sha=CHANGED), ticket,
                           "WAIT_DISPATCH_MAIN_CHANGED")

    def test_missing_ticket_main_denied(self):
        ticket = self.ticket(None)
        self.assert_denied(self.worker(ticket), ticket,
                           "WAIT_DISPATCH_MAIN_UNBOUND")

    def test_missing_worker_main_denied(self):
        ticket = self.ticket()
        self.assert_denied(self.worker(ticket, sha=None), ticket,
                           "WAIT_DISPATCH_MAIN_UNBOUND")

    def test_bad_ticket_main_denied(self):
        ticket = self.ticket("z" * 40)
        self.assert_denied(self.worker(ticket), ticket,
                           "WAIT_DISPATCH_MAIN_UNBOUND")

    def test_bad_worker_main_denied(self):
        ticket = self.ticket()
        self.assert_denied(self.worker(ticket, sha="z" * 40), ticket,
                           "WAIT_DISPATCH_MAIN_UNBOUND")

    def test_short_ticket_sha_denied(self):
        ticket = self.ticket("a" * 39)
        self.assert_denied(self.worker(ticket), ticket,
                           "WAIT_DISPATCH_MAIN_UNBOUND")

    def test_uppercase_worker_sha_denied(self):
        ticket = self.ticket()
        self.assert_denied(self.worker(ticket, sha=SOURCE.upper()), ticket,
                           "WAIT_DISPATCH_MAIN_UNBOUND")

    def test_worker_cannot_adopt_before_ticket_issue(self):
        ticket = self.ticket()
        self.assert_denied(self.worker(ticket, at=BEFORE_ISSUE), ticket,
                           "WAIT_DISPATCH_BEFORE_ISSUE")

    def test_expiry_keeps_pr139_priority(self):
        ticket = self.ticket()
        self.assert_denied(self.worker(ticket, at=EXPIRED), ticket,
                           "WAIT_DISPATCH_EXPIRED")

    def test_late_changed_main_still_denied_as_expired(self):
        ticket = self.ticket()
        self.assert_denied(self.worker(ticket, at=EXPIRED, sha=CHANGED), ticket,
                           "WAIT_DISPATCH_EXPIRED")

    def test_rejected_adoption_never_mutates_original_ticket(self):
        ticket = self.ticket()
        original = copy.deepcopy(ticket)
        self.worker(ticket, sha=CHANGED)
        self.assertEqual(ticket, original)

    def test_other_role_controller_not_adopted(self):
        controller = acquire(initial_state(), "CONTROLLER", ISSUER, ISSUED)["state"]
        r = self.worker(controller)
        self.assertEqual(r["action"], "WAIT_LOCK")
        self.assertFalse(r["write"])

    def test_foreign_worker_cannot_steal_active_worker(self):
        ticket = self.ticket()
        adopted = self.worker(ticket)["state"]
        r = self.worker(adopted, owner=FOREIGN)
        self.assertEqual(r["action"], "JOIN_EXISTING")
        self.assertFalse(r["write"])


if __name__ == "__main__":
    unittest.main()
