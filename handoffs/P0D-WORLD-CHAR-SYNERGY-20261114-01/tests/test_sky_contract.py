#!/usr/bin/env python3
"""WCS F02 isolated static contract checks (not actual Roblox engine tests)."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SKY = ROOT / "src" / "InvertedSkyLab.server.luau"

class SkyLabSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SKY.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.src.splitlines() if not line.lstrip().startswith("--"))

    def test_explicit_opt_in_and_duplicate_rejection(self):
        self.assertIn('FindFirstChild("P0D_InvertedSkyAnchor")', self.code)
        self.assertIn('GetAttribute("P0DWorldOptIn") ~= true', self.code)
        self.assertIn('FindFirstChild("P0D_WCS_InvertedSkyLab")', self.code)

    def test_symmetric_owl_interactions(self):
        self.assertIn('createOwl("FukuroruWest", -62)', self.code)
        self.assertIn('createOwl("FukuroruEast", 62)', self.code)
        self.assertIn("prompt.Triggered:Connect(function(player)", self.code)
        self.assertIn("(root.Position - body.Position).Magnitude > 13", self.code)

    def test_permanent_ground_and_stair_route(self):
        self.assertIn('"AlwaysOpenGroundRoute"', self.code)
        self.assertIn('"WestSafeStair_" .. i', self.code)
        self.assertIn('"EastSafeStair_" .. i', self.code)
        self.assertIn('"SkyWalkway"', self.code)

    def test_wind_has_finite_duration_and_cooldowns(self):
        self.assertIn("WIND_SECONDS = 20", self.code)
        self.assertIn("REARM_SECONDS = 4", self.code)
        self.assertIn("PAD_COOLDOWN_SECONDS = 3", self.code)
        self.assertIn("if now < windUntil or now < nextWind then", self.code)

    def test_launch_is_server_verified(self):
        self.assertIn("Players:GetPlayerFromCharacter(character)", self.code)
        self.assertIn("(root.Position - spec.part.Position).Magnitude > 10", self.code)
        self.assertIn("humanoid.Health <= 0 or humanoid.Sit or root.Anchored", self.code)
        self.assertIn("lastLaunch[player.UserId] = now", self.code)
        self.assertIn("root.AssemblyLinearVelocity =", self.code)

    def test_fall_rescue_goes_to_same_side(self):
        self.assertIn('"FallRecoveryFloor"', self.code)
        self.assertIn("localPosition.X < 0 and -55 or 55", self.code)
        self.assertIn("lastRecovery[player.UserId] = now", self.code)

    def test_does_not_claim_game_server_authority(self):
        for forbidden in ["DataStoreService", "MarketplaceService", "RemoteEvent",
                          "RemoteFunction", "SetAsync", "GetAsync", "UpdateAsync",
                          "leaderstats", "TakeDamage"]:
            self.assertNotIn(forbidden, self.code)

    def test_clear_per_player_tables_on_exit(self):
        self.assertIn("Players.PlayerRemoving:Connect(function(player)", self.code)
        self.assertIn("lastLaunch[player.UserId] = nil", self.code)
        self.assertIn("lastRecovery[player.UserId] = nil", self.code)

if __name__ == "__main__":
    unittest.main()
