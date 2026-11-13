"""Independent state-model oracle: Python tests do not constitute native Luau/Studio QA."""
import math
import unittest

WARN, OPEN = 2.0, 10.0

class Gate:
    def __init__(self, round_id):
        assert round_id
        self.round_id = round_id
        self.phase = "LOCKED"
        self.triggered = False
        self.warning_until = None
        self.open_until = None
        self.last_now = 0.0

    def _ok(self, rid, now):
        if rid != self.round_id or not isinstance(now, (int,float)) or not math.isfinite(now) or now < self.last_now:
            return False
        self.last_now = now
        return True

    def ko(self, rid, elite, now):
        if not self._ok(rid, now) or elite is not True or self.triggered or self.phase != "LOCKED":
            return False
        self.triggered = True
        self.phase = "WARNING"
        self.warning_until = now + WARN
        self.open_until = now + WARN + OPEN
        return True

    def step(self, rid, now, occupants):
        if type(occupants) is not int or not 0 <= occupants <= 128 or not self._ok(rid, now):
            return False
        if self.phase == "WARNING" and now >= self.warning_until:
            self.phase = "OPEN" if now < self.open_until else ("WAIT_CLEAR" if occupants else "CLOSED")
        if self.phase == "OPEN" and now >= self.open_until:
            self.phase = "WAIT_CLEAR" if occupants else "CLOSED"
        if self.phase == "WAIT_CLEAR" and occupants == 0:
            self.phase = "CLOSED"
        return True

    def passable(self):
        return self.phase in ("OPEN", "WAIT_CLEAR")

class GateTests(unittest.TestCase):
    def setUp(self):
        self.g = Gate("round-7")

    def test_locked_initially(self):
        self.assertEqual(self.g.phase, "LOCKED")
        self.assertFalse(self.g.passable())

    def test_nonelite_does_not_open(self):
        self.assertFalse(self.g.ko("round-7", False, 1))
        self.assertEqual(self.g.phase, "LOCKED")

    def test_stale_round_rejected(self):
        self.assertFalse(self.g.ko("round-6", True, 1))

    def test_first_real_ko_only(self):
        self.assertTrue(self.g.ko("round-7", True, 1))
        self.assertFalse(self.g.ko("round-7", True, 1.1))

    def test_warning_exact_two_seconds(self):
        self.assertTrue(self.g.ko("round-7", True, 1))
        self.assertTrue(self.g.step("round-7", 2.99, 0))
        self.assertEqual(self.g.phase, "WARNING")
        self.assertTrue(self.g.step("round-7", 3, 0))
        self.assertEqual(self.g.phase, "OPEN")

    def test_open_until_twelve_seconds_after_ko(self):
        self.g.ko("round-7", True, 1)
        self.g.step("round-7", 12.99, 0)
        self.assertTrue(self.g.passable())
        self.g.step("round-7", 13, 0)
        self.assertEqual(self.g.phase, "CLOSED")

    def test_door_does_not_crush_occupant(self):
        self.g.ko("round-7", True, 1)
        self.g.step("round-7", 13, 1)
        self.assertEqual(self.g.phase, "WAIT_CLEAR")
        self.assertTrue(self.g.passable())
        self.g.step("round-7", 14, 0)
        self.assertEqual(self.g.phase, "CLOSED")

    def test_no_reopen_same_round(self):
        self.g.ko("round-7", True, 1)
        self.g.step("round-7", 13, 0)
        self.assertFalse(self.g.ko("round-7", True, 14))

    def test_backward_clock_rejected(self):
        self.g.ko("round-7", True, 10)
        self.assertFalse(self.g.step("round-7", 9.9, 0))

    def test_nan_inf_rejected(self):
        for bad in (math.nan, math.inf, -math.inf):
            self.assertFalse(self.g.ko("round-7", True, bad))
        self.assertEqual(self.g.phase, "LOCKED")

    def test_negative_and_huge_occupancy(self):
        self.assertFalse(self.g.step("round-7", 1, -1))
        self.assertFalse(self.g.step("round-7", 1, 129))

    def test_wrong_round_cannot_progress(self):
        self.g.ko("round-7", True, 1)
        self.assertFalse(self.g.step("round-x", 15, 0))
        self.assertEqual(self.g.phase, "WARNING")

    def test_if_skip_clock_to_after_open_with_people(self):
        self.g.ko("round-7", True, 1)
        self.g.step("round-7", 40, 2)
        self.assertEqual(self.g.phase, "WAIT_CLEAR")

    def test_fairness_always_shared(self):
        self.g.ko("round-7", True, 1)
        self.g.step("round-7", 3, 0)
        # No team parameter or paywall; both teams read the same state.
        self.assertTrue(self.g.passable())

if __name__ == "__main__":
    unittest.main()
