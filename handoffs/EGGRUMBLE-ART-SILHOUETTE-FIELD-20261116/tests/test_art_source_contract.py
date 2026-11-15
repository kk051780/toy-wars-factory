"""Source-only regression for additive EGGRUMBLE studio art.

Run: python3 -m unittest discover -s handoffs/EGGRUMBLE-ART-SILHOUETTE-FIELD-20261116/tests
This is NOT a Luau compiler, real Studio device, or art/FUN approval.
"""
from pathlib import Path
import re
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERO = (ROOT / "EGGRUMBLE_HeroSilhouetteArt.server.luau").read_text(encoding="utf-8")
FIELD = (ROOT / "EGGRUMBLE_FlagshipFieldArt.server.luau").read_text(encoding="utf-8")
ROLES = {"WARRIOR", "MAGE", "NINJA", "TRAPPER", "BUILDER", "BEAST", "ZOMBIE"}


def executable_lines(src: str) -> str:
    return "\n".join(s for s in src.splitlines() if not s.lstrip().startswith("--"))


class VisualLayersSourceContract(unittest.TestCase):
    def test_studio_private_only(self):
        for src in (HERO, FIELD):
            self.assertIn('game:GetService("RunService")', src)
            self.assertIn("if not RunService:IsStudio() then return end", src)

    def test_all_seven_distinct_role_silhouettes(self):
        self.assertEqual(set(re.findall(r'role=="([A-Z]+)"', HERO)), ROLES)
        for role in ROLES:
            self.assertIn(role + "={base=Color3.fromRGB(", HERO)
        self.assertIn("GetAttributeChangedSignal", HERO)
        self.assertIn('"P0DPreviewRole"', HERO)

    def test_no_dynamic_gameplay_authority(self):
        forbidden = (
            "DataStoreService", "RemoteEvent", "RemoteFunction", "TeleportService",
            "TakeDamage(", "LoadAnimation(", "DamageCastle(", "depositEggs(",
            "takeEggs(", "Coins", "Robux", "ProcessReceipt", "Humanoid.Health=",
            "Terrain:Fill", "Terrain:Clear", ".CanCollide=true",
        )
        for src in (executable_lines(HERO), executable_lines(FIELD)):
            for token in forbidden:
                self.assertNotIn(token, src, f"new art may not own {token}")

    def test_art_parts_cannot_block_paths(self):
        for src in (HERO, FIELD):
            for token in ("p.CanCollide=false", "p.CanTouch=false", "p.CanQuery=false", "p.CastShadow=false"):
                self.assertIn(token, src)
        self.assertNotIn("Touched:Connect", HERO + FIELD)
        self.assertNotIn("BillboardGui", executable_lines(HERO + FIELD))

    def test_fixed_low_mobile_budgets(self):
        self.assertIn("PART_BUDGET_PER_SUBJECT = 13", HERO)
        self.assertIn("made>=PART_BUDGET_PER_SUBJECT", HERO)
        self.assertIn("MAX_VISUAL_PARTS_PER_ARENA = 320", FIELD)
        self.assertIn("MAX_CASTLE_PARTS = 11", FIELD)
        self.assertIn("used>=MAX_CASTLE_PARTS", FIELD)
        self.assertIn("(budgets[arena] or 0)>=MAX_VISUAL_PARTS_PER_ARENA", FIELD)
        self.assertLessEqual(16 * 11 + 3 * 4 * 2 + 20 * 4 + 10 * 2 + 2 * 2, 320)

    def test_only_existing_v3_arena_decorated(self):
        for token in ("TEAM_Arena", "BATTLE_ROYALE_Arena", "TacticalBattlefield", "StandardCore"):
            self.assertIn(token, FIELD)
        self.assertIn("EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW", FIELD)
        self.assertIn("EGGRUMBLE_CastleArt_VisualOnly", FIELD)
        self.assertNotIn('Instance.new("SpawnLocation")', FIELD)
        self.assertNotIn('Instance.new("Terrain")', FIELD)

    def test_rojo_previews_pin_only_existing_author_sources(self):
        projects = {
            "EGGRUMBLE_V3_ART_STUDIO.project.json": 7,
            "EGGRUMBLE_SEVEN_HERO_ART_STUDIO.project.json": 2,
        }
        for filename, expected in projects.items():
            project = json.loads((ROOT / filename).read_text(encoding="utf-8"))
            nodes = project["tree"]["ServerScriptService"]
            self.assertEqual(len(nodes) - 1, expected)  # one $className entry
            for name, spec in nodes.items():
                if name == "$className":
                    continue
                resolved = (ROOT / spec["$path"]).resolve()
                self.assertTrue(resolved.is_file(), f"broken Rojo source: {filename}:{name}")

    def test_reversible_visual_only_namespaces(self):
        self.assertIn('"EGGRUMBLE_RoleVisuals"', HERO)
        self.assertIn('"EGGRUMBLE_BotVisuals"', HERO)
        self.assertIn('"EGGRUMBLE_FlagshipLandscape_VisualOnly"', FIELD)
        self.assertIn('existing:Destroy()', HERO)
        self.assertNotIn('script.Parent:WaitForChild("Game")', HERO + FIELD)


if __name__ == "__main__":
    unittest.main()
