"""Current OFFICIAL31 item source only; adverse mutants reject changes."""
import os
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from patch_item import (
    apply,inverse,native_harness,MARKER,HELPER,OLD_ITEM,NEW_ITEM,
    NEW_HIDE,NEW_SHOW,GAMEPLAY_ANCHORS
)
class TestItemSculptures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        file=os.environ.get("GQ802_REAL_ITEM_SOURCE")
        if not file:raise RuntimeError("RED_NO_OFFICIAL_ITEM_SOURCE")
        cls.original=Path(file).read_bytes()
    def test_real_original_neon_only_before(self):
        source=self.original.decode()
        self.assertEqual(source.count(OLD_ITEM),1)
        self.assertNotIn(MARKER,source)
        for anchor in GAMEPLAY_ANCHORS:self.assertIn(anchor,source)
    def test_exact_one_item_visual_overlay(self):
        candidate=apply(self.original).decode()
        self.assertEqual(candidate.count(HELPER),1)
        self.assertEqual(candidate.count(NEW_ITEM),1)
        self.assertEqual(candidate.count(NEW_HIDE),1)
        self.assertEqual(candidate.count(NEW_SHOW),1)
        self.assertIn('v.CanCollide=false;v.CanTouch=false;v.CanQuery=false',candidate)
        self.assertIn('part.Material=Enum.Material.SmoothPlastic',candidate)
    def test_original_31_byte_exact_off(self):
        self.assertEqual(inverse(apply(self.original)),self.original)
    def test_no_gameplay_change_except_four_known_hunks(self):
        selected=apply(self.original).decode()
        before=selected.replace(NEW_SHOW,"    part.Transparency=0;part.CanQuery=true;prompt.Enabled=true\n",1)
        before=before.replace(NEW_HIDE,"   part.Transparency=1;part.CanQuery=false\n",1)
        before=before.replace(NEW_ITEM,OLD_ITEM,1).replace(HELPER,"",1)
        self.assertEqual(before,self.original.decode())
        self.assertEqual(selected.count('hum.Health=math.min'),1)
        self.assertEqual(selected.count('hum.WalkSpeed=math.max'),1)
        self.assertEqual(selected.count('local force=Instance.new("ForceField")'),1)
        self.assertEqual(selected.count('lastUse[key]=now'),1)
    def test_mutated_visibility_rejected(self):
        selected=apply(self.original).replace(b"v.Transparency=1 end",b"v.Transparency=0 end",1)
        with self.assertRaisesRegex(ValueError,"RED_GQ802_SELECTED_ITEM_DRIFT"):inverse(selected)
    def test_mutated_canquery_rejected(self):
        selected=apply(self.original).replace(b"v.CanQuery=false",b"v.CanQuery=true",1)
        with self.assertRaisesRegex(ValueError,"RED_GQ802_SELECTED_ITEM_DRIFT"):inverse(selected)
    def test_original_source_change_rejected(self):
        broken=self.original.replace(b"part.Material=Enum.Material.Neon",b"part.Material=Enum.Material.Glass",1)
        with self.assertRaisesRegex(ValueError,"RED_GQ802_ITEM_VISUAL_ANCHOR_CHANGED"):apply(broken)
    def test_double_patch_and_bad_inverse_rejected(self):
        with self.assertRaises(ValueError):apply(apply(self.original))
        with self.assertRaises(ValueError):inverse(self.original)
    def test_native_harness_exact_helper(self):
        selected=apply(self.original)
        vm=native_harness(selected)
        self.assertIn(HELPER,vm)
        self.assertIn(NEW_SHOW,vm)
        self.assertIn(NEW_HIDE,vm)
        self.assertIn("GQ802_REAL_ITEM_ART_NATIVE_VM_PASS",vm)
if __name__=="__main__":unittest.main()
