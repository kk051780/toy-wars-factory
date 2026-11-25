"""Negative/rollback gate for actual existing-author #515 field egg drop selection."""
import importlib.util
import json
import unittest
from pathlib import Path
from importlib.machinery import SourceFileLoader

SCRIPT=Path("rc_fastlane/quality_egg515_rc31/select_original_egg_bounds.py")
mod=SourceFileLoader("gq515_current_selector",str(SCRIPT)).load_module()
ROOT=Path("artifacts/gq515_official_select")
BASE=Path("artifacts/gq583_official_select/GQ583_SELECTED31.project.json")
AUTHOR=Path("_gq515_original/quality_gameplay/field_egg_drop_recovery_20261116/EGGRUMBLE_FieldEggDropBounds.luau")

class OriginalEggBoundsOnCurrentRC(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mapper=mod.original_mapper()
  cls.base,cls.sources=cls.mapper.scan(BASE)
  cls.selected,cls.output=cls.mapper.scan(ROOT/"GQ515_SELECTED31.project.json")
  cls.original=cls.sources[mod.HOST].read_bytes()
  cls.actual=cls.output[mod.HOST].read_bytes()
  cls.policy=AUTHOR.read_bytes()
 def test_original_source_lock(self):
  self.assertEqual(mod.blob(self.policy),mod.AUTHOR_POLICY_BLOB)
 def test_no_new_authority(self):
  self.assertEqual(len(self.sources),len(self.output))
  self.assertEqual(len(self.output),31)
  self.assertEqual(set(self.sources),set(self.output))
 def test_other_30_exact(self):
  for name,path in self.sources.items():
   if name!=mod.HOST:
    self.assertEqual(self.output[name].read_bytes(),path.read_bytes(),name)
 def test_original_policy_body_reused_without_module(self):
  full=self.actual.decode()
  self.assertIn(self.policy.decode().split("--!strict\n",1)[1].rstrip(),full)
  self.assertNotIn('WaitForChild("EGGRUMBLE_FieldEggDropBounds")',full)
  self.assertEqual(full.count("function Drop.recover("),1)
  self.assertEqual(full.count("DropBounds.recover("),1)
 def test_true_byte_exact_inverse(self):
  self.assertEqual(self.actual,mod.source_select(self.original,self.policy))
  text=self.actual.decode()
  old=text.replace(mod.REQUIRE+mod.HEADER+self.policy.decode().split("--!strict\n",1)[1].rstrip()+"\n"+mod.TAIL,mod.REQUIRE,1)
  old=old.replace(mod.ORIGINAL_SOURCE_ONLY,mod.ORIGINAL,1)
  self.assertEqual(old.encode(),self.original)
 def test_negative_mutant_author_policy_rejected(self):
  with self.assertRaises(ValueError):
   mod.source_select(self.original,self.policy+b"\n-- unauthorized mutation")
 def test_negative_stale_host_rejected(self):
  with self.assertRaises(ValueError):
   mod.source_select(self.original.replace(mod.ORIGINAL.encode(),b"local landing=nil"),self.policy)
 def test_negative_second_host_block_rejected(self):
  with self.assertRaises(ValueError):
   mod.source_select(self.original+mod.ORIGINAL.encode(),self.policy)
 def test_scores_eggs_authorities_preserved(self):
  for token in ["Rules.onCarrierEliminated(", "session.releaseEggs(", "session.refresh()", "session.rules.phase"]:
   self.assertEqual(self.original.decode().count(token),self.actual.decode().count(token),token)
 def test_author_current_source_receipt(self):
  j=json.loads((ROOT/"GQ515_SOURCE_RECEIPT.json").read_text())
  self.assertEqual(j["source_count"],31)
  self.assertTrue(j["other_30_source_byte_exact"])
  self.assertFalse(j["official_rc_adopted"])

if __name__=="__main__":unittest.main()
