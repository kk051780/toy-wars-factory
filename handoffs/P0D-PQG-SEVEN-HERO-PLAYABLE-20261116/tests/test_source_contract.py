"""Non-engine source contract tests. Not a substitute for Roblox Studio QA."""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "SevenHeroArena.server.luau"
ROLES = {
    "WARRIOR": "戦士",
    "MAGE": "魔法使い",
    "NINJA": "暗殺者",
    "TRAPPER": "超能力者",
    "BUILDER": "マッドサイエンティスト",
    "BEAST": "魔獣使い",
    "ZOMBIE": "呪術師",
}

class TestSevenHeroStudioSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_all_roles_have_new_visible_name_and_loadout(self):
        for code, name in ROLES.items():
            with self.subTest(code=code):
                self.assertIn(code + '={name="' + name + '"', self.source)
        self.assertIn('local ROLE_ORDER = {"WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"}', self.source)
        self.assertIn('addTool(player,role,"A")', self.source)
        self.assertIn('addTool(player,role,"B")', self.source)
        self.assertIn('addTool(player,role,"C")', self.source)

    def test_every_role_has_gameplay_branch(self):
        for code in ROLES:
            with self.subTest(code=code):
                # Distinct role branches in normal and signature dispatch.
                self.assertGreaterEqual(self.source.count('role=="' + code + '"'), 2)
        for mechanic in ("TakeDamage(", "ProximityPrompt", "P0D_DUMMY", "Humanoid",
                         "EsperPortalA", "MadScientistUFO", "GreatBeast",
                         "UndeadMinion", "DarkWorldCreature", "WARRIOR"):
            self.assertIn(mechanic, self.source)

    def test_studio_only_non_authoritative(self):
        self.assertIn("RunService:IsStudio()", self.source)
        self.assertIn("if not RunService:IsStudio() then return end", self.source)
        self.assertNotIn("DataStoreService", self.source)
        self.assertNotIn("RemoteEvent", self.source)
        self.assertNotIn("TeleportService", self.source)
        self.assertIn('P0DPreviewTool', self.source)
        self.assertIn('P0DPreviewRole', self.source)
        self.assertIn('P0DPreviewCarryingEgg', self.source)

    def test_safe_preview_cooldowns_and_lifetime(self):
        for token in ("os.clock()", "Debris:AddItem(", "task.delay(", "PlayerRemoving",
                      "h.Health>0", "Tool", "getRig(player)"):
            self.assertIn(token, self.source)
        self.assertGreaterEqual(self.source.count("task.wait("), 2)

if __name__ == "__main__":
    unittest.main()
