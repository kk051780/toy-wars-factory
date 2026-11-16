#!/usr/bin/env python3
"""Source identity and malicious mutation tests; runtime tested in native Luau CI."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location("vertical",ROOT/"select_vertical.py")
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
M=module
FIXTURE="--!strict\nlocal Geometry={}\n"+M.ANCHOR+" return true\nend\nreturn Geometry\n"

class VerticalReach(unittest.TestCase):
    def test_single_original_geometry_guard(self):
        chosen=M.apply(FIXTURE)
        self.assertIn("math.abs(dy)>math.min(radius,14)",chosen)
        self.assertIn("radius~=radius",chosen)
    def test_reverse_is_original_exact(self):
        chosen=M.apply(FIXTURE)
        self.assertEqual(chosen.replace(M.SELECTED,M.ANCHOR,1),FIXTURE)
    def test_duplicate_method_rejected(self):
        with self.assertRaises(ValueError):M.apply(FIXTURE+M.ANCHOR)
    def test_changed_anchor_rejected(self):
        with self.assertRaises(ValueError):M.apply(FIXTURE.replace("radius>22","radius>21"))
    def test_already_selected_rejected(self):
        with self.assertRaises(ValueError):M.apply(M.apply(FIXTURE))
    def test_no_parallel_server_authority(self):
        chosen=M.apply(FIXTURE)
        self.assertEqual(chosen.count("function Geometry.allowed("),1)
        self.assertEqual(chosen.count("return Geometry"),1)
    def test_original_and_repaired_native_differ(self):
        before=M.native(FIXTURE,False)
        after=M.native(M.apply(FIXTURE),True)
        self.assertIn('"vertical_50_circle",at(0,50,10),20,"CIRCLE",true',before)
        self.assertIn('"vertical_50_circle",at(0,50,10),20,"CIRCLE",false',after)
    def test_git_blob_sha(self):
        raw=b"test"
        import hashlib
        self.assertEqual(M.git_blob(raw),hashlib.sha1(b"blob 4\0test").hexdigest())

if __name__=="__main__":unittest.main()
