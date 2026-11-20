"""Independent item-lane SOURCE contract: 3 real consumables, no economy or RC integration."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestItemLane(unittest.TestCase):
 def test_rojo_only_item_lane(self):
  tree=json.loads((ROOT/"EGGRUMBLE_ITEM_STUDIO.project.json").read_text())["tree"]["ServerScriptService"]
  self.assertEqual(set(tree)-{"$className"},{"EGGRUMBLE_FieldItemPickups","EGGRUMBLE_FieldItemPreview"})
  for v in tree.values():
   if isinstance(v,dict):self.assertTrue((ROOT/v["$path"]).is_file())
 def test_pickups_server_validated(self):
  src=(ROOT/"EGGRUMBLE_FieldItemPickups.luau").read_text()
  for s in ['RunService:IsStudio()','session.rules.phase=="ACTIVE"','castle.alive==true','prompt.RequiresLineOfSight=true','(root.Position-part.Position).Magnitude>10','consumed[id]=true','lastUse[key]=now','hum.Health=math.min','hum.WalkSpeed=math.max','Instance.new("ForceField")']:
   self.assertIn(s,src)
  for forbidden in ["MarketplaceService","DataStoreService","RemoteEvent"]:
   self.assertNotIn(forbidden,src)
 def test_nine_world_spawns(self):
  src=(ROOT/"EGGRUMBLE_FieldItemPreview.server.luau").read_text()
  self.assertIn("for i=1,9 do",src)
  self.assertIn("Items.start(",src)
  self.assertIn('RunService:IsStudio()',src)

if __name__=="__main__":
 unittest.main()
