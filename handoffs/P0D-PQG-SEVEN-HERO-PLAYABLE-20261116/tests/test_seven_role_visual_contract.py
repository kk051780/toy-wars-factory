"""CHARACTER art: seven distinguishable silhouettes without modifying combat."""
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SevenRoleVisual(unittest.TestCase):
 def test_seven_distinct_weapon_shapes(self):
  s=(ROOT/"EGGRUMBLE_SevenRoleVisualKit.luau").read_text()
  for role in ("WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"):
   self.assertIn('id="'+role+'"',s)
  for shape in ("BLADE","STAFF","DUAL","CUBE","GUN","HORN","CURSE"):
   self.assertIn('entry.shape=="'+shape+'"',s)
  for weapon in ("GreatSwordBlade","ArcaneGem","DaggerBlade","TelekineticCube","ScienceGunBarrel","BeastHorn","CurseOrb"):
   self.assertIn(weapon,s)
 def test_no_live_combat_or_remote(self):
  s=(ROOT/"EGGRUMBLE_SevenRoleVisualKit.luau").read_text()
  for forbidden in ("TakeDamage","RemoteEvent","DataStoreService","MarketplaceService"):
   self.assertNotIn(forbidden,s)
  self.assertIn('RunService:IsStudio()',s)
 def test_gallery_is_separate(self):
  tree=json.loads((ROOT/"EGGRUMBLE_SEVEN_ROLE_VISUAL_STUDIO.project.json").read_text())["tree"]["ServerScriptService"]
  self.assertEqual(set(tree)-{"$className"},{"EGGRUMBLE_SevenRoleVisualKit","EGGRUMBLE_SevenRoleGallery"})
  for k,v in tree.items():
   if k!="$className":self.assertTrue((ROOT/v["$path"]).exists())
if __name__=="__main__":unittest.main()
