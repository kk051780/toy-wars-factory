#!/usr/bin/env python3
"""FB019 V2 regression contract for confirmed server damage visible with no tutorial."""
from __future__ import annotations
import unittest
from pathlib import Path
from apply_fb019_hit_visibility import patched,blob,read,GAME,GOV,GAME_BASE,GOV_BASE
BASE=Path("/tmp/p0d_fb019_attack_gesture_dist")
class ConfirmedHitVisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.src=read(BASE)
    def test_canonical_pins(self):
        self.assertEqual(blob(self.src[GAME]),GAME_BASE)
        self.assertEqual(blob(self.src[GOV]),GOV_BASE)
    def test_two_sources_only(self):
        next=patched(self.src)
        self.assertEqual({k for k in self.src if self.src[k]!=next[k]}, {GAME,GOV})
        self.assertEqual(len(next),80)
    def test_ack_only_server_hit_and_no_extra_remote(self):
        text=patched(self.src)[GAME].decode("utf8")
        anchor=text.index("        mobHits=touched")
        sample=text[anchor:text.index("    local chosen = nil",anchor)]
        self.assertIn("if touched>0 then",sample)
        self.assertIn("mobLastKOs[player]=defeated",sample)
        self.assertIn("remote:FireClient(player,snapshotFor(player))",sample)
        self.assertLess(sample.index("if touched>0 then"),sample.index("remote:FireClient(player,snapshotFor(player))"))
        self.assertEqual(text.count("remote.OnServerEvent:Connect("),1)
        self.assertNotIn("Instance.new(\"RemoteEvent\")",sample)
        self.assertNotIn("TakeDamage(",sample)
    def test_ui_exemption_only_for_real_short_server_damage(self):
        text=patched(self.src)[GOV].decode("utf8")
        self.assertIn('node.Name=="RealDamagePopup"',text)
        self.assertIn('core.Name=="Core"',text)
        self.assertIn('npc:IsDescendantOf(arena)',text)
        self.assertIn('^MUSOU_MINION_%d+$',text)
        self.assertIn('node.Name=="S1_CARRIED_EGG"',text)
        self.assertIn('noGuidanceActive=true',text)
        self.assertIn('g.Enabled=false',text)
    def test_author_drift_rejected(self):
        bad=dict(self.src)
        bad[GAME]=bad[GAME]+b"\n-- untrusted drift\n"
        with self.assertRaises(AssertionError):patched(bad)
if __name__=="__main__":unittest.main()
