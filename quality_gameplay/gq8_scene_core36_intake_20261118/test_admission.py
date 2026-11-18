#!/usr/bin/env python3
"""Actual-file based positive/negative source-selection tests; no synthetic game."""
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("admission",ROOT/"validate_admission.py")
adm=importlib.util.module_from_spec(spec)
spec.loader.exec_module(adm)

class Core36SceneAdmission(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=adm.SOURCE.read_text(encoding="utf-8")

 def test_pinned_source_and_authoritative_manifests(self):
  report=adm.verify_locks()
  self.assertEqual(report["source_git_blob"],adm.EXPECTED_BLOB)
  self.assertTrue(report["lss_bytes"]>35000)

 def test_exact_promotion_on_real_source(self):
  expected=self.original.replace(adm.STUDIO_GATE,adm.PROMOTION,1)
  adm.ensure_promoted_source(self.original,expected)
  self.assertNotIn(adm.STUDIO_GATE,expected)
  self.assertIn("flightDismountNeedsRescue",expected)
  self.assertIn("retireScene(true)",expected)

 def test_each_missing_critical_guard_is_a_red(self):
  needles=[
    "local function retireScene(removeVisual)",
    "worldDestroyingConnection=world.Destroying:Connect(function() retireScene(false) end)",
    "worldDestroyingConnection:Disconnect()",
    "retireScene(true)",
    "flightDismountNeedsRescue(",
    "emptyCraftLease(",
    "if removeVisual and scene.Parent then scene:Destroy() end",
  ]
  for token in needles:
   with self.subTest(token=token):
    corrupted=self.original.replace(token,"-- MUTANT_GUARD_REMOVED",1)
    with self.assertRaises(adm.AdmissionError):
     adm.assert_runtime_source(corrupted,exact_blob=False)

 def test_corrupted_selected_source_is_not_admitted(self):
  expected=self.original.replace(adm.STUDIO_GATE,adm.PROMOTION,1)
  with self.assertRaisesRegex(adm.AdmissionError,"RED_CORE36_SELECTED_LSS"):
   adm.ensure_promoted_source(self.original,expected.replace("retireScene(true)","-- lost",1))

 def test_wrong_original_blob_is_a_red(self):
  with self.assertRaisesRegex(adm.AdmissionError,"RED_LSS_SOURCE_BLOB"):
   adm.assert_runtime_source(self.original+"\n-- drift",exact_blob=True)

 def test_missing_studio_gate_and_unapproved_authorities_are_red(self):
  with self.assertRaisesRegex(adm.AdmissionError,"RED_STUDIO_PROMOTION"):
   adm.assert_runtime_source(self.original.replace(adm.STUDIO_GATE,"-- removed",1),False)
  with self.assertRaisesRegex(adm.AdmissionError,"RED_SECOND_REMOTE_OR_STORE"):
   adm.assert_runtime_source(self.original+'\nInstance.new("RemoteEvent")',False)

if __name__=="__main__":
 unittest.main()
