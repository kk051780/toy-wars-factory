#!/usr/bin/env python3
"""A-PREP coastal vista fail-closed source QA (no actual Roblox runtime claim)."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from apply_live_coast_safe import AUTHOR,AUTHOR_BLOB,TARGET,FEATURE,blob,read,check_author,apply

FLAGS = [
    "FB016_FOLIAGE_PASSAGE_20261114",
    "FB017_NO_PERSISTENT_BATTLE_GUIDES",
    "FB018_ACTION_BUTTON_TEXT_INIT",
    "FB019_RESPONSIVE_ATTACK_INPUT_SWING",
    "FB015_FOREST_BIOMES_MONUMENTS_V2",
    "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
    "FB016_ART_CAMERA_SIGHTLINE_V2",
    "FB015_GOROGAN_MOBILE_LOD_V1",
    "FB015_LIVE_CASTLE_SAFE_PARITY_V1",
]

class PrivateCoastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = AUTHOR.read_bytes()
        assert blob(cls.raw)==AUTHOR_BLOB, "EXACT_AUTHOR_REQUIRED"
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        root = Path(self.t.name)
        self.base = root/"base"
        self.out = root/"out"
        (self.base/"src/server").mkdir(parents=True)
        (self.base/"src/client").mkdir(parents=True)
        (self.base/"src/server/Game.server.luau").write_text("-- only authoritative Game")
        (self.base/"src/client/HUD.client.luau").write_text("-- only original HUD")
        (self.base/"src/server/P0DLiveCastleArt.server.luau").write_text("-- official castle fallback")
        for i in range(78):
            (self.base/"src/server"/f"Prior_{i:02d}.luau").write_text("-- unchanged source "+str(i))
        current = read(self.base)
        assert len(current)==81
        pins = {k:blob(v) for k,v in sorted(current.items())}
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps({"total_scripts":81,"blobs":pins}))
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources":81,"source_gitblobs":pins,
            "feature_flags":{k:True for k in FLAGS}
        }))
        (self.base/"default.project.json").write_text(json.dumps({
            "tree":{"ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}}}
        }))
    def tearDown(self):
        self.t.cleanup()
    def test_author_is_pinned(self):
        check_author(self.raw)
        self.assertEqual(blob(self.raw),AUTHOR_BLOB)
    def test_flag_is_required_in_both_studio_and_nonstudio(self):
        source=self.raw.decode("utf8")
        self.assertIn('if workspace:GetAttribute("P0D_PRIVATE_LIVE_COAST") ~= true then return end',source)
        self.assertNotIn("if not RunService:IsStudio() then return end",source)
        self.assertIn('if not RunService:IsStudio() and game.PrivateServerId == "" then',source)
        self.assertIn('P0D_LIVE_COAST_PUBLIC_SERVER_ALWAYS_OFF',source)
    def test_gameplay_surface_unchanged_and_outside_boundary(self):
        s=self.raw.decode("utf8")
        for v in ('math.abs(north.Position.Z + 71)',
                  'math.abs(ground.Size.Z - 142)',
                  'Vector3.new(0, -1.5, -105)',
                  'Vector3.new(0, -1.55, -148)',
                  'p.CanCollide = false',
                  'p.CanQuery = false',
                  'p.CastShadow = false',
                  'local MAX_PARTS = 40'):
            self.assertIn(v,s)
        for banned in ('Terrain:Fill','terrain:Fill',
                       'CanCollide = true','TakeDamage(',
                       'OnServerEvent:Connect(', 'GetDataStore('):
            self.assertNotIn(banned,s)
    def test_disabled_never_creates_output(self):
        before=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(read(self.base),before)
    def test_82_candidate_preserves_every_original_script(self):
        before=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read(self.out)
        self.assertEqual(len(after),82)
        self.assertEqual({k for k in after if k not in before},{TARGET})
        self.assertTrue(all(after[k]==v for k,v in before.items()))
        self.assertEqual(after[TARGET],self.raw)
        self.assertEqual(read(self.base),before)
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        sl=json.loads((self.out/"SOURCE_LOCK.json").read_text())
        self.assertEqual(fl["source_gitblobs"],sl["blobs"])
        self.assertEqual(sl["total_scripts"],82)
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertFalse(fl["fb011_live_coast_v1"]["owner_accepted"])
    def test_baseline_pin_mutation_rejected(self):
        (self.base/"src/client/HUD.client.luau").write_text("-- tampered source")
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_required_camera_mobile_parent_rejected_when_missing(self):
        x=self.base/"RC_FEATURE_LOCK.json"
        y=json.loads(x.read_text())
        y["feature_flags"]["FB015_GOROGAN_MOBILE_LOD_V1"]=False
        x.write_text(json.dumps(y))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_duplicate_adoption_rejected(self):
        x=self.base/"RC_FEATURE_LOCK.json"
        y=json.loads(x.read_text())
        y["feature_flags"][FEATURE]=True
        x.write_text(json.dumps(y))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_project_root_change_rejected(self):
        x=self.base/"default.project.json"
        x.write_text(json.dumps({"tree":{}}))
        with self.assertRaises((AssertionError,KeyError)):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_invalid_author_byte_change_rejected(self):
        with self.assertRaises(AssertionError):
            check_author(self.raw+b"\n-- unreviewed")
if __name__ == "__main__":
    unittest.main()
