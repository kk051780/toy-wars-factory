"""P0 Game+HUD source-only 1human SCORE vote Classic guard quality regressions."""
import tempfile,unittest
from pathlib import Path
from rc_fastlane import apply_p0_solo78 as s
class Solo78(unittest.TestCase):
 def test_only_game_and_hud_updated(self):
  self.assertEqual(s.GAME,"server/Game.server.luau")
  self.assertEqual(s.HUD,"client/HUD.client.luau")
  self.assertEqual(s.ID,"FB005_SOLO_FIVE_EGG_BOTLESS_MODE_GUARD_QA_V1")
 def test_author_mode_guard_source_pin(self):
  self.assertIn('#Players:GetPlayers()>1 and chosenMode==ModeVote.SCORE',s.NEW)
  self.assertIn('EXPERIMENTAL_FIVE_EGG_MODE',s.NEW)
 def test_hud_no_new_overlay(self):
  self.assertIn("local function phaseText(s): string",s.HUD_NEW)
  self.assertNotIn('Instance.new("ScreenGui")',s.HUD_NEW)
  self.assertIn('ソロ：通常卵戦＋AI5体',s.HUD_NEW)
 def test_old_anchor_single_game(self):
  with self.assertRaises(AssertionError):s.patch_game("random game")
 def test_off_writes_nothing(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);self.assertFalse(s.compose(p/"none",p/"out",False))
   self.assertEqual(list(p.iterdir()),[])
 def test_bad_78_parent_refused(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/"bad").mkdir()
   with self.assertRaises(AssertionError):s.compose(p/"bad",p/"out",True)
   self.assertFalse((p/"out").exists())
if __name__=="__main__":unittest.main()
