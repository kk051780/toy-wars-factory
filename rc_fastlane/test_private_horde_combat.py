#!/usr/bin/env python3
"""#444 latest canonical RC81: negative + source-exact tests for attack/tick only."""
from __future__ import annotations
import json,os,shutil,tempfile,unittest
from pathlib import Path
from apply_private_horde_combat import (
 GAME,HORDE,GAME_OFFICIAL_BLOB,HORDE_OFFICIAL_BLOB,PARENT_FEATURE,FEATURE,
 RESET_AUTH,HIT_NEW,TICK_NEW,BOT_NEW,apply,blob,read,patch
)
BASE=Path(os.environ.get("P0D_HORDE_V2_PARENT","/tmp/p0d_private_live_horde81_dist"))

@unittest.skipUnless(BASE.is_dir(),"real canonical RC81 source-lock parent required")
class PrivateHordeFullCombat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=read(BASE)
        assert len(cls.original)==81
        assert blob(cls.original[GAME])==GAME_OFFICIAL_BLOB
        assert blob(cls.original[HORDE])==HORDE_OFFICIAL_BLOB
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)/"base"
        self.out=Path(self.temp.name)/"out"
        shutil.copytree(BASE,self.base)
    def test_real_game_pins(self):
        self.assertEqual(blob(self.original[GAME]),GAME_OFFICIAL_BLOB)
        self.assertEqual(blob(self.original[HORDE]),HORDE_OFFICIAL_BLOB)
    def test_existing_b_reset_is_unchanged(self):
        g=patch(self.original[GAME]).decode()
        self.assertEqual(g.count(RESET_AUTH),1)
        self.assertEqual(g.count("horde:reset("),1)
    def test_exact_attack_and_tick_added(self):
        g=patch(self.original[GAME]).decode()
        self.assertIn(HIT_NEW,g)
        self.assertIn(TICK_NEW,g)
        self.assertEqual(g.count('game.PrivateServerId ~= ""'),3)
    def test_solo_bot_tick_must_remain_studio_only(self):
        g=patch(self.original[GAME]).decode()
        self.assertEqual(g.count(BOT_NEW),1)
        self.assertEqual(g.count("remote.OnServerEvent:Connect("),1)
        self.assertEqual(g.count("horde:tick("),1)
    def test_nine_real_original_mobs_one_elite(self):
        h=self.original[HORDE].decode()
        self.assertIn("local MAX_ACTIVE = 9",h)
        self.assertIn("local MINIONS = 8",h)
        self.assertIn("for i=1,MAX_ACTIVE do",h)
        self.assertIn("local elite=(i==MAX_ACTIVE)",h)
    def test_off_zero_write(self):
        old=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(old,read(self.base))
    def test_only_game_edited_other80_exact(self):
        before=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read(self.out)
        self.assertEqual({p for p in before if before[p]!=after[p]},{GAME})
        self.assertEqual(after[HORDE],before[HORDE])
        self.assertEqual(len(after),81)
        sl=json.loads((self.out/"SOURCE_LOCK.json").read_text())
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        self.assertEqual(sl["blobs"],fl["source_gitblobs"])
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertTrue(fl["live_horde_attack_tick_v2"]["original_reset_from_B_unchanged"])
    def test_game_author_drift_fails_closed(self):
        p=self.base/"src"/GAME;p.write_bytes(p.read_bytes()+b"\n-- unauthorized")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
    def test_horde_drift_fails_closed(self):
        p=self.base/"src"/HORDE;p.write_bytes(p.read_bytes()+b"\n-- unauthorized")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
    def test_missing_b_parent_flag_fails_closed(self):
        p=self.base/"RC_FEATURE_LOCK.json";j=json.loads(p.read_text())
        j["feature_flags"][PARENT_FEATURE]=False;p.write_text(json.dumps(j))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
    def test_duplicate_fails_closed(self):
        p=self.base/"RC_FEATURE_LOCK.json";j=json.loads(p.read_text())
        j["feature_flags"][FEATURE]=True;p.write_text(json.dumps(j))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
    def test_linked_file_fails_closed(self):
        (self.base/"src/server/malicious.luau").symlink_to(self.base/"src"/GAME)
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)

if __name__=="__main__":unittest.main()
