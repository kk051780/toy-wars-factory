"""Tests for eight-lane readiness semantics (source != official RC)."""
import importlib.util,unittest
from pathlib import Path
P=Path(__file__).resolve().parent/"p0d_rc_intake_readiness.py"
spec=importlib.util.spec_from_file_location("p0d_rc_intake_readiness",P)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class IntakeGate(unittest.TestCase):
 def test_all_domains(self):
  self.assertEqual(set(mod.LANES),{"CHARACTER","FIELD","BATTLE","CASTLE","NEUTRAL","ITEM","LOBBY","BALANCE"})
 def test_source_is_not_integration(self):
  r=mod.report()
  self.assertEqual(r["lane_total"],8)
  self.assertEqual(r["rc_integrated"],0)
  self.assertEqual(r["rc_percent_verified"],0)
  for lane,entry in r["lanes"].items():
   self.assertFalse(entry["rc_integrated"],lane)
   self.assertFalse(entry["owner_accepted"],lane)
   self.assertEqual(entry["studio"],"UNVERIFIED")
   self.assertEqual(entry["android"],"UNVERIFIED")
if __name__=="__main__":unittest.main()
