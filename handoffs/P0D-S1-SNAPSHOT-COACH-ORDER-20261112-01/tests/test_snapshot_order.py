import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("order",P/"tools/test_snapshot_order.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class MonotonicOriginalSnapshotSource(unittest.TestCase):
    def test_official_original_pin(self):
        self.assertEqual(m.RC,"1263a03701211a652b99b91d2339575dc8104eff")
    def test_upstream_actual_seven_source_pin(self):
        self.assertEqual(m.UPSTREAM,"24061fd7fc165c506f9a862ba48ceaf80b6345bb")
    def test_original_game_blob(self):
        self.assertEqual(m.GAME_ORIGINAL_SHA,"7c5229f600f17537bc1bbbb0b96b6a2435875374")
    def test_original_coach_blob(self):
        self.assertEqual(m.COACH_ORIGINAL_SHA,"967ea52df79884e6c73e3e0952d5a97de0d1796e")
    def test_candidate_game_ordinal_limited_to_snapshot(self):
        self.assertEqual(len(m.GAME_PATCHES),2)
        self.assertIn("snapshotUpdateId += 1",m.GAME_PATCHES[0][1])
        self.assertIn("updateId = snapshotUpdateId",m.GAME_PATCHES[1][1])
    def test_candidate_coach_state_and_serial_rule(self):
        self.assertEqual(len(m.COACH_PATCHES),4)
        self.assertIn("lastUpdateId: number",m.COACH_PATCHES[0][1])
        self.assertIn("wholeNumber(id)",m.COACH_PATCHES[2][1])
        self.assertIn("id <= state.lastUpdateId",m.COACH_PATCHES[2][1])
    def test_original_lobby_role_reordering(self):
        self.assertIn("real_same_serial_old_lobby_rejected","".join(m.EXTRA_BY_ANCHOR.values()))
    def test_original_egg_carrier_vs_score_reordering(self):
        self.assertIn("real_same_serial_late_carrier_rejected","".join(m.EXTRA_BY_ANCHOR.values()))
    def test_round_transition_never_resets_update_id(self):
        self.assertIn("real_update_sequence_never_reset_at_rematch","".join(m.EXTRA_BY_ANCHOR.values()))
    def test_bad_fractional_and_string_id(self):
        val="".join(m.EXTRA_BY_ANCHOR.values())
        self.assertIn("real_fractional_id_rejected",val)
        self.assertIn("real_string_id_rejected",val)
    def test_unversioned_backward_compatibility(self):
        val="".join(m.EXTRA_BY_ANCHOR.values())
        self.assertIn("real_fresh_legacy_unversioned_accepted",val)
        self.assertIn("real_unversioned_after_version_rejected",val)
    def test_six_deliberately_unsafe_mutants(self):
        self.assertEqual(len(m.MUTANTS),6)
        self.assertEqual({t[1] for t in m.MUTANTS},{"Game","Coach"})
    def test_nonunique_anchor_is_fatal(self):
        with self.assertRaisesRegex(RuntimeError,"NON_UNIQUE"):
            m.exact("double double","double","a","negative")
    def test_sha_git_blob(self):
        self.assertEqual(m.blob_sha(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")

if __name__=="__main__":
    unittest.main()
