#!/usr/bin/env python3
"""Negative/rollback proof for the original BEAST-B single-Combat candidate."""
import os
import unittest
from pathlib import Path
from compose_single_combat import (
    ORIGINAL_482_BLOB, OLD_BEAST_B, NEW_BEAST_B, INSERT_ANCHOR,
    git_blob, compose, rollback
)

ROOT = Path(__file__).resolve().parent
PINNED = Path(os.getenv(
    "GQ482_COMBAT_FILE",
    "_gq_original482/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau",
))


class BeastSourceLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = PINNED.read_bytes()
        cls.original = cls.raw.decode("utf-8")
        cls.runtime = (ROOT / "EGGRUMBLE_BeastEscort.luau").read_text("utf-8")

    def test_01_immutable_owner_exact(self):
        self.assertEqual(git_blob(self.raw), ORIGINAL_482_BLOB)

    def test_02_real_server_companion(self):
        self.assertIn('Instance.new("Humanoid")', self.runtime)
        self.assertIn("hum:MoveTo(", self.runtime)
        self.assertIn("SetNetworkOwner(nil)", self.runtime)
        self.assertIn("session.rules.phase", self.runtime)
        self.assertIn('player:GetAttribute("EGGRUMBLE_Role") == "BEAST"', self.runtime)

    def test_03_no_duplicate_damage_authority(self):
        for forbidden in ("TakeDamage(", 'Instance.new("RemoteEvent")', "DataStoreService",
                          "MarketplaceService", "SetAsync(", "UpdateAsync("):
            self.assertNotIn(forbidden, self.runtime)

    def test_04_beast_original_only_one_anchor(self):
        self.assertEqual(self.original.count(OLD_BEAST_B), 1)
        self.assertEqual(self.original.count(INSERT_ANCHOR), 1)

    def test_05_single_combat_changed(self):
        changed, inline = compose(self.original, self.runtime)
        self.assertNotEqual(changed, self.original)
        self.assertEqual(changed.count("BeastEscort.begin(session,p,char,root,h,owner,"), 1)
        self.assertEqual(changed.count("function BeastEscort.begin("), 1)
        self.assertNotIn('giant.Name="BeastFeedGiant"', changed)
        self.assertEqual(changed.count("return HeroCombat"), 1)
        self.assertEqual(changed.count("elseif role==\"ZOMBIE\""), 1)

    def test_06_off_byte_exact(self):
        changed, inline = compose(self.original, self.runtime)
        self.assertEqual(rollback(changed, inline).encode("utf-8"), self.raw)

    def test_07_original_missing_anchor_red(self):
        with self.assertRaisesRegex(ValueError, "RED_BEAST_COMBAT_ANCHOR_DRIFT"):
            compose(self.original.replace(OLD_BEAST_B, "", 1), self.runtime)

    def test_08_duplicate_beast_anchor_red(self):
        with self.assertRaisesRegex(ValueError, "RED_BEAST_COMBAT_ANCHOR_DRIFT"):
            compose(self.original + OLD_BEAST_B, self.runtime)

    def test_09_mutated_runtime_red(self):
        with self.assertRaisesRegex(ValueError, "RED_DUPLICATE_AUTHORITY"):
            compose(self.original, self.runtime + '\nInstance.new("RemoteEvent")\n')

    def test_10_non_author_game_red(self):
        with self.assertRaisesRegex(ValueError, "RED_COMBAT_AUTHORITY_DRIFT"):
            compose(self.original.replace("return HeroCombat", "return EvilCombat"), self.runtime)

    def test_11_preserve_zombie_and_other_job_source(self):
        changed, inline = compose(self.original, self.runtime)
        self.assertEqual(rollback(changed, inline), self.original)
        self.assertIn('elseif role=="MAGE"', changed)
        self.assertIn('elseif role=="NINJA"', changed)
        self.assertIn('elseif role=="TRAPPER"', changed)
        self.assertIn('elseif role=="BUILDER"', changed)

    def test_12_old_round_and_death_fences(self):
        self.assertIn('session.isCurrentHuman', self.runtime)
        self.assertIn('player.Character == character', self.runtime)
        self.assertIn("humanoid.Health > 0", self.runtime)
        self.assertIn('ownerState.alive == true', self.runtime)
        self.assertIn('active[player.UserId] == state', self.runtime)

if __name__ == "__main__":
    unittest.main()
