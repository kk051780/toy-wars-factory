"""WF32 standalone static checks; execute python -m unittest discover -s tests."""
from pathlib import Path
import json, unittest
root=Path(__file__).resolve().parents[1]
src=(root/"src/WF32Forest.server.lua").read_text()
rules=(root/"src/ForestGateRules.lua").read_text()
project=json.loads((root/"default.project.json").read_text())
class WF32Contract(unittest.TestCase):
 def test_studio_only(self):
  self.assertIn("if not RunService:IsStudio() then return end",src)
 def test_symmetric_routes(self):
  for s in ("{-96,96}","{-25,25}","SAFE_GROUND_ROAD_ALWAYS_OPEN","NORTH_SHORTCUT_ROAD","SOLID_ROOT_GATE"):
   self.assertIn(s,src)
 def test_real_collision_gate(self):
  self.assertIn("door.CanCollide=not opened",src)
  self.assertIn("prompt.Triggered:Connect(function(player)",src)
  self.assertIn("HumanoidRootPart",src)
  self.assertIn("Gate.activate(state",src)
 def test_rules(self):
  for s in ("Gate.OPEN_SECONDS=7","Gate.COOLDOWN_SECONDS=11","Gate.RADIUS=12","distance>Gate.RADIUS","now<s.nextAllowed"):
   self.assertIn(s,rules)
 def test_three_creature_types(self):
  for s in ("POKOSPO_VISUAL_MINION","TSUTAHUNTER_VISUAL_ELITE","MORINOS_VISUAL_BOSS","ELITE_TELEGRAPH_NO_DAMAGE"):
   self.assertIn(s,src)
 def test_single_authority(self):
  for value in ("RemoteEvent","DataStoreService","UpdateAsync(","FireServer(","TakeDamage(","MarketplaceService"):
   self.assertNotIn(value,src+rules)
 def test_wiring(self):
  t=project["tree"]["ServerScriptService"]
  self.assertEqual(t["ForestGateRules"]["$path"],"src/ForestGateRules.lua")
  self.assertEqual(t["WF32Forest"]["$path"],"src/WF32Forest.server.lua")
 def test_spawn_limits(self):
  for s in ("for i=1,6 do","for i=1,10 do","ticked<0.1"):
   self.assertIn(s,src)
if __name__=="__main__": unittest.main()
