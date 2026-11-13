import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_compass import verify_source,verify_contract
class CompassSourceQA(unittest.TestCase):
 def test_original_source_27_byte_identical(self):self.assertTrue(verify_source())
 def test_new_client_ui_contract(self):self.assertTrue(verify_contract())
 def test_snapshot_is_authoritative(self):
  text=(ROOT/"src/client/D18MascotGuideRules.luau").read_text(encoding="utf8")
  self.assertIn('if carrying then "SCORE_PAD" else "EGG"',text)
  self.assertIn('update<=previousUpdate',text)
 def test_real_map_part_names(self):
  s=(ROOT/"src/server/MapBuilder.luau").read_text(encoding="utf8")
  self.assertIn('name .. "_EGG"',s);self.assertIn('name .. "_SCORE_PAD"',s)
 def test_original_raider_wind_and_guardian_trap_still_present(self):
  s=(ROOT/"src/server/Game.server.luau").read_text(encoding="utf8")
  self.assertIn("WIND_BURST",s);self.assertIn("PLACE_TRAP",s)
 def test_original_two_moving_neutrals_preserved(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  self.assertIn('Models.create("SPACE"',s)
  self.assertIn('Models.create("CELESTIAL"',s)
 def test_old_mascot_17_part_art_preserved(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")
  self.assertIn('Catalog.get("TRCA-BE-063")',s)
 def test_reject_fake_remote_action(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")+'\nremote:FireServer({action="SCORE"})'
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_no_studio_only_gate(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('RunService:IsStudio()','true')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_fixed_mascot_position_bearing(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('goal.Position-avatar.Position','goal.Position-state.origin.Position')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_no_live_camera_tracking(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('camera.CFrame.LookVector','state.origin.LookVector')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_hidden_guide_no_gui_destroy(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('guideGui:Destroy()','')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_legacy_fake_breadcrumb(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")+'\ndrawPath(current)'
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_unsafe_touch_capture(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('panel.Active=false','panel.Active=true')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_no_camera_heading_numeric_guard(self):
  s=(ROOT/"src/client/D18ObjectiveCompassRules.luau").read_text(encoding="utf8").replace('if not (finite(rx)','if false and (finite(rx)')
  with self.assertRaises(ValueError):verify_contract(compass=s)
 def test_reject_wrong_objective_label(self):
  s=(ROOT/"src/client/D18ObjectiveCompassRules.luau").read_text(encoding="utf8").replace('"じぶんの台の方向"','"敵の卵の方向"')
  with self.assertRaises(ValueError):verify_contract(compass=s)
 def test_reject_missing_rojo_module_mount(self):
  p=json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
  p["tree"]["StarterPlayer"]["StarterPlayerScripts"].pop("D18ObjectiveCompassRules")
  with self.assertRaises(ValueError):verify_contract(project=p)
 def test_one_remote_only_original_game(self):
  names=[]
  for p in (ROOT/"src").rglob("*.luau"):
   if 'Instance.new("RemoteEvent")' in p.read_text(encoding="utf8"):names.append(p.name)
  self.assertEqual(names,["Game.server.luau"])
if __name__=="__main__":unittest.main()

