"""Persisted/supplied epoch types must not alias integer fencing generations."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests")]
import repair_control as control
from test_system_owned_lease_finalization import Host, RUN, TASK, REPO, NOW, EXPIRED


class HolderEpochFencingTests(unittest.TestCase):
    def host(self, bad=None):
        h = Host()
        if bad is not None:
            h.state["holder"]["epoch"] = bad
        return h

    def scope(self, h, epoch=1):
        return control.owned_lease(repository=REPO, kind="REVIEWER",
            owner_id=RUN, epoch=epoch, task_id=TASK,
            read=h.read, cas=h.cas, peek=h.peek, clock=h.clock)

    def test_validate_rejects_boolean_persisted_epoch(self):
        with self.assertRaises(ValueError):
            control.validate(self.host(True).state)

    def test_validate_rejects_float_persisted_epoch(self):
        with self.assertRaises(ValueError):
            control.validate(self.host(1.0).state)

    def test_owns_rejects_bad_persisted_generations(self):
        for bad in (True, 1.0):
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                control.owns(self.host(bad).state, "REVIEWER", RUN, 1, NOW)

    def test_release_rejects_bad_persisted_generation_without_mutation(self):
        for bad in (True, 1.0):
            with self.subTest(bad=repr(bad)):
                h = self.host(bad)
                before = deepcopy(h.state)
                with self.assertRaises(ValueError):
                    control.release(h.state, "REVIEWER", RUN, 1, NOW)
                self.assertEqual(h.state, before)
                self.assertFalse(h.writes)

    def test_acquire_cannot_resume_malformed_stored_holder(self):
        for bad in (True, 1.0):
            with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                control.acquire(self.host(bad).state, "REVIEWER", RUN, NOW,
                                actor_task_id=TASK, work_branch="main")

    def test_owned_scope_has_no_body_or_cas_for_bad_stored_holder(self):
        for bad in (True, 1.0):
            with self.subTest(bad=repr(bad)):
                h = self.host(bad)
                entered = []
                with self.assertRaises(ValueError):
                    with self.scope(h):
                        entered.append(True)
                self.assertFalse(entered)
                self.assertFalse(h.writes)

    def test_owns_boolean_argument_is_false(self):
        self.assertFalse(control.owns(self.host().state, "REVIEWER", RUN, True, NOW))

    def test_owns_float_argument_is_false(self):
        self.assertFalse(control.owns(self.host().state, "REVIEWER", RUN, 1.0, NOW))

    def test_release_wrong_or_untyped_arguments_still_rejected(self):
        for epoch in (True, 1.0, 0, 2, "1", None):
            with self.subTest(epoch=repr(epoch)), self.assertRaises(ValueError):
                control.release(self.host().state, "REVIEWER", RUN, epoch, NOW)

    def test_strict_integer_generation_positive_control(self):
        h = self.host()
        self.assertIs(control.validate(h.state), h.state)
        self.assertTrue(control.owns(h.state, "REVIEWER", RUN, 1, NOW))
        with self.scope(h) as receipt:
            pass
        self.assertEqual(receipt["status"], "RELEASED_READBACK")
        self.assertIsNone(h.state["holder"])

    def test_same_owner_late_primitive_release_remains_supported(self):
        h = self.host()
        self.assertFalse(control.owns(h.state, "REVIEWER", RUN, 1, EXPIRED))
        released = control.release(h.state, "REVIEWER", RUN, 1, EXPIRED)
        self.assertIsNone(released["holder"])
        self.assertEqual(released["last_completed"]["epoch"], 1)
        self.assertEqual(released["last_completed"]["owner_id"], RUN)
        self.assertNotIn("recovered_from_service_evidence", released["last_completed"])

    def test_finally_cannot_release_holder_that_became_malformed(self):
        for bad in (True, 1.0):
            with self.subTest(bad=repr(bad)):
                h = self.host()
                with self.assertRaises(RuntimeError):
                    with self.scope(h) as receipt:
                        h.state["holder"]["epoch"] = bad
                self.assertEqual(receipt["status"], "NOT_RELEASED")
                self.assertFalse(h.writes)
                self.assertIs(type(h.state["holder"]["epoch"]), type(bad))


if __name__ == "__main__":
    unittest.main()
