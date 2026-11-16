#!/usr/bin/env python3
"""Fail-closed original-author source tests; never changes current RC."""
from __future__ import annotations
import os
from pathlib import Path
import unittest
from patch_takeover import ANCHOR, PREEXISTING_GUARD, REPLACEMENT, patch

class TakeoverSelectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = Path(os.environ["GQ_AUTHOR_BOT"]).read_text(encoding="utf-8")

    def test_one_hunk_and_byte_exact_rollback(self):
        selected = patch(self.original)
        self.assertEqual(selected.count(REPLACEMENT), 1)
        self.assertEqual(selected.replace(REPLACEMENT, ANCHOR, 1), self.original)

    def test_no_duplicate_authority(self):
        selected = patch(self.original)
        self.assertEqual(selected.count(' session.takeover=function'), 1)
        self.assertEqual(selected.count('function BotActors.start('), self.original.count('function BotActors.start('))
        self.assertEqual(selected.count(PREEXISTING_GUARD), 1)

    def test_idempotent_selection_is_rejected(self):
        with self.assertRaises(ValueError):
            patch(patch(self.original))

    def test_missing_anchor_is_rejected(self):
        with self.assertRaises(ValueError):
            patch(self.original.replace(ANCHOR, "", 1))

    def test_modified_original_alive_gate_is_rejected(self):
        with self.assertRaises(ValueError):
            patch(self.original.replace(PREEXISTING_GUARD, "", 1))

    def test_duplicate_takeover_is_rejected(self):
        with self.assertRaises(ValueError):
            patch(self.original + "\n" + ANCHOR + PREEXISTING_GUARD)

    def test_other_bot_behavior_preserved(self):
        selected = patch(self.original)
        for marker in ("local function tryHeroAttack(", "local function clearActionPath(",
                       "local function hitNeutralSafely(", "Router.navigate(", "Rules.takeEggs(",
                       "Rules.depositEggs(", "Rules.damageCastle(", "session.dropCarrierEggs("):
            self.assertEqual(self.original.count(marker), selected.count(marker), marker)

if __name__ == "__main__":
    unittest.main()
