#!/usr/bin/env python3
"""#444 genuine current full81 source and negative tests for private Horde enable."""
from __future__ import annotations
import json,os,shutil,tempfile,unittest
from pathlib import Path
from apply_private_live_horde import GAME,HORDE,FEATURE,OPT_IN,OLD,NEW,apply,read,blob,patch
BASE=Path(os.environ.get("P0D_PRIVATE_HORDE_PARENT","/tmp/p0d_live_safe_castle81_source"))

@unittest.skipUnless(BASE.is_dir(),"canonical real RC81 dist required")
class PrivateHordeCanary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent=read(BASE)
        assert len(cls.parent)==81 and GAME in cls.parent and HORDE in cls.parent
        assert cls.parent[GAME].decode().count(OLD)==1
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.base=Path(self.temp.name)/"base"
        self.out=Path(self.temp.name)/"candidate"
        shutil.copytree(BASE,self.base)
    def tearDown(self):self.temp.cleanup()
    def test_exact_original_and_one_horde_reset(self):
        source=read(self.base)[GAME].decode()
        self.assertEqual(source.count(OLD),1)
        self.assertEqual(source.count("horde:reset(match.serial,serverNow())"),1)
    def test_private_optin_denies_public_and_default(self):
        source=patch(read(self.base)[GAME]).decode()
        self.assertIn('game.PrivateServerId ~= "" and workspace:GetAttribute("'+OPT_IN+'") == true',source)
        self.assertNotIn(OLD,source)
        # Pure logical policy, not a claim of real Roblox runtime.
        permitted=lambda studio,privateid,optin: studio or (bool(privateid) and optin is True)
        self.assertTrue(permitted(True,"",False))
        self.assertFalse(permitted(False,"",False))
        self.assertFalse(permitted(False,"",True))
        self.assertFalse(permitted(False,"private",False))
        self.assertTrue(permitted(False,"private",True))
    def test_horde_authority_not_duplicated(self):
        original=read(self.base)[GAME]
        candidate=patch(original)
        self.assertEqual(candidate.decode().count("horde:reset(match.serial,serverNow())"),1)
        self.assertEqual(candidate.replace(NEW.encode(),OLD.encode(),1),original)
    def test_off_zero_write(self):
        source=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(read(self.base),source)
    def test_real81_one_game_modified_80_exact(self):
        old=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read(self.out)
        self.assertEqual(len(after),81)
        self.assertEqual({p for p in old if old[p]!=after[p]},{GAME})
        self.assertEqual(old[HORDE],after[HORDE])
        self.assertEqual(read(self.base),old)
        sl=json.loads((self.out/"SOURCE_LOCK.json").read_text())
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        self.assertEqual(sl["blobs"],fl["source_gitblobs"])
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertTrue(fl["private_live_horde"]["other80_sources_byte_exact"])
    def test_no_extra_horde_reset_accepted(self):
        s=read(self.base)[GAME].decode()
        with self.assertRaises(AssertionError):patch((s+"\n"+OLD).encode())
    def test_missing_original_guard_rejected(self):
        s=read(self.base)[GAME].decode().replace(OLD,"-- guard removed")
        with self.assertRaises(AssertionError):patch(s.encode())
    def test_source_lock_corruption_rejected(self):
        p=self.base/"SOURCE_LOCK.json"
        x=json.loads(p.read_text());x["blobs"][GAME]="0"*40
        p.write_text(json.dumps(x))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_missing_prior_art_feature_rejected(self):
        p=self.base/"RC_FEATURE_LOCK.json"
        x=json.loads(p.read_text());x["feature_flags"]["FB015_LIVE_CASTLE_SAFE_PARITY_V1"]=False
        p.write_text(json.dumps(x))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
    def test_duplicate_feature_rejected(self):
        p=self.base/"RC_FEATURE_LOCK.json"
        x=json.loads(p.read_text());x["feature_flags"][FEATURE]=True
        p.write_text(json.dumps(x))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
    def test_parent_output_symlink_rejected(self):
        link=Path(self.temp.name)/"link"
        link.symlink_to(self.base,target_is_directory=True)
        with self.assertRaises(AssertionError):apply(self.base,link/"bad",True)
        self.assertFalse((self.base/"bad").exists())

if __name__=="__main__":unittest.main()
