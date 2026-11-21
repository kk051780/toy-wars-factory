"""Source-level fade/stream recovery checks for original #982 A route only.
No Roblox engine, screenshot, FPS or ART_PASS claim.
"""
from pathlib import Path
import unittest

SRC = Path(__file__).with_name("EGGRUMBLE_CastleFoundationMatte.client.luau")

def inspect(s: str) -> None:
    required = [
        "local LOD_FADE_START = 150",
        "local wanted: {[BasePart]: number} = {}",
        "wanted[ranked[i].core] = ranked[i].distance",
        "decoration.folder.Parent ~= core",
        "stone.Parent ~= decoration.folder",
        "if existing and not decorIntact(core, existing) then clear(core) end",
        "local distance = wanted[core]",
        "local fade = math.clamp((distance - LOD_FADE_START) /",
        "(MAX_DISTANCE_STUDS - LOD_FADE_START), 0, 1)",
        "stone.Transparency = fade",
        "local PARTS_PER_CASTLE = 8",
        "if UserInputService.TouchEnabled then 2 else 3",
        "stone.CanCollide = false",
        "stone.CanTouch = false",
        "stone.CanQuery = false",
        "stone.CastShadow = false",
    ]
    for token in required:
        if s.count(token) != 1:
            raise ValueError("RED_FADE_OR_REPAIR_MISSING_" + token)
    if s.count('Instance.new("WedgePart")') != 1 or s.count("track(") != 5:
        raise ValueError("RED_EXTRA_PARTS_OR_SIGNALS")
    if "RenderStepped" in s or "FireServer" in s or "Enum.Material.Neon" in s:
        raise ValueError("RED_AUTHORITY_OR_GLOW")

class FadeRepairTests(unittest.TestCase):
    def test_exact_source_contract(self):
        inspect(SRC.read_text(encoding="utf-8"))

    def test_distance_envelope(self):
        def opacity(dist):
            return min(1, max(0, (dist - 150) / (190 - 150)))
        xs = [-500, 0, 149, 150, 160, 170, 180, 189, 190, 500]
        actual = [opacity(x) for x in xs]
        self.assertEqual(actual[:4], [0, 0, 0, 0])
        self.assertAlmostEqual(opacity(170), .5)
        self.assertAlmostEqual(opacity(190), 1.0)
        self.assertEqual(actual, sorted(actual))
        self.assertTrue(all(0 <= x <= 1 for x in actual))

    def test_source_mutation_negatives(self):
        s = SRC.read_text(encoding="utf-8")
        mutants = [
            ("local LOD_FADE_START = 150", "local LOD_FADE_START = 0"),
            ("wanted[ranked[i].core] = ranked[i].distance", "wanted[ranked[i].core] = 0"),
            ("stone.Parent ~= decoration.folder", "false"),
            ("decoration.folder.Parent ~= core", "false"),
            ("if existing and not decorIntact(core, existing) then clear(core) end", "if false then clear(core) end"),
            ("stone.Transparency = fade", "stone.Transparency = 0"),
            ("local fade = math.clamp((distance - LOD_FADE_START) /", "local fade = (distance - LOD_FADE_START) /"),
            ("(MAX_DISTANCE_STUDS - LOD_FADE_START), 0, 1)", "(MAX_DISTANCE_STUDS - LOD_FADE_START)"),
            ('stone.CanCollide = false', 'stone.CanCollide = true'),
        ]
        for before, after in mutants:
            self.assertIn(before, s)
            with self.subTest(mutant=before), self.assertRaises(ValueError):
                inspect(s.replace(before, after, 1))

if __name__ == "__main__":
    unittest.main()
