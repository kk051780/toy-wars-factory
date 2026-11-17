import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_hit_chain import INSERT,REPLACE,TEXT_ANCHOR,patch,unpatch,START_MARKER

BASE='''local pulse=0
local RECENT_CD=.12
local now=os.clock()
if reduced() then return end
hitToast.Name="ConfirmedHit042"
player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")
 local now=os.clock()
 local chainType=1
'''+TEXT_ANCHOR+'''if thisPulse==pulse and hitToast.Parent then hitToast.Visible=false end
'''
class GQ8ChainTest(unittest.TestCase):
 def test_round_trip(self):
  changed=patch(BASE)
  self.assertEqual(unpatch(changed),BASE)
  self.assertEqual(changed.count("hitToast.Name"),1)
 def test_mode_reset_and_bounds(self):
  changed=patch(BASE)
  self.assertIn('GetAttributeChangedSignal("EGGRUMBLE_QueuedMode")',changed)
  self.assertIn('now-lastChainAt>1.6',changed)
  self.assertIn('chainHits=math.min(30,chainHits+1)',changed)
 def test_no_duplication_of_score_owner(self):
  changed=patch(BASE)
  self.assertNotIn('RemoteEvent',changed)
  self.assertNotIn('TakeDamage',changed)
  self.assertNotIn('SetAttribute("EGGRUMBLE_Combo"',changed)
  self.assertIn('hitToast.Text="CHAIN x"..tostring(chainCount)',changed)
 def test_reapply_rejected(self):
  with self.assertRaisesRegex(ValueError,"RED_DOUBLE_APPLY"):patch(patch(BASE))
 def test_corrupt_original_rejected(self):
  with self.assertRaisesRegex(ValueError,"RED_HIT042_CLIENT_ANCHOR_DRIFT"):patch(BASE.replace(TEXT_ANCHOR,""))
 def test_bad_rollback_rejected(self):
  with self.assertRaisesRegex(ValueError,"RED_BAD_REVERSE"):unpatch(BASE)
 def test_mutation_rollback_detected(self):
  bad=patch(BASE).replace("chainHits=math.min(30,chainHits+1)","chainHits+=999",1)
  with self.assertRaisesRegex(ValueError,"RED_BAD_REVERSE"):unpatch(bad)
 def test_no_extra_local_script(self):
  self.assertEqual(INSERT.count(START_MARKER),1)
  self.assertIn("chainHits=0",INSERT)
if __name__=="__main__":unittest.main()
