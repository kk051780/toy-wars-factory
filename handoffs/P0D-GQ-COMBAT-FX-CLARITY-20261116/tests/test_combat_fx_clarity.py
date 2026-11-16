"""Isolated source/build-admission tests: not Studio/Android product evidence."""
import json
import pathlib
import re
import unittest

PACK = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = PACK.parent / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
MODEL = (PACK / "EGGRUMBLE_CombatFXBudget.luau").read_text(encoding="utf-8")
CLIENT = (PACK / "EGGRUMBLE_CombatFXClarity.client.luau").read_text(encoding="utf-8")
PROJECT = json.loads((PACK / "EGGRUMBLE_V3_FX_CLARITY.project.json").read_text(encoding="utf-8"))

def mapped(node):
    if isinstance(node, dict):
        if "$path" in node:
            yield node["$path"]
        for key, value in node.items():
            if key != "$path":
                yield from mapped(value)
    elif isinstance(node, list):
        for value in node:
            yield from mapped(value)

class TestCombatFXClarity(unittest.TestCase):
    def test_exact_21_author_plus_2_isolated_sources(self):
        paths = list(mapped(PROJECT))
        self.assertEqual(23, len(paths))
        self.assertEqual(23, len(set(paths)))
        original = [p for p in paths if p.startswith("../P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/")]
        isolated = sorted(p for p in paths if not p.startswith("../"))
        self.assertEqual(21, len(original))
        self.assertEqual(["EGGRUMBLE_CombatFXBudget.luau",
                          "EGGRUMBLE_CombatFXClarity.client.luau"], isolated)
        for path in paths:
            self.assertTrue((PACK / path).is_file(), path)

    def test_original_gameplay_map_unchanged(self):
        baseline = json.loads((ORIGINAL / "EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))
        current = [p.removeprefix("../P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/")
                   for p in mapped(PROJECT) if p.startswith("../")]
        self.assertEqual(sorted(mapped(baseline)), sorted(current))

    def test_starterplayer_only_and_no_second_game(self):
        scripts = PROJECT["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertIn("EGGRUMBLE_CombatFXBudget", scripts)
        self.assertIn("EGGRUMBLE_CombatFXClarity", scripts)
        server = PROJECT["tree"]["ServerScriptService"]
        self.assertNotIn("EGGRUMBLE_CombatFXClarity", server)

    def test_visual_write_only(self):
        self.assertIn("LocalTransparencyModifier", CLIENT)
        for text in ("FireServer(", "InvokeServer(", "RemoteEvent", "TakeDamage(",
                     "GetPartBoundsInRadius(", "Humanoid.Health", "CanCollide=",
                     "CanTouch=", "CanQuery=", "DataStore", "TeleportService"):
            self.assertNotIn(text, CLIENT, text)

    def test_explicit_server_confirmed_vfx_names_only(self):
        for name in ("ULTIMATE_", "FX_", "EGGRUMBLE_KO_BURST",
                     "WarGod_", "Mage_", "Assassin_", "Esper_", "MadScientist_",
                     "Beast_", "CurseMaster_"):
            self.assertIn(name, CLIENT)
        self.assertNotIn("ART_", CLIENT)
        self.assertNotIn("WeaponSilhouettes", CLIENT)

    def test_capped_duty_cycle(self):
        self.assertIn("MAX_TRACKED = 128", CLIENT)
        self.assertIn("UPDATE_SECONDS = 0.22", CLIENT)
        self.assertNotIn("GetDescendants(", CLIENT)
        self.assertIn("DescendantAdded:Connect", CLIENT)
        self.assertIn("DescendantRemoving:Connect", CLIENT)

    def test_touch_low_load_and_explicit_accessibility(self):
        self.assertIn("UserInputService.TouchEnabled", CLIENT)
        self.assertIn("EGGRUMBLE_ReducedEffects", CLIENT)
        self.assertIn("TOUCH_LIMITS", MODEL)
        self.assertIn("DESKTOP_LIMITS", MODEL)
        self.assertIn("active >= 72", MODEL)
        self.assertIn('kind == "ULTIMATE" and distance <= 85', MODEL)
        self.assertIn('kind == "KO" and distance <= 40', MODEL)

    def test_fail_open_for_unknown_names_and_invalid_distance(self):
        self.assertIn("if not limit then return false", MODEL)
        self.assertIn("distance ~= distance or distance < 0", MODEL)

    def test_rollback_is_two_source_removal(self):
        readme = (PACK / "README.md").read_text(encoding="utf-8")
        for name in ("EGGRUMBLE_CombatFXBudget", "EGGRUMBLE_CombatFXClarity", "ROLLBACK"):
            self.assertIn(name, readme)
        self.assertIn("STUDIO_NOT_TESTED", readme)

if __name__ == "__main__":
    unittest.main()
