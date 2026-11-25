#!/usr/bin/env python3
"""Independent negative QA for actual authored Gorogan source and RC80 lock."""
from __future__ import annotations
import copy,json,os,shutil,tempfile,unittest
from pathlib import Path
from apply_fb015_gorogan_mobile_lod import apply,patch,blob,read,TARGET,BASE_BLOB,FEATURE

BASE=Path(os.environ.get("P0D_MOBILE_LOD_PARENT","/tmp/p0d_fb019_hit_visibility_dist"))

@unittest.skipUnless(BASE.is_dir(),"real FB019 V2 canonical parent dist required")
class GoroganMobileLOD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=read(BASE)
        assert len(cls.original)==80
        assert blob(cls.original[TARGET])==BASE_BLOB
        cls.source_before=cls.original[TARGET]
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.parent=root/"author"
        self.out=root/"lod"
        shutil.copytree(BASE,self.parent,symlinks=False)
    def tearDown(self):
        self.tmp.cleanup()
    def test_original_source_pin_is_real(self):
        self.assertEqual(blob(self.source_before),BASE_BLOB)
    def test_patch_pc_near_full_art_mobile_real_lod(self):
        s=patch(self.source_before).decode("utf8")
        self.assertIn('LOW_END_TOUCH',s)
        self.assertIn('art:SetAttribute("BeastLodPolicy", "FB015_GOROGAN_MOBILE_LOD_V1")',s)
        self.assertNotIn('art:SetAttribute("BeastLodPolicy", FEATURE)',s)
        self.assertIn('MobileDetailRadiusStuds", 52)',s)
        self.assertIn('MobileSilhouetteRadiusStuds", 118)',s)
        self.assertIn('name == "ObsidianChestPlate"',s)
        self.assertIn('name:find("CrownHorn")',s)
        self.assertIn('name == "ShoulderSigil"',s)
        self.assertIn('LocalTransparencyModifier',s)
        self.assertIn('RunService.Heartbeat:Connect',s)
        self.assertIn('if not LOW_END_TOUCH then pulse:Play() end',s)
        self.assertIn('p.CastShadow = not LOW_END_TOUCH',s)
        for forbidden in ("TakeDamage(","FireServer(","GetDataStore(",
                          'Instance.new("ScreenGui")',"CanCollide = true"):
            self.assertNotIn(forbidden,s)
    def test_disabled_does_not_write(self):
        b=read(self.parent)
        self.assertFalse(apply(self.parent,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(read(self.parent),b)
    def test_full80_other79_byte_exact(self):
        orig=read(self.parent)
        self.assertTrue(apply(self.parent,self.out,True))
        after=read(self.out)
        self.assertEqual(len(after),80)
        self.assertEqual({p for p in orig if orig[p]!=after[p]},{TARGET})
        self.assertEqual(read(self.parent),orig)
        for important in ("server/Game.server.luau","client/HUD.client.luau",
                          "client/BattleHUDGovernor.client.luau",
                          "server/MusouHorde.luau"):
            self.assertEqual(orig[important],after[important])
        data=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text("utf8"))
        self.assertTrue(data["feature_flags"][FEATURE])
        self.assertEqual(data["fb015_beast_mobile_lod"]["changed_source"],[TARGET])
    def test_source_drift_fails_closed(self):
        target=self.parent/"src"/TARGET
        target.write_bytes(target.read_bytes()+b"\n-- unauthorized")
        with self.assertRaises(AssertionError):
            apply(self.parent,self.out,True)
        self.assertFalse(self.out.exists())
    def test_lock_tamper_fails_closed(self):
        lock=self.parent/"SOURCE_LOCK.json"
        data=json.loads(lock.read_text("utf8"))
        data["blobs"][TARGET]="0"*40
        lock.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            apply(self.parent,self.out,True)
        self.assertFalse(self.out.exists())
    def test_duplicate_feature_fails_closed(self):
        lock=self.parent/"RC_FEATURE_LOCK.json"
        data=json.loads(lock.read_text("utf8"))
        data["feature_flags"][FEATURE]=True
        lock.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            apply(self.parent,self.out,True)
        self.assertFalse(self.out.exists())
    def test_parent_missing_fb019_fails_closed(self):
        lock=self.parent/"RC_FEATURE_LOCK.json"
        data=json.loads(lock.read_text("utf8"))
        data["feature_flags"]["FB019_RESPONSIVE_ATTACK_INPUT_SWING"]=False
        lock.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            apply(self.parent,self.out,True)
        self.assertFalse(self.out.exists())
if __name__=="__main__":
    unittest.main()
