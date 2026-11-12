import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/"tools/check_hud_native.py"
spec=importlib.util.spec_from_file_location("actual_hud",PATH)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FullActualHudClientOrdering(unittest.TestCase):
    def test_frozen_7_safe_game(self):
        self.assertEqual(m.PARENT,"6cc131d3de06fe8799d00f475fc446a526e4b2c4")
    def test_official_hud_blob(self):
        self.assertEqual(m.BASE_HUD_BLOB,"b3d3996c40c690e19007a36a847d5b10fc6a1522")
    def test_candidate_hud_blob(self):
        self.assertEqual(m.CANDIDATE_BLOB,"50823390853989ccdda78e28c16ea4757bbe0715")
    def test_original_server_has_corresponding_update_field(self):
        self.assertEqual(m.BASE_GAME_BLOB,"e684ca79b8f5ed279bcdf033f4118bf77d552abb")
    def test_exact_three_hunks(self):
        self.assertEqual(len(m.PATCHES),3)
    def test_keep_touch_controls_and_boss_visual(self):
        self.assertIn('UDim2.new(1, -140, 1, -110)',
            (Path(__file__).resolve().parents[1]/"candidate/src/client/HUD.client.luau").read_text())
        self.assertIn("BOSS_VISUAL",m.LUAU_TESTS)
    def test_same_serial_role_replay(self):
        self.assertIn("late_same_serial_role_rejected",m.LUAU_TESTS)
    def test_results_not_rolled_back(self):
        self.assertIn("late_score_does_not_rollback",m.LUAU_TESTS)
    def test_cross_round_global_ordinal(self):
        self.assertIn("old_cross_round_update_id_rejected",m.LUAU_TESTS)
    def test_legacy_protocol_support(self):
        self.assertIn("legacy_replay_after_upgrade_rejected",m.LUAU_TESTS)
        self.assertIn("fresh_legacy_lobby",m.LUAU_TESTS)
    def test_six_original_source_mutations(self):
        self.assertEqual(len(m.MUTANTS),6)
        self.assertEqual(len({x[0] for x in m.MUTANTS}),6)
        for row in m.MUTANTS:
            self.assertTrue(row[3].startswith("HUD_S1_ASSERT_"))
    def test_no_source_silent_patch(self):
        with self.assertRaisesRegex(RuntimeError,"NON_UNIQUE_PATCH"):
            m.exact("a a","a","bad","no")
    def test_no_source_patch_missing(self):
        with self.assertRaisesRegex(RuntimeError,"NON_UNIQUE_PATCH"):
            m.exact("text","missing","bad","no")
    def test_git_blob_fixture(self):
        self.assertEqual(m.blob(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")

if __name__=="__main__":
    unittest.main()
