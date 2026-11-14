#!/usr/bin/env python3
"""#361 authentic additive private67 scene regression tests."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "rc_fastlane/apply_owner361_castle.py"
OLD_MAP = ROOT / "releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau"
spec = importlib.util.spec_from_file_location("owner361_castle", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CastleWorldTests(unittest.TestCase):
    def setUp(self):
        self.authored = mod.SOURCE.read_text("utf8")

    def test_one_exact_native_addon(self):
        self.assertEqual(mod.blob(mod.SOURCE.read_bytes()), mod.PIN)
        mod.check_authored(self.authored.encode("utf8"))
        self.assertIn("server/Owner361CastleBattlefield.server.luau", mod.DEST)

    def test_actual_map_untouched_not_a_clone(self):
        original = OLD_MAP.read_text("utf8")
        self.assertIn('MapBuilder.build(config)', original)
        self.assertNotIn('function MapBuilder.build(config)', self.authored)
        self.assertNotIn('Instance.new("RemoteEvent")', self.authored)
        self.assertNotIn('TakeDamage(', self.authored)
        self.assertIn('if not RunService:IsStudio() then return end', self.authored)

    def test_real_location_anchors_and_objectives_not_moved(self):
        for marker in (
            'world:WaitForChild("RED_CASTLE", 10)',
            'world:WaitForChild("BLUE_CASTLE", 10)',
            'world:WaitForChild("GrassArena", 10)',
            'grass.Size = Vector3.new(370, 4, 294)',
            'north.Position = Vector3.new(0, 7, -147)',
            'south.Position = Vector3.new(0, 7, 147)',
        ):
            self.assertIn(marker, self.authored)
        self.assertNotIn('_CASTLE_CORE.Position =', self.authored)
        self.assertNotIn('_EGG.Position =', self.authored)

    def test_three_routes_two_castles_crest_and_low_labels(self):
        for marker in (
            'fortress(-1, "RED"', 'fortress(1, "BLUE"',
            '"GRAND_KEEP"', '"OPEN_GATE_ARCH"', '"GATE_TOWER_"',
            '"NORTH_WOODLAND_TRAIL"', '"SOUTH_WETLAND_TRAIL"',
            '"NORTH_LOOKOUT_PLATEAU_"', '"SOUTH_SHALLOW_WATER_"',
            "descendant.MaxDistance = 26",
            "descendant.AlwaysOnTop = false",
        ):
            self.assertIn(marker, self.authored)

    def test_off_is_absolute_no_write(self):
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "nonexistent"
            self.assertFalse(mod.apply(dest, False))
            self.assertFalse(dest.exists())

    def test_altered_author_fails_closed(self):
        with self.assertRaises(AssertionError):
            mod.check_authored(self.authored.replace("GRAND_KEEP", "BROKEN").encode("utf8"))


if __name__ == "__main__":
    unittest.main()
