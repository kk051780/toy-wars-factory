import importlib.util
from pathlib import Path
import unittest

SRC=Path(__file__).resolve().parents[1]/"tools/seven_safe_real_native.py"
spec=importlib.util.spec_from_file_location("s1_seven", SRC)
x=importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)

class SevenSafeRealOriginalNativeCross(unittest.TestCase):
    def test_frozen_seven_safe_source(self):
        self.assertEqual(x.SEVEN,"d319b56d1552713da482189048473f266c7b3fdc")
    def test_six_safe_predecessor(self):
        self.assertEqual(x.SIX,"65785c2e3b9bc37a6962f9ace128fbfcbb670901")
    def test_exact_old_RC_frozen(self):
        self.assertEqual(x.OFFICIAL,"1263a03701211a652b99b91d2339575dc8104eff")
    def test_real_prior_native_engine_sources(self):
        self.assertEqual(x.NATIVE,"24061fd7fc165c506f9a862ba48ceaf80b6345bb")
        self.assertEqual(len(x.NATIVE_BLOB),40)
    def test_real_game_and_guardian_git_blobs(self):
        self.assertEqual(x.GAME_SEVEN_BLOB,"e684ca79b8f5ed279bcdf033f4118bf77d552abb")
        self.assertEqual(x.COACH_SEVEN_BLOB,"d8dda6b1781375612c123f8c83b6f23fe45d09f1")
    def test_manifest_fixed_thirty_seven_source(self):
        self.assertEqual(x.MANIFEST_BLOB,"24d36159e91f927fdfbf38a74048072ab31387a7")
    def test_new_real_player_removing_cross_interaction(self):
        self.assertIn("seven_safe_pre_exit_active",x.ADDED_PRE_EXIT)
        self.assertIn("seven_safe_departure_results_snapshot_consumed",x.ADDED_POST_EXIT)
        self.assertIn("seven_safe_stale_active_after_departure_rejected",x.ADDED_POST_EXIT)
    def test_interoperability_original_game_and_coach(self):
        self.assertEqual(len(x.MUTANT_EXPECTED),6)
        self.assertIn("real_same_serial_old_lobby_rejected",x.MUTANT_EXPECTED)
    def test_strict_source_anchor_disallows_missing(self):
        with self.assertRaisesRegex(RuntimeError,"NON_UNIQUE"):
            x.exact("abc","xy","x","missing")
    def test_strict_source_anchor_disallows_duplicate(self):
        with self.assertRaisesRegex(RuntimeError,"NON_UNIQUE"):
            x.exact("hi hi","hi","z","duplicate")
    def test_git_blob_reference_sha(self):
        self.assertEqual(x.blob(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")
    def test_no_real_studio_claims_in_test_scope(self):
        self.assertNotIn("Studio",x.ADDED_PRE_EXIT+x.ADDED_POST_EXIT)

if __name__=="__main__":
    unittest.main()
