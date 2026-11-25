import unittest
import select_cast_cue as mod

SAMPLE='''--!strict
local player=Players.LocalPlayer
local TweenService=game:GetService("TweenService")
mark.Parent=gui
local function reduced():boolean
 return false
end
player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(function()
end)
'''

class TestServerAcceptedCastCue(unittest.TestCase):
 def test_exact_inverse(self):
  on=mod.patch(SAMPLE)
  self.assertEqual(mod.undo(on),SAMPLE)
  mod.safety_checks(on)
 def test_prevents_double_insertion(self):
  with self.assertRaisesRegex(ValueError,"RED_ALREADY_SELECTED"):
   mod.patch(mod.patch(SAMPLE))
 def test_original_hit_signal_not_replaced(self):
  on=mod.patch(SAMPLE)
  self.assertEqual(on.count("EGGRUMBLE_ImpactSequence"),1)
  self.assertIn('GetAttributeChangedSignal("EGGRUMBLE_SkillCastSignature")',on)
  self.assertIn('if not tones[role] then return end',on)
 def test_gq504_existing_audio_kept_byte_exact(self):
  audio='''-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117
player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(confirmedHit)
-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117
'''
  before=SAMPLE+audio
  chosen=mod.patch(before)
  self.assertEqual(mod.undo(chosen),before)
  mod.safety_checks(chosen)
  self.assertEqual(chosen.count('player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")'),2)
  self.assertTrue(chosen.endswith(audio))
 def test_gq504_duplicate_audio_marker_fails_closed(self):
  audio='''-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_BEGIN_20261117
player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(confirmedHit)
-- GQ504_CONFIRMED_HIT_AUDIO_INLINE_END_20261117
'''
  with self.assertRaisesRegex(ValueError,"RED_DUPLICATE_AUDIO_OWNER"):
   mod.patch(SAMPLE+audio+audio)
 def test_second_hit_listener_without_original_audio_owner_is_rejected(self):
  mutant=SAMPLE+'player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(confirmedHit)'
  with self.assertRaisesRegex(ValueError,"RED_SOURCE_CONTRACT"):
   mod.patch(mutant)
 def test_no_gameplay_authority(self):
  for forbidden in ("FireServer(", "TakeDamage(", "RemoteEvent", "DataStoreService", ":Activate("):
   self.assertNotIn(forbidden,mod.INSERT)
 def test_fail_closed_anchor_drift(self):
  with self.assertRaisesRegex(ValueError,"RED_ANCHOR_DRIFT"):mod.patch(SAMPLE.replace("mark.Parent=gui","mark.Parent=nil"))
 def test_fail_closed_hit_path_change(self):
  with self.assertRaisesRegex(ValueError,"RED_SOURCE_CONTRACT"):mod.patch(SAMPLE.replace('GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence")',"GetAttributeChangedSignal(\"Different\")"))
 def test_mutant_visible_always(self):
  mutant=mod.patch(SAMPLE).replace("castCue.Visible=false","castCue.Visible=true")
  with self.assertRaisesRegex(ValueError,"RED_OFF_SOURCE_DRIFT"):
   mod.undo(mutant)
 def test_git_blob_known_content(self):
  self.assertEqual(mod.git_blob(b"hello"),"b6fc4c620b67d95f953a5c1c1230aaab5db5a1b0")
if __name__=="__main__":unittest.main()
