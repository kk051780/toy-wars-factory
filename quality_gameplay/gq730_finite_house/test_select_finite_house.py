import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("gq730",ROOT/"select_finite_house.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class FiniteDecorSelector(unittest.TestCase):
    def setUp(self):
        self.src = """local M={}
function M.placeHouseDecoration(m:any,ownerId:any,actorId:any,piece:any)
""" + m.BEFORE + """
 table.insert(m.homePieces,piece)
end
return M
"""
    def test_single_existing_guard_only(self):
        patched=m.select(self.src)
        self.assertEqual(patched.count(m.AFTER),1)
        self.assertNotIn(m.BEFORE,patched)
        self.assertEqual(patched.count("finiteDecorCoordinate(value:any)"),1)
        self.assertEqual(patched.replace(m.HELPER,"",1).replace(m.AFTER,m.BEFORE,1),self.src)
    def test_fail_closed_when_changed(self):
        with self.assertRaises(ValueError):
            m.select(self.src.replace(m.BEFORE," assert(true)"))
        with self.assertRaises(ValueError):
            m.select(m.select(self.src))
        with self.assertRaises(ValueError):
            m.select(self.src.replace(m.FUNCTION,"function other()"))
    def test_harness_uses_actual_module(self):
        h=m.make_harness(m.select(self.src))
        self.assertIn("M.placeHouseDecoration(",h)
        self.assertIn("GQ730_FINITE_DECOR_NATIVE_PASS",h)
        self.assertEqual(h.count("local M={}"),1)
    def test_infinity_and_nan_fences(self):
        p=m.select(self.src)
        self.assertIn("value==value",p)
        self.assertIn("value>-math.huge and value<math.huge",p)
        for axis in ("x","y","z"):
            self.assertIn('"' + axis + '"',m.HARNESS)
if __name__=="__main__":
    unittest.main()
