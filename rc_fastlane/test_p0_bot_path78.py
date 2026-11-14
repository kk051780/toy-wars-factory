"""Native #402 17 authorized source replacements on #401 78 unique Bot module."""
from pathlib import Path
import tempfile,unittest
from rc_fastlane import apply_p0_bot_path78 as m
class BotPath78(unittest.TestCase):
 def test_author_blob_and_pairlineage(self):
  self.assertEqual(m.gitblob(m.AUTHOR.read_bytes()),m.AUTHOR_BLOB)
  self.assertEqual(len(m.authored_pairs()),16)
 def test_real_source_markers_preserved(self):
  pairs=m.authored_pairs()
  content="\n".join(x[1] for x in pairs)
  for expected in ("MAX_PENDING_PATH_TASKS=10",
       "releasePathLease(bot)","detourGoal=position+detour",
       "now<bot.detourUntil and gap>2.5"):
   self.assertIn(expected,content)
 def test_no_gameplay_authority_in_author_pairs(self):
  new="\n".join(x[1] for x in m.authored_pairs())
  for unwanted in ('FireServer(','OnServerEvent:Connect(','TakeDamage(',
    'DataStoreService','MarketplaceService','UpdateAsync('):
   self.assertNotIn(unwanted,new)
 def test_reject_bad_source_fail_closed(self):
  with self.assertRaises(AssertionError):m.patch_bot("not the bot")
 def test_off_zero_write(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   self.assertFalse(m.apply(root/"none",root/"new",False))
   self.assertFalse(list(root.iterdir()))
 def test_bad_parent_no_output(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder)
   with self.assertRaises(AssertionError):m.apply(root/"no",root/"new",True)
   self.assertFalse((root/"new").exists())
if __name__=="__main__":unittest.main()
