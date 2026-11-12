import importlib.util
from pathlib import Path
import unittest

THIS = Path(__file__).resolve().parents[1]/"tools/validate_remove_order_native.py"
spec=importlib.util.spec_from_file_location("remove_order",THIS)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RemovingOrderSourceQA(unittest.TestCase):
    def test_current_official_pin(self):
        self.assertEqual(m.OFFICIAL,"1263a03701211a652b99b91d2339575dc8104eff")
    def test_exact_original_game_pin(self):
        self.assertEqual(m.GAME_ORIGINAL_BLOB,"7c5229f600f17537bc1bbbb0b96b6a2435875374")
    def test_frozen_actual_upstream_roster(self):
        self.assertEqual(m.UPSTREAM,"664284d6ec29741060bead3bd0df66e9ea6b1e76")
        self.assertRegex(m.UPSTREAM_BLOB,r"^[a-f0-9]{40}$")
    def test_candidate_is_not_official_game(self):
        self.assertNotEqual(m.GAME_ORIGINAL_BLOB,m.GAME_CANDIDATE_BLOB)
    def test_leave_callback_before_and_after(self):
        self.assertIn("Players.users={pRed,pBlue,pFour}",m.PRE_ADD)
        self.assertIn("Players.PlayerRemoving:Fire(pAfter)",m.PRE_ADD)
        self.assertIn("Players.PlayerRemoving:Fire(pReturn)",m.POST_ADD)
    def test_four_luau_source_mutants(self):
        self.assertEqual(len(m.MUTANTS),4)
        self.assertEqual(len({x[0] for x in m.MUTANTS}),4)
    def test_no_main_or_live_publish_operation(self):
        self.assertNotIn("HttpService",m.NEW)
        self.assertNotIn("DataStore",m.NEW)
        self.assertNotIn("Publish",m.NEW)
    def test_exclude_only_departing_person(self):
        self.assertIn("other ~= player and getTeamName(other) == side",m.NEW)
    def test_zero_teammates_only_ends(self):
        self.assertIn("if teammates == 0 then",m.NEW)
        self.assertNotIn("teamCount(side)",m.NEW)
    def test_exact_patch_integrity_negative_duplicate(self):
        with self.assertRaisesRegex(RuntimeError,"UNSAFE_ANCHOR"):
            m.exactly("x x","x","y","negative")
    def test_exact_patch_integrity_negative_missing(self):
        with self.assertRaisesRegex(RuntimeError,"UNSAFE_ANCHOR"):
            m.exactly("x","y","z","negative")
    def test_standard_git_blob(self):
        self.assertEqual(m.gitblob(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")
if __name__=="__main__":
    unittest.main()
