"""P0 real Git probe planner / interleaving tests (NO host identity grant)."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import acquire, initial_state, owns, release, scoped_lease_migration_block
from repair_source_action_fence import propose_probe, reconcile_probe, WORK, FILE

RUN = "83a23b59-9eb0-4ec6-9f4d-753ea02694ea"
ACTION = "fa6971a6-8a13-4fc8-a2fe-b061e490db84"
SHA_A, SHA_B, SHA_C = "a"*40, "b"*40, "c"*40
BRANCH = "controller/p0-legacy-shadow-compat-20261108-76116caf"
REPO = "kk051780/toy-wars-factory"
NOW = "2026-11-08T02:11:10Z"

class SourceProbeTests(unittest.TestCase):
    def setUp(self):
        st = initial_state()
        st = acquire(st, "CONTROLLER", RUN, "2026-11-08T02:10:00Z",
                     base_main_sha=SHA_A, work_branch=BRANCH)["state"]
        self.snap = {"repository": REPO, "coordinator_ref": SHA_C,
                     "main_head": SHA_A, "work_branch": BRANCH,
                     "source_head": SHA_B, "state": st}
        self.req = {"operation_id": ACTION, "owner_id": RUN,
                    "owner_epoch": 1, "work_id": WORK,
                    "source_path": FILE, "before_head": SHA_B,
                    "after_head": "d"*40}

    def propose(self):
        return propose_probe(self.snap, self.req, NOW)

    def test_candidate_keeps_no_provider_authority(self):
        orig = copy.deepcopy(self.snap)
        p = self.propose()
        self.assertEqual(p["action"], "PROPOSE_CAS_SOURCE_ACTION")
        self.assertFalse(p["may_write"])
        self.assertFalse(p["provider_authenticated"])
        self.assertEqual(p["expected_coordinator_ref"], SHA_C)
        self.assertEqual(self.snap, orig)

    def test_pending_action_blocks_claim_owns_and_release(self):
        state = self.propose()["state"]
        self.assertTrue(scoped_lease_migration_block(state))
        self.assertFalse(owns(state, "CONTROLLER", RUN, 1, NOW))
        self.assertEqual(acquire(state, "WORKER", ACTION, NOW)["action"],
                         "WAIT_SCOPED_LEASES")
        with self.assertRaisesRegex(ValueError, "pending source action"):
            release(state, "CONTROLLER", RUN, 1, NOW)

    def test_pending_blocks_after_expiry(self):
        state = self.propose()["state"]
        self.assertTrue(scoped_lease_migration_block(state))
        self.assertFalse(owns(state, "CONTROLLER", RUN, 1,
                              "2026-11-09T02:00:00Z"))
        with self.assertRaises(ValueError):
            release(state, "CONTROLLER", RUN, 1,
                    "2026-11-09T02:00:00Z")

    def test_legacy_mode_and_occupied_writer_block(self):
        self.snap["state"]["parallel_write_migration"] = "SCOPED_ACTIVE"
        self.assertEqual(self.propose()["action"], "WAIT_EXISTING_ACTION_OR_MIGRATION")

    def test_no_holder_blocks_proposal(self):
        self.snap["state"]["holder"] = None
        self.assertEqual(self.propose()["action"], "WAIT_NOT_LIVE_CONTROLLER")

    def test_malformed_request_blocks(self):
        self.req["after_head"] = SHA_B
        self.assertEqual(self.propose()["action"], "WAIT_INVALID_SOURCE_PROPOSAL")

    def test_rejects_main_branch_and_coordinator_branch(self):
        for branch in ("main", "twf-repair-coordinator"):
            self.snap["work_branch"] = branch
            self.assertEqual(self.propose()["action"], "WAIT_INVALID_SOURCE_PROPOSAL")

    def test_rejects_foreign_repo_with_valid_syntax(self):
        for repository in ("another/repository", "kk051780/toy-wars-factory-fork"):
            self.snap["repository"] = repository
            self.assertEqual(self.propose()["action"], "WAIT_INVALID_SOURCE_PROPOSAL")

    def test_rejects_other_p0_branch_even_with_matching_holder(self):
        for branch in ("controller/p0-other-project", "controller/p0b-pr208-progressmode-lifecycle-20261108"):
            self.snap["work_branch"] = branch
            self.snap["state"]["holder"]["work_branch"] = branch
            self.assertEqual(self.propose()["action"], "WAIT_INVALID_SOURCE_PROPOSAL")

    def test_rejects_forged_task_or_owner(self):
        self.req["owner_id"] = ACTION
        self.assertEqual(self.propose()["action"], "WAIT_NOT_LIVE_CONTROLLER")
        self.req["owner_id"] = RUN
        self.snap["state"]["holder"]["task_id"] = "forged-task"
        self.assertEqual(self.propose()["action"], "WAIT_NOT_LIVE_CONTROLLER")

    def test_rejects_changed_main_or_source_head(self):
        self.snap["main_head"] = SHA_C
        self.assertEqual(self.propose()["action"], "WAIT_NOT_LIVE_CONTROLLER")
        self.snap["main_head"] = SHA_A
        self.snap["source_head"] = SHA_A
        self.assertEqual(self.propose()["action"], "WAIT_INVALID_SOURCE_PROPOSAL")

    def test_duplicate_action_denied(self):
        self.snap["state"] = self.propose()["state"]
        self.assertEqual(self.propose()["action"], "WAIT_EXISTING_ACTION_OR_MIGRATION")

    def test_bad_pending_schema_causes_fail_closed(self):
        state = self.propose()["state"]
        state["pending_source_action"]["before_head"] = None
        with self.assertRaises(ValueError):
            scoped_lease_migration_block(state)
        with self.assertRaises(ValueError):
            release(state, "CONTROLLER", RUN, 1, NOW)

    def test_valid_two_readback_settlement_is_only_a_proposal(self):
        self.snap["state"] = self.propose()["state"]
        p = reconcile_probe(self.snap, self.req,
                            source_ref_first="d"*40,
                            source_ref_second="d"*40,
                            now="2026-11-08T02:12:00Z")
        self.assertEqual(p["action"], "PROPOSE_CAS_RECONCILIATION")
        self.assertFalse(p["may_write"])
        self.assertFalse(p["provider_authenticated"])
        self.assertNotIn("pending_source_action", p["state"])
        self.assertEqual(p["state"]["last_source_action_probe"]["after_head"],
                         "d"*40)

    def test_no_settlement_when_source_unchanged(self):
        self.snap["state"] = self.propose()["state"]
        p = reconcile_probe(self.snap, self.req,
                            source_ref_first=SHA_B,
                            source_ref_second=SHA_B, now=NOW)
        self.assertEqual(p["action"], "WAIT_UNVERIFIED_GIT_READBACK")

    def test_source_changed_by_third_party_aborts(self):
        self.snap["state"] = self.propose()["state"]
        p = reconcile_probe(self.snap, self.req,
                            source_ref_first=SHA_C,
                            source_ref_second=SHA_C, now=NOW)
        self.assertEqual(p["action"], "WAIT_UNVERIFIED_GIT_READBACK")

    def test_different_readbacks_abort(self):
        self.snap["state"] = self.propose()["state"]
        p = reconcile_probe(self.snap, self.req,
                            source_ref_first="d"*40,
                            source_ref_second=SHA_C, now=NOW)
        self.assertEqual(p["action"], "WAIT_UNVERIFIED_GIT_READBACK")

    def test_wrong_operation_cannot_settle_other(self):
        self.snap["state"] = self.propose()["state"]
        self.req["operation_id"] = RUN
        p = reconcile_probe(self.snap, self.req,
                            source_ref_first="d"*40,
                            source_ref_second="d"*40, now=NOW)
        self.assertEqual(p["action"], "WAIT_UNVERIFIED_GIT_READBACK")

    def test_settlement_is_not_provider_authenticated(self):
        self.snap["state"] = self.propose()["state"]
        p = reconcile_probe(self.snap, self.req,
                            source_ref_first="d"*40,
                            source_ref_second="d"*40, now=NOW)
        self.assertFalse(p["host_action_fence_verified"])
        self.assertFalse(p["may_merge"])
        self.assertFalse(p["real_parallel"])

if __name__ == "__main__":
    unittest.main()
