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
    "EGGRUMBLE_SwarmCombat": "EGGRUMBLE_SwarmCombat.luau",
    "EGGRUMBLE_LobbyCastleModesPreview": "EGGRUMBLE_LobbyCastleModesPreview.server.luau",
}


class TestStudioProjectWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = json.loads(PROJECT.read_text(encoding="utf-8"))
        cls.tree = cls.project["tree"]["ServerScriptService"]

    def test_exactly_one_studio_match_host_and_five_modules(self):
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
        ]
        module_names = set(REQUIRED) - {"EGGRUMBLE_LobbyCastleModesPreview"}
        for filename in source_files:
            src = (ROOT / filename).read_text(encoding="utf-8")
            required = re.findall(r'script\.Parent:WaitForChild\("([^"]+)"\)', src)
            for name in required:
                with self.subTest(script=filename, required=name):
                    self.assertIn(name, module_names)

    def test_private_studio_only(self):
        game = (ROOT / REQUIRED["EGGRUMBLE_LobbyCastleModesPreview"]).read_text(encoding="utf-8")
        self.assertIn("if not RunService:IsStudio() then return end", game)
        self.assertNotIn("MarketplaceService", game)
        self.assertNotIn("DataStoreService", game)


if __name__ == "__main__":
    unittest.main()
