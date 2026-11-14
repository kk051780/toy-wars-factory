#!/usr/bin/env python3
"""Nine source/negative QA cases for P0 #431 private live-forest MapBuilder pilot."""
from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from apply_live_forest_safe import AUTHOR,AUTHOR_BLOB,DEST,FEATURE,apply,blob,read,author

MAP=Path(__file__).resolve().parents[1]/"releases/P0D_S1_KIDS_RC01/src/server/MapBuilder.luau"
class LiveForest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=AUTHOR.read_bytes()
        assert blob(cls.raw)==AUTHOR_BLOB
        cls.map=MAP.read_bytes()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        parent=Path(self.temp.name)
        self.base=parent/"base";self.out=parent/"out"
        (self.base/"src/server").mkdir(parents=True)
        (self.base/"src/client").mkdir(parents=True)
        (self.base/"src/server/MapBuilder.luau").write_bytes(self.map)
        (self.base/"src/server/P0DLiveCastleArt.server.luau").write_text("-- canonical visual-only castle pilot")
        (self.base/"src/server/Game.server.luau").write_text("-- one authoritative Game")
        (self.base/"src/server/SoloTeamBots.luau").write_text("-- one original bots")
        (self.base/"src/client/HUD.client.luau").write_text("-- one original HUD")
        for i in range(76):
            (self.base/"src/server"/f"Legacy_{i:02d}.luau").write_text(f"-- old {i}")
        orig=read(self.base);assert len(orig)==81
        pins={k:blob(v) for k,v in sorted(orig.items())}
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps({"total_scripts":81,"blobs":pins}))
        feats={
            "FB017_NO_PERSISTENT_BATTLE_GUIDES":True,
            "FB019_RESPONSIVE_ATTACK_INPUT_SWING":True,
            "FB015_FOREST_BIOMES_MONUMENTS_V2":True,
            "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3":True,
            "FB016_ART_CAMERA_SIGHTLINE_V2":True,
            "FB015_GOROGAN_MOBILE_LOD_V1":True,
            "FB015_LIVE_CASTLE_SAFE_PARITY_V1":True
        }
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps(
           {"total_sources":81,"source_gitblobs":pins,"feature_flags":feats}))
        (self.base/"default.project.json").write_text(json.dumps(
           {"tree":{"ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}}}}))
    def test_author_exact_and_relevant_map_shapes(self):
        author(self.raw)
        s=self.raw.decode()
        self.assertIn("local BUDGET = 60",s)
        self.assertIn("NORTH_FROST_CEDAR",s)
        self.assertIn("SOUTH_SUNSET_BLOSSOM",s)
        self.assertIn("Vector3.new(250, 4, 142)",self.map.decode())
    def test_private_server_optin_and_studio_default_off(self):
        s=self.raw.decode()
        self.assertIn('if game.PrivateServerId == "" then return end',s)
        self.assertIn('workspace:GetAttribute("P0D_PRIVATE_LIVE_FOREST") ~= true then return end',s)
        self.assertIn('if script:GetAttribute("EnablePrivatePreview") ~= true then return end',s)
        self.assertNotIn('workspace:SetAttribute("P0D_PRIVATE_LIVE_FOREST"',s)
    def test_zero_write_when_off(self):
        before=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertEqual(read(self.base),before)
        self.assertFalse(self.out.exists())
    def test_82_source_single_additive_script(self):
        before=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read(self.out)
        self.assertEqual(set(after)-set(before),{DEST})
        self.assertEqual(len(after),82)
        self.assertEqual(after[DEST],self.raw)
        self.assertTrue(all(after[k]==s for k,s in before.items()))
        l=json.loads((self.out/"SOURCE_LOCK.json").read_text())
        f=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        self.assertEqual(l["total_scripts"],82)
        self.assertEqual(f["total_sources"],82)
        self.assertEqual(l["blobs"],f["source_gitblobs"])
        self.assertTrue(f["feature_flags"][FEATURE])
        self.assertEqual(f["live_forest_private_pilot"]["static_decor_parts"],60)
    def test_author_corruption_rejected(self):
        with self.assertRaises(AssertionError):author(self.raw+b"-- tampered")
    def test_original_map_change_fails_closed(self):
        p=self.base/"src/server/MapBuilder.luau"
        p.write_text("-- invalid map signature")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_mutated_parent_lock_rejected(self):
        p=self.base/"SOURCE_LOCK.json";v=json.loads(p.read_text())
        v["blobs"]["server/Game.server.luau"]="0"*40
        p.write_text(json.dumps(v))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_duplicate_or_missing_art4_feature_rejected(self):
        p=self.base/"RC_FEATURE_LOCK.json";v=json.loads(p.read_text())
        v["feature_flags"][FEATURE]=True
        p.write_text(json.dumps(v))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
        v["feature_flags"].pop(FEATURE)
        v["feature_flags"]["FB015_GOROGAN_MOBILE_LOD_V1"]=False
        p.write_text(json.dumps(v))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_symlink_rejected(self):
        p=self.base/"src/server/linked.luau"
        p.symlink_to(self.base/"src/server/Game.server.luau")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())

if __name__=="__main__":
    unittest.main()
