#!/usr/bin/env python3
"""Eight source and negative tests for the privately staged #431 live-castle fallback."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from apply_live_castle_safe import AUTHOR,AUTHOR_BLOB,DEST,FEATURE,apply,blob,read_sources,verify_author

class LiveCastle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=AUTHOR.read_bytes()
        assert blob(cls.raw)==AUTHOR_BLOB,"REAL_AUTHOR_SOURCE_BLOB_REQUIRED"
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.base=root/"base"
        self.out=root/"out"
        (self.base/"src/server").mkdir(parents=True)
        (self.base/"src/client").mkdir(parents=True)
        (self.base/"src/server/Game.server.luau").write_text("-- original authoritative Game")
        (self.base/"src/client/HUD.client.luau").write_text("-- original 1 HUD")
        for i in range(78):
            (self.base/"src/server"/f"Additional_{i:02d}.luau").write_text("-- original "+str(i))
        pins={k:blob(v) for k,v in sorted(read_sources(self.base).items())}
        assert len(pins)==80
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps({"total_scripts":80,"blobs":pins}))
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps({
          "total_sources":80, "source_gitblobs":pins,
          "feature_flags":{
             "FB016_FOLIAGE_PASSAGE_20261114":True,
             "FB017_NO_PERSISTENT_BATTLE_GUIDES":True,
             "FB018_ACTION_BUTTON_TEXT_INIT":True,
             "FB019_RESPONSIVE_ATTACK_INPUT_SWING":True
          }}))
        (self.base/"default.project.json").write_text(json.dumps({
            "tree":{"ServerScriptService":{"TrapRaidersS1":{"$path":"src/server"}}}
        }))
    def tearDown(self):
        self.temp.cleanup()
    def test_author_pin_and_no_collision(self):
        verify_author(self.raw)
        text=self.raw.decode()
        self.assertIn('p.CanCollide = false',text)
        self.assertIn('p.CanQuery = false',text)
        self.assertIn('p.CastShadow = false',text)
        self.assertNotIn('TakeDamage(',text)
        self.assertNotIn('GetDataStore(',text)
        self.assertIn('local BUDGET = 36',text)
    def test_production_enabled_private_studio_default_off(self):
        text=self.raw.decode()
        self.assertIn('if not RunService:IsServer() then return end',text)
        self.assertIn('if RunService:IsStudio() and script:GetAttribute("EnablePrivatePreview") ~= true then',text)
        self.assertIn('if arena:FindFirstChild("P0D_LIVE_SAFE_CASTLE_ART_V1") then return end',text)
    def test_disabled_is_exact_zero_write(self):
        before=read_sources(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertEqual(before,read_sources(self.base))
        self.assertFalse(self.out.exists())
    def test_only_new81st_script_and_original80_all_exact(self):
        before=read_sources(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read_sources(self.out)
        self.assertEqual(len(after),81)
        self.assertEqual(after[DEST],self.raw)
        self.assertTrue(all(after[k]==v for k,v in before.items()))
        self.assertEqual(read_sources(self.base),before)
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        sl=json.loads((self.out/"SOURCE_LOCK.json").read_text())
        self.assertEqual(fl["total_sources"],sl["total_scripts"])
        self.assertEqual(fl["total_sources"],81)
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertEqual(fl["source_gitblobs"],sl["blobs"])
        self.assertEqual(fl["fb015_live_castle_production"]["official_rc_adopted"],False)
    def test_missing_project_map_rejected(self):
        path=self.base/"default.project.json"
        path.write_text("{}")
        with self.assertRaises((AssertionError,KeyError)):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_bad_original_source_lock_rejected(self):
        path=self.base/"SOURCE_LOCK.json"
        body=json.loads(path.read_text())
        body["blobs"]["server/Game.server.luau"]="0"*40
        path.write_text(json.dumps(body))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_missing_critical_owner_feedback_rejected(self):
        path=self.base/"RC_FEATURE_LOCK.json"
        body=json.loads(path.read_text())
        body["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"]=False
        path.write_text(json.dumps(body))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_duplicate_feature_rejected(self):
        path=self.base/"RC_FEATURE_LOCK.json"
        body=json.loads(path.read_text())
        body["feature_flags"][FEATURE]=True
        path.write_text(json.dumps(body))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_author_corruption_rejected(self):
        with self.assertRaises(AssertionError):
            verify_author(self.raw+b"\n-- corrupt")
if __name__=="__main__":
    unittest.main()
