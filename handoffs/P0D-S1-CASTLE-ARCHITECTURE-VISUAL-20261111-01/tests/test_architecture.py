from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE = ROOT / "assets" / "architecture_spec.json"
PLAN_FILE = ROOT / "src" / "CastleArchitecturePlan.luau"
RUNTIME_FILE = ROOT / "src" / "CastleArchitecture.luau"
GEN_FILE = ROOT / "tools" / "generate_architecture.py"
spec = importlib.util.spec_from_file_location("architecture_generator", GEN_FILE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ArchitectureGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(SPEC_FILE.read_text(encoding="utf8"))
        cls.src = RUNTIME_FILE.read_text(encoding="utf8")
        cls.entries = cls.doc["elements"]

    def test_01_schema_identity(self): self.assertEqual(self.doc["schema"], "TRAP_RAIDERS_S1_ARCHITECTURE_V1")
    def test_02_game_map_exact(self): self.assertEqual(self.doc["source_map"], "TRAP_RAIDERS_S1")
    def test_03_no_collision_flag(self): self.assertIs(self.doc["collision"], False)
    def test_04_bounded_part_budget(self): self.assertLessEqual(len(self.entries), 80)
    def test_05_exact_art_budget(self): self.assertEqual(len(self.entries), 50)
    def test_06_unique_names(self): self.assertEqual(len({e["id"] for e in self.entries}), len(self.entries))
    def test_07_red_blue_symmetry(self):
        by_name = {e["id"]:e for e in self.entries}
        for e in self.entries:
            if e["id"].startswith("RED_"):
                twin = by_name[e["id"].replace("RED_", "BLUE_", 1)]
                self.assertEqual(e["center"][0], -twin["center"][0])
                self.assertEqual(e["center"][1:], twin["center"][1:])
                self.assertEqual(e["size"], twin["size"])
    def test_08_style_allowlist(self):
        for e in self.entries: self.assertIn(e["style"], module.STYLES)
    def test_09_root_schema_valid(self): module.validate(self.doc)
    def test_10_expected_two_team_roofs(self):
        self.assertEqual(sum("ROOF_PLATE" in e["id"] for e in self.entries), 4)
    def test_11_parapet_both_sides(self):
        self.assertEqual(sum("PARAPET" in e["id"] for e in self.entries), 4)
    def test_12_crown_both_sides(self):
        self.assertEqual(sum("CORE_CROWN" in e["id"] for e in self.entries), 2)
    def test_13_edge_only_landmark(self):
        edge = [e for e in self.entries if e["id"].startswith("MID_")]
        self.assertEqual(len(edge), 10)
        self.assertTrue(all(abs(e["center"][2]) == 71 for e in edge))
    def test_14_no_custom_geometry_around_egg(self):
        self.assertFalse(any("EGG" in e["id"] for e in self.entries))
    def test_15_no_castle_banners_owned_by_D17(self):
        self.assertFalse(any("BANNER" in e["id"] or "FLAG" in e["id"] for e in self.entries))
    def test_16_not_in_player_path(self):
        # All parts attach above preexisting collidable back wall/towers/core, or boundary wall.
        self.assertTrue(all(e["center"][1] >= 14 for e in self.entries))
    def test_17_id_name_prefix(self):
        self.assertTrue(all(e["id"].startswith(("RED_", "BLUE_", "MID_")) for e in self.entries))
    def test_18_generator_idempotent(self):
        self.assertEqual(module.make_spec(), self.doc)
    def test_19_generated_plan_exact(self):
        self.assertEqual(module.plan_luau(self.doc), PLAN_FILE.read_text(encoding="utf8"))
    def test_20_generator_check_mode(self):
        result = subprocess.run([sys.executable, str(GEN_FILE), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("50", result.stdout)
    def test_21_boundary_bounding_boxes(self):
        for e in self.entries:
            x,y,z = e["center"]; sx,sy,sz = e["size"]
            self.assertLessEqual(abs(x)+sx/2, 129)
            self.assertLessEqual(abs(z)+sz/2, 75)
            self.assertLessEqual(y+sy/2, 32)
            self.assertGreaterEqual(y-sy/2, 0)
    def test_22_plan_bad_duplicate_rejected(self):
        x=copy.deepcopy(self.doc); x["elements"].append(copy.deepcopy(x["elements"][0]))
        with self.assertRaises(AssertionError): module.validate(x)
    def test_23_plan_bad_style_rejected(self):
        x=copy.deepcopy(self.doc); x["elements"][0]["style"] = "P2W_RED_BANNER"
        with self.assertRaises(AssertionError): module.validate(x)
    def test_24_plan_bad_large_size_rejected(self):
        x=copy.deepcopy(self.doc); x["elements"][0]["size"] = [999,2,2]
        with self.assertRaises(AssertionError): module.validate(x)
    def test_25_plan_bad_bounds_rejected(self):
        x=copy.deepcopy(self.doc); x["elements"][0]["center"] = [130,22,0]
        with self.assertRaises(AssertionError): module.validate(x)
    def test_26_plan_bad_extra_key_rejected(self):
        x=copy.deepcopy(self.doc); x["elements"][0]["loot"] = "paid"
        with self.assertRaises(AssertionError): module.validate(x)
    def test_27_plan_bad_collision_rejected(self):
        x=copy.deepcopy(self.doc); x["collision"] = True
        with self.assertRaises(AssertionError): module.validate(x)
    def test_28_plan_bad_missing_map_rejected(self):
        x=copy.deepcopy(self.doc); x["source_map"] = "OTHER_GAME"
        with self.assertRaises(AssertionError): module.validate(x)
    def test_29_plan_budget_exceeded_rejected(self):
        x=copy.deepcopy(self.doc)
        for i in range(90):
            e=copy.deepcopy(self.doc["elements"][0]); e["id"] = f"RED_TEST_{i}"
            x["elements"].append(e)
        with self.assertRaises(AssertionError): module.validate(x)

class RuntimeSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.source = RUNTIME_FILE.read_text(encoding="utf8")
    def test_30_module_is_not_autorunning(self):
        self.assertIn("function Architecture.build(root: Instance)",self.source)
        self.assertTrue(self.source.rstrip().endswith("return Architecture"))
    def test_31_disabled_collisions(self):
        for token in ["p.Anchored = true", "p.CanCollide = false", "p.CanTouch = false", "p.CanQuery = false"]:
            self.assertIn(token, self.source)
    def test_32_map_root_guard(self):
        self.assertIn('ROOT_NAME = "TRAP_RAIDERS_S1"',self.source)
        self.assertIn('root:FindFirstChild("RED_CASTLE")',self.source)
        self.assertIn('root:FindFirstChild("BLUE_CASTLE")',self.source)
    def test_33_duplicate_guard(self): self.assertIn('return false, "ALREADY_BUILT"',self.source)
    def test_34_no_runtime_services_or_remote(self):
        for forbidden in ["FireServer", "FireClient", "RemoteEvent", "DataStore", "OnServerEvent", "GetService", "Players", "Humanoid", "TakeDamage", "ProximityPrompt", "TweenService", "task.spawn"]:
            self.assertNotIn(forbidden, self.source)
    def test_35_no_gameplay_authority(self):
        for forbidden in ["match.serial", "roundId", "score +=", "match.hp", "OnClientEvent", "ServerTimeNow", "winner ="]:
            self.assertNotIn(forbidden, self.source)
    def test_36_fail_closed_creating(self):
        self.assertIn("pcall(function()",self.source)
        self.assertIn('return false, "VISUAL_CREATION_FAILED"',self.source)
        self.assertIn("folder:Destroy()",self.source)
    def test_37_atomic_attachment(self):
        self.assertLess(self.source.index("local ok = pcall"),self.source.index("folder.Parent = root"))
    def test_38_invalid_nans_rejected(self):
        self.assertIn("value == value", self.source)
        self.assertIn("math.abs(value)",self.source)
    def test_39_luau_plan_required_once(self):
        self.assertEqual(self.source.count('WaitForChild("CastleArchitecturePlan")'),1)
    def test_40_visual_subfolder_only(self):
        self.assertIn('VISUAL_NAME = "S1_ARCHITECTURE_VISUAL_ONLY"',self.source)
        self.assertNotIn("root:Destroy()",self.source)

if __name__ == "__main__":
    unittest.main()
