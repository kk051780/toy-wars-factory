import importlib.util
import unittest
from pathlib import Path

DIR=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("lss_spatial",DIR/"make_native_trap_slots.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class TrapSpatialSeparation(unittest.TestCase):
 def test_two_live_traps_not_co_located(self):
  src=mod.SOURCE.read_text(encoding="utf-8")
  fn=mod.extract(src)
  self.assertIn("if not occupied[1] then return 1 end",fn)
  self.assertIn("if not occupied[2] then return 2 end",fn)
  self.assertIn("local anchor=Vector3.new(x+48+(slot-1)*30,y+3,shoreZ-57)",src)
  self.assertLess(src.index("local slot=chooseUnoccupiedTrapSlot()"),
                  src.index('t:SetAttribute("LSS_TrapSlot",slot)'))
  self.assertIn("if not canReserveTrapSlot(owner.UserId)",src)
  self.assertIn("traps[t]=owner.UserId",src)
  self.assertIn("t.Destroying:Connect(function() traps[t]=nil end)",src)

 def test_native_mutant_is_different(self):
  src=mod.SOURCE.read_text(encoding="utf-8")
  good=mod.build(src)
  bad=mod.build(src,mutant=True)
  self.assertIn("GQ8_LSS_TRAP_SPATIAL_6_NATIVE_CASES_PASS",good)
  self.assertIn("RED_SECOND_OWNER_MUST_HAVE_DISTINCT_SLOT",bad)
  self.assertIn("if not occupied[2] then return 1 end",bad)
  self.assertNotEqual(good,bad)

 def test_required_wiring_deletion_goes_red(self):
  src=mod.SOURCE.read_text(encoding="utf-8")
  for a,b in [(mod.BEGIN,""),(mod.END,""),
              ("x+48+(slot-1)*30","x+48"),
              ('t:SetAttribute("LSS_TrapSlot",slot)',""),
              ("if not occupied[2] then return 2 end","if true then return 2 end")]:
   with self.subTest(a=a):
    with self.assertRaisesRegex(ValueError,"RED_TRAP_SLOT"):
     mod.extract(src.replace(a,b,1))
