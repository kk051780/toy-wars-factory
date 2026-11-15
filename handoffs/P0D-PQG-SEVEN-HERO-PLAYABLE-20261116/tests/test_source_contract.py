"""Non-engine source contract tests. Not a substitute for Roblox Studio QA."""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "SevenHeroArena.server.luau"
ROLES = {
    "WARRIOR": "武神",
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

    def test_warlord_has_three_weapon_stances_and_distinct_divine_avatars(self):
        for term in ("P0DPreviewWarlordStance", "WarlordKatana", "WarlordSpear",
                     "WarlordFist", "P0DPreviewKami", "KamiStorm", "KamiFlame",
                     "KamiOrochi", "OrochiDivineHead_", 'role=="WARRIOR"'):
            with self.subTest(term=term):
                self.assertIn(term, self.source)
        # The mythological avatar is a short-lived effect, not a persistent pet.
        self.assertIn('Debris:AddItem(p,.55)', self.source)
        self.assertIn('P0DPreviewDivineActive', self.source)

    def test_beast_feed_choices_change_morphology_and_team_count(self):
        for term in ("BeastFeedGiant", "BeastFeedSplit", "BeastFeedArmor",
                     'mode=="GIANT"', 'mode=="SPLIT"', 'mode=="ARMORED"',
                     'then 3 else 1', 'ScaleTo(', "ArmorShell",
                     "BeastCompanion_", "GreatBeast_"):
            with self.subTest(term=term):
                self.assertIn(term, self.source)

    def test_world_choice_stations_do_not_change_game_authority(self):
        self.assertIn('ProximityPrompt', self.source)
        self.assertIn('P0DPreviewRole', self.source)
        self.assertIn('if p:GetAttribute("P0DPreviewRole")==role then', self.source)
        self.assertIn('if not RunService:IsStudio() then return end', self.source)
        self.assertNotIn('DataStoreService', self.source)

    def test_war_god_ranged_slash_and_duelist_bonus(self):
        for term in ('WarGodFlyingSlash', 'if num==1 then',
                     'P0DPreviewDivineActive', 'local boost=if divineActive then 1.55 else 1',
                     'WARRIOR={name="武神"', 'warHit(forward(root,30),9,38)'):
            with self.subTest(term=term):
                self.assertIn(term, self.source)

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
