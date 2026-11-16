import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from compose_result import AUTHOR_PATH, AUTHOR_BLOB, git_blob, patch, MAKE_HEADER, CALL

class SourceExactTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.orig=AUTHOR_PATH.read_bytes()
 def test_source_blob_pin(self): self.assertEqual(git_blob(self.orig),AUTHOR_BLOB)
 def test_off_exact(self): self.assertEqual(patch(self.orig,False),self.orig)
 def test_on_exact_one_policy(self):
  t=patch(self.orig,True).decode()
  self.assertEqual(t.count("ResultRetry.deliver("),1)
  self.assertEqual(t.count("local ResultRetry=require("),1)
 def test_result_scoring_remains_one(self):
  t=patch(self.orig,True).decode()
  self.assertEqual(t.count("ScoreBalance.build("),1)
  self.assertEqual(t.count("session.resultsDelivered=true"),1)
 def test_lossy_original_bug_is_real(self):
  t=self.orig.decode()
  self.assertEqual(t.count('if not container then return end'),1)
  self.assertEqual(t.count(CALL),1)
  self.assertEqual(t.count(MAKE_HEADER),1)
 def test_negative_mutated_blob_fails_closed(self):
  with self.assertRaises(ValueError):patch(self.orig+b" ",True)
 def test_no_new_score_api(self):
  t=patch(self.orig,True).decode()
  self.assertIn("EGGRUMBLE_QueuedMode",t)
  self.assertIn('session.rules.phase=="FINISHED"',t)
  self.assertIn("session.world.Parent~=nil",t)
  self.assertIn("return true",t)
 def test_no_original_source_modified(self):
  self.assertEqual(git_blob(self.orig),AUTHOR_BLOB)

if __name__=="__main__":unittest.main()
