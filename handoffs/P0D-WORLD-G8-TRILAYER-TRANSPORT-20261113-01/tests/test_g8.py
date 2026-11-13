import pathlib,json,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_g8 import source,contract
W=(ROOT/"src/G8World.server.luau").read_text(encoding="utf8")
R=(ROOT/"src/G8TravelRules.luau").read_text(encoding="utf8")
class G8Tests(unittest.TestCase):
 def test_lock_source_five(self):self.assertTrue(source())
 def test_policy_good(self):self.assertTrue(contract())
 def test_invalid_no_studio_guard(self):
  with self.assertRaises(ValueError):contract(world=W.replace('if not RunService:IsStudio() then return end','if true then return end'))
 def test_invalid_missing_remote_safety(self):
  with self.assertRaises(ValueError):contract(world=W+'\nInstance.new("RemoteEvent")')
 def test_invalid_commerce(self):
  with self.assertRaises(ValueError):contract(world=W+'\ngame:GetService("MarketplaceService")')
 def test_invalid_damage(self):
  with self.assertRaises(ValueError):contract(world=W+'\nHumanoid:TakeDamage(100)')
 def test_invalid_gravity(self):
  with self.assertRaises(ValueError):contract(world=W+'\nWorkspace.Gravity=0')
 def test_invalid_arbitrary_destination(self):
  with self.assertRaises(ValueError):contract(world=W.replace('Rules.destination(link.to)','{x=999,y=999,z=999}'))
 def test_invalid_no_actual_range(self):
  with self.assertRaises(ValueError):contract(world=W.replace('delta:Dot(delta)','0'))
 def test_invalid_no_movement_validation(self):
  with self.assertRaises(ValueError):contract(world=W.replace('Rules.validate(link.from,link.to','false or ('))
 def test_invalid_cooldown_policy(self):
  with self.assertRaises(ValueError):contract(rules=R.replace('R.COOLDOWN=1.6','R.COOLDOWN=0'))
 def test_invalid_distance_policy(self):
  with self.assertRaises(ValueError):contract(rules=R.replace('R.MAX_DISTANCE_SQUARED=196','R.MAX_DISTANCE_SQUARED=1e8'))
 def test_invalid_unlimited_graph(self):
  with self.assertRaises(ValueError):contract(rules=R.replace('PORT={SEA=true}','PORT={SEA=true,SKY=true}'))
 def test_invalid_no_sea_return(self):
  with self.assertRaises(ValueError):contract(world=W.replace('{from="SEA",to="PORT",short="港にもどる",dx=-14},',''))
 def test_invalid_no_sky_return(self):
  with self.assertRaises(ValueError):contract(world=W.replace('{from="SKY",to="PORT",short="港にもどる",dx=14}',''))
 def test_invalid_health_check(self):
  with self.assertRaises(ValueError):contract(rules=R.replace('health<=0','health<-100'))
 def test_invalid_no_server_character_check(self):
  with self.assertRaises(ValueError):contract(world=W.replace('FindFirstChild("HumanoidRootPart")','FindFirstChild("Torso")'))
 def test_invalid_safety_rails_removed(self):
  with self.assertRaises(ValueError):contract(world=W.replace('G8_"..id.."_SIDE_RAIL_','G8_"..id.."_NONE_'))
 def test_invalid_no_real_trip_trigger(self):
  with self.assertRaises(ValueError):contract(world=W.replace('prompt.Triggered:Connect(function(player)','prompt.PromptShown:Connect(function(player)'))
 def test_invalid_no_client_touch_prompt(self):
  with self.assertRaises(ValueError):contract(world=W.replace('prompt.KeyboardKeyCode=Enum.KeyCode.E','prompt.KeyboardKeyCode=nil'))
 def test_invalid_bad_rojo_mount(self):
  p=json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
  p["tree"]["ServerScriptService"]["G8_Three_Level_Demo"].pop("G8World")
  with self.assertRaises(KeyError):contract(project=p)
 def test_story_is_not_H1_egg_game(self):
  self.assertIn("not h1", (ROOT/"README.md").read_text(encoding="utf8").lower())
if __name__=="__main__":unittest.main()

