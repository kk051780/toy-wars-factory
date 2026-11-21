"""Pure geometry/property budget tests; NOT Studio visual acceptance."""
from math import cos, sin, pi
import unittest

def approach_positions(core_x, core_z, yaw, width, depth):
    assert width > 0 and depth > 0
    offset = min(72.0, max(12.0, max(width, depth) / 2.0 + 9.0))
    points = []
    for side in range(4):
        theta = side * pi / 2
        # The Lua uses core.CFrame rotation then CFrame.new(local dx,dz).
        dx, dz = sin(theta) * offset, cos(theta) * offset
        world_x = core_x + dx * cos(yaw) + dz * sin(yaw)
        world_z = core_z - dx * sin(yaw) + dz * cos(yaw)
        points.append((world_x, world_z))
    return offset, points

class TestApproachGeometry(unittest.TestCase):
    def test_stays_outside_castle_footprint_normal_sizes(self):
        for width, depth in ((4, 4), (12, 18), (36, 22), (60, 60), (120, 120)):
            for yaw in (0, pi / 5, pi / 2):
                with self.subTest(width=width, depth=depth, yaw=yaw):
                    offset, pts = approach_positions(30, -41, yaw, width, depth)
                    self.assertGreaterEqual(offset, max(width, depth) / 2 + 8)
                    self.assertEqual(4, len(pts))
                    self.assertEqual(4, len(set((round(x, 5), round(z, 5)) for x, z in pts)))
    def test_bounds_and_mobile_budgets(self):
        for width, depth in ((1, 1), (130, 40), (140, 140), (1000, 10)):
            offset, pts = approach_positions(0, 0, 0, width, depth)
            self.assertGreaterEqual(offset, 12)
            self.assertLessEqual(offset, 72)
            self.assertEqual(len(pts) * 2, 8)
        self.assertEqual(2 * 8, 16)
        self.assertEqual(3 * 8, 24)
    def test_rotation_preserves_radius(self):
        for yaw in (0, pi/7, pi/3, pi):
            offset, pts = approach_positions(19, -8, yaw, 12, 27)
            for x, z in pts:
                self.assertAlmostEqual((x - 19)**2 + (z + 8)**2, offset**2, places=6)

if __name__ == "__main__":
    unittest.main()
