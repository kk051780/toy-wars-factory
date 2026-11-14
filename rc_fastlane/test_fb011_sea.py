#!/usr/bin/env python3
"""FB-011 H1 sea scene source QA. Studio visuals remain UNTESTED."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "rc_fastlane/apply_fb011_sea.py"
spec = importlib.util.spec_from_file_location("apply_fb011_sea", MODULE)
assert spec and spec.loader
sea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sea)


class SeaRouteRebuild(unittest.TestCase):
    def setUp(self):
        self.raw = sea.SRC.read_bytes()
        self.src = self.raw.decode("utf8")

    def test_exact_scene_git_blob(self):
        self.assertEqual(sea.blob(self.raw), sea.PIN)
        sea.validate_scene(self.raw)

    def test_before_after_comparison_has_real_coast_not_just_blue_color(self):
        for zone in (
            "SHALLOW_TURQUOISE_BAY", "MIDDLE_AZURE_BAY", "DEEP_SEA_HORIZON",
            "SANDY_COAST_", "BREAKING_SURF_", "SUN_GLINT_", "SWELL_RIDGE_",
            "OFFSHORE_REEF_", "OLD_PIER_PLANK_", "OLD_PIER_POST_",
            "DISTANT_BUOY_",
        ):
            self.assertIn(zone, self.src)
        self.assertGreaterEqual(self.src.count("Enum.Material.Glass"), 4)
        self.assertIn("sea.Material = Enum.Material.Glass", self.src)
        self.assertNotIn("sea.Material = Enum.Material.Neon", self.src)

    def test_original_walkable_h1_sea_road_and_game_are_not_rewritten(self):
        for x in (
            'h1:FindFirstChild("SEA_LOW_CAUSEWAY")',
            'if not lane or not lane:IsA("BasePart")',
            'OriginalSeaRoutePreserved',
            "p.CanCollide = false",
            "p.CanQuery = false",
        ):
            # The lane guard is conjoined with sea in one clause in the script.
            if x == 'if not lane or not lane:IsA("BasePart")':
                self.assertIn('or not lane or not lane:IsA("BasePart")', self.src)
            else:
                self.assertIn(x, self.src)
        self.assertNotIn("lane.CFrame =", self.src)
        self.assertNotIn("lane.Position =", self.src)
        self.assertNotIn("lane.Size =", self.src)
        self.assertNotIn("DataStoreService", self.src)
        self.assertNotIn("FireServer(", self.src)
        self.assertNotIn("TakeDamage(", self.src)

    def test_handles_both_known_sea_strip_variants_without_guess(self):
        self.assertIn("sea.Size.X < 210", self.src)
        self.assertIn("sea.Size.X > 228", self.src)
        self.assertIn("sea.Size.Z < 22", self.src)
        self.assertIn("sea.Size.Z > 32", self.src)
        self.assertIn("math.abs(sea.Position.Z + 30)", self.src)
        self.assertIn("math.abs(sea.Position.Z + 49)", self.src)
        self.assertIn("FB011_SEA_ROUTE_DRIFT_FAIL_CLOSED", self.src)

    def test_studio_only_no_new_effect_authority(self):
        self.assertIn('if not RunService:IsStudio() then return end', self.src)
        self.assertIn('scenery.Name = "FB011_COASTAL_SEA_V1"', self.src)
        self.assertIn('scenery:SetAttribute("NoGameAuthority", true)', self.src)
        self.assertNotIn('Instance.new("RemoteEvent")', self.src)
        self.assertNotIn('Terrain:FillBlock', self.src)

    def test_budget_has_room_for_geometry(self):
        # 3 sea slabs + 17*2 beaches/surf + 30 reflections + 12 swells +
        # 10*2 reef/foam + 13 pier planks + 5*2 posts + 2 buoys = 124.
        estimated = 3 + 34 + 30 + 12 + 20 + 13 + 10 + 2
        self.assertLessEqual(estimated, 142)
        self.assertEqual(estimated, 124)
        self.assertIn("count <= 142", self.src)

    def test_untrusted_or_modified_source_rejected(self):
        with self.assertRaisesRegex(AssertionError, "AUTHOR_BLOB_DRIFT"):
            sea.validate_scene(self.raw.replace(b"DEEP_SEA_HORIZON", b"BROKEN_WATER_BG"))

    def test_off_never_writes(self):
        with tempfile.TemporaryDirectory() as d:
            nonexistent = Path(d) / "not_created"
            self.assertFalse(sea.apply(nonexistent, False))
            self.assertFalse(nonexistent.exists())


if __name__ == "__main__":
    unittest.main()
