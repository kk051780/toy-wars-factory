"""Source-locked adaptation of #390 to full P0D private77, not engine acceptance."""
import tempfile, unittest
from pathlib import Path
from rc_fastlane import apply_p0_motion78 as m
class Motion78(unittest.TestCase):
 def test_author_source_exact(self):
  s=m.author_source()
  self.assertEqual(m.gitblob(s),m.MOTION_PIN)
 def test_wont_change_authority(self):
  s=m.author_source()
  for x in (b"TakeDamage(",b"OnServerEvent",b"FireServer(",b"DataStoreService"):
   self.assertNotIn(x,s)
 def test_watched_art_lineage(self):
  self.assertEqual(m.ORIGINAL_ART_PIN,"ed5cd56789abc4a7bc8ee3a44b8982aae4f3ff62")
  self.assertEqual(m.DEST,"client/P0DNeutralMotion.client.luau")
  self.assertIn(b"P0D_ART_MINION_V1",m.author_source())
 def test_off_does_not_touch_any_files(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)
   self.assertFalse(m.compose(r/"missing",r/"not-made",False))
   self.assertEqual(list(r.iterdir()),[])
 def test_bad_parent77_writes_nothing(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/"bad").mkdir()
   with self.assertRaises(AssertionError):m.compose(r/"bad",r/"out",True)
   self.assertFalse((r/"out").exists())
if __name__=="__main__":unittest.main()
