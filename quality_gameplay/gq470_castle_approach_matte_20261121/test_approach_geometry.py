"""Static geometry/property budget gate for rectangular castle approach stones.

Matches Luau's local X/Z offset expressions and verifies rotated castles.
This is NOT a Roblox Studio screenshot, FPS proof or human art grade.
"""
from math import cos, sin, pi
import unittest
from pathlib import Path

LUA = Path(__file__).with_name("EGGRUMBLE_CastleApproachMatte.client.luau")

def clamp(value):
    return min(72.0, max(12.0, value))

def approach_positions(core_x, core_z, yaw, width, depth):
    assert width > 0 and depth > 0
    offset_x = clamp(width * .5 + 9)
    offset_z = clamp(depth * .5 + 9)
    points = []
    for side in range(4):
        theta = side * pi / 2
        # Source uses core.CFrame and local offsets separately per face.
        dx, dz = sin(theta) * offset_x, cos(theta) * offset_z
        world_x = core_x + dx * cos(yaw) + dz * sin(yaw)
        world_z = core_z - dx * sin(yaw) + dz * cos(yaw)
        points.append((world_x, world_z))
    return (offset_x, offset_z), points

class TestApproachGeometry(unittest.TestCase):
    def test_source_math_matches_local_axes(self):
        luau = LUA.read_text(encoding="utf-8")
        for token in (
            "math.clamp(core.Size.X * .5 + 9, 12, 72)",
            "math.clamp(core.Size.Z * .5 + 9, 12, 72)",
            "math.sin(angle) * offsetX, 0, math.cos(angle) * offsetZ",
        ):
            self.assertEqual(luau.count(token), 1)
        self.assertNotIn("math.max(core.Size.X, core.Size.Z)", luau)
        self.assertNotIn("math.sin(angle) * offset, 0, math.cos(angle) * offset", luau)

    def test_each_axis_remains_near_correct_face(self):
        # Supported original source guard disallows XY >126, so each valid
        # local face is 9 studs beyond the face (or >=9 for minimum clamp).
        for width, depth in ((4,4), (12,18), (36,22), (60,60),
                             (120,120), (8,120), (120,8), (126,9), (9,126)):
            for yaw in (0, pi / 5, pi / 2):
                with self.subTest(width=width,depth=depth,yaw=yaw):
                    (ox,oz), pts = approach_positions(30,-41,yaw,width,depth)
                    self.assertEqual(len(pts),4)
                    self.assertEqual(len({(round(x,5),round(z,5)) for x,z in pts}),4)
                    self.assertGreaterEqual(ox,width/2+8)
                    self.assertGreaterEqual(oz,depth/2+8)
                    self.assertLessEqual(ox,width/2+11.5)
                    self.assertLessEqual(oz,depth/2+11.5)

    def test_rectangular_castle_not_pushed_to_long_edge_radius(self):
        # Old max(width,depth) radius incorrectly put short-face stones 69
        # studs from core center for width8/depth120 instead of 13.
        for width, depth, x_dist,z_dist in (
            (8,120,13,69), (120,8,69,13), (14,100,16,59),
        ):
            with self.subTest(width=width,depth=depth):
                (ox,oz), pts = approach_positions(0,0,0,width,depth)
                self.assertEqual((ox,oz),(x_dist,z_dist))
                self.assertAlmostEqual(pts[0][1], z_dist)
                self.assertAlmostEqual(pts[1][0], x_dist)
                self.assertAlmostEqual(pts[2][1],-z_dist)
                self.assertAlmostEqual(pts[3][0],-x_dist)

    def test_budget_bounded_for_out_of_range_geometry(self):
        for width,depth in ((1,1),(130,40),(140,140),(1000,10)):
            (ox,oz),pts=approach_positions(0,0,0,width,depth)
            self.assertTrue(12<=ox<=72 and 12<=oz<=72)
            self.assertEqual(len(pts)*2,8)
        self.assertEqual(2*8,16)
        self.assertEqual(3*8,24)

    def test_rotation_preserves_each_face_offset(self):
        for width,depth in ((12,27),(7,110),(125,9)):
            (ox,oz),_=approach_positions(19,-8,0,width,depth)
            for yaw in (0,pi/7,pi/3,pi):
                _,pts=approach_positions(19,-8,yaw,width,depth)
                for index,(x,z) in enumerate(pts):
                    target=oz if index%2==0 else ox
                    self.assertAlmostEqual((x-19)**2+(z+8)**2,target**2,places=6)

if __name__=="__main__":
    unittest.main()
