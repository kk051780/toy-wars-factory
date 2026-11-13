import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_g7 import check_source,check_contract
class G7WorldQA(unittest.TestCase):
 def test_all_5_actual_source_sha(self):self.assertTrue(check_source())
 def test_showroom_and_director_contract(self):self.assertTrue(check_contract())
 def test_three_realm_cards_meaningful(self):
  doc=(ROOT/"FIELD_CARDS.md").read_text(encoding="utf8")
  for x in ("WF-13","WF-14","WF-15","S1","S2","S3","3秒理解","Counterplay","Fail-safe","7-sec clip"):
   self.assertIn(x,doc)
 def test_three_named_3d_part_lists(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")
  for name in ("G7_SPACE_STAR_","G7_HEAVEN_CLOUD_","G7_ABYSS_OBSIDIAN_SPIRE_","G7_HEAVEN_SKY_CASTLE"):
   self.assertIn(name,s)
 def test_three_free_permanent_bridges(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")
  self.assertEqual(s.count('_PERMANENT_BRIDGE"'),3)
 def test_private_studio_only(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")
  self.assertIn('if not RunService:IsStudio() then return end',s)
 def test_no_actual_game_server_in_showroom(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")
  self.assertNotIn('TrapRaidersS1Remote',s)
 def test_reject_world_without_studio_gate(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8").replace('RunService:IsStudio()','true')
  with self.assertRaises(ValueError):check_contract(world=s)
 def test_reject_world_adds_new_remote(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")+'\\nInstance.new("RemoteEvent")'
  with self.assertRaises(ValueError):check_contract(world=s)
 def test_reject_world_enables_real_gravity_change(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")+'\\nWorkspace.Gravity=50'
  with self.assertRaises(ValueError):check_contract(world=s)
 def test_reject_no_open_sky_bridge(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8").replace('G7_HEAVEN_PERMANENT_BRIDGE','G7_NO_SKY_ROUTE')
  with self.assertRaises(ValueError):check_contract(world=s)
 def test_reject_world_pays_items(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")+'\\ngame:GetService("MarketplaceService")'
  with self.assertRaises(ValueError):check_contract(world=s)
 def test_reject_world_kills_players(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8")+'\\nHumanoid:TakeDamage(99)'
  with self.assertRaises(ValueError):check_contract(world=s)
 def test_reject_director_paid_unfair_event(self):
  s=(ROOT/"src/RiftDirector.luau").read_text(encoding="utf8").replace('server_gameplay_bonus=false','server_gameplay_bonus=true')
  with self.assertRaises(ValueError):check_contract(director=s)
 def test_reject_director_no_persistent_ground_path(self):
  s=(ROOT/"src/RiftDirector.luau").read_text(encoding="utf8").replace('permanent_ground_route_open=true','permanent_ground_route_open=false')
  with self.assertRaises(ValueError):check_contract(director=s)
 def test_reject_director_active_change_too_long(self):
  s=(ROOT/"src/RiftDirector.luau").read_text(encoding="utf8").replace('D.ACTIVE_SECONDS=25','D.ACTIVE_SECONDS=999')
  with self.assertRaises(ValueError):check_contract(director=s)
 def test_reject_exclusive_heaven_gate(self):
  s=(ROOT/"src/FieldShowcase.server.luau").read_text(encoding="utf8").replace('G7_SPACE_PERMANENT_BRIDGE','PAID_ONLY')
  with self.assertRaises(ValueError):check_contract(world=s)
 def test_reject_bad_rojo_mount(self):
  p=json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
  p["tree"]["ServerScriptService"]["G7_Fantasy_Realms"].pop("RiftDirector")
  with self.assertRaises(KeyError):check_contract(project=p)
 def test_card_metadata_not_implemented_gameplay(self):
  cards=(ROOT/"FIELD_CARDS.md").read_text(encoding="utf8")
  self.assertIn('no actual zero-G',cards.lower().replace('gravity','zero-g'))
if __name__=="__main__":unittest.main()

