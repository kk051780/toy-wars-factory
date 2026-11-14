"""Source-locked owner Game results-lobby recovery on full private78."""
from pathlib import Path
import tempfile,unittest
from rc_fastlane import apply_p0_results78 as repair
class Results78(unittest.TestCase):
 def test_output_no_new_game(self):
  self.assertEqual(repair.GAME,"server/Game.server.luau")
  self.assertNotIn('remote.OnServerEvent:Connect(',repair.NEW)
  self.assertEqual(repair.NEW.count(repair.REPAIR),1)
 def test_author_391_logic(self):
  for s in ('task.defer(function()','if p.Parent~=Players or match.phase~="LOBBY" then return end',
            'local refreshed=healthy(p)','pcall(function() p:LoadCharacter() end)'):
   self.assertIn(s,repair.NEW)
 def test_off_zero_write(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)
   self.assertFalse(repair.apply(p/"none",p/"none2",False))
   self.assertEqual(list(p.iterdir()),[])
 def test_missing_input_fails_without_writes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"bad").mkdir()
   with self.assertRaises(AssertionError):repair.apply(p/"bad",p/"out",True)
   self.assertFalse((p/"out").exists())
 def test_fail_closed_wrong_game(self):
  with self.assertRaises(AssertionError):repair.patch_game("local function tickRound()")
if __name__=="__main__":unittest.main()
