"""P0 write-permission fence / self-cleanup regressions for mixed legacy + v2.

No actual provider actors are authenticated by these synthetic host fixtures.
"""
import copy
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
import repair_control as control
from test_system_owned_lease_finalization import Host, REPO, NOW, RUN, TASK, OTHER


def scoped(epoch=1, expire="2026-10-30T00:20:00Z"):
    return {
        "scope": {"work_id": "p0-scope-alpha", "branch": "controller/p0-alpha"},
        "owner_id": "11111111-1111-4111-8111-111111111111",
        "run_id": "22222222-2222-4222-8222-222222222222",
        "nonce": "33333333-3333-4333-8333-333333333333",
        "lease_epoch": epoch,
        "acquired_at": "2026-10-30T00:00:00Z",
        "expires_at": expire,
    }


class LegacyOwnershipMigrationTests(unittest.TestCase):
    def setUp(self):
        self.h = Host()

    def add_scoped(self, key="shadow_parallel_leases", **settings):
        self.h.state[key] = {"schema": 1, "entries": [scoped(**settings)]}

    def session(self):
        return control.owned_lease(
            repository=REPO, kind="REVIEWER", owner_id=RUN, epoch=1,
            task_id=TASK, read=self.h.read, cas=self.h.cas,
            peek=self.h.peek, clock=self.h.clock)

    def owns(self):
        return control.owns(self.h.state, "REVIEWER", RUN, 1, NOW)

    def test_legacy_owner_is_accepted_before_migration(self):
        self.assertTrue(self.owns())

    def test_legacy_owner_is_no_longer_write_authorized_if_shadow_row_exists(self):
        self.add_scoped()
        self.assertFalse(self.owns())

    def test_expired_scoped_row_does_not_restore_old_write_permission(self):
        self.add_scoped(expire="2026-10-30T00:00:30Z")
        self.assertFalse(self.owns())

    def test_production_registry_alias_denies_old_write_permission(self):
        self.add_scoped(key="parallel_leases")
        self.assertFalse(self.owns())

    def test_migration_flag_denies_even_without_scoped_rows(self):
        self.h.state["parallel_write_migration"] = "SCOPED_ACTIVE"
        self.assertFalse(self.owns())

    def test_unknown_migration_state_raises_not_grants(self):
        self.h.state["parallel_write_migration"] = "LEGACY_ALLOW_EVERYTHING"
        with self.assertRaises(ValueError):
            self.owns()

    def test_wrong_epoch_stays_denied_without_any_scopes(self):
        self.assertFalse(control.owns(self.h.state, "REVIEWER", RUN, 2, NOW))

    def test_mixed_state_can_only_release_its_exact_existing_owner(self):
        self.add_scoped()
        original = copy.deepcopy(self.h.state)
        self.assertFalse(self.owns())
        out = control.release(self.h.state, "REVIEWER", RUN, 1, NOW)
        self.assertIsNone(out["holder"])
        self.assertEqual(out["shadow_parallel_leases"],
                         original["shadow_parallel_leases"])
        self.assertIsNotNone(original["holder"])
        with self.assertRaises(ValueError):
            control.release(self.h.state, "REVIEWER", OTHER, 1, NOW)

    def test_mixed_state_rejected_at_owned_lease_entry(self):
        self.add_scoped()
        with self.assertRaisesRegex(ValueError, "owned lease entry not verified"):
            with self.session():
                self.fail("new protected legacy work must never start")
        self.assertFalse(self.h.writes)

    def test_scoped_entry_appearing_mid_body_preserves_legitimate_self_release(self):
        with self.session() as receipt:
            self.assertTrue(self.owns())
            self.add_scoped()
            self.assertFalse(self.owns())
        self.assertEqual(receipt["status"], "RELEASED_READBACK")
        self.assertIsNone(self.h.state["holder"])
        self.assertEqual(len(self.h.state["shadow_parallel_leases"]["entries"]), 1)
        self.assertEqual(self.h.state["last_completed"]["owner_id"], RUN)
        self.assertEqual(len(self.h.writes), 1)

    def test_new_foreign_holder_is_never_released_even_with_scoped_entry(self):
        with self.assertRaises(RuntimeError):
            with self.session():
                self.add_scoped()
                self.h.state["holder"]["owner_id"] = OTHER
        self.assertFalse(self.h.writes)
        self.assertEqual(self.h.state["holder"]["owner_id"], OTHER)

    def test_malformed_scoped_entry_after_body_blocks_finalization_write(self):
        with self.assertRaises(RuntimeError):
            with self.session():
                self.h.state["shadow_parallel_leases"] = {"schema": 1, "entries": [{"invalid": True}]}
        self.assertFalse(self.h.writes)

    def test_new_owner_epoch_mid_body_never_released(self):
        with self.assertRaises(RuntimeError):
            with self.session():
                self.add_scoped()
                self.h.state["epoch"] = 2
                self.h.state["holder"]["epoch"] = 2
        self.assertFalse(self.h.writes)

if __name__ == "__main__":
    unittest.main()
