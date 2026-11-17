#!/usr/bin/env python3
"""Source-derived negative assertions for GQ81 0.42s, never a fake Studio pass."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_hit042 import (AUTHOR_BLOB,LABEL_ADD,PULSE_ADD,gitblob,patch)

ROOT=Path("_v3_original/handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")
SRC=ROOT/"EGGRUMBLE_CombatFeel.client.luau"
class ConfirmedHitPortTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=SRC.read_bytes()
        cls.original=cls.raw.decode("utf-8")
    def test_pinned_author_blob(self):
        self.assertEqual(gitblob(self.raw),AUTHOR_BLOB)
    def test_forward_and_reverse_source_exact(self):
        changed=patch(self.original)
        self.assertNotEqual(self.original,changed)
        self.assertEqual(changed.replace(PULSE_ADD,"",1).replace(LABEL_ADD,"",1),self.original)
    def test_pure_confirmed_hit_existing_sequence(self):
        c=patch(self.original)
        self.assertEqual(c.count('GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")'),1)
        self.assertEqual(c.count("local RECENT_CD=.12"),1)
        self.assertIn("if reduced() then return end",c)
    def test_real_042_and_017_timers_independent(self):
        c=patch(self.original)
        self.assertEqual(c.count("task.delay(.42,function()"),1)
        self.assertEqual(c.count("task.delay(.17,function()"),1)
        self.assertIn("if thisPulse==pulse and hitToast.Parent then hitToast.Visible=false end",c)
        # The mark is hidden after .17s; the .42s badge MUST NOT be its child.
        self.assertIn("hitToast.Parent=gui",c)
        self.assertIn("hitToast.Position=UDim2.new(.5,6,.49,34)",c)
        self.assertNotIn("hitToast.Parent=mark",c)
    def test_runtime_unchanged_and_no_extra_authority(self):
        c=patch(self.original)
        self.assertIn("if not RunService:IsStudio() then return end",c)
        self.assertNotIn('Instance.new("RemoteEvent")',c)
        self.assertNotIn("TakeDamage",c)
    def test_repeated_port_rejected(self):
        with self.assertRaisesRegex(ValueError,"RED_"):patch(patch(self.original))
    def test_mutant_missing_hit_sequence_rejected(self):
        m=self.original.replace("EGGRUMBLE_ImpactSequence","EGGRUMBLE_ImpactPrediction")
        with self.assertRaisesRegex(ValueError,"RED_"):patch(m)
    def test_mutant_no_reduced_motion_rejected(self):
        m=self.original.replace("if reduced() then return end","if false then return end",1)
        with self.assertRaisesRegex(ValueError,"RED_"):patch(m)
    def test_mutant_client_unlocked_rejected(self):
        m=self.original.replace("if not RunService:IsStudio() then return end","-- removed",1)
        with self.assertRaisesRegex(ValueError,"RED_"):patch(m)
    def test_mutant_anchor_changed_rejected(self):
        m=self.original.replace("mark.Parent=gui","mark.Parent=workspace",1)
        with self.assertRaisesRegex(ValueError,"RED_"):patch(m)
if __name__=="__main__":unittest.main()
