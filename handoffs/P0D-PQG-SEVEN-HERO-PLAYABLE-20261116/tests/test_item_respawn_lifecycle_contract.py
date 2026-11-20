"""ITEM respawn lifecycle: prevent one-use-only dead field and post-match respawns."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ItemRespawn(unittest.TestCase):
 def test_reusable_in_active_match(self):
  s=(ROOT/"EGGRUMBLE_FieldItemPickups.luau").read_text()
  for line in ('local RESPAWN_SECONDS=35','consumed[id]=true','prompt.Enabled=false','part.Transparency=1;part.CanQuery=false','task.delay(RESPAWN_SECONDS,function()','if not matchActive() or not part.Parent then return end','consumed[id]=nil','part.Transparency=0;part.CanQuery=true;prompt.Enabled=true'):
   self.assertIn(line,s)
  self.assertNotIn('part:Destroy()',s)
 def test_stop_prevents_orphan_respawn(self):
  s=(ROOT/"EGGRUMBLE_FieldItemPickups.luau").read_text()
  self.assertIn('session.itemStop=function()',s)
  self.assertIn('active=false',s)
  self.assertIn('folder:Destroy()',s)
if __name__=="__main__":unittest.main()
