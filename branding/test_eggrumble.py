"""Regression checks for EGGRUMBLE title rename. Run: python -m unittest branding.test_eggrumble"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD_PATH = ROOT / "releases/P0D_S1_KIDS_RC01/src/client/HUD.client.luau"
ROJO_PATH = ROOT / "releases/P0D_S1_KIDS_RC01/default.project.json"

class EGGRUMBLEBrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hud = HUD_PATH.read_text(encoding="utf-8")
        cls.project = json.loads(ROJO_PATH.read_text(encoding="utf-8"))

    def test_exact_new_product_title_in_hud_surfaces(self):
        for surface in (
            'top.Text = "EGGRUMBLE · 接続中..."',
            'return "EGGRUMBLE｜準備中',
            'return "EGGRUMBLE｜開始まで ',
            'return "EGGRUMBLE｜" .. resultLine(s)',
        ):
            with self.subTest(surface=surface):
                self.assertIn(surface, self.hud)
        self.assertNotIn("TRAP RAIDERS", self.hud)
        self.assertNotIn("Trap Raiders", self.hud)

    def test_rojo_project_name_is_new_and_tree_is_not_renamed(self):
        self.assertEqual(self.project["name"], "EGGRUMBLE_S1_CHAT_RC01")
        tree = self.project["tree"]
        self.assertIn("TrapRaidersShared", tree["ReplicatedStorage"])
        self.assertIn("TrapRaidersS1", tree["ServerScriptService"])
        scripts = tree["StarterPlayer"]["StarterPlayerScripts"]
        self.assertIn("TrapRaidersHUD", scripts)
        self.assertIn("TrapRaidersCoach", scripts)
        self.assertEqual(scripts["TrapRaidersHUD"]["$path"], "src/client/HUD.client.luau")

    def test_network_api_and_active_hud_unmodified(self):
        self.assertIn('WaitForChild("TrapRaidersS1Remote")', self.hud)
        self.assertIn('gui.Name = "TrapRaidersS1HUD"', self.hud)
        self.assertIn('remote:FireServer(', self.hud)
        self.assertIn('attack.Visible = s.phase == "ACTIVE"', self.hud)
        self.assertIn('top.Text = string.format(', self.hud)
        self.assertNotIn('DataStoreService', self.hud)

if __name__ == "__main__":
    unittest.main()
