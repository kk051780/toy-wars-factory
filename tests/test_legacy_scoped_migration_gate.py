"""P0: existing exclusive coordinator must fence any scoped v2 occupants.

These tests prove only the policy in this candidate source checkout.
Unupgraded old runners can still ignore the new gate, so live activation
requires independent review, deployment and matching runner revision.
"""
import copy
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from repair_control import (
    acquire, release, validate, initial_state, TASK_ID,
    scoped_lease_migration_block,
)

OWNER = "11111111-1111-4111-8111-111111111111"
RUN = "22222222-2222-4222-8222-222222222222"
NONCE = "33333333-3333-4333-8333-333333333333"
META = "6add445e4138819197d9cf2b1a02534d"
REVIEWER = "6add6aaceb4c8191b1666fe15f97cd88"
NOW = "2026-11-08T00:10:00+00:00"


def base():
    state = initial_state()
    state["epoch"] = 19
    state["authorized_tasks"].update({"META": META, "REVIEWER": REVIEWER})
    return state


def scoped_row(epoch=19, work_id="parallel-work-alpha",
               branch="controller/parallel-alpha"):
    return {
        "scope": {"work_id": work_id, "branch": branch},
        "owner_id": OWNER, "run_id": RUN, "nonce": NONCE,
        "lease_epoch": epoch,
        "acquired_at": "2026-11-08T00:00:00+00:00",
        "expires_at": "2026-11-08T00:20:00+00:00",
    }


def with_rows(rows, key="shadow_parallel_leases"):
    state = base()
    state[key] = {"schema": 1, "entries": rows}
    return state


def claim_any(state, kind):
    owner = "44444444-4444-4444-8444-444444444444"
    args = {"base_main_sha": "a"*40}
    if kind == "WORKER":
        args.update(work_branch="auto/twf-game-repair-" + owner,
                    actor_task_id=TASK_ID)
    elif kind == "META":
        args.update(work_branch="auto/twf-system-review-" + owner,
                    actor_task_id=META)
    elif kind == "REVIEWER":
        args.update(work_branch="main", actor_task_id=REVIEWER)
    elif kind == "CONTROLLER":
        args.update(work_branch="controller/unrelated-work")
    elif kind == "DISPATCH":
        args.update(service_status="completed", work_branch="main")
    return acquire(state, kind, owner, NOW, **args)


class LegacyScopedCompatibilityTests(unittest.TestCase):

    def test_legacy_all_five_roles_wait_when_scoped_writer_active(self):
        for kind in ("DISPATCH", "WORKER", "META", "REVIEWER", "CONTROLLER"):
            with self.subTest(kind=kind):
                state = with_rows([scoped_row()])
                out = claim_any(state, kind)
                self.assertEqual(out["action"], "WAIT_SCOPED_LEASES")
                self.assertFalse(out["write"])
                self.assertIs(out["state"], state)
                self.assertEqual(state["epoch"], 19)
                self.assertIsNone(state["holder"])

    def test_scoped_expiry_alone_never_allows_legacy_takeover(self):
        state = with_rows([scoped_row()])
        state["shadow_parallel_leases"]["entries"][0]["expires_at"] = "2026-11-08T00:01:00+00:00"
        self.assertEqual(claim_any(state, "CONTROLLER")["action"],
                         "WAIT_SCOPED_LEASES")

    def test_production_registry_alias_also_blocks(self):
        state = with_rows([scoped_row()], key="parallel_leases")
        self.assertEqual(claim_any(state, "CONTROLLER")["action"],
                         "WAIT_SCOPED_LEASES")

    def test_both_registry_names_conflict_fail_closed(self):
        state = with_rows([scoped_row()])
        state["parallel_leases"] = {"schema": 1, "entries": [scoped_row()]}
        self.assertEqual(claim_any(state, "CONTROLLER")["action"],
                         "WAIT_SCOPED_LEASES")

    def test_explicit_migration_marker_blocks_empty_scoped_list(self):
        state = with_rows([])
        state["parallel_write_migration"] = "SCOPED_ACTIVE"
        self.assertEqual(claim_any(state, "CONTROLLER")["action"],
                         "WAIT_SCOPED_LEASES")

    def test_empty_registry_backward_compatible(self):
        state = with_rows([])
        self.assertEqual(claim_any(state, "CONTROLLER")["action"], "ACQUIRE")
        self.assertTrue(claim_any(state, "CONTROLLER")["write"])

    def test_old_coordinator_without_field_remains_compatible(self):
        state = base()
        self.assertFalse(scoped_lease_migration_block(state))
        self.assertEqual(claim_any(state, "CONTROLLER")["action"], "ACQUIRE")

    def test_invalid_registry_fail_closed(self):
        variants = [
            None, [], {}, {"schema": True, "entries": []},
            {"schema": 9, "entries": []},
            {"schema": 1, "entries": "not-an-array"},
            {"schema": 1, "entries": [{}, {}, {}]},
            {"schema": 1, "entries": [], "allow_legacy": True},
        ]
        for entry in variants:
            with self.subTest(value=entry):
                state = base()
                state["shadow_parallel_leases"] = entry
                with self.assertRaises(ValueError):
                    claim_any(state, "CONTROLLER")

    def test_malformed_entry_and_owner_identity_fail_closed(self):
        variants = [
            {"fake": True},
            dict(scoped_row(), owner_id="fake-chat"),
            dict(scoped_row(), lease_epoch=True),
            dict(scoped_row(), lease_epoch=100),
            dict(scoped_row(), acquired_at="2026-11-08T00:30:00+00:00"),
        ]
        for entry in variants:
            with self.subTest(value=entry):
                with self.assertRaises(ValueError):
                    claim_any(with_rows([entry]), "CONTROLLER")

    def test_duplicate_work_scope_blocks(self):
        a = scoped_row()
        b = copy.deepcopy(a)
        b["owner_id"] = "55555555-5555-4555-8555-555555555555"
        b["run_id"] = "66666666-6666-4666-8666-666666666666"
        b["nonce"] = "77777777-7777-4777-8777-777777777777"
        with self.assertRaises(ValueError):
            claim_any(with_rows([a, b]), "CONTROLLER")

    def test_unknown_migration_marker_fails_closed(self):
        for marker in (None, True, "ACTIVE_WRITES_ALLOW", {}, 1):
            with self.subTest(mode=marker):
                state = base()
                state["parallel_write_migration"] = marker
                with self.assertRaises(ValueError):
                    claim_any(state, "CONTROLLER")

    def test_explicit_legacy_mode_still_blocks_active_scopes(self):
        state = with_rows([scoped_row()])
        state["parallel_write_migration"] = "LEGACY_ONLY"
        self.assertEqual(claim_any(state, "CONTROLLER")["action"],
                         "WAIT_SCOPED_LEASES")

    def test_legitimate_current_global_owner_can_release_without_deleting_scopes(self):
        state = with_rows([scoped_row()])
        state["holder"] = {
            "kind": "CONTROLLER", "owner_id": OWNER, "task_id": None,
            "epoch": state["epoch"],
            "acquired_at": "2026-11-08T00:00:00+00:00",
            "expires_at": "2026-11-08T00:20:00+00:00",
            "base_main_sha": "a"*40,
            "work_branch": "controller/current",
        }
        validate(state)
        next_state = release(state, "CONTROLLER", OWNER, state["epoch"], NOW)
        self.assertIsNone(next_state["holder"])
        self.assertEqual(next_state["shadow_parallel_leases"],
                         state["shadow_parallel_leases"])
        self.assertEqual(len(next_state["shadow_parallel_leases"]["entries"]), 1)

    def test_nonwriter_dispatch_join_can_still_wait_with_valid_legacy_holder(self):
        state = with_rows([scoped_row()])
        state["holder"] = {
            "kind": "DISPATCH", "owner_id": OWNER, "task_id": None,
            "epoch": 19, "acquired_at": "2026-11-08T00:00:00+00:00",
            "expires_at": "2026-11-08T00:20:00+00:00",
            "base_main_sha": "a"*40,
            "work_branch": "main",
        }
        self.assertEqual(claim_any(state, "WORKER")["action"],
                         "WAIT_SCOPED_LEASES")


if __name__ == "__main__":
    unittest.main()
