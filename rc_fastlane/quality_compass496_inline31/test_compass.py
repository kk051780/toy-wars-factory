"""GQ496 source-derived inverse, double-owner, mobile budget, original attribution tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_compass import addition,original,patch,unpatch,FEATURE,AUTHOR_BLOB,blob

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL=ROOT/"_gq496_original/handoffs/EGGRUMBLE-GQ-OBJECTIVE-COMPASS-20261116/EGGRUMBLE_ObjectiveCompass.client.luau"
SAMPLE='''--!strict
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local player=Players.LocalPlayer
if not RunService:IsStudio() then return end
local hitToast=Instance.new("TextLabel"); hitToast.Name="ConfirmedHit042"
-- GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117
local fxSecondaryNames={}
'''
class Compass(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.a=original(ORIGINAL)
 def test_01_immutable_original(self):self.assertEqual(blob(ORIGINAL.read_bytes()),AUTHOR_BLOB)
 def test_02_source_byte_identity(self):
  patched=patch(SAMPLE,self.a)
  self.assertEqual(unpatch(patched,self.a),SAMPLE)
  self.assertIn(addition(self.a),patched)
  self.assertIn("GQ503_SEVEN_ROLE_SECONDARY_FX_LOD_20261117",patched)
 def test_03_second_compass_red(self):
  with self.assertRaisesRegex(ValueError,"ALREADY_PRESENT"):patch(patch(SAMPLE,self.a),self.a)
 def test_04_no_previous_hit_regression(self):
  with self.assertRaisesRegex(ValueError,"PREV_FX_HIT_LOST"):patch(SAMPLE.replace("ConfirmedHit042","LOST"),self.a)
 def test_05_only_one_screen_and_marker(self):
  self.assertEqual(self.a.count('Instance.new("ScreenGui")'),1)
  self.assertEqual(self.a.count('Instance.new("BillboardGui")'),1)
  self.assertIn("marker.AlwaysOnTop=false",self.a)
 def test_06_lobby_hidden_and_kill_switch(self):
  for s in ('if not RunService:IsStudio() then return end',
            'toggle.Visible=false;bar.Visible=false',
            'player:GetAttribute("EGGRUMBLE_Eliminated")==true',
            'marker.Enabled=false;marker.Adornee=nil'):
   self.assertIn(s,self.a)
 def test_07_enemy_mode_and_return_home(self):
  for s in ("BATTLE_ROYALE",'mode~="TEAM"',
            "if own==other then return false end",
            "if homeSelected then",
            'return home,"自城へ帰還（手動）"',
            "NEUTRAL_BOSS_STONE_GIANT","EGGRUMBLE_FieldItems"):
   self.assertIn(s,self.a)
 def test_08_small_mobile_throttle(self):
  for s in ("UPDATE_SECONDS = 0.8","INITIAL_SECONDS = 18",
            "camera.ViewportSize.X",
            "math.min(294,math.max(90,width-132))",
            "RunService.Heartbeat:Connect"):
   self.assertIn(s,self.a)
 def test_09_no_new_authorities(self):
  for s in ("FireServer(","InvokeServer(","RemoteEvent","DataStore",
            "TakeDamage(","MarketplaceService","ProximityPrompt.Triggered"):
   self.assertNotIn(s,self.a)
 def test_10_source_marker_unique(self):
  out=patch(SAMPLE,self.a)
  self.assertEqual(out.count(FEATURE),1)
  self.assertEqual(out.count('gui.Name="EGGRUMBLE_GQ_ObjectiveCompass"'),1)
  self.assertEqual(out.count('if playerGui:FindFirstChild("EGGRUMBLE_GQ_ObjectiveCompass") then return end'),1)
if __name__=="__main__":unittest.main()
