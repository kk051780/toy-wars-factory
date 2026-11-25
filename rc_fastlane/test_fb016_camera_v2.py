#!/usr/bin/env python3
"""Cheap fail-closed FB016 art overlay regression without Roblox/Studio."""
import json,tempfile,unittest
from pathlib import Path
from apply_fb016_camera_v2 import ROOT,SOURCE,TARGET,OLD_BLOB,NEW_BLOB,FEATURE,read,gitblob,apply

class FoliageArtTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        root=Path(self.t.name)
        self.base=root/"original";self.out=root/"candidate"
        src=self.base/"src";(src/"server").mkdir(parents=True)
        (src/"client").mkdir(parents=True)
        old=(ROOT/"features/fb016_passage/FoliageCameraFade.client.luau").read_bytes()
        self.assertEqual(gitblob(old),OLD_BLOB)
        (src/TARGET).write_bytes(old)
        (src/"server/Game.server.luau").write_text("-- one Game\n")
        for i in range(78):
            (src/"server"/f"DUMMY_{i:02d}.luau").write_text(f"-- inert test {i}\n")
        pins={k:gitblob(v) for k,v in sorted(read(self.base).items())}
        self.assertEqual(len(pins),80)
        sl={"total_scripts":80,"blobs":pins}
        fl={"total_sources":80,"source_gitblobs":pins,
            "feature_flags":{
                "FB016_FOLIAGE_PASSAGE_20261114":True,
                "FB017_NO_PERSISTENT_BATTLE_GUIDES":True,
                "FB018_ACTION_BUTTON_TEXT_INIT":True
            }}
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps(sl))
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl))

    def tearDown(self):self.t.cleanup()

    def test_source_art_budget_and_authority(self):
        text=SOURCE.read_text("utf8")
        self.assertEqual(gitblob(SOURCE.read_bytes()),NEW_BLOB)
        self.assertIn("blocksAvatar(",text)
        self.assertIn("LocalTransparencyModifier",text)
        self.assertIn("script.Destroying:Connect",text)
        self.assertNotIn("FireServer(",text)
        self.assertNotIn("CanCollide=true",text)
        self.assertNotIn("ScreenGui",text)

    def test_off_is_zero_write(self):
        before=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(before,read(self.base))

    def test_exactly_one_existing_client_source_changes(self):
        before=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read(self.out)
        self.assertEqual(len(after),80)
        self.assertEqual({k for k in before if before[k]!=after[k]},{TARGET})
        self.assertEqual(after["server/Game.server.luau"],before["server/Game.server.luau"])
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertEqual(read(self.base),before)

    def test_source_drift_rejected(self):
        p=self.base/"src"/TARGET
        p.write_bytes(p.read_bytes()+b"-- unpinned drift\n")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())

    def test_lock_drift_rejected(self):
        fl=self.base/"RC_FEATURE_LOCK.json"
        obj=json.loads(fl.read_text())
        obj["source_gitblobs"][TARGET]="0"*40
        fl.write_text(json.dumps(obj))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())

if __name__=="__main__":unittest.main()
