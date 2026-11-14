#!/usr/bin/env python3
"""#431: fail-closed source tests for private non-Studio castle-only pilot."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from apply_fb015_live_castle_canary import (
    FEATURE, ATTR, TARGET, expected_original, patch, apply, blob, read
)
from apply_fb015_castle_gate_silhouette import FEATURE as CASTLE_V3

class PrivateLiveCastleCanary(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p=Path(self.tmp.name)
        self.base=p/"original"
        self.dest=p/"patched"
        (self.base/"src/server").mkdir(parents=True)
        (self.base/"src/client").mkdir(parents=True)
        (self.base/"src"/TARGET).write_bytes(expected_original())
        (self.base/"src/server/Game.server.luau").write_text("-- unchanged Game")
        (self.base/"src/client/HUD.client.luau").write_text("-- unchanged HUD")
        for i in range(77):
            (self.base/"src/server"/f"Other_{i}.luau").write_text("-- original_"+str(i))
        original=read(self.base)
        assert len(original)==80
        pins={k:blob(v) for k,v in sorted(original.items())}
        (self.base/"SOURCE_LOCK.json").write_text(json.dumps({
            "total_scripts":80,"blobs":pins}),encoding="utf8")
        (self.base/"RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources":80, "source_gitblobs":pins,
            "feature_flags":{CASTLE_V3:True},
        }),encoding="utf8")

    def test_v3_parent_exact_and_no_public_default(self):
        s=patch(expected_original()).decode("utf8")
        self.assertIn('workspace:GetAttribute("'+ATTR+'") ~= true then return end',s)
        self.assertNotIn('if not RunService:IsStudio() then return end',s)
        self.assertIn('if isStudioPreview then',s)
        self.assertIn('assert(made==36,"LIVE_GATE_PART_BUDGET_DRIFT")',s)
        self.assertIn('teamCastle(-1,"RED",C(235,103,92))',s)
        self.assertIn('teamCastle(1,"BLUE",C(95,161,232))',s)
        self.assertIn('local MAX_PARTS = 190',s)
        self.assertNotIn('CanCollide = true',s)
        self.assertNotIn('CanQuery = true',s)
    def test_roll_back_off_exact_zero_writes(self):
        self.assertFalse(apply(self.base,self.dest,False))
        self.assertFalse(self.dest.exists())
    def test_single_source_changed_other79_byte_exact(self):
        original=read(self.base)
        self.assertTrue(apply(self.base,self.dest,True))
        actual=read(self.dest)
        self.assertEqual({k for k in original if original[k]!=actual[k]},{TARGET})
        self.assertEqual(len(actual),80)
        self.assertEqual(original["server/Game.server.luau"],actual["server/Game.server.luau"])
        self.assertEqual(original["client/HUD.client.luau"],actual["client/HUD.client.luau"])
        sl=json.loads((self.dest/"SOURCE_LOCK.json").read_text())
        fl=json.loads((self.dest/"RC_FEATURE_LOCK.json").read_text())
        self.assertEqual(sl["blobs"],fl["source_gitblobs"])
        self.assertTrue(fl["feature_flags"][FEATURE])
        self.assertEqual(fl["live_castle_canary"]["nonstudio_max_art_parts"],36)
    def test_stale_source_rejected(self):
        p=self.base/"src"/TARGET
        p.write_bytes(p.read_bytes()+b"\n-- unauthorized")
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_changed_lock_rejected(self):
        f=self.base/"SOURCE_LOCK.json"
        d=json.loads(f.read_text())
        d["blobs"][TARGET]="0"*40
        f.write_text(json.dumps(d))
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_duplicate_adoption_rejected(self):
        f=self.base/"RC_FEATURE_LOCK.json"
        d=json.loads(f.read_text())
        d["feature_flags"][FEATURE]=True
        f.write_text(json.dumps(d))
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_missing_castle_v3_rejected(self):
        f=self.base/"RC_FEATURE_LOCK.json"
        d=json.loads(f.read_text())
        d["feature_flags"][CASTLE_V3]=False
        f.write_text(json.dumps(d))
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())
    def test_double_patch_rejected(self):
        with self.assertRaises(AssertionError):
            patch(patch(expected_original()))
    def test_outside_parent_source_protected(self):
        # A linked child in the 80-source dist may not be trusted.
        path=self.base/"src"/"server"/"evil.luau"
        path.symlink_to(self.base/"src"/TARGET)
        with self.assertRaises(AssertionError):
            apply(self.base,self.dest,True)
        self.assertFalse(self.dest.exists())

if __name__=="__main__":
    unittest.main()
