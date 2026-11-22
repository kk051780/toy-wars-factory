#!/usr/bin/env python3
"""Art #372: author-source contract; no Studio rendering claims."""
from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
mod_file = ROOT / "rc_fastlane/apply_art_minion.py"
spec = importlib.util.spec_from_file_location("apply_art_minion", mod_file)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class MinionArtTest(unittest.TestCase):
    def setUp(self):
        self.raw = mod.AUTHOR.read_bytes()
        self.src = self.raw.decode("utf8")

    def test_exact_3species_and_elite_body_source(self):
        self.assertEqual(mod.blob(self.raw), mod.PIN)
        mod.validate_scene(self.raw)
        for marker in ("KNIGHT_HELMET", "KNIGHT_SHIELD", "KNIGHT_SPEAR_TIP",
                       "WRAITH_HOOD", "WRAITH_ORB", "WRAITH_SHROUD",
                       "BRUTE_TUSK_", "BRUTE_MAUL_HEAD", "BRUTE_BACK_FUR",
                       "ELITE_MASK", "ELITE_WAR_CORE", "ELITE_BACK_BANNER"):
            self.assertIn(marker, self.src)

    def test_original_horde_lifecycle_not_fake_ai_or_second_controller(self):
        self.assertIn("mobsFolder.ChildAdded:Connect(", self.src)
        self.assertIn('arena:WaitForChild("EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT", 45)', self.src)
        self.assertIn('model:GetAttribute("P0D_ART_MINION_V1") == true', self.src)
        self.assertIn('model:SetAttribute("P0D_ART_MINION_V1", true)', self.src)
        self.assertIn('model.PrimaryPart', self.src)
        self.assertNotIn('Instance.new("RemoteEvent")', self.src)
        self.assertNotIn("TakeDamage(", self.src)

    def test_hit_feedback_only_from_existing_author_cues(self):
        self.assertIn('item.core.Color.R > .9', self.src)
        self.assertIn('string.find(tag.Text, "撃破")', self.src)
        self.assertIn('sparks.Rate = 0', self.src)
        self.assertIn('item.sparks:Emit(4)', self.src)
        self.assertIn('item.sparks:Emit(10)', self.src)
        self.assertIn('heartbeatAcc < .14', self.src)

    def test_collision_and_billboard_view_limits(self):
        self.assertIn("item.CanCollide = false", self.src)
        self.assertIn("item.CanQuery = false", self.src)
        self.assertIn("item.CanTouch = false", self.src)
        self.assertIn("item.MaxDistance = 27", self.src)
        self.assertIn("item.AlwaysOnTop = false", self.src)

    def test_reject_unexpected_author_bytes(self):
        with self.assertRaisesRegex(AssertionError, "SOURCE_DRIFT"):
            mod.validate_scene(self.raw.replace(b"KNIGHT_HELMET", b"UNKNOWN_MASK"))

    def test_off_preserves_uncreated_dist_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "missing"
            self.assertFalse(mod.apply(p, False))
            self.assertFalse(p.exists())


if __name__ == "__main__":
    unittest.main()
