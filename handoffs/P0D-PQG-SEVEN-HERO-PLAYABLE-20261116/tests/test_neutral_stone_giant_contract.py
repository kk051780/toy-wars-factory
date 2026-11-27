"""Independent NEUTRAL boss static source checks."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NeutralBoss(unittest.TestCase):
 def test_studio_project_is_isolated(self):
  tree=json.loads((ROOT/"EGGRUMBLE_NEUTRAL_BOSS_STUDIO.project.json").read_text())["tree"]["ServerScriptService"]
  self.assertEqual(set(tree)-{"$className"},{"EGGRUMBLE_NeutralStoneGiant","EGGRUMBLE_NeutralBossPreview"})
  for name,item in tree.items():
   if name!="$className":self.assertTrue((ROOT/item["$path"]).exists())
 def test_telegraph_and_damage_server_authority(self):
  s=(ROOT/"EGGRUMBLE_NeutralStoneGiant.luau").read_text()
  for phrase in ('RunService:IsStudio()','GroundTelegraph','task.wait(2)','h:TakeDamage(28)','d<=11','math.abs(root.Position.Y-at.Y)<=8','health=math.max(0,health-amount)','root.Position-eye.Position','params.FilterDescendantsInstances={c,model}'):
   self.assertIn(phrase,s)
  for forbidden in ('RemoteEvent','MarketplaceService','DataStoreService'):
   self.assertNotIn(forbidden,s)
 def test_standalone_spawn(self):
  s=(ROOT/"EGGRUMBLE_NeutralBossPreview.server.luau").read_text()
  self.assertIn('Boss.spawn(workspace',s)
  self.assertIn('Instance.new("SpawnLocation")',s)
if __name__=="__main__":unittest.main()
