import pathlib,sys,json,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_unified import verify_source,geometry,contract
class H1UnifiedTest(unittest.TestCase):
 def test_manifest_source_28(self):self.assertTrue(verify_source())
 def test_geometry_six_and_no_castle_wall_overlap(self):self.assertEqual(len(geometry()),6)
 def test_studio_local_contract(self):self.assertTrue(contract())
 def test_reject_original_sea_blocking_solid_walls(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  bad=s.replace('Vector3.new(-72,0,-55),Vector3.new(72,0,-55)','Vector3.new(-99,0,-45),Vector3.new(99,0,-45)')
  with self.assertRaises(ValueError):geometry(bad)
 def test_reject_original_sky_wall_intersection(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  bad=s.replace('Vector3.new(-86,0,32.5),Vector3.new(-46,16,32.5)','Vector3.new(-91,0,43),Vector3.new(-52,16,43)')
  with self.assertRaises(ValueError):geometry(bad)
 def test_reject_absent_sea_connector(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  with self.assertRaises(ValueError):geometry(s.replace('path("SEA_ENTRY_RED"','path("DELETED_ENTRY"'))
 def test_reject_impossible_steep_sky(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  with self.assertRaises(ValueError):geometry(s.replace('Vector3.new(-86,0,32.5),Vector3.new(-46,16,32.5)','Vector3.new(-66,0,32.5),Vector3.new(-46,16,32.5)'))
 def test_reject_route_outside_bounds(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  with self.assertRaises(ValueError):geometry(s.replace('Vector3.new(-72,0,-55)','Vector3.new(-172,0,-55)'))
 def test_reject_sea_front_wall_collision(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  with self.assertRaises(ValueError):geometry(s.replace('Vector3.new(72,0,-20)','Vector3.new(106,0,-44)'))
 def test_reject_missing_free_route_attribute(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")
  with self.assertRaises(ValueError):geometry(s.replace('FreeToAllRoles','GatedToCertainRole'))
 def test_reject_remote_creation_world(self):
  s=(ROOT/"src/server/H1FunWorld.server.luau").read_text(encoding="utf8")+'\nInstance.new("RemoteEvent")'
  with self.assertRaises(ValueError):geometry(s)
 def test_reject_local_client_authority(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")+'\nremote:FireServer({action="WIN"})'
  with self.assertRaises(ValueError):contract(local=s)
 def test_reject_studio_gate_drop(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('if not RunService:IsStudio() then return end','if false then return end')
  with self.assertRaises(ValueError):contract(local=s)
 def test_reject_unbounded_hint_redraw(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('state.lastHintName~=current.partName','true')
  with self.assertRaises(ValueError):contract(local=s)
 def test_reject_wrong_egg_guide_on_carrying(self):
  s=(ROOT/"src/client/D18MascotGuideRules.luau").read_text(encoding="utf8").replace('if carrying then "SCORE_PAD" else "EGG"','if carrying then "EGG" else "EGG"')
  with self.assertRaises(ValueError):contract(rules=s)
 def test_reject_deleted_guide_project_mount(self):
  p=json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
  p["tree"]["StarterPlayer"]["StarterPlayerScripts"].pop("D18MascotGuide")
  with self.assertRaises(ValueError):contract(project=p)
 def test_original_egg_scorepads_unmodified(self):
  src=(ROOT/"src/server/MapBuilder.luau").read_text(encoding="utf8")
  for tag in ('"_EGG"','"_SCORE_PAD"','"_SPAWN"','"TRAP_RAIDERS_S1"'):
   self.assertIn(tag,src)
 def test_two_real_active_roles_only(self):
  src=(ROOT/"src/shared/Config.luau").read_text(encoding="utf8")
  self.assertIn('RAIDER = 100',src);self.assertIn('GUARDIAN = 135',src)
 def test_one_original_remote_owner(self):
  original=(ROOT/"src/server/Game.server.luau").read_text(encoding="utf8")
  self.assertIn('local remote = Instance.new("RemoteEvent")',original)
  for p in (ROOT/"src/server").rglob("*.luau"):
   if p.name!="Game.server.luau":self.assertNotIn('Instance.new("RemoteEvent")',p.read_text(encoding="utf8"))
if __name__=="__main__":unittest.main()
