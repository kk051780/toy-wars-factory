#!/usr/bin/env python3
"""Guard the *existing* optional32 airborne expiry return against seven mutants.

Static source/negative-mutation gate only. A native Luau compile plus the
current true-31/32 Rojo pipeline is required before source admission; Studio
flight physics and Android performance remain NOT_TESTED.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "EGGRUMBLE_LandSeaSkyTraversal.server.luau"
SOURCE = SCRIPT.read_text(encoding="utf-8")
MARKER = "GQ8_LSS_FLIGHT_EXPIRY_SAFE_LANDING_20261118"


def expiry_clause(source):
    start = source.index("craft.Destroying:Connect(function()")
    end = source.index("data.alive=false", start)
    return source[start:end]


def flight_clause(source):
    chunk = expiry_clause(source)
    return chunk.split(MARKER, 1)[1]


def flight_guard_ok(clause):
    required = (
        "if active and data.flying then",
        "local pilot=data.lastPilot",
        "local ch=player.Character",
        'ch:FindFirstChild("HumanoidRootPart")',
        "pilot and pilot.Parent==ch and pilot.Health>0 and root",
        "pilot.Sit and seat.Occupant==pilot",
        "matchHuman(player,mode,world,role)",
        "(root.Position-craft:GetPivot().Position).Magnitude<28",
        "craft:GetPivot().Position.Y>y+FLIGHT_MIN_Y_ABOVE_GROUND-4",
        "safeMove(player,landDock.Position+Vector3.new(0,4,0),mode,world)",
    )
    return all(s in clause for s in required)


class FlightExpirySafety(unittest.TestCase):
    def test_air_rescue_is_inside_actual_debris_destroy_path(self):
        self.assertEqual(SOURCE.count(MARKER), 1)
        self.assertIn("Debris:AddItem(craft,VEHICLE_LIFETIME)", SOURCE)
        self.assertIn("VEHICLE_LIFETIME = 180", SOURCE)
        real = expiry_clause(SOURCE)
        self.assertTrue(flight_guard_ok(flight_clause(SOURCE)))
        self.assertLess(SOURCE.index("Debris:AddItem(craft,VEHICLE_LIFETIME)"),
                        SOURCE.index("craft.Destroying:Connect(function()"))
        self.assertLess(real.index(MARKER), real.index("safeMove(player,landDock.Position",
                                                                 real.index(MARKER)))
        self.assertLess(SOURCE.index(MARKER),
                        SOURCE.index("data.alive=false", SOURCE.index(MARKER)))

    def test_existing_sea_expiry_safety_unchanged_and_mutually_exclusive(self):
        real = expiry_clause(SOURCE)
        sea = real.split(MARKER, 1)[0]
        self.assertIn("if active and not data.flying then", sea)
        self.assertIn("if not standingOnDock then", sea)
        self.assertIn("craft:GetPivot().Position.Z>z+halfZ+10", sea)
        self.assertIn("safeMove(player,landDock.Position", sea)
        self.assertIn("if active and data.flying then", flight_clause(SOURCE))
        self.assertIn("if perUser[player.UserId]==data then perUser[player.UserId]=nil end",
                      SOURCE)

    def test_seven_independent_unsafe_mutants_fail_closed(self):
        clause = flight_clause(SOURCE)
        changes = (
            ("if active and data.flying then", "if active then"),
            ("pilot and pilot.Parent==ch and pilot.Health>0 and root",
             "pilot and root"),
            ("pilot.Sit and seat.Occupant==pilot", "true"),
            ("matchHuman(player,mode,world,role)", "true"),
            ("(root.Position-craft:GetPivot().Position).Magnitude<28", "true"),
            ("craft:GetPivot().Position.Y>y+FLIGHT_MIN_Y_ABOVE_GROUND-4", "true"),
            ("safeMove(player,landDock.Position+Vector3.new(0,4,0),mode,world)",
             "print('unsafe success')"),
        )
        self.assertEqual(len(changes), 7)
        for needle, replacement in changes:
            with self.subTest(unsafe_mutant=needle):
                self.assertIn(needle, clause)
                self.assertFalse(flight_guard_ok(clause.replace(needle, replacement, 1)))

    def test_exact_git_blob_locked_in_both_optional32_manifests(self):
        data = SCRIPT.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        manifest = json.loads((ROOT.parents[1] / "rc_fastlane" /
                               "EGGRUMBLE_V3_LSS_OPTIONAL32.json").read_text())
        lock = json.loads((ROOT / "GQ8_RC32_SOURCE_LOCK.json").read_text())
        self.assertEqual(manifest["added_source_git_blob"], blob)
        self.assertEqual(manifest["gq8_air_expiry_safe_landing"]["source_git_blob"], blob)
        self.assertEqual(lock["optional_profile"]["source_blob_sha"], blob)
        self.assertIn(MARKER, manifest["feature_ids"])
        self.assertEqual(manifest["source_count"], 32)
        self.assertEqual(lock["optional_profile"]["original31_script_count"], 31)
        self.assertTrue(manifest["original31_must_remain_byte_exact"])

    def test_no_new_game_authority_and_studio_only(self):
        self.assertIn("if not RunService:IsStudio() then return end", SOURCE)
        self.assertIn("matchHuman(player,mode,world,role)", flight_clause(SOURCE))
        self.assertIn("seat.Occupant==pilot", flight_clause(SOURCE))
        for forbidden in ('Instance.new("RemoteEvent")', "DataStoreService",
                          'Instance.new("Humanoid")', "TakeDamage(",
                          'SetAttribute("EGGRUMBLE_NeutralKOs"',
                          'SetAttribute("EGGRUMBLE_Combo"'):
            self.assertNotIn(forbidden, SOURCE)


if __name__ == "__main__":
    unittest.main()
