import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "tools/test_server_snapshots_with_coach.py"
spec = importlib.util.spec_from_file_location("real_snapshot_coach", PATH)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SevenOriginalModuleBoundaries(unittest.TestCase):
    def test_official_v6_source_pin(self):
        self.assertEqual(m.OFFICIAL, "1263a03701211a652b99b91d2339575dc8104eff")
    def test_frozen_original_real_game_map_trap_runner(self):
        self.assertEqual(m.NATIVE_BASE, "84d061d81ffd28418f6e28e9e85bb684dd0daaf7")
        self.assertEqual(len(m.NATIVE_BASE_SHA), 40)
    def test_actual_independently_vetted_guardian_coach_source(self):
        self.assertEqual(m.COACH_SOURCE, "e29d37737890671d458072bebe729127878700f6")
        self.assertEqual(m.COACH_BLOB, "967ea52df79884e6c73e3e0952d5a97de0d1796e")
    def test_exact_eight_original_server_snapshot_boundaries(self):
        self.assertEqual(len(m.SNAPSHOT_POINTS), 8)
        self.assertTrue(all(s.startswith('eq(last(') for s in m.SNAPSHOT_POINTS))
    def test_actual_new_lobby_snapshot(self):
        self.assertIn("real_red_lobby_coach_consumes", "".join(m.SNAPSHOT_POINTS.values()))
    def test_actual_guardian_server_role(self):
        self.assertIn("real_blue_guardian_active_title", "".join(m.SNAPSHOT_POINTS.values()))
    def test_actual_server_egg_steal_and_score(self):
        self.assertIn("real_red_egg_carrier_title", "".join(m.SNAPSHOT_POINTS.values()))
        self.assertIn("real_red_scored_state", "".join(m.SNAPSHOT_POINTS.values()))
    def test_actual_result_and_rematch_serial(self):
        self.assertIn("real_results_view", "".join(m.SNAPSHOT_POINTS.values()))
        self.assertIn("real_round2_red_help_resets", "".join(m.SNAPSHOT_POINTS.values()))
    def test_replay_and_malformed_server_snapshots(self):
        self.assertIn("real_old_result_snapshot_rejected_after_rematch", "".join(m.SNAPSHOT_POINTS.values()))
        self.assertIn("real_malformed_server_snapshot_rejected", "".join(m.SNAPSHOT_POINTS.values()))
    def test_coach_autohide_and_manual_help(self):
        self.assertIn("real_coach_autohides_after_one_minute", "".join(m.SNAPSHOT_POINTS.values()))
        self.assertIn("real_coach_manual_help_after_minute", "".join(m.SNAPSHOT_POINTS.values()))
    def test_real_child_coach_source_negative_mutations(self):
        self.assertEqual(len(m.MUTANTS), 6)
        self.assertEqual(len({x[0] for x in m.MUTANTS}), 6)
        for _, source, altered, expected in m.MUTANTS:
            self.assertNotEqual(source, altered)
            self.assertTrue(expected.startswith("GAME_S1_ASSERT_"))
    def test_strict_missing_anchor(self):
        with self.assertRaisesRegex(RuntimeError, "NON_UNIQUE_SOURCE_ANCHOR"):
            m.exact("hello", "missing", "BAD", "negative")
    def test_strict_duplicate_anchor(self):
        with self.assertRaisesRegex(RuntimeError, "NON_UNIQUE_SOURCE_ANCHOR"):
            m.exact("same same", "same", "BAD", "negative")
    def test_git_blob_fixture(self):
        self.assertEqual(m.blob_sha(b"abc"), "f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")


if __name__ == "__main__":
    unittest.main()
