"""Independent battle feel lane contract."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MusouCombo(unittest.TestCase):
 def test_server_combat(self):
  s=(ROOT/"EGGRUMBLE_MusouComboPreview.luau").read_text()
  for phrase in ('COMBO_DAMAGE={18,22,30}','COMBO_RADIUS={8,9,12}','COMBO_ANGLE={105,120,150}','COMBO_WINDOW=1.25','if count>=12 then break end','RaycastParams.new()','h:TakeDamage(COMBO_DAMAGE[step])','EGGRUMBLE_NeutralTarget'):
   self.assertIn(phrase,s)
  for forbidden in ('RemoteEvent','MarketplaceService','DataStoreService'):
   self.assertNotIn(forbidden,s)
 def test_playtest_has_targets(self):
  s=(ROOT/"EGGRUMBLE_MusouComboStandalone.server.luau").read_text()
  self.assertIn('for i=1,18 do',s)
  self.assertIn('Combo.attack(player,targets,scene)',s)
  self.assertIn('RunService:IsStudio()',s)
 def test_standalone_project(self):
  tree=json.loads((ROOT/"EGGRUMBLE_MUSOU_COMBO_STUDIO.project.json").read_text())["tree"]["ServerScriptService"]
  self.assertEqual(set(tree)-{"$className"},{"EGGRUMBLE_MusouComboPreview","EGGRUMBLE_MusouComboStandalone"})
  for k,v in tree.items():
   if k!="$className":self.assertTrue((ROOT/v["$path"]).exists())
if __name__=="__main__":unittest.main()
