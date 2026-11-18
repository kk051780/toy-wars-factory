#!/usr/bin/env python3
"""Airborne voluntary-dismount source-bound regression; no simulated engine claim."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE=Path(__file__).resolve().parent
SOURCE=(HERE/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("air_dismount",HERE/"make_air_dismount_native.py")
generator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class AirDismountTests(unittest.TestCase):
    def test_real_flight_guard_and_avatar_fence(self):
        guard=generator.extract()
        self.assertIn("and highCraft and highAvatar and not solidBelow", guard)
        self.assertIn("matchHuman(v.owner,mode,world,v.role)",SOURCE)
        self.assertIn("v.owner.Character==ch and departed.Parent==ch and departed.Health>0",SOURCE)

    def test_actual_callback_uses_existing_safe_move_and_cleanup(self):
        self.assertEqual(SOURCE.count(generator.HEARTBEAT),1)
        self.assertEqual(SOURCE.count(generator.RESCUE),1)
        call=SOURCE.split("elseif v.flying and ch and departed.Parent==ch",1)[1].split("if idleExpired then",1)[0]
        self.assertIn(generator.HEARTBEAT,call)
        self.assertIn("craft:Destroy()",call)
        self.assertIn("groundParams.FilterDescendantsInstances={ch,craft}",call)
        self.assertIn("groundParams.RespectCanCollide=true",call)
        self.assertIn("Workspace:Raycast(root.Position,Vector3.new(0,-12,0)",call)

    def test_no_new_authority_and_sea_and_idle_unchanged(self):
        self.assertIn("if not v.flying and ch and departed.Parent==ch and root",SOURCE)
        self.assertIn("emptyCraftLease(activePilot,v.emptySince,os.clock())",SOURCE)
        self.assertIn("if idleExpired then",SOURCE)
        self.assertIn('if not RunService:IsStudio() then return end',SOURCE)
        self.assertNotIn('Instance.new("RemoteEvent")',SOURCE)
        self.assertNotIn("DataStoreService",SOURCE)

    def test_native_generated_from_pinned_actual_helper_and_mutant_diff(self):
        with TemporaryDirectory() as tmp:
            good=Path(tmp)/"good.luau"
            mutant=Path(tmp)/"mutant.luau"
            generator.generate(good,mutant)
            self.assertIn(generator.extract(),good.read_text())
            self.assertIn("and highCraft and highAvatar and true",mutant.read_text())
            self.assertNotEqual(good.read_bytes(),mutant.read_bytes())

    def test_fail_closed_for_ground_ray_deleted(self):
        altered=SOURCE.replace("groundParams.RespectCanCollide=true","groundParams.RespectCanCollide=false")
        with self.assertRaisesRegex(ValueError,"RED_AIR_DISMOUNT_UNTRUSTWORTHY_GROUND_CHECK"):
            generator.extract(altered)

    def test_fail_closed_for_missing_owner_avatar_guard(self):
        altered=SOURCE.replace(
            "v.owner.Character==ch and departed.Parent==ch and departed.Health>0",
            "true")
        with self.assertRaisesRegex(ValueError,"RED_AIR_DISMOUNT_STALE_AVATAR"):
            generator.extract(altered)

    def test_fail_closed_for_unwired_heartbeat(self):
        altered=SOURCE.replace(generator.HEARTBEAT,"if false then")
        with self.assertRaisesRegex(ValueError,"RED_AIR_DISMOUNT_CALLBACK_UNWIRED"):
            generator.extract(altered)


if __name__=="__main__":
    unittest.main()
