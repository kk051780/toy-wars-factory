#!/usr/bin/env python3
"""GQ8 unique sea-craft lifetime rescue: verify scoped real Luau source.

Only the existing optional32 LSS Script changes; canonical31 is untouched.
These source/negative-mutant checks DO NOT establish Studio physics behavior.
"""
from pathlib import Path
import hashlib
import json
import unittest

SOURCE=(Path(__file__).resolve().parent /
        "EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")
MARKER="GQ8_LSS_CRAFT_EXPIRY_OFFSHORE_RESCUE_20261118"


def expiry_clause(source):
    assert source.count("craft.Destroying:Connect(function()")==1
    # Scope the sea-only contract to its own if-block. The adjacent new
    # airborne guard intentionally repeats owner/match/proximity checks;
    # counting those would let a removed SEA guard evade negative mutants.
    return source.split("craft.Destroying:Connect(function()",1)[1].split(
        "GQ8_LSS_FLIGHT_EXPIRY_SAFE_LANDING_20261118",1)[0]


def meets_contract(clause):
    required=(
        MARKER,
        "if active and not data.flying then",
        "local pilot=data.lastPilot",
        "local ch=player.Character",
        'ch:FindFirstChild("HumanoidRootPart")',
        "pilot and pilot.Parent==ch and pilot.Health>0 and root",
        "matchHuman(player,mode,world,role)",
        "(root.Position-craft:GetPivot().Position).Magnitude<28",
        "craft:GetPivot().Position.Z>z+halfZ+10",
        "for _,dock in pairs(offshorePads) do",
        "math.abs(root.Position.X-dock.Position.X)<=dock.Size.X/2-2",
        "math.abs(root.Position.Z-dock.Position.Z)<=dock.Size.Z/2-2",
        "if not standingOnDock then",
        "safeMove(player,landDock.Position+Vector3.new(0,4,0),mode,world)",
    )
    return all(x in clause for x in required)


class OffshoreExpiryRescue(unittest.TestCase):
    def test_actual_expiry_path(self):
        self.assertEqual(SOURCE.count(MARKER),1)
        self.assertIn("Debris:AddItem(craft,VEHICLE_LIFETIME)", SOURCE)
        self.assertIn("VEHICLE_LIFETIME = 180",SOURCE)
        clause=expiry_clause(SOURCE)
        self.assertTrue(meets_contract(clause))
        self.assertLess(clause.index("if active and not data.flying"),
                        clause.index("safeMove(player,landDock.Position"))
        self.assertLess(SOURCE.index("Debris:AddItem(craft,VEHICLE_LIFETIME)"),
                        SOURCE.index("craft.Destroying:Connect(function()"))
        self.assertLess(SOURCE.index("safeMove(player,landDock.Position",
                                             SOURCE.index("craft.Destroying:Connect(function()")),
                        SOURCE.index("data.alive=false", SOURCE.index("craft.Destroying:Connect(function()")))
        self.assertIn("if perUser[player.UserId]==data then perUser[player.UserId]=nil end",SOURCE)

    def test_fail_closed_negative_mutants(self):
        clause=expiry_clause(SOURCE)
        mutations=(
            ("if active and not data.flying then", "if active then"),
            ("pilot and pilot.Parent==ch and pilot.Health>0 and root",
             "pilot and pilot.Health>0 and root"),
            ("matchHuman(player,mode,world,role)", "true"),
            ("(root.Position-craft:GetPivot().Position).Magnitude<28","true"),
            ("craft:GetPivot().Position.Z>z+halfZ+10","true"),
            ("if not standingOnDock then","if true then"),
        )
        for before,after in mutations:
            with self.subTest(mutation=before):
                self.assertIn(before,clause)
                self.assertFalse(meets_contract(clause.replace(before,after,1)))

    def test_optional_profile_source_lock_is_real_git_blob(self):
        src=Path(__file__).resolve().parent / "EGGRUMBLE_LandSeaSkyTraversal.server.luau"
        data=src.read_bytes()
        blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        manifest=json.loads((src.parents[2] / "rc_fastlane" /
                             "EGGRUMBLE_V3_LSS_OPTIONAL32.json").read_text())
        self.assertEqual(manifest["added_source_git_blob"],blob)
        self.assertEqual(manifest["gq8_craft_expiry_offshore_rescue"]["source_git_blob"],blob)
        self.assertIn(MARKER, data.decode("utf-8"))
        self.assertIn(MARKER, manifest["feature_ids"])

    def test_dismount_guard_and_single_authority_preserved(self):
        self.assertIn("not hum and v.lastPilot", SOURCE)
        self.assertIn("and not dismountOnDock",SOURCE)
        self.assertIn("not matchHuman(v.owner,mode,world,v.role)",SOURCE)
        for forbidden in (
            'Instance.new("RemoteEvent")',
            'DataStoreService',
            'Instance.new("Humanoid")',
            'TakeDamage(',
        ):
            self.assertNotIn(forbidden,SOURCE)


if __name__=="__main__":
    unittest.main()
