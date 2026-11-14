"""Smoke-test emergency source transforms against tracked original S1 game.

The live compiled RC66 has subsequent overlays, so this test is not a
replacement for latest-HEAD Rojo/Luau and human Studio FUN acceptance.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "releases" / "P0D_S1_KIDS_RC01" / "src"
s = importlib.util.spec_from_file_location("urgent", Path(__file__).with_name("apply_core_round_ready.py"))
u = importlib.util.module_from_spec(s)
s.loader.exec_module(u)


class TrackedCoreSmokeTest(unittest.TestCase):
    def test_original_game_server_anchor_compatibility(self):
        baseline = (ENGINE / "server/Game.server.luau").read_text("utf8")
        actual = u.patch_game(baseline)
        self.assertIn("roundReady[player] = false", actual)
        self.assertIn('if not everybodyReady() then return end', actual)
        self.assertEqual(actual.count('remote.OnServerEvent:Connect('), 1)
        self.assertNotIn('Instance.new("RemoteEvent")\nremote.Name', actual)

    def test_original_hud_anchor_compatibility(self):
        baseline = (ENGINE / "client/HUD.client.luau").read_text("utf8")
        actual = u.patch_hud(baseline)
        self.assertEqual(actual.count('VoluntaryReady'), 1)
        self.assertEqual(actual.count('FireServer({action="READY"'), 1)
        self.assertIn('readyButton.Visible = s.phase == "LOBBY" or s.phase == "COUNTDOWN"', actual)

    def test_original_config_900_seconds(self):
        baseline = (ENGINE / "shared/Config.luau").read_text("utf8")
        actual = u.patch_config(baseline)
        self.assertIn('MatchSeconds = 900', actual)
        self.assertNotIn('MatchSeconds = 360', actual)


if __name__ == "__main__":
    unittest.main()
