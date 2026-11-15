import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location("p0d_field_audit", HERE / "field_baseline.py")
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)

class SourceRealFieldTest(unittest.TestCase):
    def setUp(self):
        self.mb = ROOT / audit_module.DEFAULT_MAP
        self.studio = ROOT / audit_module.DEFAULT_STUDIO
        self.r = audit_module.audit(self.mb, self.studio)

    def test_real_mapbuilder_ground_exact(self):
        self.assertEqual([250.0,4.0,142.0], self.r["base_map"]["ground_studs_xyz"])
        self.assertEqual(35500, self.r["base_map"]["ground_plan_area_studs2"])
        self.assertEqual([226.0,.3,24.0], self.r["base_map"]["center_road_studs_xyz"])

    def test_studio_only_expansion_is_not_verified_live(self):
        self.assertEqual([370.0,4.0,294.0], self.r["studio_only_extension"]["ground_studs_xyz"])
        self.assertEqual(108780, self.r["studio_only_extension"]["ground_plan_area_studs2"])
        self.assertEqual(3.0642, self.r["studio_only_extension"]["area_multiplier_vs_base"])
        self.assertFalse(self.r["studio_only_extension"]["public_build_expansion_verified"])
        self.assertTrue(self.r["studio_only_extension"]["studio_guard_source_confirmed"])

    def test_flanks_outside_original_ground_and_not_path_verification(self):
        routes = self.r["studio_only_extension"]["decorative_flank_trails"]
        self.assertEqual(2, len(routes))
        self.assertTrue(all(x["center_outside_base_ground_z"] for x in routes))
        self.assertIsNone(self.r["studio_only_extension"]["walkable_routes_engine_verified"])
        self.assertIsNone(self.r["base_map"]["other_effective_traversal_routes"])

    def test_straight_distance_not_fabricated_walk_time(self):
        d=self.r["objective_geometry_lower_bounds"]
        self.assertEqual(136.0, d["red_blue_spawn_straight_line_studs"])
        self.assertAlmostEqual(167.201, d["red_spawn_to_blue_egg_straight_line_studs"], delta=.002)
        self.assertAlmostEqual(184.391, d["blue_egg_to_red_scoring_pad_straight_line_studs"], delta=.002)
        self.assertIsNone(d["walking_seconds"])
        self.assertIsNone(d["pathfinding_success_by_route"])

    def test_guard_removed_is_not_assumed_to_be_studio_only(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"m.luau"
            p.write_text(self.studio.read_text(encoding="utf8").replace("if not RunService:IsStudio() then return end","-- guard removed"),encoding="utf8")
            with self.assertRaisesRegex(ValueError, "STUDIO_ONLY_GUARD_UNKNOWN"):
                audit_module.audit(self.mb,p)

    def test_misleading_duplicate_arena_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"m.luau"
            p.write_text(self.mb.read_text(encoding="utf8") +
                         '\npart(folder, "GrassArena", Vector3.new(999,1,999), foo)\n',encoding="utf8")
            with self.assertRaisesRegex(ValueError, "SOURCE_PATTERN_AMBIGUOUS_OR_MISSING"):
                audit_module.audit(p,self.studio)

if __name__ == "__main__":
    unittest.main()
