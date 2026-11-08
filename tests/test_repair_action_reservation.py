"""P0 action reservation negative tests: no real GitHub merge authority."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import acquire, initial_state, owns, release, scoped_lease_migration_block
from repair_action_reservation import proposed_reservation, apply_once

RUN = "00000000-0000-0000-0000-00000000a101"
TASK = "6add6aaceb4c8191b1666fe15f97cd88"
NOW = "2026-11-08T01:00:20Z"
ACTION = "11111111-1111-4111-8111-111111111111"
SHA1 = "a" * 40
SHA2 = "b" * 40
SHA3 = "c" * 40

class MockGitHost:
    def __init__(self, snapshot):
        self.row = copy.deepcopy(snapshot)
        self.cas_calls = 0
        self.fail_ack = False
        self.mutate_on_read = False
    def read(self):
        if self.mutate_on_read:
            self.row["main_head"] = "f"*40
        return copy.deepcopy(self.row)
    def cas(self, expected, state):
        self.cas_calls += 1
        if self.fail_ack:
            self.row["state"] = copy.deepcopy(state)
            self.row["ref_sha"] = SHA3
            raise RuntimeError("ambiguous after write")
        if self.row["ref_sha"] != expected:
            raise ValueError("CAS lost")
        self.row["state"] = copy.deepcopy(state)
        self.row["ref_sha"] = SHA3
        return SHA3

class ActionReservationTests(unittest.TestCase):
    def setUp(self):
        state = initial_state()
        state["authorized_tasks"]["REVIEWER"] = TASK
        state = acquire(state, "REVIEWER", RUN, "2026-11-08T01:00:00Z",
                        actor_task_id=TASK, work_branch="main",
                        base_main_sha=SHA1)["state"]
        self.snap = {"repository": "kk051780/toy-wars-factory",
                     "main_head": SHA1, "pr_head": SHA2,
                     "ref_sha": "d"*40, "state": state}
        self.req = {"action_id": ACTION, "reviewer_run_id": RUN,
                    "reviewer_task_id": TASK, "holder_epoch": 1,
                    "pr_number": 203, "pr_head": SHA2, "main_head": SHA1}

    def plan(self):
        return proposed_reservation(self.snap, self.req, NOW)

    def test_valid_review_owner_can_propose_but_never_execute(self):
        original = copy.deepcopy(self.snap)
        p = self.plan()
        self.assertEqual(p["action"], "PROPOSE_CAS_RESERVATION")
        self.assertFalse(p["may_execute"])
        self.assertFalse(p["provider_authenticated"])
        self.assertEqual(self.snap, original)
        self.assertEqual(p["expected_sha"], "d"*40)
        self.assertEqual(p["state"]["epoch"], 1)

    def test_reservation_blocks_legacy_acquisition_and_writes(self):
        p = self.plan()
        self.assertTrue(scoped_lease_migration_block(p["state"]))
        self.assertFalse(owns(p["state"], "REVIEWER", RUN, 1, NOW))
        other = acquire(p["state"], "CONTROLLER", ACTION, NOW)
        self.assertEqual(other["action"], "WAIT_SCOPED_LEASES")
        self.assertFalse(other["write"])

    def test_release_rejected_until_external_provider_reconciles(self):
        p = self.plan()
        with self.assertRaisesRegex(ValueError, "pending provider action"):
            release(p["state"], "REVIEWER", RUN, 1, NOW)
        self.assertIsNotNone(p["state"]["holder"])
        self.assertIsNotNone(p["state"]["pending_provider_action"])

    def test_no_holder_or_wrong_epoch_rejected(self):
        self.snap["state"]["holder"] = None
        self.assertNotEqual(self.plan()["action"], "PROPOSE_CAS_RESERVATION")
        self.snap["state"] = copy.deepcopy(self.setUpAndGetState())
        self.req["holder_epoch"] = 2
        self.assertEqual(self.plan()["action"], "WAIT_AUTHENTIC_REVIEWER_HOLDER")

    def setUpAndGetState(self):
        state = initial_state()
        state["authorized_tasks"]["REVIEWER"] = TASK
        return acquire(state, "REVIEWER", RUN, "2026-11-08T01:00:00Z",
                       actor_task_id=TASK, work_branch="main")["state"]

    def test_wrong_task_or_run_denied(self):
        self.req["reviewer_task_id"] = "different-task"
        self.assertNotEqual(self.plan()["action"], "PROPOSE_CAS_RESERVATION")
        self.req["reviewer_task_id"] = TASK
        self.req["reviewer_run_id"] = ACTION
        self.assertNotEqual(self.plan()["action"], "PROPOSE_CAS_RESERVATION")

    def test_pr_and_main_drift_denied(self):
        self.req["pr_head"] = SHA1
        self.assertEqual(self.plan()["action"], "WAIT_INVALID_OR_STALE_REQUEST")
        self.req["pr_head"] = SHA2
        self.req["main_head"] = SHA3
        self.assertEqual(self.plan()["action"], "WAIT_INVALID_OR_STALE_REQUEST")

    def test_scoped_migration_denies_reservation(self):
        self.snap["state"]["parallel_write_migration"] = "SCOPED_ACTIVE"
        self.assertEqual(self.plan()["action"], "WAIT_ACTION_OR_MIGRATION")

    def test_preexisting_reservation_cannot_be_replayed(self):
        p = self.plan()
        self.snap["state"] = p["state"]
        self.assertEqual(self.plan()["action"], "WAIT_ACTION_OR_MIGRATION")

    def test_malformed_reservation_fails_closed(self):
        p = self.plan()
        state = p["state"]
        state["pending_provider_action"]["pr_head"] = 123
        with self.assertRaises(ValueError):
            scoped_lease_migration_block(state)
        with self.assertRaises(ValueError):
            release(state, "REVIEWER", RUN, 1, NOW)

    def test_mock_cas_success_is_still_not_provider_permission(self):
        host = MockGitHost(self.snap)
        result = apply_once(self.snap, self.plan(), read=host.read,
                            cas=host.cas, clock=lambda: "2026-11-08T01:00:21Z")
        self.assertEqual(result["action"], "MOCK_RESERVATION_READBACK_NO_PROVIDER_ACTION")
        self.assertTrue(result["cas_attempted"])
        self.assertFalse(result["may_execute"])
        self.assertFalse(result["provider_write_proven"])
        self.assertEqual(host.cas_calls, 1)

    def test_pre_cas_drift_cannot_write(self):
        host = MockGitHost(self.snap)
        host.mutate_on_read = True
        r = apply_once(self.snap, self.plan(), read=host.read,
                       cas=host.cas, clock=lambda: "2026-11-08T01:00:21Z")
        self.assertEqual(r["action"], "WAIT_PRE_CAS_DRIFT")
        self.assertEqual(host.cas_calls, 0)

    def test_proposal_mutation_cannot_write(self):
        p = self.plan()
        p["state"]["pending_provider_action"]["pr_number"] = 204
        host = MockGitHost(self.snap)
        r = apply_once(self.snap, p, read=host.read,
                       cas=host.cas, clock=lambda: "2026-11-08T01:00:21Z")
        self.assertEqual(r["action"], "WAIT_PRE_CAS_DRIFT")
        self.assertEqual(host.cas_calls, 0)

    def test_stale_proposal_expiry_rejected(self):
        host = MockGitHost(self.snap)
        r = apply_once(self.snap, self.plan(), read=host.read,
                       cas=host.cas, clock=lambda: "2026-11-08T01:01:00Z")
        self.assertEqual(r["action"], "WAIT_PRE_CAS_DRIFT")
        self.assertEqual(host.cas_calls, 0)

    def test_uncertain_ack_stays_blocked_without_retry(self):
        host = MockGitHost(self.snap)
        host.fail_ack = True
        r = apply_once(self.snap, self.plan(), read=host.read,
                       cas=host.cas, clock=lambda: "2026-11-08T01:00:21Z")
        self.assertEqual(r["action"], "WAIT_CAS_ACK_UNKNOWN")
        self.assertEqual(host.cas_calls, 1)
        self.assertFalse(r["may_execute"])
        self.assertTrue(scoped_lease_migration_block(host.row["state"]))

    def test_new_ref_alone_not_authorizing(self):
        p = self.plan()
        host = MockGitHost(self.snap)
        host.cas = lambda e,s: SHA3
        r = apply_once(self.snap, p, read=host.read, cas=host.cas,
                       clock=lambda: "2026-11-08T01:00:21Z")
        self.assertEqual(r["action"], "WAIT_CAS_READBACK_UNCONFIRMED")
        self.assertFalse(r["may_execute"])

if __name__ == "__main__":
    unittest.main()
