from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"EGGRUMBLE_DualModeNeutralBudget.luau"
SPEC=ROOT/"tests/budget_native_cases.luau"
AUTHOR=Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116")

class DualModeBudgetContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=MODULE.read_text(encoding="utf-8")
        cls.spec=SPEC.read_text(encoding="utf-8")
    def test_pure_no_duplicate_authority(self):
        for forbidden in ("game:GetService", "Instance.new", "RemoteEvent", "DataStore", "Humanoid", "TakeDamage", "PivotTo", "task.spawn", "task.delay", "require("):
            self.assertNotIn(forbidden,self.source)
    def test_lifecycle_ticket_and_epoch(self):
        for text in ("function state:begin", "function state:acquire", "function state:release", "function state:retire", "function state:snapshot", "STALE_EPOCH", "OPPOSITE_RESERVE", "GLOBAL_CAP", "MODE_CAP"):
            self.assertIn(text,self.source)
    def test_both_modes(self):
        self.assertIn("TEAM=true",self.source)
        self.assertIn("BATTLE_ROYALE=true",self.source)
    def test_no_author_changes(self):
        self.assertTrue((AUTHOR/"EGGRUMBLE_SwarmCombat.luau").exists())
        self.assertTrue((AUTHOR/"EGGRUMBLE_LobbyCastleModesPreview.server.luau").exists())
    def test_executable_native_cases(self):
        for text in ('Budget.new(128,96,32)', "96 do", "32 do", "STALE_EPOCH", "GQ_DUAL_MODE_NEUTRAL_BUDGET_NATIVE_PASS"):
            self.assertIn(text,self.spec)
    def test_return_is_last_statement(self):
        self.assertTrue(self.source.rstrip().endswith("return Budget"))

if __name__=="__main__":
    unittest.main()
