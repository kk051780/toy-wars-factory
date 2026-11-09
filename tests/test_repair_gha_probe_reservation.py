"""Fail-closed tests for the non-authorizing PR210 GHA reservation proposal."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import (acquire, initial_state, owns, release,
                            scoped_lease_migration_block)
from repair_gha_probe_reservation import propose_branch_reservation

OWNER = "2c6dc0ab-e850-4d68-9b0f-489c7d59383a"
SECOND = "d60368f2-b2c4-4dd0-b56e-0efc5d53c5b6"
OP = "b71adb15-4111-4348-a1a2-c20a8e346c08"
REPO = "kk051780/toy-wars-factory"
RUN = 41199998877
BRANCH = f"controller/gha-write-probe-{RUN}-a1"
SHA = "a" * 40
START = "2026-11-09T01:00:00Z"
NOW = "2026-11-09T01:00:05Z"


class OwnerGhaReservationTests(unittest.TestCase):
    def setUp(self):
        initial = initial_state()
        lease = acquire(initial, "CONTROLLER", OWNER, START,
                        base_main_sha=SHA, work_branch=BRANCH)
        self.assertEqual(lease["action"], "ACQUIRE")
        self.snapshot = {"repository": REPO, "coordinator_ref": "c" * 40,
                         "main_head": SHA, "state": lease["state"]}
        self.request = {"operation_id": OP, "owner_id": OWNER,
                        "owner_epoch": 1, "run_id": RUN,
                        "run_attempt": 1, "mode": "BRANCH_ONLY"}

    def proposal(self):
        return propose_branch_reservation(self.snapshot, self.request, NOW)

    def test_proposal_is_pure_and_never_authorizes_actual_write(self):
        before = deepcopy(self.snapshot)
        result = self.proposal()
        self.assertEqual(result["action"], "PROPOSE_CAS_OWNER_GHA_PROBE_RESERVATION")
        for forbidden in ("may_write", "may_merge", "may_dispatch", "may_release",
                          "provider_authenticated", "real_parallel"):
            self.assertFalse(result[forbidden])
        self.assertEqual(result["expected_coordinator_ref"], "c" * 40)
        self.assertEqual(self.snapshot, before)
        pending = result["state"]["pending_source_action"]
        self.assertEqual(pending["source_path"], f"ops/probes/gha-write-{RUN}-a1.json")
        self.assertEqual(pending["work_branch"], BRANCH)
        self.assertEqual(pending["main_head"], SHA)

    def test_pending_rejects_second_controller_even_after_expiry(self):
        blocked = self.proposal()["state"]
        self.assertTrue(scoped_lease_migration_block(blocked))
        self.assertFalse(owns(blocked, "CONTROLLER", OWNER, 1, NOW))
        self.assertEqual(acquire(blocked, "CONTROLLER", SECOND, NOW)["action"],
                         "WAIT_SCOPED_LEASES")
        self.assertEqual(acquire(blocked, "CONTROLLER", SECOND,
                                 "2026-11-10T01:00:00Z")["action"],
                         "WAIT_SCOPED_LEASES")
        with self.assertRaisesRegex(ValueError, "pending source action"):
            release(blocked, "CONTROLLER", OWNER, 1, NOW)

    def test_exact_provenance_schema_rejects_spoofed_and_mutated_record(self):
        original = self.proposal()["state"]
        modifications = (
            ("kind", "SOURCE_UPDATE_PROBE"),
            ("repository", "other/repository"),
            ("work_branch", "main"),
            ("source_path", "ops/probes/not-the-request.json"),
            ("work_id", "ANY_OTHER_WORK"),
            ("mode", "DRAFT_PR"),
            ("phase", "SETTLED"),
            ("run_id", True),
            ("run_attempt", 2),
            ("main_head", "b" * 40),
            ("owner_epoch", 2),
            ("owner_id", SECOND),
            ("schema", True),
        )
        for field, value in modifications:
            with self.subTest(field=field, value=value):
                invalid = deepcopy(original)
                invalid["pending_source_action"][field] = value
                with self.assertRaises(ValueError):
                    scoped_lease_migration_block(invalid)

    def test_pending_reservation_must_match_holder_and_time(self):
        for mutation in ("holder", "epoch", "branch", "main", "timestamp"):
            with self.subTest(mutation=mutation):
                invalid = deepcopy(self.proposal()["state"])
                if mutation == "holder":
                    invalid["holder"] = None
                elif mutation == "epoch":
                    invalid["pending_source_action"]["owner_epoch"] = 77
                elif mutation == "branch":
                    invalid["holder"]["work_branch"] = "controller/p0-foreign"
                elif mutation == "main":
                    invalid["holder"]["base_main_sha"] = "b" * 40
                else:
                    invalid["pending_source_action"]["reserved_at"] = "2099-01-01T00:00:00Z"
                with self.assertRaises(ValueError):
                    scoped_lease_migration_block(invalid)

    def test_request_does_not_accept_fake_run_or_broader_mode(self):
        for field, val in (("run_id", True), ("run_id", -3),
                           ("run_attempt", 2), ("run_attempt", 1.0),
                           ("mode", "DRAFT_PR"), ("owner_id", SECOND),
                           ("owner_epoch", True)):
            with self.subTest(field=field, val=val):
                self.request[field] = val
                self.assertNotEqual(self.proposal()["action"],
                                    "PROPOSE_CAS_OWNER_GHA_PROBE_RESERVATION")
                self.setUp()

    def test_absent_lease_or_other_branch_rejected(self):
        self.snapshot["state"]["holder"] = None
        self.assertNotEqual(self.proposal()["action"],
                            "PROPOSE_CAS_OWNER_GHA_PROBE_RESERVATION")
        self.setUp()
        self.snapshot["state"]["holder"]["work_branch"] = "controller/other"
        self.assertEqual(self.proposal()["action"], "WAIT_AUTHENTIC_OWNER_LEASE")

    def test_duplicate_reservation_not_a_second_write_permit(self):
        self.snapshot["state"] = self.proposal()["state"]
        self.assertEqual(self.proposal()["action"], "WAIT_PENDING_ACTION_OR_MIGRATION")


if __name__ == "__main__":
    unittest.main()
