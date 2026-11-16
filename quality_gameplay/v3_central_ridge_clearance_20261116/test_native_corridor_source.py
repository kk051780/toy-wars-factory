"""Source-locked native physics/LOS harness integrity (not a Studio engine test)."""
import tempfile
import unittest
from pathlib import Path
from patch_ridge import HOST, ITEMS, OLD, NEW
from make_native_corridor import source_readback,make_vm

class RidgeNativeVMInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=HOST.read_text(encoding="utf-8")
        cls.items=ITEMS.read_text(encoding="utf-8")
        cls.base=cls.author+"\n-- CastleAccessRamp from original #484\n"
        cls.after=cls.base.replace(OLD,NEW)

    def test_real_source_extracts_one_luau_ridge_for_each(self):
        old,new=source_readback(self.author,self.base,self.after,self.items)
        self.assertEqual(old,OLD)
        self.assertEqual(new,NEW)

    def test_generated_vm_embeds_actual_executable_original_and_patch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            paths=[root/x for x in ("original.luau","base.luau","after.luau",
                                     "item.luau","vm.luau")]
            for p,s in zip(paths[:4],(self.author,self.base,self.after,self.items)):
                p.write_text(s,encoding="utf-8")
            make_vm(*paths)
            vm=paths[-1].read_text(encoding="utf-8")
            self.assertEqual(vm.count(OLD),1)
            self.assertEqual(vm.count(NEW),1)
            self.assertIn("GQ520_ORIGINAL_RIDGE_REAL_LUAU_VM_PASS",vm)
            self.assertIn("assert(not isBlocked(fresh",vm)
            self.assertIn("assert(lineBlocked(old",vm)

    def test_refuse_unrelated_core_author_mutation(self):
        with self.assertRaisesRegex(ValueError,"unrelated Game"):
            source_readback(self.author,self.base,self.after+"\n--changed",self.items)

    def test_refuse_item_site_offset_mutation(self):
        item=self.items.replace('x=0,z=470,kind="SHIELD"',
                                 'x=8,z=470,kind="SHIELD"')
        with self.assertRaisesRegex(ValueError,"item real world position drift"):
            source_readback(self.author,self.base,self.after,item)

    def test_refuse_unpatched_or_double_patch(self):
        with self.assertRaisesRegex(ValueError,"terrain source not unique"):
            source_readback(self.author,self.base,self.base,self.items)
        with self.assertRaisesRegex(ValueError,"terrain source not unique"):
            source_readback(self.author,self.base,self.after+NEW,self.items)

    def test_refuse_changed_original_author_source(self):
        with self.assertRaisesRegex(ValueError,"immutable source blob changed"):
            source_readback(self.author+"\n--tampered",self.base,self.after,self.items)

if __name__=="__main__":unittest.main()
