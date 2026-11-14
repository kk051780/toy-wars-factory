#!/usr/bin/env python3
"""Fail-closed forest-v2 art QA; exact original visual author is test input."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from apply_fb015_forest_v2 import apply,patch,blob,read,TARGET,BASE_BLOB,FEATURE

HERE=Path(__file__).resolve().parent
AUTHOR=HERE/"features/p0_playable_art77/FantasyWorldArt.server.luau"

class ForestV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=AUTHOR.read_bytes()
        assert blob(cls.raw)==BASE_BLOB
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        parent=Path(self.t.name)
        self.base=parent/"base"
        self.out=parent/"candidate"
        (self.base/"src/server").mkdir(parents=True)
        (self.base/"src/client").mkdir(parents=True)
        (self.base/"src"/TARGET).write_bytes(self.raw)
        (self.base/"src/server/Game.server.luau").write_text("-- Game canonical\n","utf8")
        (self.base/"src/client/HUD.client.luau").write_text("-- attack untouched\n","utf8")
        for i in range(77):
            (self.base/"src/server"/f"Other_{i:02d}.luau").write_text(f"-- {i}\n","utf8")
        pins={p:blob(data) for p,data in sorted(read(self.base).items())}
        assert len(pins)==80
        sl={"total_scripts":80,"blobs":pins}
        fl={"total_sources":80,"source_gitblobs":pins,"feature_flags":{
            "FB016_FOLIAGE_PASSAGE_20261114":True,
            "FB017_NO_PERSISTENT_BATTLE_GUIDES":True,
            "FB018_ACTION_BUTTON_TEXT_INIT":True,
            "FB019_RESPONSIVE_ATTACK_INPUT_SWING":True}}
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps(sl),"utf8")
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl),"utf8")
    def tearDown(self):
        self.t.cleanup()
    def test_patch_art_is_nonphysical_and_bounded(self):
        out=patch(self.raw).decode("utf8")
        self.assertIn("LeafMass_BiomeBlossom_",out)
        self.assertIn("AncientForestGate_",out)
        self.assertIn('ForestArtPartBudgetExpectedMax",226)',out)
        self.assertIn("MAX_PARTS=255",out)
        self.assertIn('p.CanCollide=false',out)
        self.assertIn('p.CanQuery=false',out)
        self.assertNotIn('Instance.new("ScreenGui")',out)
        self.assertNotIn("TakeDamage(",out)
    def test_disabled_zero_writes(self):
        initial=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(initial,read(self.base))
    def test_one_art_source_other79_unchanged(self):
        initial=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        output=read(self.out)
        self.assertEqual({x for x in output if output[x]!=initial[x]},{TARGET})
        self.assertEqual(len(output),80)
        self.assertEqual(initial["server/Game.server.luau"],output["server/Game.server.luau"])
        self.assertEqual(initial["client/HUD.client.luau"],output["client/HUD.client.luau"])
        flags=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())["feature_flags"]
        self.assertTrue(flags[FEATURE])
        self.assertEqual(read(self.base),initial)
    def test_drift_pin_rejected_no_output(self):
        f=self.base/"src"/TARGET
        f.write_bytes(f.read_bytes()+b"\n-- stale art\n")
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_feature_double_adoption_rejected(self):
        f=self.base/"RC_FEATURE_LOCK.json"
        data=json.loads(f.read_text())
        data["feature_flags"][FEATURE]=True
        f.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_lock_tamper_rejected(self):
        f=self.base/"SOURCE_LOCK.json"
        data=json.loads(f.read_text())
        data["blobs"][TARGET]="0"*40
        f.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_anchor_tamper_rejected(self):
        stale=self.raw.decode("utf8").replace(
            "-- Color grading is global but only in the author's Studio preview.",
            "-- Different anchor")
        with self.assertRaises(AssertionError):
            patch(stale.encode("utf8"))
if __name__=="__main__":
    unittest.main()
