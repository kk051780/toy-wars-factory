#!/usr/bin/env python3
"""FB019 P0: native source-only negative & positive gates on the actual RC80 HUD."""
from __future__ import annotations
import unittest
from pathlib import Path
from apply_fb019_attack_gesture import patch,blob,PIN
BASE=Path("/tmp/p0d_fb018_button_label_dist/src/client/HUD.client.luau")
class AttackGestureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=BASE.read_bytes()
    def test_exact_author_input(self):
        self.assertEqual(blob(self.original),PIN)
    def test_new_attack_controller_single_authority(self):
        text=patch(self.original).decode("utf8")
        self.assertEqual(text.count("attack.Activated:Connect(pressAttack)"),1)
        self.assertEqual(text.count("if input.KeyCode == Enum.KeyCode.F then pressAttack()"),1)
        self.assertEqual(text.count('action("ATTACK",nil)'),1)
        self.assertIn('if now-attackLocalLastAt<.85 then return end',text)
        self.assertIn('snapshot.phase~="ACTIVE"',text)
        self.assertIn('flash.CanCollide=false',text)
        self.assertIn('flash.CanQuery=false',text)
        self.assertIn('flash.CanTouch=false',text)
    def test_author_drift_fails_closed(self):
        with self.assertRaises(AssertionError):
            patch(self.original+b"\n-- UNAUTHORIZED DRIFT")
    def test_never_emits_fake_damage(self):
        add=patch(self.original).decode("utf8").split("-- FB-019 OWNER P0: visible SWING",1)[1].split("-- Single existing HUD sequence counter",1)[0]
        for value in ("TakeDamage(", "Instance.new(\"RemoteEvent\")","FireServer({action=","UpdateAsync("):
            self.assertNotIn(value,add)
        self.assertIn('action("ATTACK",nil)',add)
if __name__=="__main__":
    unittest.main()
