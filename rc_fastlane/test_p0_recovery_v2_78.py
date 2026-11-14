"""Author 393 actual source, Game-only patch, fail-closed write-isolation test."""
import unittest,tempfile
from pathlib import Path
from rc_fastlane import apply_p0_recovery_v2_78 as m
class RecoveryV2(unittest.TestCase):
    def test_author_source_exact(self):
        self.assertEqual(m.gitblob(m.AUTHOR.read_bytes()),m.AUTHOR_BLOB)
    def test_real_guarded_scheduler(self):
        s=m.author_helper()
        for term in ("Players.CharacterAutoLoads","player.Character~=originalCharacter",
                "lobbyRecoveryPending[player]","task.delay(grace,",
                "task.delay(2,","number < 3"):
            self.assertIn(term,s)
    def test_single_lobby_and_results_owner(self):
        self.assertIn("scheduleLobbyRecovery(p)",m.RESULTS_NEW)
        self.assertIn("scheduleLobbyRecovery(entrant)",m.OBSERVER_NEW)
        self.assertNotIn("LoadCharacter",m.RESULTS_NEW+m.OBSERVER_NEW)
    def test_invalid_game_rejected(self):
        with self.assertRaises(AssertionError):m.patch_game("game")
    def test_off_writes_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertFalse(m.apply(root/"bad",root/"candidate",False))
            self.assertEqual(list(root.iterdir()),[])
    def test_missing_parent_raises_without_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(AssertionError):m.apply(root/"bad",root/"candidate",True)
            self.assertFalse((root/"candidate").exists())
if __name__=="__main__": unittest.main()
