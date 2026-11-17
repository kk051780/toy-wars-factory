#!/usr/bin/env python3
"""Source-level regression tests for GQ8 burn reset; engine proof is separate."""
import unittest
from patch_burn_reset import ANCHOR, PATCH, patch, unpatch

ORIGINAL = (
    'function Replay.captureWalkBaseline(p:Player):number\n'
    ' return 16\n'
    'end\n'
    'function Replay.resetHuman(p:Player,returnTo:Vector3,baseWalkSpeed:number?):()\n'
    ' -- GQ8_MULTI_SHIELD_REPLAY_CLEANUP_END\n'
    ' if hum then\n'
    + ANCHOR +
    ' end\n'
    'end\n'
)

class BurnReplaySourceTests(unittest.TestCase):
    def test_selects_one_existing_round_replay(self):
        result = patch(ORIGINAL)
        self.assertIn('hum:SetAttribute("EGGRUMBLE_BurnUntil",nil)', result)
        self.assertEqual(result.count("EGGRUMBLE_BurnUntil"), 1)
        self.assertEqual(result.count("GQ8_MULTI_SHIELD_REPLAY_CLEANUP_END"), 1)

    def test_exact_inverse(self):
        self.assertEqual(unpatch(patch(ORIGINAL)), ORIGINAL)

    def test_no_older_shield_owner_is_red(self):
        with self.assertRaisesRegex(ValueError, "SHIELD_OWNER"):
            patch(ORIGINAL.replace("GQ8_MULTI_SHIELD_REPLAY_CLEANUP_END", "no-shield-owner"))

    def test_reapply_is_red(self):
        with self.assertRaisesRegex(ValueError, "DRIFT"):
            patch(patch(ORIGINAL))

    def test_duplicate_anchor_is_red(self):
        with self.assertRaisesRegex(ValueError, "DRIFT"):
            patch(ORIGINAL.replace(ANCHOR, ANCHOR + ANCHOR))

    def test_preexisting_burn_is_red(self):
        with self.assertRaisesRegex(ValueError, "DRIFT"):
            patch(ORIGINAL.replace(ANCHOR, ANCHOR + ' hum:SetAttribute("EGGRUMBLE_BurnUntil",0)\n'))

    def test_owner_drift_is_red(self):
        with self.assertRaisesRegex(ValueError, "OWNER"):
            patch(ORIGINAL.replace("Replay.resetHuman", "Other.resetHuman"))

    def test_no_altered_rollback(self):
        mutant = patch(ORIGINAL).replace('hum:SetAttribute("EGGRUMBLE_BurnUntil",nil)',
                                          'hum:SetAttribute("EGGRUMBLE_BurnUntil",3)')
        with self.assertRaisesRegex(ValueError, "DRIFT"):
            unpatch(mutant)

    def test_unpatch_original_is_red(self):
        with self.assertRaisesRegex(ValueError, "DRIFT"):
            unpatch(ORIGINAL)

    def test_preserves_existing_slow_and_mark_reset(self):
        result=patch(ORIGINAL)
        self.assertEqual(result.count(ANCHOR),1)
        self.assertIn("GQ8_MULTI_SHIELD_REPLAY_CLEANUP_END",result)

if __name__ == "__main__":
    unittest.main()
