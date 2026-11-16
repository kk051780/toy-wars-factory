"""Isolated safety/source contracts: no Studio or Android product claims."""
import json
import pathlib
import unittest

PACK = pathlib.Path(__file__).resolve().parents[1]
ORIGINAL = PACK.parent / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
POLICY = (PACK / "EGGRUMBLE_CombatFXBudget.luau").read_text(encoding="utf-8")
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
    def test_21_author_sources_exact_and_2_local_only(self):
        paths = list(mapped(PROJECT))
        self.assertEqual(23, len(paths))
        self.assertEqual(23, len(set(paths)))
        original = [p for p in paths if p.startswith("../P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/")]
        isolated = sorted(p for p in paths if not p.startswith("../"))
        self.assertEqual(21, len(original))
        self.assertEqual(["EGGRUMBLE_CombatFXBudget.luau",
                          "EGGRUMBLE_CombatFXClarity.client.luau"], isolated)
        for p in paths:
            self.assertTrue((PACK / p).is_file(), p)

    def test_original_owner_map_and_host_unchanged(self):
        baseline = json.loads((ORIGINAL / "EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8"))
        current = [p.removeprefix("../P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/")
                   for p in mapped(PROJECT) if p.startswith("../")]
        self.assertEqual(sorted(mapped(baseline)),sorted(current))
        self.assertEqual("EGGRUMBLE_V3_COMBAT_FX_CLARITY_SOURCE_ONLY",PROJECT["name"])

    def test_starterplayer_only_no_second_game(self):
        scripts = PROJECT["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        self.assertIn("EGGRUMBLE_CombatFXBudget",scripts)
        self.assertIn("EGGRUMBLE_CombatFXClarity",scripts)
        self.assertNotIn("EGGRUMBLE_CombatFXClarity",PROJECT["tree"]["ServerScriptService"])

    def test_local_visual_only(self):
        self.assertIn("LocalTransparencyModifier",CLIENT)
        for text in ("FireServer(", "InvokeServer(", "RemoteEvent", "TakeDamage(",
                     "GetPartBoundsInRadius(", "Humanoid.Health", "CanCollide=",
                     "CanTouch=", "CanQuery=", "DataStore", "TeleportService",
                     "Instance.new(", "PlayerGui", "SoundService"):
            self.assertNotIn(text,CLIENT,text)

    def test_all_core_ko_ultimate_excluded(self):
        self.assertIn('kind ~= "SECONDARY"',POLICY)
        self.assertNotIn('"FX_"',CLIENT)
        self.assertNotIn('"ULTIMATE_"',CLIENT)
        self.assertNotIn('"EGGRUMBLE_KO_BURST"',CLIENT)

    def test_seven_original_subtype_prefixes(self):
        for name in ("WarGod_", "Mage_", "Assassin_", "Esper_", "MadScientist_",
                     "Beast_", "CurseMaster_"):
            self.assertIn(name,CLIENT)
        self.assertNotIn('"ART_"',CLIENT)

    def test_only_original_v3_arena_parts(self):
        for name in ("TEAM_Arena", "BATTLE_ROYALE_Arena","EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"):
            self.assertIn('"'+name+'"',CLIENT)
        self.assertIn("isOriginalArenaFX(inst)",CLIENT)
        self.assertIn("isOriginalArenaFX(part)",CLIENT)

    def test_bounded_event_handler_and_restoration(self):
        self.assertIn("MAX_TRACKED = 128",CLIENT)
        self.assertIn("UPDATE_SECONDS = 0.22",CLIENT)
        self.assertNotIn("GetDescendants(",CLIENT)
        self.assertIn("DescendantAdded:Connect",CLIENT)
        self.assertIn("DescendantRemoving:Connect",CLIENT)
        self.assertIn("part.LocalTransparencyModifier = record.original",CLIENT)

    def test_far_threshold_hysteresis_and_near_guard(self):
        for name in ("NEAR_PROTECTION = 40", "HYSTERESIS = 9",
                     "TOUCH_FAR = 85", "DESKTOP_FAR = 130",
                     "active >= 96", "active >= 60"):
            self.assertIn(name,POLICY)
        self.assertIn("record.hidden",CLIENT)

    def test_unknown_or_invalid_distance_fail_open(self):
        self.assertIn('kind ~= "SECONDARY"',POLICY)
        self.assertIn("distance ~= distance",POLICY)
        self.assertIn("distance == math.huge",POLICY)
        self.assertIn("distance < 0",POLICY)

    def test_optin_rollback_and_separate_native_functional_spec(self):
        readme=(PACK/"README.md").read_text(encoding="utf-8")
        self.assertIn("ROLLBACK",readme)
        self.assertIn("STUDIO_NOT_TESTED",readme)
        self.assertIn("EGGRUMBLE_CombatFXBudget.spec.luau",readme)
        self.assertTrue((PACK/"tests/EGGRUMBLE_CombatFXBudget.spec.luau").is_file())

if __name__ == "__main__":
    unittest.main()
