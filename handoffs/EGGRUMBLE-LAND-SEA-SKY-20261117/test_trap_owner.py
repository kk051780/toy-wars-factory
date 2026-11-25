import unittest
from pathlib import Path
import importlib.util

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("trap_fairness_native",HERE/"make_native_trap_owner.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class TrapOwnerFairness(unittest.TestCase):
 def test_real_lss_one_owner_one_active_trap(self):
  src=mod.SOURCE.read_text(encoding="utf-8")
  fn=mod.extract(src)
  self.assertIn("if previousOwner==ownerId then return false end",fn)
  self.assertIn("return live<MAX_LIVE_TRAPS",fn)
  self.assertIn("traps[t]=owner.UserId",src)
  self.assertIn("if not canReserveTrapSlot(owner.UserId) or liveParts>=MAX_PARTS_PER_WORLD then return end",src)
  self.assertNotIn("traps[t]=true",src)
 def test_native_positive_and_mutant_are_distinct(self):
  src=mod.SOURCE.read_text(encoding="utf-8")
  good=mod.build(src)
  mutant=mod.build(src,mutant=True)
  self.assertIn("RED_SAME_OWNER_TWO_TRAPS",good)
  self.assertIn("GQ8_LSS_TRAP_OWNER_LUAU_11_CASES_PASS",good)
  self.assertNotEqual(good,mutant)
  self.assertIn("if previousOwner==-1 then return false end",mutant)
 def test_marker_or_owner_intake_drift_is_red(self):
  src=mod.SOURCE.read_text(encoding="utf-8")
  for changed in [src.replace(mod.BEGIN,"",1),src.replace(mod.END,"",1),
                  src.replace("traps[t]=owner.UserId","traps[t]=true",1),
                  src.replace(mod.ANCHOR,"if false then return false end",1)]:
   with self.subTest(changed=changed.count("GQ8_LSS_TRAP_OWNER_FAIRNESS_20261118")):
    with self.assertRaisesRegex(ValueError,"RED_TRAP_OWNER"):
     mod.extract(changed)
