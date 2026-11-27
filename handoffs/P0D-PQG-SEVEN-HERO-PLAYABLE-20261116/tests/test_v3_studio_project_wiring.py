"""Fail closed if V3 Studio Place omits a source module or wires parallel Game owners.

Static source/project validation only; this does not replace real Rojo/Studio QA.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "EGGRUMBLE_V3_STUDIO.project.json"
REQUIRED = {
    "EGGRUMBLE_CastleMatchRules": "EGGRUMBLE_CastleMatchRules.luau",
    "EGGRUMBLE_BotPathRouter": "EGGRUMBLE_BotPathRouter.luau",
    "EGGRUMBLE_BotActors": "EGGRUMBLE_BotActors.luau",
    "EGGRUMBLE_InteractionGuard": "EGGRUMBLE_InteractionGuard.luau",
    "EGGRUMBLE_SevenRoleCombat": "EGGRUMBLE_SevenRoleCombat.luau",
    "EGGRUMBLE_CombatBalance": "EGGRUMBLE_CombatBalance.luau",
    "EGGRUMBLE_SkillFX": "EGGRUMBLE_SkillFX.luau",
    "EGGRUMBLE_AttackGeometry": "EGGRUMBLE_AttackGeometry.luau",
    "EGGRUMBLE_ImpactFeedback": "EGGRUMBLE_ImpactFeedback.luau",
    "EGGRUMBLE_WeaponSilhouettes": "EGGRUMBLE_WeaponSilhouettes.luau",
    "EGGRUMBLE_DivineMantle": "EGGRUMBLE_DivineMantle.luau",
    "EGGRUMBLE_FieldItemPickups": "EGGRUMBLE_FieldItemPickups.luau",
    "EGGRUMBLE_RaidItemIntake": "EGGRUMBLE_RaidItemIntake.luau",
    "EGGRUMBLE_NeutralStoneGiant": "EGGRUMBLE_NeutralStoneGiant.luau",
    "EGGRUMBLE_BossSessionFence": "EGGRUMBLE_BossSessionFence.luau",
    "EGGRUMBLE_SwarmCombat": "EGGRUMBLE_SwarmCombat.luau",
    "EGGRUMBLE_MatchResultService": "EGGRUMBLE_MatchResultService.luau",
    "EGGRUMBLE_RoundReplay": "EGGRUMBLE_RoundReplay.luau",
    "EGGRUMBLE_LobbyCastleModesPreview": "EGGRUMBLE_LobbyCastleModesPreview.server.luau",
}


class TestStudioProjectWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = json.loads(PROJECT.read_text(encoding="utf-8"))
        cls.tree = cls.project["tree"]["ServerScriptService"]

    def test_exactly_one_studio_match_host_and_all_modules(self):
        self.assertEqual(self.project["tree"]["$className"], "DataModel")
        self.assertEqual(self.tree["$className"], "ServerScriptService")
        sources = {k: v["$path"] for k, v in self.tree.items() if k != "$className"}
        self.assertEqual(sources, REQUIRED)
        for name, source in REQUIRED.items():
            with self.subTest(name=name):
                self.assertTrue((ROOT / source).is_file(), source)
        self.assertNotIn("Game", sources)
        self.assertNotIn("SevenHeroArena", sources)
        self.assertNotIn("EGGRUMBLE_MassBattleCastlePreview", sources)

    def test_sibling_requires_all_wired(self):
        source_files = [
            "EGGRUMBLE_LobbyCastleModesPreview.server.luau",
            "EGGRUMBLE_BotActors.luau",
            "EGGRUMBLE_SevenRoleCombat.luau",
        ]
        module_names = set(REQUIRED) - {"EGGRUMBLE_LobbyCastleModesPreview"}
        for filename in source_files:
            src = (ROOT / filename).read_text(encoding="utf-8")
            required = re.findall(r'script\.Parent:WaitForChild\("([^"]+)"\)', src)
            for name in required:
                with self.subTest(script=filename, required=name):
                    self.assertIn(name, module_names)

    def test_local_combat_feedback_is_in_starter_player(self):
        local=self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["EGGRUMBLE_CombatFeel"]
        self.assertEqual(local["$path"],"EGGRUMBLE_CombatFeel.client.luau")
        self.assertTrue((ROOT/local["$path"]).is_file())
        gestures=self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["EGGRUMBLE_ProceduralSkills"]
        self.assertEqual(gestures["$path"],"EGGRUMBLE_ProceduralSkills.client.luau")
        self.assertTrue((ROOT/gestures["$path"]).is_file())

    def test_private_studio_only(self):
        game = (ROOT / REQUIRED["EGGRUMBLE_LobbyCastleModesPreview"]).read_text(encoding="utf-8")
        self.assertIn("if not RunService:IsStudio() then return end", game)
        self.assertNotIn("MarketplaceService", game)
        self.assertNotIn("DataStoreService", game)


if __name__ == "__main__":
    unittest.main()
