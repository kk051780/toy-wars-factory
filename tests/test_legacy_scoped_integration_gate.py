"""P0 migration: legacy integration must not merge while v2 scoped writers exist.

Fake fixtures exercise decision logic only. No registered provider authorizes a merge.
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from repair_control import acquire, initial_state
from repair_integration import decide, REVIEW_CHECKS

NOW = "2026-10-25T01:00:00Z"
REVIEWER = "00000000-0000-0000-0000-00000000a101"
AUTHOR = "039874ac-64a0-8323-bc57-5c35cf58ec90"


class ScopedIntegrationGuardTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / "config/autonomous_repair.json").read_text())
        task = self.policy["integration"]["task_id"]
        base = initial_state()
        base["authorized_tasks"]["REVIEWER"] = task
        self.lease = acquire(base, "REVIEWER", REVIEWER, NOW,
                             actor_task_id=task, work_branch="main")["state"]
        self.main = {"sha": "c"*40, "qa_head": "c"*40,
                     "qa_conclusion": "success", "qa_url": "main-ci"}
        self.pr = {
            "number": 57, "repository": self.policy["repository"],
            "branch": self.policy["branch_prefix"] + AUTHOR,
            "state": "open", "head": "b"*40, "mergeable": True,
            "author_task_id": self.policy["task_id"],
            "author_run_id": AUTHOR,
            "ci": {"head": "b"*40, "conclusion": "success",
                   "required_jobs_passed": True,
                   "scope_and_claim_gate": "PASS"},
        }
        self.review = {
            "reviewer_task_id": task,
            "reviewer_run_id": REVIEWER,
            "lease_epoch": self.lease["epoch"],
            "head": self.pr["head"],
            "base_main_sha": self.main["sha"],
            "reviewed_at": NOW, "verdict": "APPROVE",
            "blockers": [],
            "checks": {name: True for name in REVIEW_CHECKS},
        }

    def decision(self):
        return decide(self.policy, self.main, self.pr, self.review, self.lease, NOW)

    def registry(self, key="shadow_parallel_leases", expired=False):
        owner = "11111111-1111-4111-8111-111111111111"
        entry = {
            "scope": {"work_id": "parallel-work", "branch": "controller/new"},
            "owner_id": owner,
            "run_id": "22222222-2222-4222-8222-222222222222",
            "nonce": "33333333-3333-4333-8333-333333333333",
            "lease_epoch": self.lease["epoch"],
            "acquired_at": "2026-10-25T00:55:00Z",
            "expires_at": ("2026-10-25T00:57:00Z" if expired
                           else "2026-10-25T01:25:00Z"),
        }
        self.lease[key] = {"schema": 1, "entries": [entry]}

    def test_negative_control_original_review_is_only_preflight(self):
        self.assertEqual(self.decision()["action"], "WAIT_HOST_ACTION_FENCE")

    def test_active_shadow_scopes_block_authorized_merge(self):
        self.registry()
        result = self.decision()
        self.assertEqual(result["action"], "WAIT_SCOPED_LEASES")
        self.assertNotIn("merge_method", result)

    def test_production_scopes_block_authorized_merge(self):
        self.registry("parallel_leases")
        self.assertEqual(self.decision()["action"], "WAIT_SCOPED_LEASES")

    def test_expired_scoped_entry_does_not_unblock_merge(self):
        self.registry(expired=True)
        self.assertEqual(self.decision()["action"], "WAIT_SCOPED_LEASES")

    def test_explicit_migration_flag_blocks_without_rows(self):
        self.lease["parallel_write_migration"] = "SCOPED_ACTIVE"
        result = self.decision()
        self.assertEqual(result["action"], "WAIT_SCOPED_LEASES")

    def test_empty_registry_legacy_preflight_still_requires_host_fence(self):
        self.lease["shadow_parallel_leases"] = {"schema": 1, "entries": []}
        self.assertEqual(self.decision()["action"], "WAIT_HOST_ACTION_FENCE")

    def test_invalid_scoped_schema_waits_instead_of_merging(self):
        self.lease["parallel_leases"] = {"schema": 2, "entries": []}
        self.assertEqual(self.decision()["action"], "WAIT_LOCK")

    def test_spoofed_registry_flag_does_not_bypass(self):
        self.registry()
        self.lease["parallel_write_migration"] = "LEGACY_ONLY"
        self.assertEqual(self.decision()["action"], "WAIT_SCOPED_LEASES")

    def test_malformed_broken_row_no_merge(self):
        self.lease["shadow_parallel_leases"] = {
            "schema": 1, "entries": [{"owner_id": "fake"}]}
        self.assertEqual(self.decision()["action"], "WAIT_LOCK")


if __name__ == "__main__":
    unittest.main()
