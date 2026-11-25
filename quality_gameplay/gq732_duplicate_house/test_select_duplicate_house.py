import importlib.util,unittest
from pathlib import Path

D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("selector",D/"select_duplicate_house.py")
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class DecorDupSource(unittest.TestCase):
 def setUp(self):
  self.src="local M={}\n"+s.FUNCTION+"\n"+s.ANCHOR+"\nend\nreturn M\n"
 def test_source_delta_and_inverse(self):
  after=s.select(self.src)
  self.assertIn(s.MARKER,after)
  self.assertEqual(s.off(after),self.src)
  self.assertEqual(after.count(s.ANCHOR),1)
 def test_invariant_kind_and_position(self):
  after=s.select(self.src)
  for condition in ("existing.kind==piece.kind","existing.x==piece.x","existing.y==piece.y","existing.z==piece.z"):
   self.assertIn(condition,after)
 def test_fail_closed(self):
  with self.assertRaises(ValueError):s.select(self.src.replace(s.ANCHOR," assert(true)"))
  with self.assertRaises(ValueError):s.select(s.select(self.src))
  with self.assertRaises(ValueError):s.off(self.src)
 def test_real_author_module_harness(self):
  self.assertIn("GQ732_DUPLICATE_HOUSE_DECOR_REAL_RULES_NATIVE_PASS",s.native(s.select(self.src)))
  self.assertIn("GQ732_DUPLICATE_REJECT_MISSING_",s.native(self.src))
 if __name__=="__main__":unittest.main()
