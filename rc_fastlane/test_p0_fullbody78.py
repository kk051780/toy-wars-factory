"""P0D full9 NPC costume #392 author exact and backward-compatible 78 source."""
import tempfile,unittest
from pathlib import Path
from rc_fastlane import apply_p0_fullbody78 as full
class FullBody78(unittest.TestCase):
 def test_source_author_pin(self):
  self.assertEqual(full.gitblob(full.AUTHOR.read_bytes()),full.ORIGINAL_BLOB)
 def test_compat_without_nonexistent_new_remote(self):
  src=full.derived_source().decode("utf8")
  self.assertIn('horde:FindFirstChild("P0D_ART_COMBAT_SIGNAL_V1")',src)
  self.assertNotIn('horde:WaitForChild("P0D_ART_COMBAT_SIGNAL_V1")',src)
  self.assertIn('if not cueConnection then',src)
  self.assertIn('RealDamagePopup',src)
 def test_all_41_and_9_body_parts(self):
  src=full.derived_source().decode("utf8")
  block=src.split("local watchedParts = {",1)[1].split("\n}\n",1)[0]
  import re
  matches=re.findall(r'"ART_[A-Z_0-9-]+"',block)
  self.assertEqual(len(matches),41)
  self.assertIn("MAX_ACTIVE_COSMETIC_PARTS = 104",src)
  self.assertIn('local copy = source:Clone()',src)
  self.assertIn('visual.original.LocalTransparencyModifier = 1',src)
 def test_no_gameplay_side_effect(self):
  src=full.derived_source().decode("utf8")
  for bad in ("TakeDamage(","FireServer(","OnServerEvent:","DataStoreService","MarketplaceService"):
   self.assertNotIn(bad,src)
 def test_off_zero_write(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)
   self.assertFalse(full.apply(p/"none",p/"none2",False))
   self.assertFalse(list(p.iterdir()))
 def test_bad_input_has_no_outputs(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp);(p/"bad").mkdir()
   with self.assertRaises(AssertionError):full.apply(p/"bad",p/"out",True)
   self.assertFalse((p/"out").exists())
if __name__=="__main__":unittest.main()
