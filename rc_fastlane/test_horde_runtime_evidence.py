#!/usr/bin/env python3
"""#444 real 81 parent -> isolated 82 passive probe, 10 negative+contract tests."""
from __future__ import annotations
import json,os,shutil,tempfile,unittest
from pathlib import Path
from apply_horde_runtime_evidence import (
    AUTHOR,AUTHOR_BLOB,DEST,GAME,HORDE,FEATURE,blob,read,verify_author,apply
)
BASE=Path(os.environ.get("P0D_HORDE_RUNTIME_EVIDENCE_PARENT",
                         "/tmp/p0d_horde_private_lifecycle_v2_81"))
@unittest.skipUnless(BASE.is_dir(),"REAL_RC81_V2_DIST_REQUIRED")
class PrivateHordeWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=read(BASE)
        assert len(cls.before)==81 and blob(AUTHOR.read_bytes())==AUTHOR_BLOB
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.base=root/"parent"
        self.out=root/"output"
        shutil.copytree(BASE,self.base,symlinks=False)
    def test_author_exact(self):
        verify_author(AUTHOR.read_bytes())
    def test_must_hard_reject_public_and_require_two_owner_flags(self):
        s=AUTHOR.read_text("utf8")
        self.assertIn('if not RunService:IsStudio() and game.PrivateServerId == "" then return end',s)
        self.assertIn('workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") ~= true',s)
        self.assertIn('workspace:GetAttribute("P0D_PRIVATE_HORDE_EVIDENCE") ~= true',s)
    def test_no_mutation_no_gui_no_network_and_bounded_sampling(self):
        s=AUTHOR.read_text("utf8")
        for forbidden in ("Instance.new(", "FireServer(", "OnServerEvent",
                          "SetAttribute(", "HttpService:PostAsync",
                          "Humanoid:TakeDamage(", "RemoteEvent"):
            self.assertNotIn(forbidden,s)
        self.assertIn("local MAX_SAMPLES = 360",s)
        self.assertIn("task.wait(SAMPLE_SECONDS)",s)
        self.assertIn('print("P0D_HORDE_PRIVATE_EVIDENCE "',s)
    def test_truly_observed_popup_not_fake_hit_receipt(self):
        s=AUTHOR.read_text("utf8")
        self.assertIn('local popup = core:FindFirstChild("RealDamagePopup")',s)
        self.assertIn('popup.Enabled and text ~= nil',s)
        self.assertIn('not lastVisible[child]',s)
        self.assertIn('modelMovementSamples = motionEvents',s)
        self.assertIn('liveCombatQualityApproved = false',s)
        self.assertIn('ownerAccepted = false',s)
    def test_off_must_not_write(self):
        before=read(self.base)
        self.assertFalse(apply(self.base,self.out,False))
        self.assertFalse(self.out.exists())
        self.assertEqual(read(self.base),before)
    def test_82_luau_old81_byte_exact(self):
        before=read(self.base)
        self.assertTrue(apply(self.base,self.out,True))
        after=read(self.out)
        self.assertEqual(len(after),82)
        self.assertEqual({p for p in after if p not in before},{DEST})
        self.assertTrue(all(after[k]==v for k,v in before.items()))
        self.assertEqual(read(self.base),before)
        self.assertEqual(after[DEST],AUTHOR.read_bytes())
        sl=json.loads((self.out/"SOURCE_LOCK.json").read_text("utf8"))
        fl=json.loads((self.out/"RC_FEATURE_LOCK.json").read_text("utf8"))
        self.assertEqual(sl["total_scripts"],fl["total_sources"])
        self.assertEqual(sl["total_scripts"],82)
        self.assertEqual(sl["blobs"],fl["source_gitblobs"])
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertFalse(fl["horde_runtime_probe_v1"]["owner_accepted"])
    def test_game_corruption_refused(self):
        f=self.base/"src"/GAME
        f.write_bytes(f.read_bytes()+b"\n-- drift")
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_source_lock_corruption_refused(self):
        f=self.base/"SOURCE_LOCK.json"
        data=json.loads(f.read_text("utf8"));data["blobs"][GAME]="0"*40
        f.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_missing_v2_gameplay_flag_refused(self):
        f=self.base/"RC_FEATURE_LOCK.json"
        data=json.loads(f.read_text("utf8"))
        data["feature_flags"]["P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2"]=False
        f.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_duplicate_adoption_refused(self):
        f=self.base/"RC_FEATURE_LOCK.json"
        data=json.loads(f.read_text("utf8"));data["feature_flags"][FEATURE]=True
        f.write_text(json.dumps(data))
        with self.assertRaises(AssertionError):apply(self.base,self.out,True)
        self.assertFalse(self.out.exists())
    def test_author_drift_refused(self):
        with self.assertRaises(AssertionError):
            verify_author(AUTHOR.read_bytes()+b"\n-- unauthorized")
if __name__=="__main__":
    unittest.main()
