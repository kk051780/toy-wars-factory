#!/usr/bin/env python3
"""Native-extracted full vehicle footprint regression for optional32 LSS.
The native function is copied from the real shipping candidate, not reimplemented.
CI also mutates it to the old hull-only 8x2x11 and requires an expected RED.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE_PATH = HERE / "EGGRUMBLE_LandSeaSkyTraversal.server.luau"
SIDECAR = REPO / "rc_fastlane/EGGRUMBLE_V3_LSS_OPTIONAL32.json"
LOCK = HERE / "GQ8_RC32_SOURCE_LOCK.json"

def extract_size_function(src: str) -> str:
    hits = re.findall(r"local function craftSweepSize\(flying\)\n.*?\nend",
                      src, flags=re.S)
    if len(hits) != 1:
        raise AssertionError("RED_NO_EXACT_SINGLE_ORIGINAL_SWEEP_FUNCTION")
    return hits[0]

def native_cases(src: str, mutant: bool = False) -> str:
    actual = extract_size_function(src)
    if mutant:
        actual = actual.replace(
            "return flying and Vector3.new(24,8,19) or Vector3.new(18,8,19)",
            "return Vector3.new(8,2,11)")
    return """local Vector3={new=function(x,y,z) return {X=x,Y=y,Z=z} end}
""" + actual + """
local fly=craftSweepSize(true)
local boat=craftSweepSize(false)
assert(fly.X>=23,"GQ8_SWEEP_WING_TOO_NARROW")
assert(boat.X>=15,"GQ8_SWEEP_PONTOON_TOO_NARROW")
assert(fly.Y>=7.5 and boat.Y>=5.5,"GQ8_SWEEP_SEAT_LEVER_TOO_SHORT")
assert(fly.Z>=17 and boat.Z>=17,"GQ8_SWEEP_BOW_TOO_SHORT")
assert(fly.X>boat.X,"GQ8_SWEEP_ROLE_ENVELOPE_LOST")
print("GQ8_LSS_ACTUAL_FULL_FOOTPRINT_5_NATIVE_CASES_PASS")
"""

class LSSFullCraftSourceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SOURCE_PATH.read_text(encoding="utf-8")
        cls.sidecar = json.loads(SIDECAR.read_text(encoding="utf-8"))
        cls.lock = json.loads(LOCK.read_text(encoding="utf-8"))

    def test_real_one_source_and_exact_git_blob(self):
        s=self.src.encode("utf-8")
        blob=hashlib.sha1(b"blob "+str(len(s)).encode()+b"\0"+s).hexdigest()
        self.assertEqual(blob,self.sidecar["added_source_git_blob"])
        self.assertEqual(blob,self.lock["optional_profile"]["source_blob_sha"])
        self.assertEqual(blob,self.sidecar["gq8_craft_full_footprint"]["source_git_blob"])
        self.assertTrue(self.lock["authority"]["canonical_v3_31_profile_untouched"])
        self.assertFalse(self.lock["authority"]["production_enabled"])
        self.assertFalse(self.sidecar["robot_release_authorized"])

    def test_full_footprint_and_turn_only_in_real_motion_path(self):
        scope=self.src.split("local delta=point-cf.Position",1)[1].split(
            "elseif v.flying then",1)[0]
        required=[
            "local targetCF=CFrame.new(point)*cf.Rotation",
            "local sweepSize=craftSweepSize(v.flying)",
            "local exclude=vehicleSweepExclusions(",
            "craft,water,offshoreWater,hum.Parent)",
            "Workspace:Blockcast(cf,sweepSize,delta,params)==nil",
            "overlap.FilterDescendantsInstances=exclude",
            "overlap.RespectCanCollide=true",
            "overlap.MaxParts=1",
            "#Workspace:GetPartBoundsInBox(targetCF,sweepSize,overlap)==0",
            "craft:PivotTo(targetCF)",
        ]
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token,scope)
        self.assertLess(scope.index("Workspace:Blockcast"),
                        scope.index("Workspace:GetPartBoundsInBox"))
        self.assertLess(scope.index("Workspace:GetPartBoundsInBox"),
                        scope.index("craft:PivotTo(targetCF)"))
        self.assertNotIn("Vector3.new(8,2,11)",self.src)
        self.assertNotIn("craft:PivotTo(CFrame.new(point)*cf.Rotation)",scope)

    def test_no_duplicate_authority_and_same_rollback(self):
        for token in [
            'if not RunService:IsStudio() then return end',
            'MAX_CRAFT = 4','MAX_PARTS_PER_WORLD = 95',
            'if not currentCraftOwner(v.owner,mode,world,v.role) then',
            'if not root or not hum or hum.Health<=0 then return false end',
            'world:FindFirstChild("NeutralHorde")',
        ]:
            self.assertIn(token,self.src)
        for forbidden in ['Instance.new("RemoteEvent")',
                          'SetAttribute("EGGRUMBLE_NeutralKOs"',
                          'SetAttribute("EGGRUMBLE_Combo"',
                          "TakeDamage(", "DataStoreService"]:
            self.assertNotIn(forbidden,self.src)
        self.assertTrue(self.sidecar["original31_must_remain_byte_exact"])
        self.assertEqual(self.sidecar["source_count"],32)
        self.assertEqual(self.lock["optional_profile"]["original31_script_count"],31)

    def test_native_old_hull_mutant_present(self):
        a=native_cases(self.src)
        b=native_cases(self.src,True)
        self.assertIn("Vector3.new(24,8,19)",a)
        self.assertIn("Vector3.new(8,2,11)",b)
        self.assertNotIn("Vector3.new(24,8,19)",b)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--native",type=Path)
    parser.add_argument("--mutant",type=Path)
    args,_=parser.parse_known_args()
    if args.native and args.mutant:
        s=SOURCE_PATH.read_text(encoding="utf-8")
        args.native.write_text(native_cases(s),encoding="utf-8")
        args.mutant.write_text(native_cases(s,True),encoding="utf-8")
        print("GQ8_LSS_NATIVE_EXTRACTS_WRITTEN")
    else:
        unittest.main()
