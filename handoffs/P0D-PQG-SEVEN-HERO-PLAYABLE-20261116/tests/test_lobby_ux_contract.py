"""Independent LOBBY UX source contract."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LobbyUX(unittest.TestCase):
 def test_seven_roles_and_two_gates(self):
  s=(ROOT/"EGGRUMBLE_LobbyUXPreview.luau").read_text()
  for role in ("武神","魔法使い","暗殺者","超能力者","マッドサイエンティスト","魔獣使い","呪術師"):
   self.assertIn(role,s)
  self.assertIn('name="TEAM"',s)
  self.assertIn('name="BATTLE_ROYALE"',s)
  self.assertIn('roles=7,portals=2',s)
 def test_small_world_prompts_no_forced_hud_or_queue(self):
  s=(ROOT/"EGGRUMBLE_LobbyUXPreview.luau").read_text()
  self.assertIn('ui.MaxDistance=42',s)
  self.assertIn('ui.AlwaysOnTop=false',s)
  self.assertIn('MaxActivationDistance=9',s)
  for forbidden in ("ScreenGui","TeleportService","RemoteEvent","MarketplaceService"):
   self.assertNotIn(forbidden,s)
 def test_standalone_project(self):
  tree=json.loads((ROOT/"EGGRUMBLE_LOBBY_UX_STUDIO.project.json").read_text())["tree"]["ServerScriptService"]
  self.assertEqual(set(tree)-{"$className"},{"EGGRUMBLE_LobbyUXPreview","EGGRUMBLE_LobbyUXStandalone"})
  for k,v in tree.items():
   if k!="$className":self.assertTrue((ROOT/v["$path"]).exists())
if __name__=="__main__":unittest.main()
