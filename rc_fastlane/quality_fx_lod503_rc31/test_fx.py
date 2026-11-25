"""GQ503 original FX Budget and arena-only LocalScript inline contract tests."""
import unittest
from patch_fx import patch,unpatch,ADDITION,PURE,MARKER,SOURCE
SAMPLE='''--!strict
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local player=Players.LocalPlayer
if not RunService:IsStudio() then return end
local hitToast=Instance.new("TextLabel");hitToast.Name="ConfirmedHit042"
player:GetAttributeChangedSignal("EGGRUMBLE_ImpactSequence"):Connect(function() end)
RunService:BindToRenderStep("EGGRUMBLE_RealHitFeedback",1,function() end)
'''
class TestFX(unittest.TestCase):
 def test_inverse_byte_exact(self):self.assertEqual(unpatch(patch(SAMPLE)),SAMPLE)
 def test_double_injection_rejected(self):
  with self.assertRaisesRegex(ValueError,"DOUBLE"):patch(patch(SAMPLE))
 def test_needs_actual_confirmed_hit(self):
  with self.assertRaisesRegex(ValueError,"RED_ORIGINAL"):patch(SAMPLE.replace("ConfirmedHit042","GONE"))
 def test_client_class(self):self.assertTrue(SOURCE.endswith(".client.luau"))
 def test_seven_named_legacy_skill_parts(self):
  for key in ["WarGod_FlyingSlash","Mage_CrystalStorm","Assassin_ShadowAfterimage","Esper_PsiOrbit","MadScientist_RailShot","Beast_FangClaw","CurseMaster_SoulFlame"]:self.assertIn(key,ADDITION)
 def test_ultimate_flash_and_ring_never_targeted(self):
  self.assertNotIn("ULTIMATE_",ADDITION[ADDITION.index("local fxSecondaryNames={"):ADDITION.index("local function fxOriginalArena")])
  self.assertNotIn("FX_",ADDITION[ADDITION.index("local fxSecondaryNames={"):ADDITION.index("local function fxOriginalArena")])
  self.assertIn('kind~="SECONDARY"',PURE)
 def test_two_mode_original_arena_only(self):
  self.assertIn('current.Name=="TEAM_Arena"',ADDITION)
  self.assertIn('current.Name=="BATTLE_ROYALE_Arena"',ADDITION)
  self.assertIn('current.Parent.Name=="EGGRUMBLE_LOBBY_CASTLE_MODES_PREVIEW"',ADDITION)
 def test_touch_near_protection_and_reduced(self):
  self.assertIn("distance<=40",PURE)
  self.assertIn("if reduced then",PURE)
  self.assertIn("far=if touch then 85 else 130",PURE)
 def test_lod_hysteresis(self):self.assertIn("if wasHidden then far-9 else far+9",PURE)
 def test_bounded_work(self):
  self.assertIn("fxTracked>=128",ADDITION)
  self.assertIn("fxElapsed<.22",ADDITION)
 def test_no_remotes_or_damage(self):
  self.assertNotIn("RemoteEvent",ADDITION)
  self.assertNotIn("TakeDamage",ADDITION)
 def test_disconnect_and_restore(self):
  self.assertIn("fxHeartbeat:Disconnect()",ADDITION)
  self.assertIn("part.LocalTransparencyModifier=record.original",ADDITION)
if __name__=="__main__":unittest.main()
