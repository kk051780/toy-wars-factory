#!/usr/bin/env python3
"""Offline safety/data regression for the D18 source-only 3D mascot experiment.

These are structural tests and Python oracles, NOT Roblox Luau/Studio execution.
"""
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IDS = {"TRCA-BE-018", "TRCA-ZO-054"}
MAX_PARTS = 24
SHAPES = {"Block", "Ball", "Cylinder"}
GROUPS = {"none", "body", "head", "leaf", "lantern", "hat", "flag", "door"}
FORBIDDEN_FACTORY = (
    "RemoteEvent", "RemoteFunction", "Humanoid", "DataStore", "MarketplaceService",
    "Touched:Connect", ".Touched", "RunService", "Heartbeat", "task.wait", "task.spawn",
    "OnServerEvent", "OnClientEvent", "FireServer", "FireClient", "HttpService",
    "InsertService", "LoadAsset", "SoundId", "GetChildren", "ApplyDamage",
    "GetPlayer", "Purchase", "CollectionService", "GetService", "Connect(",
)


def load():
    return json.loads((ROOT / "data/mascot_geometry.json").read_text(encoding="utf-8"))


class MetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load()
        cls.source = json.loads((ROOT / "data/editorial_source_excerpt.json").read_text(encoding="utf-8"))
        cls.factory = (ROOT / "luau/MascotPreviewFactory.luau").read_text(encoding="utf-8")
        cls.demo = (ROOT / "luau/ShowcaseDemo.server.luau").read_text(encoding="utf-8")

    def test_exact_game_and_work(self):
        self.assertEqual(self.data["game_id"], "TRAP_RAIDERS")
        self.assertEqual(self.data["work_id"], "p0d-siege-v19")

    def test_pinned_editorial_source_provenance(self):
        self.assertEqual(self.data["source_packet_id"], "P0D-D18-HERO72-FINAL12-20261111-01")
        self.assertEqual(self.data["source_commit_sha"], "176bfc400ef6ec561b129a8163a0f4776e1b9ee4")

    def test_exact_two_characters(self):
        self.assertEqual(set(self.data["characters"]), EXPECTED_IDS)
        self.assertEqual(set(self.source), EXPECTED_IDS)

    def test_names_rarity_world_from_original(self):
        for cid, v in self.data["characters"].items():
            with self.subTest(cid=cid):
                for field in ("name", "rarity", "world"):
                    self.assertEqual(v[field], self.source[cid][field])

    def test_editorial_is_explicitly_noncombat(self):
        for cid, entry in self.source.items():
            self.assertIn("非戦闘", entry["scope"] if cid == "TRCA-BE-018" else "非戦闘展示")
            self.assertTrue(entry["silhouette"])
            self.assertTrue(entry["tap"] and entry["win"] and entry["loss"])

    def test_part_budget_and_minimum_identity(self):
        for cid, character in self.data["characters"].items():
            with self.subTest(cid=cid):
                self.assertLessEqual(len(character["parts"]), MAX_PARTS)
                self.assertGreaterEqual(len(character["parts"]), 10)
                self.assertLess(sum(not p["detail"] for p in character["parts"]), 20)

    def test_part_names_unique_and_allowlisted(self):
        for character in self.data["characters"].values():
            names = [p["name"] for p in character["parts"]]
            self.assertEqual(len(names), len(set(names)))
            for name in names:
                self.assertRegex(name, r"^[A-Za-z][A-Za-z0-9]{2,32}$")

    def test_part_shapes_and_groups(self):
        for char in self.data["characters"].values():
            for p in char["parts"]:
                self.assertIn(p["shape"], SHAPES)
                self.assertIn(p["group"], GROUPS)
                self.assertIs(type(p["detail"]), bool)

    def test_part_geometry_finite_and_small(self):
        for char in self.data["characters"].values():
            for p in char["parts"]:
                self.assertEqual(len(p["position"]), 3)
                self.assertEqual(len(p["size"]), 3)
                self.assertEqual(len(p["rotation"]), 3)
                for n in p["position"] + p["size"] + p["rotation"]:
                    self.assertTrue(isinstance(n, (float, int)) and math.isfinite(n))
                self.assertTrue(all(0.05 <= s <= 4 for s in p["size"]))
                self.assertTrue(all(abs(c) <= 5 for c in p["position"]))
                self.assertTrue(all(abs(deg) <= 90 for deg in p["rotation"]))

    def test_colors_defined_and_valid(self):
        for char in self.data["characters"].values():
            for p in char["parts"]:
                self.assertIn(p["color"], char["palette"])
            for color in char["palette"].values():
                self.assertEqual(len(color), 3)
                self.assertTrue(all(isinstance(v, int) and 0 <= v <= 255 for v in color))

    def test_high_contrast_identity_parts(self):
        deer = {p["name"] for p in self.data["characters"]["TRCA-BE-018"]["parts"]}
        soldier = {p["name"] for p in self.data["characters"]["TRCA-ZO-054"]["parts"]}
        self.assertTrue({"AntlerLeft", "AntlerRight", "SaddleDoor", "LeafLeft"} <= deer)
        self.assertTrue({"HatTower", "HatRoof", "BootLeft", "BootRight", "Flag", "Lantern"} <= soldier)

    def test_pose_boundaries(self):
        for char in self.data["characters"].values():
            groups = {p["group"] for p in char["parts"]}
            self.assertEqual(set(char["pose_offsets"]), {"tap", "win", "loss"})
            for pose in char["pose_offsets"].values():
                self.assertTrue(set(pose).issubset(groups))
                for offset in pose.values():
                    self.assertTrue(set(offset).issubset({"dx", "dy", "dz", "rz"}))
                    self.assertTrue(all(math.isfinite(x) and abs(x) <= 30 for x in offset.values()))

    def test_deer_asymmetric_antlers(self):
        parts = {p["name"]: p for p in self.data["characters"]["TRCA-BE-018"]["parts"]}
        self.assertNotEqual(parts["AntlerLeft"]["size"][1], parts["AntlerRight"]["size"][1])

    def test_soldier_asymmetric_boots(self):
        parts = {p["name"]: p for p in self.data["characters"]["TRCA-ZO-054"]["parts"]}
        self.assertNotEqual(parts["BootLeft"]["size"], parts["BootRight"]["size"])

    def test_factory_has_safety_flags(self):
        for assertion in ("part.Anchored = true", "part.CanCollide = false", "part.CanTouch = false", "part.CanQuery = false", "part.CastShadow = false", "part.Material = Enum.Material.SmoothPlastic"):
            self.assertIn(assertion, self.factory)

    def test_factory_rejects_unknowns(self):
        self.assertIn("UNKNOWN_CHARACTER", self.factory)
        self.assertIn("INVALID_PREVIEW_CONTEXT", self.factory)
        self.assertIn("validOrigin(origin)", self.factory)

    def test_factory_owns_what_it_destroys(self):
        self.assertIn("if not ACTIVE[model] then", self.factory)
        self.assertIn("ACTIVE[model] = nil", self.factory)

    def test_factory_has_no_gameplay_side_effects(self):
        for word in FORBIDDEN_FACTORY:
            # First two comment lines are narrative and may mention banned strings.
            source = '\n'.join(x for x in self.factory.splitlines() if not x.lstrip().startswith('--'))
            self.assertNotIn(word, source)

    def test_no_runtime_listeners(self):
        for module in ("MascotPreviewFactory.luau", "ShowcaseDemo.server.luau"):
            src = (ROOT / "luau" / module).read_text(encoding="utf-8")
            self.assertNotIn(":Connect(", src)
            self.assertNotIn("task.spawn", src)
            self.assertNotIn("task.wait", src)

    def test_demo_is_opt_in_false(self):
        self.assertRegex(self.demo, r"local ENABLED = false\s+if not ENABLED then\s+return")

    def test_demo_exact_two_models_only(self):
        self.assertEqual(self.demo.count("Factory.Build("), 2)
        self.assertIn('"TRCA-BE-018"', self.demo)
        self.assertIn('"TRCA-ZO-054"', self.demo)

    def test_demo_uses_no_external_assets(self):
        for forbidden in ("rbxassetid", "http://", "https://", "LoadAsset", "InsertService", "SoundId"):
            self.assertNotIn(forbidden, self.demo)

    def test_generated_catalog_matches_data(self):
        p = subprocess.run([sys.executable, str(ROOT/"tools/generate_catalog.py"), "--check", "--root", str(ROOT)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_no_executable_user_inputs(self):
        s = self.factory
        self.assertNotIn("loadstring", s)
        self.assertNotIn("require(tonumber", s)
        self.assertNotIn("GetAttributeChangedSignal", s)


if __name__ == "__main__":
    unittest.main()
