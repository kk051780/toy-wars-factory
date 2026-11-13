#!/usr/bin/env python3
"""Static contract checks only; never present as Roblox Studio runtime QA."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LUAU = ROOT / "src" / "CrystalCanyon.server.luau"
CATALOG = ROOT / "WCS_CATALOG.json"

class WCSContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = LUAU.read_text(encoding="utf-8")
        cls.data = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_six_worlds_and_twelve_neutral_characters(self):
        self.assertEqual(len(self.data["worlds"]), 6)
        self.assertEqual(len(self.data["characters"]), 12)
        ids = [x["id"] for x in self.data["worlds"] + self.data["characters"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_f01_c01_is_only_source_ready_pair(self):
        self.assertEqual([x["id"] for x in self.data["worlds"] if x["stage"] == "SOURCE"], ["WCS-F01"])
        self.assertEqual([x["id"] for x in self.data["characters"] if x["stage"] == "SOURCE"], ["WCS-C01"])

    def test_no_core_authority_or_purchases(self):
        without_comments = "\n".join(
            line.split("--", 1)[0] for line in self.src.splitlines()
        )
        for forbidden in ["DataStoreService", "MarketplaceService", "RemoteEvent", "RemoteFunction",
                          "GetAsync", "SetAsync", "UpdateAsync", "leaderstats", "TakeDamage"]:
            self.assertNotIn(forbidden, without_comments)

    def test_off_by_default_requires_anchor_and_attribute(self):
        self.assertIn('FindFirstChild("P0D_CrystalCanyonAnchor")', self.src)
        self.assertIn('GetAttribute("P0DWorldOptIn") ~= true', self.src)
        self.assertIn('FindFirstChild("P0D_WCS_CrystalCanyon")', self.src)

    def test_symmetric_npc_prompts_and_server_distance(self):
        self.assertIn('makeMole("MoguronWest", -32)', self.src)
        self.assertIn('makeMole("MoguronEast", 32)', self.src)
        self.assertIn('prompt.Triggered:Connect(function(player)', self.src)
        self.assertIn('(root.Position - torso.Position).Magnitude > 13', self.src)

    def test_safe_detour_and_non_disappearing_bridge(self):
        self.assertIn('"AlwaysOpenSafeRoute"', self.src)
        self.assertIn('"ShortcutBridge"', self.src)
        self.assertIn('"CrystalCanyonBottom"', self.src)
        self.assertIn('"ReturnStepEast_"', self.src)
        self.assertIn('"ReturnStep_"', self.src)

    def test_gate_timer_and_occupancy_aware_close(self):
        self.assertRegex(self.src, r'OPEN_SECONDS\s*=\s*14')
        self.assertRegex(self.src, r'REOPEN_COOLDOWN\s*=\s*4')
        self.assertIn('not playerIsInGateClosureZone()', self.src)
        self.assertIn('gate.CanCollide = not open', self.src)

    def test_gate_occupancy_does_not_cover_entire_shortcut_bridge(self):
        # A camper 20 studs down the bridge must not hold the timed gate open.
        self.assertIn("local function playerIsInGateClosureZone()", self.src)
        self.assertRegex(self.src, r"math[.]abs\(localPoint[.]X\) <= 3[.]5")
        self.assertNotIn("math.abs(localPoint.X) <= 27", self.src)

    def test_reopen_cooldown_starts_on_actual_close(self):
        # Delayed closure must not consume the four-second cooldown early.
        self.assertIn("if gateOpen and not open then", self.src)
        self.assertIn("nextOpenAllowed = os.clock() + REOPEN_COOLDOWN", self.src)
        self.assertIn("now < nextOpenAllowed", self.src)

    def test_no_studio_or_release_claim(self):
        self.assertEqual(self.data["release"], "S2+_CANDIDATE_ONLY")
        self.assertEqual(self.data["integration_gate"]["native_studio"], "NOT_TESTED")
        self.assertEqual(self.data["integration_gate"]["owner_fun"], "NOT_TESTED")

if __name__ == "__main__":
    unittest.main()
