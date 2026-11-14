#!/usr/bin/env python3
"""Native source contract tests for FB-008/FB-015 ART-COMBAT.

No Studio/FUN/Android claims are made by these static safety tests.
"""
from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("apply_fb015_combat", ROOT / "apply_fb015_combat.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ArtCombatContract(unittest.TestCase):
    def setUp(self):
        self.raw = mod.AUTHOR.read_bytes()
        self.text = self.raw.decode("utf8")

    def test_real_author_source_pin(self):
        self.assertEqual(mod.blob(self.raw), mod.PIN)
        self.assertTrue(mod.validate_visual(self.raw) is None)

    def test_read_only_confirmed_hit_not_client_damage(self):
        for marker in (
            'core:FindFirstChild("RealDamagePopup")',
            'popup:GetPropertyChangedSignal("Enabled")',
            'label:GetPropertyChangedSignal("Text")',
            'string.find(cue, "撃破", 1, true)',
            'if not popup.Enabled then return end',
        ):
            if marker == 'if not popup.Enabled then return end':
                self.assertIn("or not popup.Enabled then return end", self.text)
            else:
                self.assertIn(marker, self.text)
        for forbidden in ("FireServer(", "TakeDamage(", "DataStoreService",
                          'Instance.new("RemoteEvent")', "UpdateAsync("):
            self.assertNotIn(forbidden, self.text)

    def test_visual_budget_and_mobile_bypass(self):
        for marker in ("MAX_LIVE = 8", "MAX_BURSTS_PER_SECOND = 9",
                       "if UserInputService.TouchEnabled then 1 else 2",
                       "Debris:AddItem(holder, .22)", "holder.CanQuery = false",
                       "holder.CanCollide = false", "holder.CanTouch = false"):
            self.assertIn(marker, self.text)
        self.assertNotIn("RunService.Heartbeat:Connect(", self.text)
        self.assertNotIn("RunService.RenderStepped:Connect(", self.text)

    def test_round_respawn_no_duplicate_event_connections(self):
        self.assertIn("if bound[model] then", self.text) if "if bound[model] then" in self.text else self.assertIn("or bound[model] then return", self.text)
        self.assertIn("mobs.ChildAdded:Connect(", self.text)
        self.assertIn("model.Destroying:Connect(function() detach(model) end)", self.text)
        self.assertIn("for model in pairs(bound) do detach(model) end", self.text)

    def test_source_drift_fails_closed(self):
        with self.assertRaisesRegex(AssertionError, "ART_COMBAT_SOURCE_DRIFT"):
            mod.validate_visual(self.raw.replace(b"MAX_LIVE = 8", b"MAX_LIVE = 99"))

    def test_off_writes_nothing_even_with_missing_dist(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / "this_does_not_exist"
            self.assertFalse(mod.apply(dist, enabled=False))
            self.assertFalse(dist.exists())


if __name__ == "__main__":
    unittest.main()
