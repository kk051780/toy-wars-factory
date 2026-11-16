"""Non-Roblox source-contract tests for the isolated post-elimination camera.
This deliberately does not claim Studio, Android or RC qualification.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "EGGRUMBLE_Spectate.client.luau"
PROJECT = ROOT.parent / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116" / "EGGRUMBLE_V3_STUDIO.project.json"

class SpectateContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SOURCE.read_text(encoding="utf-8")
        cls.project = json.loads(PROJECT.read_text(encoding="utf-8"))

    def test_real_client_wired_to_studio_project(self):
        scripts = self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertIn("EGGRUMBLE_EliminatedSpectate", scripts)
        self.assertEqual(
            scripts["EGGRUMBLE_EliminatedSpectate"]["$path"],
            "../P0D-PQG-SPECTATE-20261116-01/EGGRUMBLE_Spectate.client.luau",
        )
        self.assertTrue(SOURCE.exists())

    def test_no_game_authority_or_network(self):
        for forbidden in ("RemoteEvent", "FireServer(", "InvokeServer(", "DataStore",
                          "TakeDamage(", "Humanoid.Health =", "SetAttribute(",
                          "TeleportService", "MarketplaceService"):
            self.assertNotIn(forbidden, self.src)

    def test_no_active_play_camera_modification(self):
        self.assertRegex(self.src, r'GetAttribute\("EGGRUMBLE_Eliminated"\)\s*~=\s*true')
        self.assertIn("if not active then return end", self.src)
        self.assertIn("gui.Enabled = false", self.src)
        self.assertIn("camera.Focus = CFrame.new(focus)", self.src)

    def test_cleanup_and_camera_recovery(self):
        for required in ("restoreCamera()", "exitSpectate()", "getOwnArena()",
                         "candidate:FindFirstChild", "previousType", "CameraSubject",
                         'GetPropertyChangedSignal("CurrentCamera")'):
            self.assertIn(required, self.src)

    def test_exact_session_and_mobile_controls(self):
        for required in ('"TEAM"', '"BATTLE_ROYALE"', '"Castle_"',
                         '"StandardCore"', "Activated:Connect", "Enum.KeyCode.Left",
                         "Enum.KeyCode.Right"):
            self.assertIn(required, self.src)
        self.assertEqual(self.src.count('RunService.Heartbeat:Connect'), 1)
        self.assertIn("if elapsed < .5 then return end", self.src)

    def test_touch_targets_are_at_least_44_px(self):
        self.assertIn("UserInputService.TouchEnabled", self.src)
        self.assertIn("if touchLayout then 44 else 34", self.src)
        self.assertIn("if touchLayout then 44 else 30", self.src)
        self.assertIn('control("▶", if touchLayout then 204 else 166)', self.src)
        self.assertIn("gui.Enabled = false", self.src)

    def test_preserves_original_runtime_scripts(self):
        scripts = self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertIn("EGGRUMBLE_CombatFeel", scripts)
        self.assertIn("EGGRUMBLE_ProceduralSkills", scripts)
        server = self.project["tree"]["ServerScriptService"]
        self.assertIn("EGGRUMBLE_LobbyCastleModesPreview", server)
        self.assertIn("EGGRUMBLE_CastleMatchRules", server)

if __name__ == "__main__":
    unittest.main()
