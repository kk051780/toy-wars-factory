#!/usr/bin/env python3
"""#361 authored castle/map regression (source-level only, NOT Studio FUN)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "rc_fastlane/apply_owner361_castle.py"
ORIGINAL = ROOT / "releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau"

spec = importlib.util.spec_from_file_location("owner361_castle", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CastleRoutePrepTests(unittest.TestCase):
    def setUp(self):
        self.base = ORIGINAL.read_text(encoding="utf8")
        self.authored = mod.AUTHOR.read_text(encoding="utf8")

    def test_exact_authored_blob_and_contract(self):
        self.assertEqual(mod.gitblob(self.base.encode("utf8")), mod.OLD_BLOB)
        self.assertEqual(mod.gitblob(self.authored.encode("utf8")), mod.NEW_BLOB)
        mod.check_authored_map(self.authored.encode("utf8"))

    def test_sides_and_server_objectives_have_exact_original_anchors(self):
        critical = (
            'Vector3.new(sign * 107, 6.5, 0)',
            'Vector3.new(sign * 98, 2.5, -20)',
            'Vector3.new(sign * 82, -.5, 20)',
            'spawn = CFrame.new(sign * 68, 5, 0)',
            'eggPrompt = prompt(egg, "Steal egg", name .. " treasure")',
            'scorePrompt = prompt(pad, "Deliver egg", name .. " scoring pad")',
            'result.teams[name] = {core = core, egg = egg, eggPrompt = eggPrompt,',
            'b.Parent = partRef',
        )
        for anchor in critical:
            self.assertIn(anchor, self.base)
            self.assertIn(anchor, self.authored)

    def test_world_larger_and_has_symmetric_3D_castles(self):
        self.assertIn('Vector3.new(250, 4, 142)', self.base)
        self.assertNotIn('Vector3.new(250, 4, 142)', self.authored)
        self.assertIn('Vector3.new(370, 4, 294)', self.authored)
        self.assertIn('castleArchitecture(base, sign, accent)', self.authored)
        self.assertIn('Vector3.new(sign * 139, 18, 0)', self.authored)
        self.assertIn('"FRONT_TOWER_"', self.authored)
        self.assertIn('"GATE_ARCH"', self.authored)

    def test_accessible_pads_and_small_distance_limited_labels(self):
        self.assertIn('local z = side * 44', self.authored)
        self.assertIn('Vector3.new(sign * 83, 10, z)', self.authored)
        self.assertIn('b.MaxDistance = 26', self.authored)
        self.assertIn('b.AlwaysOnTop = false', self.authored)
        self.assertIn('UDim2.fromOffset(96, 22)', self.authored)
        self.assertIn('UDim2.fromOffset(210, 44)', self.base)

    def test_north_and_south_routes_and_map_bounds(self):
        for anchor in (
            '"NORTH_WOODLAND_TRAIL"', '"SOUTH_WETLAND_TRAIL"',
            '"NORTH_LOOKOUT_PLATEAU_"', '"SOUTH_SHALLOW_WATER_"',
            '"SOUTH_STEPPING_STONE_"', '"WOOD_TRUNK_"',
            '"ARENA_BOUNDARY_W"', '"ARENA_BOUNDARY_E"',
            '"CENTER_STREAM"',
        ):
            self.assertIn(anchor, self.authored)
        self.assertIn('Vector3.new(0, 7, -147)', self.authored)
        self.assertIn('Vector3.new(0, 7, 147)', self.authored)
        self.assertIn('Vector3.new(185, 7, 0)', self.authored)

    def test_off_is_zero_write(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "nonexistent"
            self.assertFalse(mod.apply(path, False))
            self.assertFalse(path.exists())

    def test_drift_fails_closed(self):
        with self.assertRaises(AssertionError):
            mod.check_authored_map(self.authored.replace("GREAT_KEEP", "BROKEN").encode("utf8"))


if __name__ == "__main__":
    unittest.main()
