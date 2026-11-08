"""Sourcery negative controls for legacy PR provenance and malformed scoped rows.

Synthetic Git and coordinator fixtures verify only a FAIL-CLOSED CLI policy,
not a real authenticated host merge or truly atomic write serialization.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import repair_control as ctrl
import repair_integration as integration

OWNER = "11111111-1111-4111-8111-111111111111"
TASK = ctrl.TASK_ID
NOW = "2026-11-08T01:00:00Z"
HEAD = "b" * 40
CLAIM = "c" * 40
CONTROL_REF = "d" * 40
HISTORY = "history/C09998_sourcery_negative.json"
BRANCH = "auto/twf-game-repair-" + OWNER


def scoped_row(epoch=1, expires_at="2026-11-08T01:20:00Z"):
    return {
        "scope": {"work_id": "sourcery-test-work", "branch": "controller/security-test"},
        "owner_id": "22222222-2222-4222-8222-222222222222",
        "run_id": "33333333-3333-4333-8333-333333333333",
        "nonce": "44444444-4444-4444-8444-444444444444",
        "lease_epoch": epoch,
        "acquired_at": "2026-11-08T00:55:00Z",
        "expires_at": expires_at,
    }


class ClaimHistoryMigrationGateTests(unittest.TestCase):
    def setUp(self):
        self.policy = {
            "queue_version": 4,
            "task_id": TASK,
            "branch": "auto/twf-game-repair",
            "branch_prefix": "auto/twf-game-repair-",
            "system_review": {
                "task_id": "6add445e4138819197d9cf2b1a02534d",
                "branch_prefix": "auto/twf-system-review-",
            },
            "coordination": {"grandfathered_pr_heads": []},
        }
        self.parent = ctrl.initial_state()
        self.parent["epoch"] = 1
        self.claim = ctrl.acquire(
            self.parent, "WORKER", OWNER, NOW, actor_task_id=TASK,
            work_branch=BRANCH, base_main_sha="a"*40)["state"]
        self.current = copy.deepcopy(self.claim)
        self.current["holder"] = None
        self.history = {
            "coordination": {"claim_commit": CLAIM,
                             "owner_run_id": OWNER, "branch": ctrl.CONTROL_BRANCH,
                             "epoch": self.claim["epoch"]}
        }

    def fake_git(self, *args):
        if args == ("rev-parse", HEAD):
            return HEAD
        if len(args) == 2 and args[0] == "show":
            objects = {
                CONTROL_REF + ":" + ctrl.CONTROL_PATH: self.current,
                HEAD + ":" + HISTORY: self.history,
                CLAIM + ":" + ctrl.CONTROL_PATH: self.claim,
                CLAIM + "^:" + ctrl.CONTROL_PATH: self.parent,
            }
            return json.dumps(objects[args[1]])
        raise AssertionError("unexpected git command: " + repr(args))

    def verify(self):
        with (patch.object(ctrl, "git", side_effect=self.fake_git),
              patch.object(ctrl.subprocess, "check_output",
                           return_value=b"A\0" + HISTORY.encode("ascii") + b"\0"),
              patch.object(ctrl.subprocess, "run")):
            return ctrl.verify_pr(self.policy, "a"*40, HEAD, BRANCH, CONTROL_REF)

    def add(self, which, key="shadow_parallel_leases", row=None):
        state = getattr(self, which)
        state[key] = {"schema": 1,
                      "entries": [row if row is not None else scoped_row(
                          epoch=state["epoch"])]}

    def test_unmigrated_claim_and_parent_still_pass_historical_preflight(self):
        self.assertEqual(self.verify(), "1 immutable coordinator claim(s) verified")

    def test_scoped_entry_in_claim_refuses_pr_verification(self):
        self.add("claim")
        with self.assertRaisesRegex(ValueError, "legacy claim contains scoped migration"):
            self.verify()

    def test_scoped_entry_in_parent_refuses_pr_verification(self):
        self.add("parent")
        with self.assertRaisesRegex(ValueError, "legacy claim parent contains scoped migration"):
            self.verify()

    def test_scoped_entry_in_current_control_ref_refuses_stale_claim(self):
        self.add("current")
        with self.assertRaisesRegex(ValueError, "legacy PR verification blocked"):
            self.verify()

    def test_explicit_scoped_active_current_ref_blocks_without_rows(self):
        self.current["parallel_write_migration"] = "SCOPED_ACTIVE"
        with self.assertRaisesRegex(ValueError, "legacy PR verification blocked"):
            self.verify()

    def test_malformed_current_ref_cannot_be_accepted(self):
        self.current = None
        with self.assertRaisesRegex(ValueError, "invalid coordinator object"):
            self.verify()

    def test_malformed_scoped_claim_timestamp_rejected_as_value_error(self):
        self.add("claim")
        self.claim["shadow_parallel_leases"]["entries"][0]["expires_at"] = 1234
        with self.assertRaises(ValueError):
            self.verify()


class MalformedCoordinatorDecisionTests(unittest.TestCase):
    def policy(self):
        return {"integration": {"enabled": True},
                "automatic_merge_authorized": True,
                "approval_authority": {"decision_owner": "ASSISTANT",
                                       "owner_reply_required": False}}

    def decision(self, lease):
        return integration.decide(self.policy(), {}, {}, {}, lease, NOW)

    def test_null_coordinator_returns_wait_lock_not_traceback(self):
        self.assertEqual(self.decision(None)["action"], "WAIT_LOCK")

    def test_nonobject_coordinator_returns_wait_lock(self):
        self.assertEqual(self.decision("not-an-object")["action"], "WAIT_LOCK")

    def test_integer_scoped_timestamp_returns_wait_lock(self):
        state = ctrl.initial_state()
        state["epoch"] = 2
        state["shadow_parallel_leases"] = {
            "schema": 1, "entries": [scoped_row(epoch=1, expires_at=1234)]}
        self.assertEqual(self.decision(state)["action"], "WAIT_LOCK")

    def test_malformed_scoped_date_returns_wait_lock(self):
        state = ctrl.initial_state()
        state["epoch"] = 2
        state["parallel_leases"] = {
            "schema": 1, "entries": [scoped_row(epoch=1, expires_at="garbage")]}
        self.assertEqual(self.decision(state)["action"], "WAIT_LOCK")


if __name__ == "__main__":
    unittest.main()
