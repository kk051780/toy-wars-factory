"""Conservative source and mutation guard for the actual C3 private Game delta."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
BUILD=(ROOT/"tools/build_48_c3_safety.py").read_text("utf-8")
RAY=(ROOT/"src/GateVisualRaySafeC3.luau").read_text("utf-8")
SOLO=(ROOT/"src/StudioSoloLatchRulesC3.luau").read_text("utf-8")

def valid_query_transitions(code):
    a="door.CanCollide = false\n        door.CanQuery = false"
    b="door.CanQuery = true\n        door.CanCollide = true"
    return a in code and b in code and code.index(a)<code.index(b)

class C3Safety(unittest.TestCase):
    def test_ray_property_change_order(self):
        self.assertTrue(valid_query_transitions(RAY))
    def test_negative_mutation_ray_open_must_not_query(self):
        self.assertFalse(valid_query_transitions(RAY.replace(
            "door.CanQuery = false","door.CanQuery = true")))
    def test_negative_mutation_ray_close_order(self):
        self.assertFalse(valid_query_transitions(RAY.replace(
            "door.CanQuery = true\n        door.CanCollide = true",
            "door.CanCollide = true\n        door.CanQuery = true")))
    def test_render_uses_authoritative_gate_snapshot(self):
        self.assertIn("snapshot.passable == true",RAY)
        self.assertIn("door.Transparency = open",RAY)
        self.assertNotIn("OnServerEvent",RAY)
    def test_old_exact_sources_pinned(self):
        for s in ('ORIGINAL_VISUAL_BLOB="f94b495725dc7c53e35e35b4e05e753a9a9dd794"',
                  'ORIGINAL_SOLO_BLOB="a0576d25c78d3c6341e8119853d646c36b42345e"'):
            self.assertIn(s,BUILD)
    def test_solo_active_gated_to_start_of_round(self):
        self.assertIn("wasSoloAtRoundStart == true",SOLO)
        self.assertIn("and Solo.isPractice(isStudio,players,red,blue)",SOLO)
    def test_game_latch_initialized_at_reset_round(self):
        self.assertIn("match.serial += 1\\n",BUILD)
        self.assertIn("match.studioSolo = StudioSoloGateRules.isPractice(",BUILD)
        self.assertIn('match.studioSolo = false',BUILD)
    def test_old_original_lobby_and_countdown_still_original(self):
        self.assertIn('g.count("StudioSoloGateRules.canStart(")==2',BUILD)
        self.assertNotIn('Solo:FireServer',BUILD)
    def test_old_single_authority_two_horde_calls(self):
        self.assertIn('g.count("s2HeistGate:beforeHit(horde)")==2',BUILD)
        self.assertIn('g.count("remote.OnServerEvent:Connect(")==1',BUILD)
        self.assertIn('g.count("s2HeistGate:startRound(")==1',BUILD)
    def test_exact_48_sources_and_45_unchanged(self):
        self.assertIn("assert len(new)==EXPECTED_TOTAL",BUILD)
        self.assertIn('assert changed==["server/Game.server.luau","server/GateVisual.luau",',BUILD)
        self.assertIn('ORIGINAL_V7="70714a081a555d716832bb6a640611e05a1f3eca"',BUILD)
    def test_public_release_refused_by_contract(self):
        for bad in ["Instance.new(\"RemoteEvent\")","DataStoreService","MarketplaceService"]:
            self.assertNotIn(bad,SOLO)
        self.assertIn("no_public_solo",BUILD)
        self.assertIn('"roblox_engine_studio":"NOT_TESTED"',BUILD)
    def test_no_manipulative_hidden_timer(self):
        self.assertNotIn("task.wait",RAY)
        self.assertNotIn("task.spawn",RAY)

if __name__=="__main__":unittest.main()
