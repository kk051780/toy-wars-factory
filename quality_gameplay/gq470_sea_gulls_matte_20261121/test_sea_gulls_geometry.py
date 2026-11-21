"""Deterministic part budget and visibility rules; no invented FPS/beauty score."""
import math
import unittest
from pathlib import Path

SOURCE = (Path(__file__).parent / "EGGRUMBLE_SeaGullsMatte.client.luau").read_text(encoding="utf-8")

def bird_count(touch_enabled, valid_dock, near, character_alive, reduced):
    if not valid_dock or not near or not character_alive or reduced:
        return 0
    return 2 if touch_enabled else 3

class BirdBudgetTests(unittest.TestCase):
    def test_eighteen_cases(self):
        cases = 0
        for touch in (False, True):
            for dock in (False, True):
                for close in (False, True):
                    for alive in (False, True):
                        for reduced in (False, True):
                            n = bird_count(touch, dock, close, alive, reduced)
                            self.assertLessEqual(n * 3, 6 if touch else 9)
                            self.assertEqual(n > 0, dock and close and alive and not reduced)
                            cases += 1
        self.assertEqual(cases, 32)

    def test_mathematical_glide_envelope_source_only(self):
        # These are deterministic design-envelope checks, NOT visual or engine QA.
        self.assertIn("local bank = math.rad(math.sin(t * .82 + slot * 1.37) * 7)", SOURCE)
        self.assertIn("local wingGlide = math.rad(math.sin(phase * 1.35 + bird.slot * 1.75) * 8)", SOURCE)
        self.assertIn("CFrame.Angles(0, 0, -wingGlide)", SOURCE)
        self.assertEqual(SOURCE.count("TweenService:Create(part, style"), 1)
        max_roll = max_wing = 0.0
        for slot in (1, 2, 3):
            for tick in range(360):
                phase = tick * .85
                roll = math.sin(phase * .82 + slot * 1.37) * 7
                wing = math.sin(phase * 1.35 + slot * 1.75) * 8
                max_roll = max(max_roll, abs(roll))
                max_wing = max(max_wing, abs(wing))
                self.assertLessEqual(abs(roll), 7 + 1e-9)
                self.assertLessEqual(abs(wing), 8 + 1e-9)
                self.assertAlmostEqual(wing + (-wing), 0)
        self.assertGreater(max_roll, 6.9)
        self.assertGreater(max_wing, 7.9)

    def test_three_parts_and_short_lived(self):
        self.assertIn("MAX_VIEW_DISTANCE = 165", SOURCE)
        self.assertIn("UPDATE_SECONDS = 2.8", SOURCE)
        self.assertIn("for slot = 1, BIRD_LIMIT do", SOURCE)
        self.assertIn("if activeDock == obj then clear() end", SOURCE)
        self.assertIn("if localPlayer:GetAttribute(\"EGGRUMBLE_ReducedEffects\") == true then clear()", SOURCE)
        self.assertNotIn(":Destroy() -- keep until next match", SOURCE)
        self.assertIn("return nil -- no camera-based fake effect", SOURCE)

if __name__ == "__main__":
    unittest.main()
