"""Castle lane: no through-wall egg pickup and equal footprint."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CastleInterior(unittest.TestCase):
 def test_walls_and_door(self):
  s=(ROOT/"EGGRUMBLE_EnterableCastleInterior.luau").read_text()
  for item in ('local w=40;local depth=48;local height=18','{-12.5,12.5}','Vector3.new(15,height,3)','Vector3.new(10,12,1)','"CastleGate"','door.CanCollide=not gateOpen','"EggVault"','"SiegeCore"','MaxActivationDistance=9','Magnitude>11'):
   self.assertIn(item,s)
  self.assertNotIn('RemoteEvent',s)
  self.assertNotIn('MarketplaceService',s)
 def test_rojo_isolated(self):
  t=json.loads((ROOT/"EGGRUMBLE_CASTLE_INTERIOR_STUDIO.project.json").read_text())["tree"]["ServerScriptService"]
  self.assertEqual(set(t)-{"$className"},{"EGGRUMBLE_EnterableCastleInterior","EGGRUMBLE_CastleWalkthrough"})
  for k,v in t.items():
   if k!="$className":self.assertTrue((ROOT/v["$path"]).exists())
 def test_studio_walkthrough(self):
  s=(ROOT/"EGGRUMBLE_CastleWalkthrough.server.luau").read_text()
  self.assertIn('RunService:IsStudio()',s)
  self.assertIn('Instance.new("SpawnLocation")',s)
if __name__=="__main__":unittest.main()
