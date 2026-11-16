"""Source-exact regression/negative tests; these are NOT Roblox engine playtests."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))
import patch_safe_warp as P
import compose_private21 as C


class WarpClearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = P.ORIGINAL.read_bytes()
        cls.patched = P.patch(cls.original)
        cls.o = cls.original.decode("utf-8")
        cls.p = cls.patched.decode("utf-8")

    def test_01_original_immutable_sha(self):
        self.assertEqual(P.git_blob_sha(self.original), P.EXPECTED_GIT_BLOB)

    def test_02_exactly_one_author_combat_module(self):
        self.assertEqual(self.o.count("local function safeMove("), 1)
        self.assertEqual(self.p.count("local function safeMove("), 1)

    def test_03_only_three_exact_original_source_anchors(self):
        reconstructed = self.p.replace(P.NEW, P.OLD, 1).replace(P.NEW_NINJA, P.OLD_NINJA, 1).replace(P.NEW_ESPER, P.OLD_ESPER, 1)
        self.assertEqual(reconstructed, self.o)

    def test_04_ninja_wind_original_distance_egg_guard_preserved(self):
        self.assertIn(P.NEW_NINJA, self.p)
        self.assertIn('p:SetAttribute("EGGRUMBLE_StealthUntil",now+3)', self.p)

    def test_05_esper_warp_original_distance_egg_guard_preserved(self):
        self.assertIn(P.NEW_ESPER, self.p)
        self.assertIn('if role=="TRAPPER"', self.p)

    def test_06_9_collision_rays_and_nearest_distance(self):
        self.assertIn("ipairs({-1.1,2,4.6})", self.p)
        self.assertIn("ipairs({-1.3,0,1.3})", self.p)
        self.assertIn("math.min(distance,math.max(0,hit.Distance-3))", self.p)
        self.assertIn("if distance<3 then return false end", self.p)

    def test_07_arena_bounds_mode_private_world(self):
        self.assertIn('session.world:FindFirstChild("TacticalBattlefield")', self.p)
        self.assertIn("arena.Size.X*.5-4.5", self.p)
        self.assertIn("arena.Size.Z*.5-4.5", self.p)

    def test_08_real_server_destination_volume(self):
        self.assertIn("workspace:GetPartBoundsInBox(", self.p)
        self.assertIn("OverlapParams.new()", self.p)
        self.assertIn("Vector3.new(3.2,4.5,3.2)", self.p)
        self.assertIn("if part.CanCollide then return false end", self.p)

    def test_09_floor_and_climb_contract_preserved(self):
        self.assertIn('if not ground or not ground.Instance.CanCollide then return false end', self.p)
        self.assertIn('if math.abs(landing.Y-ground.Position.Y)>8 then return false end', self.p)

    def test_10_unchanged_server_combat_ownership(self):
        for token in ('local HeroCombat={}', 'function HeroCombat.equip(', 'function HeroCombat.clear(',
                      'p:SetAttribute("EGGRUMBLE_SkillCastSignature",'):
            self.assertEqual(self.o.count(token), self.p.count(token), token)
        for forbidden in ('Instance.new("RemoteEvent")', 'DataStoreService', 'MarketplaceService'):
            self.assertNotIn(forbidden, self.p)

    def test_11_reject_source_drift(self):
        mutated = self.original.replace(b"local HeroCombat={}", b"local HeroCombat={};--drift", 1)
        with self.assertRaisesRegex(ValueError, "SOURCE_LOCK"):
            P.patch(mutated)

    def test_12_reject_duplicate_patch(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_LOCK"):
            P.patch(self.patched)

    def test_13_only_one_original_changed_in_private21(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "private21"
            C.prepare(target)
            manifest = json.loads((target / "SOURCE_LOCK.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["script_count"], 21)
            self.assertEqual(manifest["unchanged_originals"], 20)
            self.assertEqual(sum(x["changed"] for x in manifest["mapping"]), 1)
            self.assertFalse(manifest["official_rc_adopted"])
            for row in manifest["mapping"]:
                self.assertEqual((target / row["name"]).read_bytes(),
                                 self.patched if row["changed"] else (C.BASE / row["name"]).read_bytes())

    def test_14_refuse_original_author_source_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "Combat.luau"
            subprocess.run([sys.executable, str(PKG / "patch_safe_warp.py"),
                            "--source", str(P.ORIGINAL), "--out", str(output)], check=True,
                           capture_output=True, text=True)
            self.assertEqual(output.read_bytes(), self.patched)
            self.assertEqual(P.ORIGINAL.read_bytes(), self.original)

    def test_15_source_mapping_21_names_unique(self):
        names = C.mapped_sources()
        self.assertEqual(len(names), 21)
        self.assertEqual(names.count(P.ORIGINAL.name), 1)

    def test_16_no_other_author_patch_or_second_game(self):
        for needle in ('local function hitBotHeroes(', 'local function hitHumanHeroes(',
                       'local function neutralAndBotHit(', 'local function healAllies('):
            self.assertEqual(self.o.count(needle), self.p.count(needle))
        self.assertEqual(self.o.count("safeMove(char,root,"), 2)
        self.assertEqual(self.p.count("safeMove(session,char,root,"), 2)


if __name__ == "__main__":
    unittest.main()
