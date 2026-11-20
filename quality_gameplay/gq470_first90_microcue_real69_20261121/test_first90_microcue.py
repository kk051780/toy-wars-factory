#!/usr/bin/env python3
"""Source-locked and negative tests for a genuine REAL69 LocalScript art patch.

No claims about Studio Solo/2client, Android frame rate, or human visual score.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import shutil
import unittest

import patch_first90_microcue69 as p

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORIGINAL = ROOT / p.ORIGINAL_LOCAL

class First90MicrocueSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = ORIGINAL.read_bytes().decode("utf-8")

    def test_exact_real_original_source_and_local_one_file_patch(self):
        self.assertEqual(p.digest(self.original.encode("utf-8")), p.ORIGINAL_SHA256)
        patched = p.transform(self.original)
        self.assertEqual(p.reverse(patched), self.original)
        self.assertEqual(patched.count(p.FEATURE), 1)
        self.assertNotEqual(p.digest(patched.encode()), p.ORIGINAL_SHA256)

    def test_visible_art_delta_and_nonblocking_policy(self):
        patched = p.transform(self.original)
        self.assertIn(p.SIZE_NEW, patched)
        self.assertIn(p.BG_NEW, patched)
        self.assertNotIn(p.SIZE_OLD, patched)
        self.assertNotIn(p.BG_OLD, patched)
        self.assertIn("local CUE_VISIBLE_SECONDS=4.5", patched)
        self.assertIn("local SELECTION_REMINDER_SECONDS=24", patched)
        self.assertIn("now-cueShownAt<CUE_VISIBLE_SECONDS", patched)
        self.assertIn("elseif needsSelection and now-lastReminderAt>=SELECTION_REMINDER_SECONDS then", patched)
        self.assertIn("if message~=previousCue then", patched)
        self.assertIn("billboard.AlwaysOnTop=false", patched)
        self.assertIn("billboard.MaxDistance=32", patched)
        self.assertIn("local DURATION=90", patched)
        self.assertNotIn("UDim2.fromOffset(210,43)", patched)

    def test_semantic_server_contract_no_duplicate_authority(self):
        before, after = self.original, p.transform(self.original)
        for exact in (
            'player:GetAttribute("EGGRUMBLE_SelectedRole")',
            'player:GetAttribute("EGGRUMBLE_Role")',
            'mode~="BATTLE_ROYALE"',
            'if player:GetAttribute("EGGRUMBLE_Eliminated")==true then',
            'local DURATION=90',
            'local STEP1=22',
            'local STEP2=48',
            'characterConnection:Disconnect()',
            'billboard:Destroy()',
            'if not RunService:IsStudio() then return end',
        ):
            self.assertEqual(before.count(exact), after.count(exact))
        for forbidden in ('FireServer(', 'Instance.new("RemoteEvent")',
                          "DataStoreService", "MarketplaceService",
                          'RenderStepped:Connect('):
            self.assertNotIn(forbidden, after)

    def test_semantic_cue_timer_model(self):
        # Pure policy model; not a simulated Roblox UI render or engine result.
        shown_at, reminder_at, previous = 0.0, 0.0, ""
        def tick(now, message, needs_selection):
            nonlocal shown_at, reminder_at, previous
            if message != previous:
                previous = message
                shown_at = now
                reminder_at = now
            elif needs_selection and now - reminder_at >= 24:
                shown_at = now
                reminder_at = now
            return bool(message) and now - shown_at < 4.5
        self.assertTrue(tick(0, "role", True))
        self.assertTrue(tick(4.49, "role", True))
        self.assertFalse(tick(4.5, "role", True))
        self.assertFalse(tick(23.9, "role", True))
        self.assertTrue(tick(24.0, "role", True))
        self.assertFalse(tick(28.5, "role", True))
        self.assertTrue(tick(30, "attack", False))
        self.assertFalse(tick(36, "attack", False))
        self.assertFalse(tick(60, "", False))
        self.assertTrue(tick(64, "deliver", False))
        self.assertFalse(tick(68.5, "deliver", False))
        self.assertFalse(tick(89, "deliver", False))

    def test_delayed_avatar_head_and_respawn_rearm_once(self):
        """Pure timer logic edge cases, not an engine render assertion."""
        src=p.transform(self.original)
        self.assertIn("local lastBoundHead:BasePart?=nil",src)
        self.assertIn("if head~=lastBoundHead then",src)
        self.assertIn("if head then cueShownAt=now end",src)
        self.assertIn("if head~=lastBoundHead then\n   lastBoundHead=head",src)
        cue_time=0.0
        previous_head=None
        def visible(now, head, has_message=True):
            nonlocal cue_time, previous_head
            if head is not previous_head:
                previous_head=head
                if head is not None:
                    cue_time=now
            return has_message and head is not None and now-cue_time<4.5
        head1=object()
        head2=object()
        self.assertFalse(visible(0,None))
        self.assertFalse(visible(9,None))
        self.assertTrue(visible(10,head1))  # late spawn gets a fresh cue
        self.assertFalse(visible(14.5,head1))
        self.assertFalse(visible(30,head1))  # same head cannot perpetually rearm
        self.assertFalse(visible(31,None))
        self.assertTrue(visible(34,head2))  # respawn binding has a new window
        self.assertFalse(visible(39,head2))
        self.assertFalse(visible(40,head2,has_message=False))

    def test_mutation_rejection_is_source_exact(self):
        mutants = [
            self.original + "\n-- unrelated code change\n",
            self.original.replace(p.SIZE_OLD, "", 1),
            self.original.replace(p.LOOP_OLD, "", 1),
            self.original.replace(p.STATE_OLD, "", 1),
            self.original.replace(p.BG_OLD, "", 1),
            self.original.replace("BATTLE_ROYALE", "BR", 1),
            self.original.replace("billboard.AlwaysOnTop=false",
                                  "billboard.AlwaysOnTop=true", 1),
            self.original.replace('billboard:Destroy()', '-- no cleanup', 1),
            self.original.replace("local DURATION=90", "local DURATION=900", 1),
            self.original.replace('player:GetAttribute("EGGRUMBLE_SelectedRole")',
                                  'player:GetAttribute("EGGRUMBLE_Role")', 1),
        ]
        for i, mutant in enumerate(mutants):
            with self.subTest(mutant=i), self.assertRaises(ValueError):
                p.transform(mutant)
        with self.assertRaises(ValueError):
            p.transform(p.transform(self.original))
        with self.assertRaises(ValueError):
            p.reverse(p.transform(self.original) + "\n-- unauthorized mutation")

    def test_exact_69_artifact_when_present(self):
        path = os.environ.get("GQ470_REAL69_BASE")
        if not path:
            self.skipTest("Set GQ470_REAL69_BASE for real original 69-source artifact")
        root = Path(path)
        scripts = p.selected(root)
        self.assertEqual(len(scripts), 69)
        self.assertEqual(scripts[p.ROUTE].read_bytes(), self.original.encode("utf-8"))
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "real69"
            shutil.copytree(root / "sources", tmp / "sources")
            for filename in (p.PROJECT, p.RECEIPT, p.PLACE):
                shutil.copy2(root / filename, tmp / filename)
            p.apply(tmp)
            after = p.selected(tmp)
            off = p.selected(tmp / p.OFF)
            self.assertEqual(len(after), len(off))
            self.assertEqual(set(after), set(off))
            self.assertEqual([r for r in after if after[r].read_bytes() != off[r].read_bytes()], [p.ROUTE])
            self.assertEqual(p.reverse(after[p.ROUTE].read_text()),
                             off[p.ROUTE].read_text())
            self.assertEqual((tmp/p.OFF/p.PLACE).read_bytes(),
                             (root/p.PLACE).read_bytes())
            with self.assertRaises(ValueError):
                p.apply(tmp)

if __name__ == "__main__":
    unittest.main()
