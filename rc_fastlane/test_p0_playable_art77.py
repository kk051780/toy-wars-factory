import tempfile,unittest
from pathlib import Path
from rc_fastlane import apply_p0_playable_art77 as art
class Private77(unittest.TestCase):
 def test_all_pins(self):
  self.assertEqual(len(art.additions()),7)
 def test_no_castle_or_game_duplication(self):
  add=art.additions()
  self.assertNotIn("server/CastleBattlefield.server.luau",add)
  self.assertNotIn("server/Game.server.luau",add)
 def test_sea_ground_repair_is_present(self):
  self.assertIn("server/H1SeaGroundRepair.server.luau",art.additions())
 def test_off_is_total_no_write(self):
  with tempfile.TemporaryDirectory() as d:
   x=Path(d);self.assertFalse(art.apply(x/"none",x/"out",False))
   self.assertEqual(list(x.iterdir()),[])
 def test_invalid_incoming70_fails_without_write(self):
  with tempfile.TemporaryDirectory() as d:
   x=Path(d);(x/"bad").mkdir()
   with self.assertRaises(AssertionError): art.apply(x/"bad",x/"out",True)
   self.assertFalse((x/"out").exists())
if __name__=="__main__":unittest.main()
