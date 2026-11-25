#!/usr/bin/env python3
"""13 negative/positive source tests over genuine canonical 81-Luau parent."""
from __future__ import annotations
import json,os,shutil,tempfile,unittest
from pathlib import Path
from apply_private_onehuman_horde_post_art import (
  GAME,SOLO,HORDE,GAME_PIN,SOLO_PIN,HORDE_PIN,FEATURE,OWNER_ATTR,
  OLD_START,NEW_START,OLD_EMPTY,NEW_EMPTY,OLD_LATCH,NEW_LATCH,
  apply,patch,blob,read
)
BASE=Path(os.environ.get("P0D_PRIVATE_SOLO_PARENT","/tmp/p0d_private_horde_hit_toast_art_rc81"))

@unittest.skipUnless(BASE.is_dir(),"genuine 81-source RC parent required")
class PrivateOneHumanHordeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=read(BASE)
        assert len(cls.original)==81
        assert blob(cls.original[GAME])==GAME_PIN
        assert blob(cls.original[SOLO])==SOLO_PIN
        assert blob(cls.original[HORDE])==HORDE_PIN
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)/"base";self.out=Path(self.tmp.name)/"out"
        shutil.copytree(BASE,self.base)
    def test_parent_pins_original_authority(self):
        self.assertEqual(blob(self.original[GAME]),GAME_PIN)
        self.assertEqual(blob(self.original[SOLO]),SOLO_PIN)
        self.assertEqual(blob(self.original[HORDE]),HORDE_PIN)
    def test_studio_behavior_source_kept(self):
        g=patch(self.original[GAME]).decode()
        self.assertEqual(g.count(NEW_START),2)
        self.assertEqual(g.count(NEW_LATCH),1)
        self.assertEqual(g.count(NEW_EMPTY),1)
        self.assertIn("RunService:IsStudio() or privateHordeTrialAllowed()",g)
    def test_public_minimum_two_unchanged(self):
        g=patch(self.original[GAME]).decode()
        self.assertIn("Config.MinPlayers",g)
        self.assertIn("if everybodyReady() and StudioSolo.canStart",g)
        self.assertIn("if not everybodyReady() then",g)
        self.assertIn("match.phase = \"COUNTDOWN\"",g)
        self.assertEqual(g.count("remote.OnServerEvent:Connect("),1)
        self.assertIn('if data.action == "READY" then applyReady(player, data) return end',g)
    def test_private_gate_server_owned_and_default_off(self):
        g=patch(self.original[GAME]).decode()
        self.assertIn('game.PrivateServerId ~= ""',g)
        self.assertIn('workspace:GetAttribute("'+OWNER_ATTR+'") == true',g)
        self.assertIn('musouHitFeedback = ',g)
        self.assertIn('musouHitFeedback = ',self.original[GAME].decode())
        self.assertNotIn('workspace:SetAttribute("'+OWNER_ATTR,g)
        self.assertEqual(g.count('game.PrivateServerId ~= ""'),5)
        self.assertEqual(g.count('workspace:GetAttribute("'+OWNER_ATTR+'") == true'),5)
    def test_original_bots_studio_only(self):
        g=patch(self.original[GAME]).decode()
        self.assertIn("if RunService:IsStudio() and studioSoloRoundStarted",g)
        self.assertIn("if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then",g)
    def test_no_second_horde_or_match_authority(self):
        g=patch(self.original[GAME]).decode()
        self.assertEqual(g.count("horde:reset("),1)
        self.assertEqual(g.count("horde:tick("),1)
        self.assertEqual(g.count("remote.OnServerEvent:Connect("),1)
        self.assertEqual(g.count("local function resetRound()"),1)
    def test_default_off_zero_writes(self):
        old=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertEqual(read(self.base),old)
        self.assertFalse(self.out.exists())
    def test_single_source_changed_and_other80_exact(self):
        old=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        new=read(self.out)
        self.assertEqual({k for k in old if old[k]!=new[k]},{GAME})
        self.assertEqual(len(new),81)
        self.assertEqual(new[SOLO],old[SOLO])
        self.assertEqual(new[HORDE],old[HORDE])
        sl=json.loads((self.out/"SOURCE_LOCK.json").read_text())
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text())
        self.assertEqual(sl["blobs"],fl["source_gitblobs"])
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertFalse(fl["private_one_human_trial"]["official_rc_adopted"])
    def test_bad_Game_gitblob_rejected(self):
        path=self.base/"src"/GAME
        path.write_bytes(path.read_bytes()+b"\n-- unauthorized")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_mutated_Solo_module_rejected(self):
        path=self.base/"src"/SOLO
        path.write_bytes(path.read_bytes()+b"\n-- unauthorized")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_broken_lock_refused(self):
        path=self.base/"SOURCE_LOCK.json"
        data=json.loads(path.read_text())
        data["blobs"][GAME]="0"*40
        path.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_double_adoption_refused(self):
        path=self.base/"RC_FEATURE_LOCK.json"
        data=json.loads(path.read_text())
        data["feature_flags"][FEATURE]=True
        path.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_missing_b_horde_flag_refused(self):
        path=self.base/"RC_FEATURE_LOCK.json"
        data=json.loads(path.read_text())
        data["feature_flags"]["P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2"]=False
        path.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_symlink_refused(self):
        (self.base/"src/server/hazard.luau").symlink_to(self.base/"src"/GAME)
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())

if __name__=="__main__":
    unittest.main()
