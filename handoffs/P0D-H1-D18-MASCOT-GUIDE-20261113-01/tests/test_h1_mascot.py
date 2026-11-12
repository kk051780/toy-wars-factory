import copy,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_h1_mascot import verify_manifest,verify_original,verify_contract
class TestH1Mascot(unittest.TestCase):
 def test_original_source_exact_24(self):self.assertEqual(len(verify_original()),24)
 def test_manifest_27(self):self.assertEqual(len(verify_manifest()),27)
 def test_valid_contract(self):self.assertTrue(verify_contract())
 def test_read_only_map_goal_exists(self):
  src=(ROOT/"src/server/MapBuilder.luau").read_text(encoding="utf8")
  for name in ('"_EGG"','"_SCORE_PAD"','"_SPAWN"','"TRAP_RAIDERS_S1"'):
   self.assertIn(name,src)
 def test_displayed_mascot_canonical(self):
  cat=(ROOT/"src/client/D18Batch8Catalog.luau").read_text(encoding="utf8")
  self.assertIn('TRCA-BE-063',cat)
  self.assertIn('熔炉の角竜',cat)
 def test_private_studio_only(self):
  src=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")
  self.assertIn('if not RunService:IsStudio() then return end',src)
 def test_reject_fake_new_remote(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8")+'\nremote:FireServer({action="CAPTURE"})'
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_no_studio_guard(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('RunService:IsStudio()','true')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_collision(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('CanCollide=false','CanCollide=true')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_no_prompt(self):
  s=(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8").replace('ProximityPrompt','InertPrompt')
  with self.assertRaises(ValueError):verify_contract(client=s)
 def test_reject_snapshots_out_of_order(self):
  s=(ROOT/"src/client/D18MascotGuideRules.luau").read_text(encoding="utf8").replace('update<=previousUpdate','false')
  with self.assertRaises(ValueError):verify_contract(rules=s)
 def test_reject_fake_team(self):
  s=(ROOT/"src/client/D18MascotGuideRules.luau").read_text(encoding="utf8").replace('s.team~="RED" and s.team~="BLUE"','false')
  with self.assertRaises(ValueError):verify_contract(rules=s)
 def test_reject_wrong_egg_goal(self):
  s=(ROOT/"src/client/D18MascotGuideRules.luau").read_text(encoding="utf8").replace('if carrying then "SCORE_PAD" else "EGG"','if carrying then "EGG" else "EGG"')
  with self.assertRaises(ValueError):verify_contract(rules=s)
 def test_reject_wrong_project(self):
  p=json.loads((ROOT/"default.project.json").read_text(encoding="utf8"))
  p["tree"]["StarterPlayer"]["StarterPlayerScripts"].pop("D18MascotGuide")
  with self.assertRaises(ValueError):verify_contract(project=p)
 def test_no_extra_remote(self):
  self.assertNotIn('RemoteEvent',(ROOT/"src/client/D18MascotGuide.client.luau").read_text(encoding="utf8"))
if __name__=="__main__":unittest.main()
