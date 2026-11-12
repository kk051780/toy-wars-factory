import importlib.util
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"tools/roster_cycle_native.py"
spec=importlib.util.spec_from_file_location("roster_cycle_native", SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RealGameRosterCycle(unittest.TestCase):
    def test_original_rc_pin(self):
        self.assertEqual(m.OFFICIAL,"1263a03701211a652b99b91d2339575dc8104eff")
    def test_upstream_six_source_fixture_pin(self):
        self.assertEqual(m.UPSTREAM,"84d061d81ffd28418f6e28e9e85bb684dd0daaf7")
        self.assertRegex(m.UPSTREAM_SHA,r"^[a-f0-9]{40}$")
    def test_nonduplicate_mutants(self):
        self.assertEqual(len(m.MUTANTS),5)
        self.assertEqual(len({x[0] for x in m.MUTANTS}),5)
    def test_replay_not_reset_contract(self):
        self.assertIn("old_seq_cannot_attack_after_new_round",m.POST)
        self.assertIn("seq_counter_reset_between_rounds",{x[0] for x in m.MUTANTS})
    def test_departing_carrier_returns_egg(self):
        self.assertIn("carrier_departure_restores_egg",m.PRE)
    def test_solo_lobby_not_active(self):
        self.assertIn("solo_after_results_is_lobby",m.POST)
        self.assertIn("solo_cannot_start",m.POST)
    def test_countdown_cancellation(self):
        self.assertIn("countdown_aborted_on_departure",m.POST)
    def test_new_lobby_after_second_player_arrives(self):
        self.assertIn("replacement_starts_fresh_countdown",m.POST)
    def test_team_balance_two_vs_two(self):
        self.assertIn('two_red_players',m.PRE)
        self.assertIn('two_blue_players',m.PRE)
    def test_source_anchor_missing_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"ANCHOR_MISSING_OR_DUPLICATED"):
            m.exact("a","missing","new","negative")
    def test_source_anchor_duplicate_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"ANCHOR_MISSING_OR_DUPLICATED"):
            m.exact("a a","a","new","negative")
    def test_actual_git_blob_fixture(self):
        self.assertEqual(m.blob_sha(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")

if __name__=="__main__":
    unittest.main()
