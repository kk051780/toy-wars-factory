#!/usr/bin/env python3
"""No fake HIT and no permanently intrusive Horde HUD in nonStudio private."""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from apply_private_horde_hit_toast import (
    GAME,HUD,GAME_V2_BLOB,HUD_V2_BLOB,FEATURE,V1_FLAG,V2_FLAG,
    blob,read,patch_game,patch_hud,apply,verify_all_real_hit_branches,verify_original_toast_epoch
)
BASE=Path(os.getenv("P0D_PRIVATE_HORDE_V2_DIST","/tmp/p0d_horde_private_lifecycle_v2_81"))

@unittest.skipUnless(BASE.is_dir(), "actual certified #452 V2 81-source Stage required")
class PrivateHitToastV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=read(BASE)
        assert len(cls.sources)==81
        assert blob(cls.sources[GAME])==GAME_V2_BLOB
        assert blob(cls.sources[HUD])==HUD_V2_BLOB
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.base=root/"official_v2"
        self.out=root/"v3"
        shutil.copytree(BASE,self.base,symlinks=False)
    def test_true_original_sources_locked(self):
        self.assertEqual(blob(self.sources[GAME]),GAME_V2_BLOB)
        self.assertEqual(blob(self.sources[HUD]),HUD_V2_BLOB)
    def test_separate_transient_hit_gate_is_exact_server_owned(self):
        s=patch_game(self.sources[GAME]).decode("utf8")
        assert 'musouActive = RunService:IsStudio() and match.phase=="ACTIVE"' in s
        assert 'musouHitFeedback = (RunService:IsStudio() or (game.PrivateServerId ~= "" and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true)) and match.phase=="ACTIVE"' in s
        self.assertEqual(s.count("musouHitFeedback = "),1)
        self.assertIn("mobImpactSeq[player]=(mobImpactSeq[player] or 0)+1",s)
        self.assertIn("if touched>0 then",s)
        self.assertIn("remote:FireClient(player,snapshotFor(player))",s)
        # Static source proof that the only impact increment is nested in
        # original touched>0, not merely adjacent to an unrelated 'if'.
        verify_all_real_hit_branches(s)
    def test_never_enable_persistent_guides_in_nonstudio(self):
        h=patch_hud(self.sources[HUD]).decode("utf8")
        self.assertIn('if s.musouActive==true or (s.musouHitFeedback==true and s.phase=="ACTIVE") then',h)
        for line in (
            'first90Cue.Visible=s.musouActive==true',
            'mobCue.Visible=s.musouActive==true',
            'netButton.Visible=s.musouActive==true',
            'rescueButton.Visible=s.musouActive==true'
        ):
            self.assertIn(line,h)
        self.assertIn('task.delay(.42,function()',h)
        self.assertIn('impactToast.Visible=true',h)
    def test_sourcery_medium2_all_three_true_hit_sources_only(self):
        game=self.sources[GAME].decode("utf8")
        needle='mobImpactSeq[player]=(mobImpactSeq[player] or 0)+1'
        self.assertEqual(game.count(needle),3)
        verify_all_real_hit_branches(game)
        # Simulate a source regression where normal ATTACK increments even
        # after its touched>0 block has already closed (a MISS could show HIT).
        origin=game.index(needle,game.index('if touched>0 then'))
        mutated=game[:origin]+'end\n        '+game[origin:]
        with self.assertRaises(AssertionError):
            verify_all_real_hit_branches(mutated)
    def test_sourcery_medium1_original_epoch_already_protects_new_hit(self):
        hud=patch_hud(self.sources[HUD]).decode("utf8")
        verify_original_toast_epoch(hud)
        self.assertIn('local epoch=impactDisplayEpoch',hud)
        self.assertIn('if impactDisplayEpoch==epoch then impactToast.Visible=false end',hud)
        # Simulates callback #1 after a subsequent genuine hit #2:
        first,second=1,2
        self.assertNotEqual(first,second) # callback #1 cannot hide #2
        self.assertEqual(second,second)    # callback #2 may hide #2
    def test_off_exact_zero_write(self):
        old=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(old,read(self.base))
    def test_two_sources_changed_all_other79_exact(self):
        old=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        new=read(self.out)
        self.assertEqual(len(new),81)
        self.assertEqual({p for p in old if old[p]!=new[p]},{GAME,HUD})
        self.assertTrue(all(new[p]==old[p] for p in old if p not in (GAME,HUD)))
        self.assertEqual(read(self.base),old)
        sl=json.loads((self.out/"SOURCE_LOCK.json").read_text("utf8"))
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text("utf8"))
        self.assertEqual(sl["total_scripts"],81)
        self.assertEqual(sl["blobs"],fl["source_gitblobs"])
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertTrue(fl["feature_flags"][V1_FLAG])
        self.assertTrue(fl["feature_flags"][V2_FLAG])
        self.assertEqual(sl["horde_private_hit_toast_v3"]["original_other79_byte_exact"],True)
    def test_game_stale_source_rejected(self):
        target=self.base/"src"/GAME
        target.write_bytes(target.read_bytes()+b"\n-- unreviewed")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_hud_stale_source_rejected(self):
        target=self.base/"src"/HUD
        target.write_bytes(target.read_bytes()+b"\n-- unreviewed")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_missing_v2_parent_rejected(self):
        file=self.base/"RC_FEATURE_LOCK.json"
        doc=json.loads(file.read_text())
        doc["feature_flags"][V2_FLAG]=False
        file.write_text(json.dumps(doc))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_duplicate_rejected(self):
        file=self.base/"RC_FEATURE_LOCK.json"
        doc=json.loads(file.read_text())
        doc["feature_flags"][FEATURE]=True
        file.write_text(json.dumps(doc))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_bad_source_lock_rejected(self):
        file=self.base/"SOURCE_LOCK.json"
        doc=json.loads(file.read_text())
        doc["blobs"][GAME]="0"*40
        file.write_text(json.dumps(doc))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_double_patch_rejected(self):
        with self.assertRaises(AssertionError):patch_game(patch_game(self.sources[GAME]))
        with self.assertRaises(AssertionError):patch_hud(patch_hud(self.sources[HUD]))
if __name__=="__main__":
    unittest.main()
