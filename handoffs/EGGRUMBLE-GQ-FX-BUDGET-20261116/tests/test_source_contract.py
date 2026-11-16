import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
AUTHOR = ROOT.parent / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
class SourceContract(unittest.TestCase):
    def test_source_is_isolated(self):
        src = (ROOT / "client/EGGRUMBLE_ClientFXBudget.client.luau").read_text()
        for banned in ("FireServer(", "InvokeServer(", "DataStoreService", "Humanoid:TakeDamage", "WalkSpeed=", "CanCollide="):
            self.assertNotIn(banned, src)
        self.assertIn("RunService:IsStudio()", src)
        self.assertIn("LocalTransparencyModifier", src)
        self.assertIn("script.Destroying", src)
    def test_source_exact_project_23(self):
        obj = json.loads((ROOT / "EGGRUMBLE_GQ_FX_STUDIO.project.json").read_text())
        self.assertEqual(obj["tree"]["$className"], "DataModel")
        paths = []
        def walk(x):
            if isinstance(x, dict):
                if "$path" in x: paths.append((ROOT / x["$path"]).resolve(strict=True))
                else:
                    for key, item in x.items():
                        if not key.startswith("$"): walk(item)
        walk(obj["tree"])
        self.assertEqual(len(paths), 23)
        self.assertEqual(len(set(paths)), 23)
        original = json.loads((AUTHOR / "EGGRUMBLE_V3_STUDIO.project.json").read_text())
        expected = []
        def originals(x):
            if isinstance(x, dict):
                if "$path" in x: expected.append((AUTHOR / x["$path"]).resolve(strict=True))
                else:
                    for k, v in x.items():
                        if not k.startswith("$"): originals(v)
        originals(original["tree"])
        self.assertEqual(len(expected), 21)
        self.assertTrue(set(expected).issubset(set(paths)))
        self.assertEqual(len(set(paths)-set(expected)), 2)
    def test_all_seven_real_v3_secondary_fx_names(self):
        rules = (ROOT / "client/EGGRUMBLE_FXBudgetRules.luau").read_text()
        author = (AUTHOR / "EGGRUMBLE_SkillFX.luau").read_text()
        for name in ("WarGod_FlyingSlash","Mage_CrystalStorm","Assassin_ShadowAfterimage","Esper_PsiOrbit","MadScientist_RailShot","Beast_FangClaw","CurseMaster_SoulFlame"):
            self.assertIn('"' + name + '"', author)
            self.assertIn(name + "=true", rules)
        for protected in ("FLASH", "RING", "ULTIMATE"):
            self.assertNotIn(protected + "=true", rules)
    def test_no_duplicate_game_or_hud(self):
        project = (ROOT / "EGGRUMBLE_GQ_FX_STUDIO.project.json").read_text()
        self.assertEqual(project.count("EGGRUMBLE_LobbyCastleModesPreview.server.luau"), 1)
        self.assertEqual(project.count("EGGRUMBLE_ClientFXBudget.client.luau"), 1)
if __name__ == "__main__": unittest.main()
