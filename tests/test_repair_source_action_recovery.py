"""P0 coordinator interruption recovery — no second GitHub write or lease takeover."""
import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from repair_control import initial_state, acquire
from repair_source_action_fence import (
    WORK, FILE, propose_probe, inspect_interrupted_probe,
)

REPO = "kk051780/toy-wars-factory"
BRANCH = "controller/p0-legacy-shadow-compat-20261108-76116caf"
OWNER = "83a23b59-9eb0-4ec6-9f4d-753ea02694ea"
OP = "7c2b40e1-6bca-43b6-a49c-27cf3e7a23b8"
MAIN, BEFORE, AFTER, COORD = "a"*40, "b"*40, "c"*40, "d"*40
START = "2026-11-08T02:10:00Z"
TIME = "2026-11-08T02:12:00Z"


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        state = initial_state()
        state = acquire(state, "CONTROLLER", OWNER, START,
                        base_main_sha=MAIN, work_branch=BRANCH)["state"]
        self.snap = dict(repository=REPO, coordinator_ref=COORD,
                         main_head=MAIN, work_branch=BRANCH,
                         source_head=BEFORE, state=state)
        self.req = dict(operation_id=OP, owner_id=OWNER, owner_epoch=1,
                        work_id=WORK, source_path=FILE,
                        before_head=BEFORE, after_head=AFTER)
        p = propose_probe(self.snap, self.req, "2026-11-08T02:11:00Z")
        self.assertEqual(p["action"], "PROPOSE_CAS_SOURCE_ACTION")
        self.snap["state"] = p["state"]

    def result(self, *, source=None, pr=None, main=None, parent=BEFORE,
               second=None, now=TIME):
        source = source or self.snap["source_head"]
        pr = pr or source
        main = main or MAIN
        first = copy.deepcopy(self.snap)
        other = copy.deepcopy(first) if second is None else second
        return inspect_interrupted_probe(first, other, self.req,
                    source_heads=(source, source),
                    pr_heads=(pr, pr),
                    main_heads=(main, main),
                    target_parent=parent, now=now)

    def test_old_head_is_ambiguous_not_safe_to_retry(self):
        v = self.result()
        self.assertEqual(v["action"], "WAIT_UNCERTAIN_NOT_APPLIED_DO_NOT_RETRY")
        self.assertFalse(v["may_retry"])
        self.assertFalse(v["may_write"])

    def test_applied_source_is_only_reconciliation_candidate(self):
        self.snap["source_head"] = AFTER
        v = self.result()
        self.assertEqual(v["action"], "CANDIDATE_OWNER_RECONCILE_ONLY")
        self.assertEqual(v["coordinator_ref"], COORD)
        self.assertFalse(v["may_release"])
        self.assertFalse(v["provider_authenticated"])
        self.assertFalse(v["may_merge"])

    def test_source_ref_changed_between_reads(self):
        self.snap["source_head"] = AFTER
        v = inspect_interrupted_probe(self.snap, copy.deepcopy(self.snap), self.req,
                 source_heads=(AFTER, BEFORE), pr_heads=(AFTER, AFTER),
                 main_heads=(MAIN, MAIN), target_parent=BEFORE, now=TIME)
        self.assertEqual(v["action"], "WAIT_SOURCE_REF_DRIFT")

    def test_coordinator_ref_changed_between_reads(self):
        second = copy.deepcopy(self.snap)
        second["coordinator_ref"] = "e"*40
        self.assertEqual(self.result(second=second)["action"],
                         "WAIT_COORDINATOR_REF_DRIFT")

    def test_pr_metadata_stale_refuses_reconcile(self):
        self.snap["source_head"] = AFTER
        self.assertEqual(self.result(pr=BEFORE)["action"], "WAIT_PR_HEAD_CHANGED")

    def test_main_advanced_refuses_reconcile(self):
        self.snap["source_head"] = AFTER
        self.assertEqual(self.result(main="f"*40)["action"], "WAIT_MAIN_CHANGED")

    def test_target_parent_wrong_refuses_reconcile(self):
        self.snap["source_head"] = AFTER
        self.assertEqual(self.result(parent="e"*40)["action"],
                         "WAIT_TARGET_PARENT_MISMATCH")

    def test_expired_holder_not_reclaimed(self):
        self.snap["source_head"] = AFTER
        self.assertEqual(self.result(now="2026-11-09T01:00:00Z")["action"],
                         "WAIT_SERVICE_TERMINATION_ATTESTATION")

    def test_future_clock_refuses_reconcile(self):
        self.snap["source_head"] = AFTER
        self.assertEqual(self.result(now=START)["action"], "WAIT_CLOCK_REGRESSION")

    def test_wrong_operation_cannot_reconcile(self):
        self.snap["source_head"] = AFTER
        self.req["operation_id"] = OWNER
        self.assertEqual(self.result()["action"], "WAIT_FOREIGN_OR_CHANGED_ACTION")

    def test_wrong_owner_cannot_reconcile(self):
        self.snap["source_head"] = AFTER
        self.req["owner_id"] = OP
        self.assertEqual(self.result()["action"], "WAIT_FOREIGN_OR_CHANGED_ACTION")

    def test_action_absent_is_not_safe_to_retry(self):
        self.snap["state"].pop("pending_source_action")
        self.assertEqual(self.result()["action"],
                         "WAIT_NO_PERSISTED_MATCHING_ACTION")

    def test_previously_reconciled_detected_without_reexecution(self):
        self.snap["source_head"] = AFTER
        self.snap["state"].pop("pending_source_action")
        self.snap["state"]["last_source_action_probe"] = {
            "operation_id": OP, "before_head": BEFORE,
            "after_head": AFTER, "work_branch": BRANCH,
        }
        v = self.result()
        self.assertEqual(v["action"], "ALREADY_RECONCILED_NO_REPLAY")
        self.assertFalse(v["may_write"])
        self.assertFalse(v["may_retry"])

    def test_forged_audit_fails_closed(self):
        self.snap["source_head"] = AFTER
        self.snap["state"].pop("pending_source_action")
        self.snap["state"]["last_source_action_probe"] = {
            "operation_id": OP, "before_head": BEFORE,
            "after_head": BEFORE, "work_branch": BRANCH}
        self.assertEqual(self.result()["action"],
                         "WAIT_NO_PERSISTED_MATCHING_ACTION")

    def test_unexpected_source_commit_is_not_accepted(self):
        self.snap["source_head"] = "e"*40
        self.assertEqual(self.result()["action"], "WAIT_FOREIGN_SOURCE_UPDATE")

    def test_malformed_pending_action_rejected(self):
        self.snap["state"]["pending_source_action"]["after_head"] = None
        self.assertEqual(self.result()["action"], "WAIT_INVALID_RECOVERY_EVIDENCE")

    def test_malformed_snapshot_rejected(self):
        self.snap.pop("coordinator_ref")
        self.assertEqual(self.result()["action"], "WAIT_COORDINATOR_REF_DRIFT")

    def test_provider_result_is_never_authoritative(self):
        self.snap["source_head"] = AFTER
        v = self.result()
        for k in ("may_write", "may_merge", "may_retry",
                  "may_release", "provider_authenticated",
                  "host_action_fence_verified", "real_parallel"):
            self.assertFalse(v[k], k)

    def test_reason_metadata_does_not_turn_a_hold_into_invalid_evidence(self):
        v = self.result()
        self.assertEqual(v["action"], "WAIT_UNCERTAIN_NOT_APPLIED_DO_NOT_RETRY")
        self.assertIn("in-flight", v["reason"])
        self.assertFalse(v["may_retry"])
        self.snap["source_head"] = AFTER
        updated = self.result()
        self.assertEqual(updated["action"], "CANDIDATE_OWNER_RECONCILE_ONLY")
        self.assertIn("provider", updated["reason"])
        self.assertFalse(updated["may_write"])

    def test_pending_source_action_cannot_be_replayed_after_completion(self):
        self.snap["source_head"] = AFTER
        v = self.result()
        self.assertEqual(v["action"], "CANDIDATE_OWNER_RECONCILE_ONLY")
        self.snap["state"].pop("pending_source_action")
        v2 = self.result()
        self.assertEqual(v2["action"], "WAIT_NO_PERSISTED_MATCHING_ACTION")


if __name__ == "__main__":
    unittest.main()
