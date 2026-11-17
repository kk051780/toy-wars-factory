#!/usr/bin/env python3
"""Source-bound non-overlap, safety, rollback and native-harness contract for idle craft."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parent
SOURCE=(ROOT/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("idle_generator",ROOT/"make_idle_craft_native.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class IdleCraftLeaseSourceTests(unittest.TestCase):
    def test_single_optional_server_source_and_owner_auth(self):
        self.assertIn("if not RunService:IsStudio() then return end",SOURCE)
        self.assertIn("currentCraftOwner(v.owner,mode,world,v.role)",SOURCE)
        self.assertIn("local activePilot=hum~=nil and driver==v.owner and hum.Health>0",SOURCE)
        self.assertIn("EMPTY_CRAFT_GRACE_SECONDS = 25",SOURCE)
        self.assertNotIn('Instance.new("RemoteEvent")',SOURCE)
        self.assertNotIn("DataStoreService",SOURCE)

    def test_idle_expiry_recycles_model_without_unsafe_rescue(self):
        self.assertEqual(SOURCE.count("emptyCraftLease(activePilot,v.emptySince,os.clock())"),1)
        self.assertIn("if idleExpired then\n     -- After a 25s empty-seat grace",SOURCE)
        self.assertIn("v.lastPilot=nil\n     craft:Destroy()\n    elseif hum",SOURCE)
        self.assertIn("if not hum and v.lastPilot then",SOURCE)
        self.assertIn("safeMove(v.owner,landDock.Position",SOURCE)
        self.assertIn("if perUser[player.UserId]==data then perUser[player.UserId]=nil end",SOURCE)
        self.assertIn("vessels[craft]=nil",SOURCE)

    def test_harness_is_pinned_to_actual_source_and_mutant_diff(self):
        helper=mod.actual_helper()
        self.assertIn("if ownedPilot then return false,nil end",helper)
        self.assertIn(mod.PREDICATE,helper)
        with TemporaryDirectory() as tmp:
            good=Path(tmp)/"good.luau"
            bad=Path(tmp)/"mutant.luau"
            mod.generate(good,bad)
            self.assertIn(helper,good.read_text(encoding="utf-8"))
            self.assertNotIn(mod.PREDICATE,bad.read_text(encoding="utf-8"))
            self.assertIn("SECOND_GRACE",good.read_text(encoding="utf-8"))
            self.assertIn("OWNER_REBOARDED_RESET",good.read_text(encoding="utf-8"))

    def test_missing_real_integration_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"RED_IDLE_CRAFT_REAL_HEARTBEAT_NOT_CONNECTED"):
            mod.actual_helper(SOURCE.replace("emptyCraftLease(activePilot,v.emptySince,os.clock())",
                                             "emptyCraftLease(false,nil,os.clock())"))
        with self.assertRaisesRegex(ValueError,"RED_IDLE_CRAFT_HELPER_CHANGED"):
            mod.actual_helper(SOURCE.replace(mod.PREDICATE,"true"))

if __name__=="__main__":
    unittest.main()
