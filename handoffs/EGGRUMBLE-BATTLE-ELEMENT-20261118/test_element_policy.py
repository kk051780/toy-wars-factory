"""Source-only safety and generated actual-Luau native coverage gate."""
import re
import unittest
from pathlib import Path

from make_native_cases import ELEMENTS, SOURCE, build, oracle

DIR = Path(__file__).resolve().parent

class ElementPolicyPreparation(unittest.TestCase):
    def test_exhaustive_8x8_unique_matrix(self):
        matrix = {(a, d): oracle(a, d) for a in ELEMENTS for d in ELEMENTS}
        self.assertEqual(len(matrix), 64)
        self.assertEqual(sum(1 for _, tag in matrix.values() if tag == "MUTUAL_COUNTER"), 2)
        self.assertEqual(sum(1 for _, tag in matrix.values() if tag == "STRONG_RESISTANCE"), 8)
        self.assertEqual(sum(1 for _, tag in matrix.values() if tag == "ADVANTAGE"), 6)
        self.assertEqual(sum(1 for _, tag in matrix.values() if tag == "RESISTED"), 6)
        self.assertTrue(all(0.65 <= mul <= 1.25 for mul, _ in matrix.values()))

    def test_native_uses_actual_script_not_duplicate_mock(self):
        s = SOURCE.read_text(encoding="utf-8")
        generated = build()
        mutant = build(mutant=True)
        self.assertIn(s.split("\nreturn Policy\n")[0], generated)
        self.assertIn("local P = Policy", generated)
        self.assertEqual(generated.count("MATCHUP_FAIL_"), 64)
        self.assertIn("MATCHUP_FAIL_FIRE_ICE", mutant)
        self.assertIn("if false and CYCLE[attack] == defend then", mutant)
        self.assertNotIn("if false and CYCLE[attack] == defend then", generated)

    def test_no_double_damage_authority(self):
        s = SOURCE.read_text(encoding="utf-8")
        for forbidden in ("Instance.new", "game:GetService", "Humanoid.Health", "TakeDamage(", "FireServer(", "OnServerEvent", "DataStoreService", "MarketplaceService"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, s)
        self.assertRegex(s, r"(?m)^return Policy$")
        self.assertEqual(s.count("function Policy.resolve("), 1)

    def test_cycle_has_one_unique_target_and_no_mythic_leak(self):
        from make_native_cases import CYCLE
        self.assertEqual(set(CYCLE), set(ELEMENTS[:6]))
        self.assertEqual(set(CYCLE.values()), set(ELEMENTS[:6]))
        self.assertEqual(set(CYCLE) & {"DIVINE", "CURSE"}, set())

if __name__ == "__main__":
    unittest.main()
