#!/usr/bin/env python3
"""OFFLINE exact-source safety handoff tests. NOT a Roblox Studio engine test."""
import hashlib
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
ORIGINAL = REPO / "handoffs/P0D-WCS-FLOATING-CRYSTAL-RC55-20261114-01/rc56_rebase/src/WCS_Integrated.server.luau"
FIXED = HERE.parents[1] / "src/WCS_Integrated_Safe.server.luau"
OLD_BLOB = "5eb76749414c33c11eb70310b2d1c59c1f945c21"

REPLACEMENTS = [
  [
    "-- Original author WCS CrystalCanyon body below is source-byte-preserved.",
    "-- Original author WCS body retained except the exact PR295 gate closure and cooldown safety fix."
  ],
  [
    "local function playerIsOnBridge()",
    "local function playerIsInGateClosureZone()"
  ],
  [
    "math.abs(localPoint.X) <= 27",
    "math.abs(localPoint.X) <= 3.5"
  ],
  [
    "local function setGateOpen(open)\n    gateOpen = open",
    "local function setGateOpen(open)\n    -- PR295: grant cooldown at the actual CLOSE, including delayed closure.\n    if gateOpen and not open then\n        nextOpenAllowed = os.clock() + REOPEN_COOLDOWN\n    end\n    gateOpen = open"
  ],
  [
    "not playerIsOnBridge()",
    "not playerIsInGateClosureZone()"
  ]
]

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\\0" + data).hexdigest()

class WCSGateSafetySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_bytes = ORIGINAL.read_bytes()
        cls.old = cls.old_bytes.decode("utf-8")
        cls.safe_bytes = FIXED.read_bytes()
        cls.safe = cls.safe_bytes.decode("utf-8")

    def test_github_original_source_is_immutable(self):
        self.assertEqual(git_blob(self.old_bytes), OLD_BLOB)

    def test_only_exact_five_patch_operations(self):
        result = self.old
        for before, after in REPLACEMENTS:
            self.assertEqual(result.count(before), 1)
            result = result.replace(before, after, 1)
        self.assertEqual(result, self.safe)

    def test_gate_occupancy_is_narrow(self):
        self.assertIn("math.abs(localPoint.X) <= 3.5", self.safe)
        self.assertNotIn("math.abs(localPoint.X) <= 27", self.safe)
        self.assertIn("not playerIsInGateClosureZone()", self.safe)

    def test_actual_close_initiates_cooldown(self):
        self.assertIn("if gateOpen and not open then", self.safe)
        self.assertIn("nextOpenAllowed = os.clock() + REOPEN_COOLDOWN", self.safe)

    def test_studio_only_and_boot_off(self):
        self.assertIn('if not RunService:IsStudio() then', self.safe)
        self.assertIn('P0D_RC_ENABLE_WCS_F01_C01', self.safe)

    def test_safe_existing_map_attachment(self):
        self.assertIn("SKY_WALKWAY", self.safe)
        self.assertIn("CFrame.new(0,32,-23)", self.safe)
        self.assertIn("physical SkyV5 approach missing", self.safe)

    def test_single_additive_world_only(self):
        for forbidden in ['Instance.new("RemoteEvent")', "DataStoreService", "MarketplaceService", "UpdateAsync"]:
            self.assertNotIn(forbidden, self.safe)
        self.assertIn("P0D_WCS_CrystalCanyon", self.safe)

    def test_symmetric_moguron_and_detour(self):
        self.assertIn('makeMole("MoguronWest", -32)', self.safe)
        self.assertIn('makeMole("MoguronEast", 32)', self.safe)
        self.assertIn('AlwaysOpenSafeRoute', self.safe)
        self.assertIn('OPEN_SECONDS = 14', self.safe)
        self.assertIn('REOPEN_COOLDOWN = 4', self.safe)

if __name__ == "__main__":
    unittest.main()
