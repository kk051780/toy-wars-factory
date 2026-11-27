"""FIELD lane only: standalone visible obstacles, walkable bridges, limited part count."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class FieldKitContract(unittest.TestCase):
 def test_project_isolation(self):
  data=json.loads((ROOT/"EGGRUMBLE_FIELD_ART_STUDIO.project.json").read_text())
  children=data["tree"]["ServerScriptService"]
  self.assertEqual(set(children)-{"$className"},{"EGGRUMBLE_ValleyLandmarkKit","EGGRUMBLE_ValleyArtPreview"})
  for key,val in children.items():
   if key!="$className":self.assertTrue((ROOT/val["$path"]).is_file())
 def test_traversable_and_art_budget(self):
  s=(ROOT/"EGGRUMBLE_ValleyLandmarkKit.luau").read_text()
  for key in ('local width=300','"RaidRoad"','"RiverSurface"','"BridgeDeck_"','"BridgeRail_"','"BorderCliff"','"TreeCrown"','"RaidBanner"','for i=1,22 do','for i=1,12 do','noInvisibleWalls=true'):
   self.assertIn(key,s)
  self.assertNotIn('Instance.new("MeshPart")',s)
  self.assertNotIn('MarketplaceService',s)
 def test_private_spawn(self):
  s=(ROOT/"EGGRUMBLE_ValleyArtPreview.server.luau").read_text()
  self.assertIn('RunService:IsStudio()',s)
  self.assertIn('Kit.build(workspace',s)
  self.assertIn('Instance.new("SpawnLocation")',s)
if __name__=="__main__":unittest.main()
