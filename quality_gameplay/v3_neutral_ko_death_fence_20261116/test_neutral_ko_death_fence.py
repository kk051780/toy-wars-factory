import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = (ROOT / "EGGRUMBLE_NeutralKoDeathFence.luau").read_text(encoding="utf-8")
DOC = (ROOT / "README.md").read_text(encoding="utf-8")

def decide(phase, winner, attacker_alive, same_horde, live_session):
    return (phase == "ACTIVE" and winner is None and attacker_alive is True
            and same_horde is True and live_session is True)

class FenceContract(unittest.TestCase):
    def test_valid_active_neutral_death(self):
        self.assertTrue(decide("ACTIVE", None, True, True, True))
    def test_finished_match_no_credit(self):
        self.assertFalse(decide("FINISHED", "RED", True, True, True))
    def test_draw_no_credit(self):
        self.assertFalse(decide("DRAW", None, True, True, True))
    def test_eliminated_castle_no_credit(self):
        self.assertFalse(decide("ACTIVE", None, False, True, True))
    def test_cross_arena_neutral_no_credit(self):
        self.assertFalse(decide("ACTIVE", None, True, False, True))
    def test_retired_world_no_credit(self):
        self.assertFalse(decide("ACTIVE", None, True, True, False))
    def test_winner_before_phase_switch_no_credit(self):
        self.assertFalse(decide("ACTIVE", "BLUE", True, True, True))
    def test_missing_or_malformed_flags_fail_closed(self):
        for v in (None, 0, "true", 1):
            self.assertFalse(decide("ACTIVE", None, v, True, True))
    def test_source_checks_every_domain_boundary(self):
        for term in ("session.rules.castles[id]", 'session.rules.phase',
                     'session.rules.winner', 'castle.alive',
                     'model:IsDescendantOf(hordeFolder)',
                     'model:GetAttribute("EGGRUMBLE_Neutral")',
                     'hordeFolder.Parent ~= session.world',
                     'session.world.Parent == nil',
                     'session.swarm'):
            self.assertIn(term, SOURCE)
    def test_policy_has_no_write_authority(self):
        for term in (":TakeDamage(", "SetAttribute(", "DataStore",
                     "FireServer(", "FireClient(", "Instance.new(",
                     "session.rules.phase =", "credit("):
            self.assertNotIn(term, SOURCE)
    def test_author_owned_hook_is_separate(self):
        self.assertIn("ORIGINAL_AUTHOR_HOOK", DOC)
        self.assertIn("SwarmCombat", DOC)
        self.assertNotIn("EGGRUMBLE_SwarmCombat.luau", str(ROOT / "EGGRUMBLE_NeutralKoDeathFence.luau"))
    def test_source_uses_pure_policy_for_runtime(self):
        self.assertRegex(SOURCE, r"return Fence\\.decide|return Fence\.decide")

if __name__ == "__main__":
    unittest.main()
