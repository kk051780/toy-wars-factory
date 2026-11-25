#!/usr/bin/env python3
"""Source-locked castle v3 tests, including real author source and negative QA."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from apply_fb015_castle_gate_silhouette import (
    TARGET,BASE_BLOB,FEATURE,apply,blob,patch,read
)

AUTHOR=Path(__file__).resolve().parent/"features/p0_playable_art77/CastleDetailArt.server.luau"

class CastleV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=AUTHOR.read_bytes()
        assert blob(cls.raw)==BASE_BLOB,"NOT_REAL_OWNER_CASTLE_AUTHOR"
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        top=Path(self.temp.name)
        self.base=top/"base"
        self.dest=top/"new"
        (self.base/"src/server").mkdir(parents=True)
        (self.base/"src/client").mkdir(parents=True)
        (self.base/"src"/TARGET).write_bytes(self.raw)
        for i in range(77):
            (self.base/"src/server"/f"Other_{i:02d}.luau").write_text(f"-- author other {i}")
        (self.base/"src/server/Game.server.luau").write_text("-- 1 original Game")
        (self.base/"src/client/HUD.client.luau").write_text("-- original HUD")
        pins={name:blob(code) for name,code in sorted(read(self.base).items())}
        self.assertEqual(len(pins),80)
        (self.base/"SOURCE_LOCK.json").write_text(
            json.dumps({"total_scripts":80,"blobs":pins}))
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources":80,"source_gitblobs":pins,
            "feature_flags":{
                "FB016_FOLIAGE_PASSAGE_20261114":True,
                "FB017_NO_PERSISTENT_BATTLE_GUIDES":True,
                "FB018_ACTION_BUTTON_TEXT_INIT":True,
                "FB019_RESPONSIVE_ATTACK_INPUT_SWING":True,
            }
        }))
    def tearDown(self):
        self.temp.cleanup()
    def test_real_castle_visual_new_36_and_colors(self):
        code=patch(self.raw).decode()
        self.assertEqual(code.count("FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3"),1)
        self.assertIn('V3_GATE_PARAPET_BEAM_',code)
        self.assertIn('V3_GATE_MERLON_COPING_',code)
        self.assertIn('V3_TEAM_COLOR_STANDARD_',code)
        self.assertIn('theme,Enum.Material.Fabric,"WEDGE"',code)
        self.assertIn('art:SetAttribute("NewPartsV3",18)',code)
        self.assertIn('art:SetAttribute("AdditionalDynamicLightsV3",0)',code)
    def test_mobile_collision_budget_no_gui(self):
        code=patch(self.raw).decode()
        self.assertIn("local MAX_PARTS = 190",code)
        self.assertIn("p.CanCollide = false",code)
        self.assertIn("p.CanQuery = false",code)
        self.assertNotIn('Instance.new("ScreenGui")',code)
        self.assertNotIn('Instance.new("BillboardGui")',code)
        self.assertNotIn("TakeDamage(",code)
        self.assertNotIn("OnServerEvent:Connect(",code)
    def test_disabled_zero_write(self):
        before=read(self.base)
        self.assertFalse(apply(self.base,self.dest,False))
        self.assertFalse(self.dest.exists())
        self.assertEqual(before,read(self.base))
    def test_single_author_changed_other79_exact(self):
        before=read(self.base)
        self.assertTrue(apply(self.base,self.dest,True))
        after=read(self.dest)
        self.assertEqual(len(after),80)
        self.assertEqual({k for k in before if before[k]!=after[k]},{TARGET})
        self.assertEqual(before["server/Game.server.luau"],after["server/Game.server.luau"])
        self.assertEqual(before["client/HUD.client.luau"],after["client/HUD.client.luau"])
        self.assertEqual(before,read(self.base))
        locked=json.loads((self.dest/"SOURCE_LOCK.json").read_text())
        features=json.loads((self.dest/"RC_FEATURE_LOCK.json").read_text())
        self.assertTrue(features["feature_flags"][FEATURE])
        self.assertEqual(locked["blobs"],features["source_gitblobs"])
        self.assertEqual(features["fb015_castle_v3"]["new_parts_total_both_castles"],36)
    def test_author_drift_rejects(self):
        path=self.base/"src"/TARGET
        path.write_bytes(path.read_bytes()+b"\n-- altered without author pin")
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_tampered_source_lock_rejects(self):
        path=self.base/"SOURCE_LOCK.json"
        doc=json.loads(path.read_text())
        doc["blobs"][TARGET]="0"*40
        path.write_text(json.dumps(doc))
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_duplicate_feature_rejects(self):
        path=self.base/"RC_FEATURE_LOCK.json"
        doc=json.loads(path.read_text())
        doc["feature_flags"][FEATURE]=True
        path.write_text(json.dumps(doc))
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_missing_prior_owner_feedback_rejects(self):
        path=self.base/"RC_FEATURE_LOCK.json"
        doc=json.loads(path.read_text())
        doc["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"]=False
        path.write_text(json.dumps(doc))
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_original_raw_cannot_be_double_patched(self):
        new=patch(self.raw)
        with self.assertRaises(AssertionError):
            patch(new)

if __name__=="__main__":
    unittest.main()
