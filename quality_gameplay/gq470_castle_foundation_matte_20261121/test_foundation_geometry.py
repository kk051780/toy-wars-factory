"""Offline geometric silhouette guard for GQ470 castle footing (not a Studio screenshot)."""
from __future__ import annotations
import math
from pathlib import Path
import unittest

LUA = Path(__file__).with_name("EGGRUMBLE_CastleFoundationMatte.client.luau")


def bounded_radius(size: float) -> float:
    # Exact declared Lua expression: math.clamp(core.Size.{X,Z}*.5+.75,2.0,64.0).
    return min(64.0, max(2.0, size * .5 + .75))


def projected_side_centers(width: float, depth: float):
    return [
        (math.sin(side * math.pi * .5) * bounded_radius(width),
         math.cos(side * math.pi * .5) * bounded_radius(depth))
        for side in range(4)
    ]


class FoundationGeometrySourceTests(unittest.TestCase):
    def test_actual_source_math_contract(self):
        source = LUA.read_text(encoding="utf-8")
        self.assertIn("math.clamp(core.Size.X * .5 + .75, 2.0, 64.0)", source)
        self.assertIn("math.clamp(core.Size.Z * .5 + .75, 2.0, 64.0)", source)
        self.assertIn("for side = 0, 3 do", source)
        self.assertIn("local angle = side * math.pi * .5", source)
        self.assertIn("local alongX = math.sin(angle) * radiusX", source)
        self.assertIn("local alongZ = math.cos(angle) * radiusZ", source)
        self.assertIn("local first = side * 2 + 1", source)
        self.assertIn("CFrame.new(0, 0, .18)", source)
        self.assertIn("CFrame.new(0, .85, -.22)", source)
        self.assertIn("Vector3.new(2.4, 1.45, 1.35)", source)
        self.assertIn("Vector3.new(1.55, .42, .82)", source)

    def test_four_footing_shoulders_reach_outer_core_faces(self):
        # Static coordinates only; actual Roblox CFrame and scene must be engine-tested.
        for width, depth in ((4, 4), (8, 15), (24, 32), (72, 72), (120, 120)):
            with self.subTest(width=width, depth=depth):
                p = projected_side_centers(width, depth)
                self.assertEqual(len(p), 4)
                # Four distinct axis directions, with centerlines outside base.
                self.assertGreater(p[0][1], depth / 2)
                self.assertGreater(p[1][0], width / 2)
                self.assertLess(p[2][1], -depth / 2)
                self.assertLess(p[3][0], -width / 2)
                self.assertAlmostEqual(p[0][0], 0, delta=1e-8)
                self.assertAlmostEqual(p[1][1], 0, delta=1e-8)
                self.assertAlmostEqual(p[2][0], 0, delta=1e-8)
                self.assertAlmostEqual(p[3][1], 0, delta=1e-8)

    def test_existing_two_wedges_not_buried_inside_core(self):
        # Footing radial clearance 0.75 minus worst inward wedge projection.
        # The stone's half-depth is 1.35/2 and inset's half-depth is .82/2.
        for size in (4, 8, 24, 32, 72, 120):
            with self.subTest(size=size):
                clearance = bounded_radius(size) - size * .5
                outer_shoulder_min = clearance + .18 - 1.35 / 2
                bevel_min = clearance - .22 - .82 / 2
                self.assertGreater(outer_shoulder_min, 0.0)
                self.assertGreater(bevel_min, 0.0)

    def test_budget_unchanged_by_big_castle_geometry(self):
        source = LUA.read_text(encoding="utf-8")
        self.assertIn("local PARTS_PER_CASTLE = 8", source)
        self.assertIn("local MAX_CASTLES = if UserInputService.TouchEnabled then 2 else 3", source)
        self.assertIn("assert(#stones == PARTS_PER_CASTLE)", source)
        self.assertLessEqual(2 * 8, 16)
        self.assertLessEqual(3 * 8, 24)


if __name__ == "__main__":
    unittest.main()
